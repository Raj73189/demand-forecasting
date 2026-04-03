from flask import Flask, request, jsonify, g
import pandas as pd

from src.config import DATA_PATH, ORDER, SEASONAL_ORDER, TRAIN_MAX_ROWS
from src.preprocessing import load_and_clean
from src.forecasting import forecast

app = Flask(__name__)

def get_data():
    if 'df' not in g:
        g.df = load_and_clean(DATA_PATH, nrows=TRAIN_MAX_ROWS)
    return g.df


@app.route("/forecast", methods=["GET"])
def get_forecast():
    df = get_data()
    raw = request.args.get("store_id")
    if raw is None:
        return jsonify({"error": "store_id is required"}), 400
    try:
        store_id = int(raw)
    except ValueError:
        return jsonify({"error": "store_id must be an integer"}), 400

    try:
        days = int(request.args.get("days", 30))
    except ValueError:
        return jsonify({"error": "days must be an integer"}), 400
    if days < 1 or days > 366:
        return jsonify({"error": "days must be between 1 and 366"}), 400

    series_df = df[df["store_id"] == store_id].copy()
    if series_df.empty:
        return jsonify({"error": f"no data for store_id={store_id}"}), 404

    series_df["date"] = pd.to_datetime(series_df["date"])
    series_df = series_df.set_index("date").sort_index()
    series_df = series_df.asfreq("D")
    series_df["demand"] = series_df["demand"].fillna(0)

    pred = forecast(series_df["demand"], ORDER, SEASONAL_ORDER, days)

    forecast_rows = [
        {"date": idx.strftime("%Y-%m-%d"), "predicted_demand": float(val)}
        for idx, val in pred.items()
    ]
    return jsonify({"store_id": store_id, "days": days, "forecast": forecast_rows})


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
