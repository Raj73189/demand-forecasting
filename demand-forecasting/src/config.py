from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "raw" / "train.csv"
ORDER = (1, 1, 1)
SEASONAL_ORDER = (1, 1, 1, 7)
