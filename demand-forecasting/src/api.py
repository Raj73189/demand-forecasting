from flask import Flask, request, jsonify
import pandas as pd

from src.config import *
from src.preprocessing import load_and_clean
from src.forecasting import forecast

app = Flask(__name__)

df = load_and_clean(DATA_PATH)

@app.route("/forecast", methods=["GET"])
def get_forecast():

    store_id = int(request.args.get("store_id"))
    product_id = request.args.get("product_id")
    days = int(request.args.get("days", 30))

    series = df[
        (df["store_id"] == store_id) &
        (df["product_id"] == product_id)
    ].set_index("date")

    series = series.asfreq("D")
    series["demand"] = series["demand"].fillna(0)

    pred = forecast(
        series["demand"],
        ORDER,
        SEASONAL_ORDER,
        days
    )

    return jsonify(pred.to_dict())

if __name__ == "__main__":
    app.run(debug=True)