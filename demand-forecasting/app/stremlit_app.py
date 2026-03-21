import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Ensure these local files exist in your directory
from src import config   
from src.preprocessing import load_and_clean
from src.forecasting import forecast

st.set_page_config(page_title="Demand Forecasting", layout="wide")
st.title("📊 Demand Forecasting System")

# 1. Load Data
data_path = Path(config.DATA_PATH)

if not data_path.exists():
    st.error(f"Data file not found: {data_path}")
    st.stop()

try:
    df = load_and_clean(data_path)
except Exception as exc:
    st.error(f"Failed to load data: {exc}")
    st.stop()

if df.empty:
    st.warning("No data available after preprocessing.")
    st.stop()

# 2. Sidebar/Selection Filters
col1, col2 = st.columns(2)

with col1:
    store = st.selectbox("Select Store", df["store_id"].unique())
with col2:
    days = st.slider("Forecast Days", 7, 90, 30)

# 3. Data Processing
# Filter data based on selection
series = df[df["store_id"] == store].copy()

if series.empty:
    st.warning(f"No data found for store {store}.")
    st.stop()

# Ensure date is datetime and set as index
series["date"] = pd.to_datetime(series["date"])
series = series.set_index("date").sort_index()

# Handle frequency and missing values
series = series.asfreq("D")
series["demand"] = series["demand"].fillna(0)

# 4. Forecasting
# Added 'config.' prefix assuming ORDER and SEASONAL_ORDER are defined there
with st.spinner("Generating forecast..."):
    try:
        pred = forecast(
            series["demand"],
            config.ORDER,
            config.SEASONAL_ORDER,
            days
        )
    except Exception as exc:
        st.error(f"Forecast generation failed: {exc}")
        st.stop()

# 5. Visualization
st.subheader(f"Forecast for Store {store}")
fig, ax = plt.subplots(figsize=(10, 5))

# Plot historical data (last 90 days for clarity)
ax.plot(series.index[-90:], series["demand"].tail(90), label="Historical")
# Plot prediction
ax.plot(pred.index, pred, label="Forecast", linestyle="--", color="orange")

ax.set_ylabel("Units Demanded")
ax.legend()
st.pyplot(fig)
plt.close(fig)

# 6. Data Table
forecast_df = pd.DataFrame({
    "Date": pred.index,
    "Predicted Demand": pred.values.round(2)
})

st.write("### Forecast Details")
st.dataframe(forecast_df, use_container_width=True)
