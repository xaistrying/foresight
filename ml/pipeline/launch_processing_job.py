"""
Launch run_train.py / run_predict.py as SageMaker Processing Jobs.

Run this from inside the SageMaker Studio / Unified Studio JupyterLab terminal
or a notebook kernel — NOT the developer's laptop (see Claude.md, "Execution
environment"). Run as a single script/cell, not split across many cells.

Usage:
    python3 pipeline/launch_processing_job.py train
    python3 pipeline/launch_processing_job.py predict --target-month 2026-08
"""
import argparse
import os
import shutil
import tempfile

import yaml

ML_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_DIRS = {".venv", "__pycache__", ".git"}

# See requirements.txt — pinned to match a SageMaker-SDK-validated framework_version.
# Update both together if this ever changes; don't let them drift.
FRAMEWORK_VERSION = "1.7-1"


def verify_environment():
    assert os.path.exists(os.path.join(ML_ROOT, "scripts", "run_train.py")), (
        "scripts/run_train.py not found — is ML_ROOT pointing at the right directory?"
    )
    assert os.path.exists(os.path.join(ML_ROOT, "pipeline", "entrypoints", "train.py"))
    assert os.path.exists(os.path.join(ML_ROOT, "pipeline", "entrypoints", "predict.py"))

    with open(os.path.join(ML_ROOT, "configs", "config.yaml")) as f:
        config = yaml.safe_load(f)
    print("gate config:", config["gate"])
    print("s3 config:", config["s3"])
    return config


def stage_source_dir():
    """
    FrameworkProcessor tars the entire source_dir with no .gitignore awareness,
    so .venv (>1GB locally) must be excluded by staging a clean copy rather than
    passing ml/ directly.
    """
    staging_dir = tempfile.mkdtemp(prefix="ml_source_")
    shutil.copytree(
        ML_ROOT,
        staging_dir,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(*EXCLUDE_DIRS),
    )
    print(f"Staged clean source_dir at {staging_dir}")
    return staging_dir


def build_processor():
    from sagemaker import get_execution_role
    from sagemaker.processing import FrameworkProcessor
    from sagemaker.xgboost.estimator import XGBoost

    return FrameworkProcessor(
        estimator_cls=XGBoost,
        framework_version=FRAMEWORK_VERSION,
        role=get_execution_role(),
        instance_count=1,
        instance_type="ml.m5.xlarge",
    )


def run_train(processor, source_dir):
    processor.run(
        code="pipeline/entrypoints/train.py",
        source_dir=source_dir,
        # No outputs=[...]: run_train.py writes model/metrics/test-set directly
        # to S3 via boto3/awswrangler mid-script.
    )


def run_predict(processor, source_dir, target_month):
    processor.run(
        code="pipeline/entrypoints/predict.py",
        source_dir=source_dir,
        arguments=[target_month],
        # No outputs=[...]: run_predict.py writes predictions directly to S3.
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("job", choices=["train", "predict"])
    parser.add_argument("--target-month", help="YYYY-MM, required for predict")
    args = parser.parse_args()

    if args.job == "predict" and not args.target_month:
        parser.error("--target-month is required for predict")

    print("ML_ROOT:", ML_ROOT)
    verify_environment()

    staging_dir = stage_source_dir()
    processor = build_processor()

    if args.job == "train":
        run_train(processor, staging_dir)
    else:
        run_predict(processor, staging_dir, args.target_month)

    shutil.rmtree(staging_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
