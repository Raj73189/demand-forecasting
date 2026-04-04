import numpy as np


def evaluate(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    errors = y_true - y_pred
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(np.square(errors))))
    mape = float(
        np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1.0))) * 100.0
    )
    return {"mae": mae, "rmse": rmse, "mape": mape}
