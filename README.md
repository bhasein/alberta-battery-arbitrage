# Alberta Battery Arbitrage

Historical battery-dispatch and energy-arbitrage analysis for Alberta's electricity market.

This project uses hourly AESO pool prices to estimate the energy-arbitrage value available to a stylized grid-scale battery. It begins with a perfect-foresight linear optimization, attributes value across years and price regimes, and establishes the upper bound against which causal operating strategies can be evaluated.

## Current analysis

The reference case models a 100 MW / 200 MWh battery with:

- two hours of storage;
- 88% round-trip efficiency;
- equal opening and closing state of charge;
- a $2/MWh throughput degradation charge; and
- no self-discharge.

The current notebook:

1. audits hourly pool-price coverage from 2015 through 2025;
2. formulates and validates the battery-dispatch linear program;
3. estimates annual perfect-foresight arbitrage margins;
4. measures how strongly value is concentrated in extreme-price hours; and
5. defines the next-stage causal strategy and battery-design sensitivity tests.

The perfect-foresight results are theoretical upper bounds. They are not live trading results or an investment-grade valuation.

## Repository structure

```text
.
├── data/
│   └── README.md
├── notebooks/
│   └── 01_Battery_Arbitrage_Optimization.ipynb
├── src/
│   └── config.py
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Data

The notebook expects an hourly master dataset at:

```text
data/processed/master_dataset.parquet
```

Required columns are:

- `timestamp_utc`
- `timestamp_alberta`
- `year_alberta`
- `month_alberta`
- `hour_alberta`
- `pool_price`

The underlying market dataset is not committed to this repository. See [data/README.md](data/README.md) for details.

## Setup

Create and activate a virtual environment, then install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Start Jupyter:

```bash
jupyter lab
```

Open `notebooks/01_Battery_Arbitrage_Optimization.ipynb` and run the cells in order.

## Interpretation boundary

The current model excludes capital cost, fixed operating cost, ancillary-service revenue, market fees, price impact, forced outages, calendar aging, financing, and detailed electrochemical degradation. Reported margins deduct only the modeled charging expenditure, efficiency losses, and simplified throughput degradation charge.

## Roadmap

- Implement sequential causal dispatch benchmarks.
- Compare causal performance with the perfect-foresight upper bound.
- Run duration, efficiency, power, and degradation sensitivities.
- Test rolling-horizon operation and imperfect price forecasts.
- Add project-level cost and availability assumptions.

## License

This project is available under the MIT License.
