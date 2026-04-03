import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error


def evaluate(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mape = float(
        np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1.0))) * 100.0
    )
    return {"mae": mae, "rmse": rmse, "mape": mape}
