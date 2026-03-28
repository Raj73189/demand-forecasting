import os
import sys
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Demand Forecasting", layout="wide")

# Streamlit Community Cloud: set row limit in app Settings → Secrets, e.g.
# DEMAND_FORECAST_TRAIN_MAX_ROWS = "150000"
try:
    if hasattr(st, "secrets"):
        if "DEMAND_FORECAST_TRAIN_MAX_ROWS" in st.secrets:
            os.environ["DEMAND_FORECAST_TRAIN_MAX_ROWS"] = str(
                st.secrets["DEMAND_FORECAST_TRAIN_MAX_ROWS"]
            )
        if "DEMAND_FORECAST_DATA_FILE" in st.secrets:
            os.environ["DEMAND_FORECAST_DATA_FILE"] = str(
                st.secrets["DEMAND_FORECAST_DATA_FILE"]
            )
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import matplotlib.pyplot as plt
import pandas as pd

from src import config
from src.decomposition import decompose_series
from src.forecasting import (
    backtest_prophet,
    backtest_sarimax,
    forecast_prophet,
    forecast_sarimax,
)
from src.preprocessing import load_and_clean


@st.cache_data(show_spinner="Loading data…")
def _load_data(path_str: str, nrows: int | None):
    return load_and_clean(Path(path_str), nrows=nrows)


try:
    import prophet  # noqa: F401

    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

st.title("Demand forecasting")

data_path = Path(config.DATA_PATH)
if not data_path.exists():
    st.error(f"Data file not found: {data_path}")
    st.stop()

try:
    df = _load_data(str(data_path), config.TRAIN_MAX_ROWS)
except Exception as exc:
    st.error(f"Failed to load data: {exc}")
    st.stop()

if df.empty:
    st.warning("No data available after preprocessing.")
    st.stop()

model_options = ["SARIMAX"]
if PROPHET_AVAILABLE:
    model_options.append("Prophet")
else:
    st.info("Install **prophet** (`pip install prophet`) to enable Prophet.")

with st.sidebar:
    if config.TRAIN_MAX_ROWS is not None:
        st.caption(
            f"Demo mode: first **{config.TRAIN_MAX_ROWS:,}** CSV rows "
            "(unset `DEMAND_FORECAST_TRAIN_MAX_ROWS` for full data)."
        )
    store = st.selectbox("Store", sorted(df["store_id"].unique()))
    model_name = st.selectbox("Model", model_options)
    forecast_days = st.slider("Forward forecast horizon (days)", 7, 90, 30)
    holdout_days = st.slider(
        "Backtest holdout (days)",
        14,
        90,
        config.DEFAULT_HOLDOUT_DAYS,
    )
    decomp_period = st.selectbox(
        "Decomposition season length (days)",
        [7, 14, 30],
        index=0,
    )

series_df = df[df["store_id"] == store].copy()
if series_df.empty:
    st.warning(f"No data for store {store}.")
    st.stop()

series_df["date"] = pd.to_datetime(series_df["date"])
series_df = series_df.set_index("date").sort_index()
series_df = series_df.asfreq("D")
series_df["demand"] = series_df["demand"].fillna(0)
demand = series_df["demand"]

n = len(demand)
tab_hist, tab_decomp, tab_back, tab_fwd = st.tabs(
    ["Historical", "Decomposition", "Backtest", "Forward forecast"]
)

with tab_hist:
    st.subheader("Demand summary")
    last = demand.tail(30)
    prev = demand.iloc[-60:-30] if len(demand) >= 60 else pd.Series(dtype=float)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Days in series", n)
    c2.metric("Mean daily demand", f"{demand.mean():.1f}")
    c3.metric("Std dev", f"{demand.std():.1f}")
    if len(prev) > 0:
        delta = float(last.mean() - prev.mean())
        c4.metric("Last 30d avg vs prior 30d", f"{last.mean():.1f}", f"{delta:+.1f}")
    else:
        c4.metric("Last 30d avg", f"{last.mean():.1f}")

    fig_h, ax_h = plt.subplots(figsize=(12, 4))
    tail = min(365, n)
    ax_h.plot(demand.index[-tail:], demand.values[-tail:], linewidth=1)
    ax_h.set_ylabel("Demand")
    ax_h.set_title(f"Store {store} — last {tail} days")
    st.pyplot(fig_h)
    plt.close(fig_h)

with tab_decomp:
    st.subheader("Trend and seasonality")
    if n < 2 * decomp_period:
        st.warning(
            f"Need at least {2 * decomp_period} days for this decomposition; "
            f"this series has {n}."
        )
    else:
        try:
            dec = decompose_series(demand, period=decomp_period)
        except Exception as exc:
            st.error(str(exc))
        else:
            fig_d, axes = plt.subplots(4, 1, figsize=(12, 8), sharex=True)
            dec.observed.plot(ax=axes[0], legend=False, color="C0")
            axes[0].set_ylabel("Observed")
            dec.trend.plot(ax=axes[1], legend=False, color="C1")
            axes[1].set_ylabel("Trend")
            dec.seasonal.plot(ax=axes[2], legend=False, color="C2")
            axes[2].set_ylabel("Seasonal")
            dec.resid.plot(ax=axes[3], legend=False, color="C3")
            axes[3].set_ylabel("Residual")
            axes[3].set_xlabel("Date")
            plt.tight_layout()
            st.pyplot(fig_d)
            plt.close(fig_d)

with tab_back:
    st.subheader("Out-of-sample backtest (forecast vs actual)")
    min_obs = (
        config.MIN_OBS_SARIMAX_BACKTEST
        if model_name == "SARIMAX"
        else config.MIN_OBS_PROPHET_BACKTEST
    )
    if n < holdout_days + min_obs:
        st.warning(
            f"Need at least {holdout_days + min_obs} days for a reliable "
            f"{model_name} backtest; this series has {n}."
        )
    else:
        with st.spinner("Running backtest..."):
            try:
                if model_name == "SARIMAX":
                    actual, pred, metrics = backtest_sarimax(
                        demand,
                        config.ORDER,
                        config.SEASONAL_ORDER,
                        holdout_days,
                    )
                else:
                    actual, pred, metrics = backtest_prophet(demand, holdout_days)
            except Exception as exc:
                st.error(f"Backtest failed: {exc}")
            else:
                m1, m2, m3 = st.columns(3)
                m1.metric("MAE", f"{metrics['mae']:.2f}")
                m2.metric("RMSE", f"{metrics['rmse']:.2f}")
                m3.metric("MAPE (%)", f"{metrics['mape']:.2f}")
                fig_b, ax_b = plt.subplots(figsize=(12, 4))
                ax_b.plot(actual.index, actual.values, label="Actual", color="C0")
                ax_b.plot(pred.index, pred.values, label="Forecast", color="C1", linestyle="--")
                ax_b.set_ylabel("Demand")
                ax_b.legend()
                ax_b.set_title(f"{model_name} — last {holdout_days} days held out")
                st.pyplot(fig_b)
                plt.close(fig_b)
                cmp_df = pd.DataFrame(
                    {
                        "date": actual.index,
                        "actual": actual.values,
                        "forecast": pred.values,
                    }
                )
                st.dataframe(cmp_df, use_container_width=True)

with tab_fwd:
    st.subheader("Future demand")
    with st.spinner("Generating forecast..."):
        try:
            if model_name == "SARIMAX":
                pred = forecast_sarimax(
                    demand,
                    config.ORDER,
                    config.SEASONAL_ORDER,
                    forecast_days,
                )
            else:
                pred = forecast_prophet(demand, forecast_days)
        except Exception as exc:
            st.error(f"Forecast failed: {exc}")
        else:
            fig_f, ax_f = plt.subplots(figsize=(12, 4))
            hist_days = min(90, n)
            ax_f.plot(
                demand.index[-hist_days:],
                demand.values[-hist_days:],
                label="History",
            )
            ax_f.plot(pred.index, pred.values, label="Forecast", linestyle="--", color="orange")
            ax_f.set_ylabel("Demand")
            ax_f.legend()
            ax_f.set_title(f"Store {store} — {model_name}")
            st.pyplot(fig_f)
            plt.close(fig_f)
            out_df = pd.DataFrame(
                {"date": pred.index, "predicted_demand": pred.values.round(2)}
            )
            st.dataframe(out_df, use_container_width=True)
