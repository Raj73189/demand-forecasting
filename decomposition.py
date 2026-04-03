import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose


def decompose_series(
    series: pd.Series,
    period: int = 7,
    model: str = "additive",
) -> object:
    """Classical decomposition into trend, seasonal, and residual."""
    s = series.astype(float).copy()
    if s.isna().all():
        raise ValueError("Series is empty or all NaN.")
    s = s.fillna(0)
    if len(s) < 2 * period:
        raise ValueError(
            f"Need at least 2 × period ({2 * period}) observations; got {len(s)}."
        )
    return seasonal_decompose(
        s,
        model=model,
        period=period,
        extrapolate_trend="freq",
    )
