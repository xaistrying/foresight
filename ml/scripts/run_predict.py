import argparse
from datetime import datetime

import boto3
import pandas as pd
import yaml
from xgboost import XGBRegressor

from src.data.load_data import load_training_data
from src.features.build_features import (
    filter_outliers, add_time_features, encode_categoricals
)
from src.models.predict import build_lag_stats, build_future_dataframe, predict


def load_model_from_s3(config) -> XGBRegressor:
    bucket = config["s3"]["bucket"]
    prefix = config["s3"]["model_prefix"]
    local_path = "/tmp/model.json"

    s3 = boto3.client("s3")
    s3.download_file(bucket, f"{prefix}revenue_model_latest.json", local_path)

    model = XGBRegressor()
    model.load_model(local_path)
    return model


def load_recent_month(config, target_month: str) -> pd.DataFrame:
    """Load the full month before target_month, used as lag baseline."""
    target_start = pd.Timestamp(target_month + "-01")
    prior_end = target_start - pd.Timedelta(days=1)
    prior_start = prior_end.replace(day=1)

    df = load_training_data(config["athena"]["database"], config["athena"]["training_table"])
    df = df[(df["date"] >= prior_start) & (df["date"] <= prior_end)]
    return df


def main(config_path: str, target_month: str):
    config = yaml.safe_load(open(config_path))

    print("Loading model from S3...")
    model = load_model_from_s3(config)
    print("Model loaded")

    print(f"Loading recent data for lag baseline...")
    recent_df = load_recent_month(config, target_month)
    print(f"Loaded {len(recent_df):,} rows")

    # Apply same feature steps used in training, minus lag (lag comes from aggregation instead)
    recent_df = filter_outliers(recent_df, config["features"]["outlier_percentile"])
    recent_df = encode_categoricals(recent_df)

    lag_stats = build_lag_stats(recent_df, config["features"]["group_cols"])
    print(f"Lag stats: {len(lag_stats):,} store-hour-softype combinations")

    target_start = pd.Timestamp(target_month + "-01")
    future_dates = pd.date_range(start=target_start, end=target_start + pd.offsets.MonthEnd(1))

    future_df = build_future_dataframe(
        lag_stats, future_dates,
        config["features"]["peak_hours"], config["features"]["weekend_days"],
    )
    print(f"Future rows: {len(future_df):,}")

    result = predict(model, future_df)
    result["predicted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    output_cols = ["date", "hour", "day_of_week", "storeid", "schoolid",
                    "softype", "paymentmode", "predicted_revenue", "predicted_at"]
    # paymentmode was not re-attached in lag_stats — add it back
    output_df = result[[c for c in output_cols if c in result.columns]]

    output_path = f"s3://{config['s3']['bucket']}/predictions/{target_month}_predictions.csv"
    output_df.to_csv(output_path, index=False)
    print(f"Exported {len(output_df):,} rows → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--target-month", required=True, help="YYYY-MM")
    args = parser.parse_args()
    main(args.config, args.target_month)
