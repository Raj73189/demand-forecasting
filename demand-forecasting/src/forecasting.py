from __future__ import annotations

import importlib

import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from src.evaluation import evaluate


def _get_prophet_class():
    try:
        module = importlib.import_module("prophet")
    except ImportError as exc:
        raise ImportError("Prophet is not installed. Run `pip install prophet`.") from exc
    return getattr(module, "Prophet")


def forecast_sarimax(series: pd.Series, order, seasonal_order, steps: int) -> pd.Series:
    model = SARIMAX(
        series,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    fitted = model.fit(disp=False)
    result = fitted.get_forecast(steps=steps)
    pred = result.predicted_mean.clip(lower=0)
    return pred


def forecast(series, order, seasonal_order, steps: int) -> pd.Series:
    """Backward-compatible alias used by `api.py`."""
    return forecast_sarimax(series, order, seasonal_order, steps)


def forecast_prophet(series: pd.Series, periods: int) -> pd.Series:
    Prophet = _get_prophet_class()

    df = pd.DataFrame({"ds": pd.to_datetime(series.index), "y": series.values})
    m = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True,
    )
    m.fit(df)
    future = m.make_future_dataframe(periods=periods, freq="D")
    fcst = m.predict(future)
    out = fcst.tail(periods).set_index("ds")["yhat"].clip(lower=0)
    out.index = pd.to_datetime(out.index)
    return out


def backtest_sarimax(
    series: pd.Series,
    order,
    seasonal_order,
    holdout_days: int,
) -> tuple[pd.Series, pd.Series, dict]:
    if len(series) < holdout_days + 1:
        raise ValueError("Series shorter than holdout window.")
    train = series.iloc[:-holdout_days]
    test = series.iloc[-holdout_days:]
    model = SARIMAX(
        train,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    fitted = model.fit(disp=False)
    fc = fitted.get_forecast(steps=len(test))
    pred = fc.predicted_mean.clip(lower=0)
    pred = pred.copy()
    pred.index = test.index
    metrics = evaluate(test.values, pred.values)
    return test, pred, metrics


def backtest_prophet(series: pd.Series, holdout_days: int) -> tuple[pd.Series, pd.Series, dict]:
    Prophet = _get_prophet_class()

    if len(series) < holdout_days + 1:
        raise ValueError("Series shorter than holdout window.")
    train = series.iloc[:-holdout_days]
    test = series.iloc[-holdout_days:]
    df_train = pd.DataFrame({"ds": pd.to_datetime(train.index), "y": train.values})
    m = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True,
    )
    m.fit(df_train)
    future = pd.DataFrame({"ds": pd.to_datetime(test.index)})
    fcst = m.predict(future)
    pred = pd.Series(
        fcst["yhat"].clip(lower=0).values,
        index=test.index,
    )
    metrics = evaluate(test.values, pred.values)
    return test, pred, metrics
