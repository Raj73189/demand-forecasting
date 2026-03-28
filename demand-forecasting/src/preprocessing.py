import pandas as pd


def load_and_clean(path, nrows: int | None = None):
    read_kw = {"low_memory": False}
    if nrows is not None:
        read_kw["nrows"] = nrows
    df = pd.read_csv(path, **read_kw)

    df = df.rename(columns={
        "Date": "date",
        "Store": "store_id",
        "Sales": "demand"
    })

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    df["demand"] = df["demand"].fillna(0)
    df = df[df["demand"] >= 0]

    # Filter for open stores only (assuming Open=1 means open)
    if "Open" in df.columns:
        df = df[df["Open"] == 1]

    daily = (
        df.groupby(["date","store_id"])["demand"]
        .sum()
        .reset_index()
    )

    return daily
