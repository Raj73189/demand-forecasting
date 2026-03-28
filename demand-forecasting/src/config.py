import os
from pathlib import Path


def _env_positive_int(name: str) -> int | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError:
        return None
    return n if n > 0 else None


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "raw" / "train.csv"
# Set DEMAND_FORECAST_TRAIN_MAX_ROWS=100000 to read only the first N rows (faster local demos).
TRAIN_MAX_ROWS = _env_positive_int("DEMAND_FORECAST_TRAIN_MAX_ROWS")
ORDER = (1, 1, 1)
SEASONAL_ORDER = (1, 1, 1, 7)

DEFAULT_HOLDOUT_DAYS = 28
DEFAULT_DECOMP_PERIOD = 7
MIN_OBS_SARIMAX_BACKTEST = 90
MIN_OBS_PROPHET_BACKTEST = 60
