# Data

The battery analysis uses the repository's compact hourly market dataset:

```text
data/processed/battery_market_hourly.parquet
```

This Parquet file contains 96,432 consecutive hourly observations covering
Alberta calendar years 2015 through 2025. It was extracted from the audited
master dataset used by the broader Alberta electricity-market research
project. Only fields consumed by the battery notebook are retained.

The battery notebook currently requires the following fields:

| Column | Description |
|---|---|
| `timestamp_utc` | Unique hourly timestamp in UTC |
| `timestamp_alberta` | Corresponding Alberta-local timestamp |
| `year_alberta` | Alberta-local calendar year |
| `month_alberta` | Alberta-local calendar month |
| `hour_alberta` | Alberta-local hour |
| `pool_price` | AESO hourly pool price in CAD/MWh |

The full master table, unrelated engineered features, raw files, and
intermediate data products are excluded. The committed Parquet is the complete
input required to reproduce the current notebook.
