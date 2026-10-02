# Data

The battery analyses use the repository's compact hourly market dataset:

```text
data/processed/battery_market_hourly.parquet
```

The file contains 96,432 consecutive hourly observations for Alberta calendar
years 2015 through 2025. It was extracted from the audited master dataset used
by the broader Alberta electricity-market research project. Only fields used by
the two battery notebooks are retained.

Notebook 01 uses the timestamps, local calendar fields, and AESO pool price.
Notebook 02 additionally uses forecast-safe calendar fields, lagged prices and
system conditions, gas-price history, and the archived AESO pool-price forecast
field. The archived AESO forecast is an external benchmark only because its
historical issue and revision timing has not been verified.

The dataset contains these column families:

| Family | Columns |
|---|---|
| Time | `timestamp_utc`, `timestamp_alberta`, `year_alberta`, `month_alberta`, `hour_alberta` |
| Realized outcome | `pool_price` |
| Known calendar | cyclic hour/day/month fields, weekend and holiday flags |
| Prior market state | 1-, 24-, and 168-hour price lags; prior 24-hour price mean and volatility |
| Prior system state | lagged net load, outages, net imports, and gas price |
| External benchmark | `aeso_forecast_pool_price_cad_mwh` |

The full market master table, raw source files, unrelated engineered features,
and intermediate data products are excluded.
