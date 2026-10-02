"""Project paths and reproducibility settings used by the battery notebooks."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MASTER_PARQUET = PROCESSED_DATA_DIR / "battery_market_hourly.parquet"
RANDOM_SEED = 42
