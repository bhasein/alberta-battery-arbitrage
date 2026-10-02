"""Reusable linear battery-dispatch optimization and validation helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import lil_matrix


@dataclass(frozen=True)
class BatteryConfig:
    """Physical and variable-cost assumptions for an energy-storage asset."""

    power_mw: float = 100.0
    energy_mwh: float = 200.0
    round_trip_efficiency: float = 0.88
    degradation_cost_per_mwh: float = 2.0
    initial_soc_mwh: float | None = None
    terminal_soc_mwh: float | None = None
    self_discharge_per_hour: float = 0.0

    @property
    def charge_efficiency(self) -> float:
        return float(np.sqrt(self.round_trip_efficiency))

    @property
    def discharge_efficiency(self) -> float:
        return float(np.sqrt(self.round_trip_efficiency))

    @property
    def resolved_initial_soc(self) -> float:
        if self.initial_soc_mwh is None:
            return 0.5 * self.energy_mwh
        return float(self.initial_soc_mwh)

    @property
    def resolved_terminal_soc(self) -> float:
        if self.terminal_soc_mwh is None:
            return 0.5 * self.energy_mwh
        return float(self.terminal_soc_mwh)


REFERENCE_BATTERY = BatteryConfig(
    power_mw=100.0,
    energy_mwh=200.0,
    round_trip_efficiency=0.88,
    degradation_cost_per_mwh=2.0,
    initial_soc_mwh=100.0,
    terminal_soc_mwh=100.0,
)


def optimize_battery_dispatch(
    prices: pd.Series,
    config: BatteryConfig,
    timestep_hours: float = 1.0,
    max_discharge_mwh: float | None = None,
) -> pd.DataFrame:
    """Maximize degradation-adjusted arbitrage margin over one price horizon."""

    prices = pd.Series(prices).astype(float)
    if prices.empty:
        raise ValueError("At least one price is required.")
    if prices.isna().any():
        raise ValueError("Prices contain missing values.")
    if timestep_hours <= 0:
        raise ValueError("timestep_hours must be positive.")
    if max_discharge_mwh is not None and max_discharge_mwh < 0:
        raise ValueError("max_discharge_mwh cannot be negative.")

    periods = len(prices)
    charge_slice = slice(0, periods)
    discharge_slice = slice(periods, 2 * periods)
    soc_slice = slice(2 * periods, 3 * periods + 1)
    variable_count = 3 * periods + 1

    objective = np.zeros(variable_count)
    objective[charge_slice] = (
        prices.to_numpy() + config.degradation_cost_per_mwh
    ) * timestep_hours
    objective[discharge_slice] = (
        -prices.to_numpy() + config.degradation_cost_per_mwh
    ) * timestep_hours

    equality = lil_matrix((periods + 2, variable_count), dtype=float)
    target = np.zeros(periods + 2)
    equality[0, soc_slice.start] = 1.0
    target[0] = config.resolved_initial_soc

    carry = (1.0 - config.self_discharge_per_hour) ** timestep_hours
    for period in range(periods):
        row = period + 1
        equality[row, soc_slice.start + period + 1] = 1.0
        equality[row, soc_slice.start + period] = -carry
        equality[row, charge_slice.start + period] = (
            -config.charge_efficiency * timestep_hours
        )
        equality[row, discharge_slice.start + period] = (
            timestep_hours / config.discharge_efficiency
        )

    equality[-1, soc_slice.stop - 1] = 1.0
    target[-1] = config.resolved_terminal_soc

    upper_bound = None
    upper_target = None
    if max_discharge_mwh is not None:
        upper_bound = lil_matrix((1, variable_count), dtype=float)
        upper_bound[0, discharge_slice] = timestep_hours
        upper_target = np.array([max_discharge_mwh], dtype=float)

    bounds = (
        [(0.0, config.power_mw)] * periods
        + [(0.0, config.power_mw)] * periods
        + [(0.0, config.energy_mwh)] * (periods + 1)
    )

    solution = linprog(
        c=objective,
        A_ub=(upper_bound.tocsr() if upper_bound is not None else None),
        b_ub=upper_target,
        A_eq=equality.tocsr(),
        b_eq=target,
        bounds=bounds,
        method="highs",
    )
    if not solution.success:
        raise RuntimeError(f"Optimization failed: {solution.message}")

    charge = solution.x[charge_slice]
    discharge = solution.x[discharge_slice]
    soc = solution.x[soc_slice]
    gross_margin = prices.to_numpy() * (discharge - charge) * timestep_hours
    degradation_cost = (
        config.degradation_cost_per_mwh
        * (charge + discharge)
        * timestep_hours
    )

    return pd.DataFrame(
        {
            "price_cad_mwh": prices.to_numpy(),
            "charge_mw": charge,
            "discharge_mw": discharge,
            "net_export_mw": discharge - charge,
            "soc_start_mwh": soc[:-1],
            "soc_end_mwh": soc[1:],
            "gross_revenue_cad": gross_margin,
            "degradation_cost_cad": degradation_cost,
            "net_profit_cad": gross_margin - degradation_cost,
        },
        index=prices.index,
    )


def audit_dispatch(
    dispatch: pd.DataFrame,
    config: BatteryConfig,
    timestep_hours: float = 1.0,
    tolerance: float = 1e-6,
) -> pd.Series:
    """Audit the physical constraints and accounting identities of a dispatch."""

    carry = (1.0 - config.self_discharge_per_hour) ** timestep_hours
    expected_soc_end = (
        dispatch["soc_start_mwh"] * carry
        + config.charge_efficiency * dispatch["charge_mw"] * timestep_hours
        - dispatch["discharge_mw"]
        * timestep_hours
        / config.discharge_efficiency
    )
    simultaneous = (
        dispatch["charge_mw"].gt(tolerance)
        & dispatch["discharge_mw"].gt(tolerance)
    )
    soc_columns = ["soc_start_mwh", "soc_end_mwh"]
    revenue_error = (
        dispatch["net_profit_cad"]
        - dispatch["gross_revenue_cad"]
        + dispatch["degradation_cost_cad"]
    ).abs().max()

    return pd.Series(
        {
            "charge_within_bounds": dispatch["charge_mw"]
            .between(-tolerance, config.power_mw + tolerance)
            .all(),
            "discharge_within_bounds": dispatch["discharge_mw"]
            .between(-tolerance, config.power_mw + tolerance)
            .all(),
            "soc_within_bounds": (
                dispatch[soc_columns].ge(-tolerance).all().all()
                and dispatch[soc_columns]
                .le(config.energy_mwh + tolerance)
                .all()
                .all()
            ),
            "soc_balance_satisfied": expected_soc_end
            .sub(dispatch["soc_end_mwh"])
            .abs()
            .max()
            <= tolerance,
            "initial_soc_satisfied": abs(
                dispatch["soc_start_mwh"].iloc[0]
                - config.resolved_initial_soc
            )
            <= tolerance,
            "terminal_soc_satisfied": abs(
                dispatch["soc_end_mwh"].iloc[-1]
                - config.resolved_terminal_soc
            )
            <= tolerance,
            "no_simultaneous_operation": not simultaneous.any(),
            "revenue_identity_satisfied": revenue_error <= tolerance,
        }
    )


def summarize_dispatch(
    dispatch: pd.DataFrame,
    config: BatteryConfig,
    timestep_hours: float = 1.0,
) -> pd.Series:
    """Return the standard energy and financial metrics for one dispatch."""

    charged_mwh = dispatch["charge_mw"].sum() * timestep_hours
    discharged_mwh = dispatch["discharge_mw"].sum() * timestep_hours
    return pd.Series(
        {
            "gross_revenue_cad": dispatch["gross_revenue_cad"].sum(),
            "degradation_cost_cad": dispatch["degradation_cost_cad"].sum(),
            "net_profit_cad": dispatch["net_profit_cad"].sum(),
            "charged_mwh": charged_mwh,
            "discharged_mwh": discharged_mwh,
            "equivalent_full_cycles": discharged_mwh / config.energy_mwh,
            "profit_per_discharged_mwh": (
                dispatch["net_profit_cad"].sum() / discharged_mwh
                if discharged_mwh > 0
                else np.nan
            ),
        }
    )
