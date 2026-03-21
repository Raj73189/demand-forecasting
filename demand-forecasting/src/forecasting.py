from statsmodels.tsa.statespace.sarimax import SARIMAX

def forecast(series, order, seasonal_order, steps):

    model = SARIMAX(
        series,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False
    )

    fitted = model.fit(disp=False)
    result = fitted.get_forecast(steps=steps)

    # Ensure non-negative forecasts
    pred = result.predicted_mean.clip(lower=0)

    return pred