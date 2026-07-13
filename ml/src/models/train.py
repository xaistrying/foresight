import pandas as pd
from xgboost import XGBRegressor

from src.features.build_features import FEATURE_COLS, TARGET_COL


def split_train_test(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Last full month becomes the test set — dynamic, no hardcoded date."""
    last_date = df["date"].max()
    cutoff = last_date.replace(day=1) - pd.Timedelta(days=1)
    train = df[df["date"] <= cutoff]
    test = df[df["date"] > cutoff]
    return train, test


def train_model(train: pd.DataFrame, test: pd.DataFrame, model_config: dict) -> XGBRegressor:
    X_train, y_train = train[FEATURE_COLS], train[TARGET_COL]
    X_test, y_test = test[FEATURE_COLS], test[TARGET_COL]

    model = XGBRegressor(
        n_estimators=model_config["n_estimators"],
        max_depth=model_config["max_depth"],
        learning_rate=model_config["learning_rate"],
        subsample=model_config["subsample"],
        random_state=model_config["random_state"],
        early_stopping_rounds=model_config["early_stopping_rounds"],
        n_jobs=model_config["n_jobs"],
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    return model
