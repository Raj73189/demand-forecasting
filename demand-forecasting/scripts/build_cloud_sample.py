"""Write data/raw/train_cloud_sample.csv from the first N rows of train.csv."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data" / "raw" / "train.csv"
OUT = ROOT / "data" / "raw" / "train_cloud_sample.csv"
NROWS = 50_000


def main() -> None:
    if not TRAIN.is_file():
        raise SystemExit(f"Missing {TRAIN}")
    df = pd.read_csv(TRAIN, nrows=NROWS)
    df.to_csv(OUT, index=False)
    print(f"Wrote {len(df):,} rows to {OUT}")


if __name__ == "__main__":
    main()
