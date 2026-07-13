import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.features.build_features import FEATURE_COLS, TARGET_COL


def evaluate_model(model, test: pd.DataFrame) -> dict:
    X_test, y_test = test[FEATURE_COLS], test[TARGET_COL]
    y_pred = model.predict(X_test)

    mask = y_test.values != 0
    mape = float(np.mean(np.abs((y_test.values[mask] - y_pred[mask]) / y_test.values[mask])) * 100)

    return {
        "r2": float(r2_score(y_test, y_pred)),
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "mape": mape,
        "best_iteration": int(model.best_iteration),
    }
