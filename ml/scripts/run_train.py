import argparse
import json
from datetime import datetime

import boto3
import yaml
from xgboost import XGBRegressor

from src.data.load_data import load_training_data
from src.features.build_features import build_training_features
from src.models.train import split_train_test, train_model
from src.models.metrics import evaluate_model
from src.models.gate import should_promote


def save_versioned(model, metrics, test, config, timestamp) -> dict:
    """Always-written audit trail for this training run, regardless of promotion outcome."""
    bucket = config["s3"]["bucket"]
    prefix = config["s3"]["model_prefix"]
    s3 = boto3.client("s3")

    model_key = f"{prefix}revenue_model_{timestamp}.json"
    metrics_key = f"{prefix}metrics_{timestamp}.json"
    test_set_key = f"{prefix}test_set_{timestamp}.parquet"

    model_bytes = model.get_booster().save_raw(raw_format="json")
    metrics_bytes = json.dumps(metrics, indent=2).encode("utf-8")

    s3.put_object(Bucket=bucket, Key=model_key, Body=model_bytes)
    s3.put_object(Bucket=bucket, Key=metrics_key, Body=metrics_bytes)

    local_test_path = f"/tmp/test_set_{timestamp}.parquet"
    test.to_parquet(local_test_path, index=False)
    s3.upload_file(local_test_path, bucket, test_set_key)

    return {"model_key": model_key, "metrics_key": metrics_key, "test_set_key": test_set_key}


def load_champion(config) -> XGBRegressor | None:
    """None if no champion has ever been promoted yet (first run)."""
    bucket = config["s3"]["bucket"]
    prefix = config["s3"]["model_prefix"]
    local_path = "/tmp/champion_model.json"

    s3 = boto3.client("s3")
    try:
        s3.download_file(bucket, f"{prefix}revenue_model_champion.json", local_path)
    except s3.exceptions.ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return None
        raise

    model = XGBRegressor()
    model.load_model(local_path)
    return model


def promote_to_champion(bucket: str, prefix: str, versioned_keys: dict):
    """Promotion = copy the already-written versioned artifact onto the champion pointer."""
    s3 = boto3.client("s3")
    s3.copy_object(
        Bucket=bucket, Key=f"{prefix}revenue_model_champion.json",
        CopySource={"Bucket": bucket, "Key": versioned_keys["model_key"]},
    )
    s3.copy_object(
        Bucket=bucket, Key=f"{prefix}metrics_champion.json",
        CopySource={"Bucket": bucket, "Key": versioned_keys["metrics_key"]},
    )


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

    print("Training challenger model...")
    challenger = train_model(train, test, config["model"])
    challenger_metrics = evaluate_model(challenger, test)

    print(f"""
        \nChallenger — R2: {challenger_metrics['r2']:.4f}\n
        MAE: ${challenger_metrics['mae']:.2f}\n
        RMSE: ${challenger_metrics['rmse']:.2f}\n
        MAPE: {challenger_metrics['mape']:.2f}%
    """)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    versioned_keys = save_versioned(challenger, challenger_metrics, test, config, timestamp)

    print("Loading champion for comparison...")
    champion = load_champion(config)

    if champion is None:
        print("No champion exists yet — promoting challenger unconditionally.")
        promote_to_champion(config["s3"]["bucket"], config["s3"]["model_prefix"], versioned_keys)
        print("Promoted.")
        return

    # Champion is scored on this run's exact test dataframe — no re-fetch, no re-build.
    champion_metrics = evaluate_model(champion, test)
    print(f"Champion MAPE on this run's test set: {champion_metrics['mape']:.2f}%")

    margin = config["gate"]["promotion_margin_pct"]
    promote = should_promote(champion_metrics["mape"], challenger_metrics["mape"], margin)

    print(f"Champion MAPE: {champion_metrics['mape']:.2f}% | "
          f"Challenger MAPE: {challenger_metrics['mape']:.2f}% | "
          f"Margin required: {margin * 100:.1f}% relative | "
          f"Promote: {promote}")

    if promote:
        promote_to_champion(config["s3"]["bucket"], config["s3"]["model_prefix"], versioned_keys)
        print("Challenger promoted to champion.")
    else:
        print("Challenger did not beat champion by required margin — champion unchanged.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/config.yaml")
    args = parser.parse_args()
    main(args.config)
