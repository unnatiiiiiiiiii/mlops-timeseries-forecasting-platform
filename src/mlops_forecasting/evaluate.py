import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error


def regression_metrics(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    non_zero = np.where(y_true == 0, 1e-9, y_true)
    mape = float(np.mean(np.abs((y_true - y_pred) / non_zero)) * 100)
    return {"mae": mae, "rmse": rmse, "mape": mape}
