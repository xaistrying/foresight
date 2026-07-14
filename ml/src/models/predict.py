"""Build future feature rows and generate predictions."""
import pandas as pd
from xgboost import XGBRegressor

from src.features.build_features import FEATURE_COLS


def build_lag_stats(recent_df: pd.DataFrame, group_cols: list) -> pd.DataFrame:
    """Aggregate recent history into per-group baselines used as lag proxies for future dates."""
    agg = recent_df.groupby(group_cols).agg(
        revenue_lag_1d=("total_revenue", "mean"),
        revenue_lag_7d=("total_revenue", "mean"),
        revenue_rolling_7d=("total_revenue", "mean"),
        txn_count=("txn_count", "mean"),
        avg_amount=("avg_amount", "mean"),
        schoolid=("schoolid", "first"),
        paymentmode=("paymentmode", "first"),
        softype_encoded=("softype_encoded", "first"),
        paymentmode_encoded=("paymentmode_encoded", "first"),
    ).reset_index()
    return agg


def build_future_dataframe(
        lag_stats: pd.DataFrame, future_dates: pd.DatetimeIndex,
        peak_hours: list,
        weekend_days: list
    ) -> pd.DataFrame:
    rows = []
    for date in future_dates:
        temp = lag_stats.copy()
        temp["date"] = date
        temp["day_of_week"] = date.dayofweek + 1
        temp["is_weekend"] = int(date.dayofweek in weekend_days)
        temp["is_peak_hour"] = temp["hour"].isin(peak_hours).astype(int)
        temp["month"] = date.month
        temp["week"] = date.isocalendar()[1]
        rows.append(temp)
    return pd.concat(rows, ignore_index=True)


def predict(model: XGBRegressor, future_df: pd.DataFrame) -> pd.DataFrame:
    future_df = future_df.copy()
    future_df["predicted_revenue"] = model.predict(future_df[FEATURE_COLS])
    return future_df
