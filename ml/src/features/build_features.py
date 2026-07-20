import pandas as pd

from src.features.category_mappings import SOFTYPE_MAPPING, PAYMENTMODE_MAPPING


TARGET_COL = "total_revenue"


FEATURE_COLS = [
    'hour', 'day_of_week', 'is_weekend', 'is_peak_hour',
    'month', 'week', 'txn_count', 'avg_amount',
    'softype_encoded', 'paymentmode_encoded',
    'revenue_lag_1d', 'revenue_lag_7d', 'revenue_rolling_7d'
]


def filter_outliers(df: pd.DataFrame, percentile: float) -> pd.DataFrame:
    threshold = df[TARGET_COL].quantile(percentile)
    return df[df[TARGET_COL] <= threshold].copy()


def add_time_features(df: pd.DataFrame, peak_hours: list, weekend_days: list) -> pd.DataFrame:
    df = df.copy()
    df["is_weekend"] = df["day_of_week"].isin(weekend_days).astype(int)
    df["is_peak_hour"] = df["hour"].isin(peak_hours).astype(int)
    df["month"] = df["date"].dt.month
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    return df


def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    unmapped_softype = set(df["softype"].unique()) - SOFTYPE_MAPPING.keys()
    if unmapped_softype:
        raise ValueError(f"Unmapped softype value(s): {unmapped_softype}")
    unmapped_paymentmode = set(df["paymentmode"].unique()) - PAYMENTMODE_MAPPING.keys()
    if unmapped_paymentmode:
        raise ValueError(f"Unmapped paymentmode value(s): {unmapped_paymentmode}")

    df["softype_encoded"] = df["softype"].map(SOFTYPE_MAPPING)
    df["paymentmode_encoded"] = df["paymentmode"].map(PAYMENTMODE_MAPPING)
    return df


def add_lag_features(df: pd.DataFrame, group_cols: list) -> pd.DataFrame:
    df = df.sort_values(group_cols + ["date", "hour"]).copy()
    grouped = df.groupby(group_cols)[TARGET_COL]
    df["revenue_lag_1d"] = grouped.shift(1)
    df["revenue_lag_7d"] = grouped.shift(7)
    df["revenue_rolling_7d"] = grouped.transform(lambda x: x.rolling(7, min_periods=1).mean())
    return df


def build_training_features(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Full pipeline: outlier filter => time features => encode => lag. Order matters."""
    df = filter_outliers(df, config["features"]["outlier_percentile"])
    df = add_time_features(df, config["features"]["peak_hours"], config["features"]["weekend_days"])
    df = encode_categoricals(df)
    df = add_lag_features(df, config["features"]["group_cols"])
    df = df.dropna()
    return df
