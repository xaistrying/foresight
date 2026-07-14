import argparse
import json
from datetime import datetime

import boto3
import yaml

from src.data.load_data import load_training_data
from src.features.build_features import build_training_features
from src.models.train import split_train_test, train_model
from src.models.metrics import evaluate_model


def save_model_to_s3(model, metrics, config):
    bucket = config["s3"]["bucket"]
    prefix = config["s3"]["model_prefix"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    s3 = boto3.client("s3")

    # Serialize model directly to memory
    model_bytes = model.get_booster().save_raw(raw_format="json")
    metrics_bytes = json.dumps(metrics, indent=2).encode("utf-8")

    # Versioned
    s3.put_object(Bucket=bucket, Key=f"{prefix}revenue_model_{timestamp}.json", Body=model_bytes)
    s3.put_object(Bucket=bucket, Key=f"{prefix}metrics_{timestamp}.json", Body=metrics_bytes)

    # Latest
    s3.put_object(Bucket=bucket, Key=f"{prefix}revenue_model_latest.json", Body=model_bytes)
    s3.put_object(Bucket=bucket, Key=f"{prefix}metrics_latest.json", Body=metrics_bytes)


def main(config_path: str):
    config = yaml.safe_load(open(config_path))

    print("Loading data from Athena...")
    df = load_training_data(config["athena"]["database"], config["athena"]["training_table"])
    print(f"Loaded {len(df):,} rows")

    print("Building features...")
    df = build_training_features(df, config)
    print(f"After feature engineering: {len(df):,} rows")

    train, test = split_train_test(df)
    print(f"Train: {len(train):,} | Test: {len(test):,}")

    print("Training model...")
    model = train_model(train, test, config["model"])
    metrics = evaluate_model(model, test)

    print(f"""
        \nR2: {metrics['r2']:.4f}\n
        MAE: ${metrics['mae']:.2f}\n
        RMSE: ${metrics['rmse']:.2f}\n
        MAPE: {metrics['mape']:.2f}%
    """)

    save_model_to_s3(model, metrics, config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/config.yaml")
    args = parser.parse_args()
    main(args.config)
