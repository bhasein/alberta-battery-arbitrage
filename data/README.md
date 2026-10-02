# Data

The market data used in this analysis are not committed to GitHub.

Place the hourly analysis dataset at:

```text
data/processed/master_dataset.parquet
```

The battery notebook currently requires the following fields:

| Column | Description |
|---|---|
| `timestamp_utc` | Unique hourly timestamp in UTC |
| `timestamp_alberta` | Corresponding Alberta-local timestamp |
| `year_alberta` | Alberta-local calendar year |
| `month_alberta` | Alberta-local calendar month |
| `hour_alberta` | Alberta-local hour |
| `pool_price` | AESO hourly pool price in CAD/MWh |

Large raw, intermediate, and processed datasets are excluded by `.gitignore`.
