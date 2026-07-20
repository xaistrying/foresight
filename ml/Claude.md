# CLAUDE.md

Rules for AI coding agents working in `ml/` of **Foresight** (revenue prediction for SmartBuddy school canteen payments). Read before touching any code in `ml/`. Scope: `ml/` only — excludes Next.js app and CT automation infra (Lambda, Step Functions, QuickSight, Bedrock).

## Overview

Pipeline: `S3 (raw CSV) → Athena (aggregate) → SageMaker (train XGBoost, predict) → S3 (model + predictions) → Athena (actual vs predicted)`.

`ml/` covers train + predict only. Input: aggregated data from `txns_db.training_data` (Athena). Output: model artifact + metrics JSON on S3, plus future-month predictions.

## Directory structure

```
ml/
├── Makefile
├── configs/config.yaml
├── requirements.txt
├── scripts/
│   ├── run_train.py          — load → train → evaluate → save
│   └── run_predict.py        — load model → build future df → predict
└── src/
    ├── data/load_data.py             — load_training_data(), load_recent_data()
    ├── features/
    │   ├── build_features.py         — filter_outliers, add_time_features,
    │   │                                encode_categoricals, add_lag_features,
    │   │                                build_training_features (orchestrator)
    │   └── category_mappings.py      — SOFTYPE_MAPPING, PAYMENTMODE_MAPPING
    ├── models/
    │   ├── train.py                  — split_train_test(), train_model()
    │   ├── predict.py                — build_lag_stats(), build_future_dataframe(), predict()
    │   └── metrics.py                — evaluate_model()
    └── visualization/                — unused
```

`src/` = pure functions only, no I/O, independently testable. `scripts/` = orchestration, I/O and side-effects allowed. Never put I/O in `src/`.

## Hard rules — do not violate

Settled through real debate, not style preference. If a change conflicts with any rule below, stop and ask — don't "optimize" around it.

| Rule | Reason |
|---|---|
| Outlier filtering: **Q99 percentile**, never IQR | IQR drops 8.6% of data — too aggressive for right-skewed revenue data |
| Filter only on `paymentStatus = 'COMPLETED'`, never on `errorCode` | Transactions with `errorCode <> 0` can still be genuinely completed; filtering on errorCode loses real revenue |
| MAPE/accuracy always on **SUM** (`sum(actual)` vs `sum(predicted)`), never row-by-row average | Rows with tiny actual values (<$1) blow up % error meaninglessly if averaged per-row |
| Category encoding via **fixed dict** (`category_mappings.py`), never `LabelEncoder` | `LabelEncoder().fit_transform()` refits every run → mapping drifts between runs, breaking champion/challenger comparisons |
| Unmapped category → **`raise ValueError`**, never silent NaN | Forces a human decision on genuinely new categories instead of hiding them |
| Train/test split always **dynamic on `df['date'].max()`**, never a hardcoded date | Data grows monthly; a hardcoded date breaks after the next training run |
| Champion vs challenger comparison **only valid on the same test set** — reload champion and re-predict, never compare stored MAPE from two different training runs | Comparing two numbers from two different "exams" is meaningless |
| Retrain: **blind, every month**; gate only at **promote** step, not at "should we retrain" | XGBoost training compute is far cheaper than a delayed drift-detection cycle |
| XGBoost: **full retrain** on all (or rolling-window) data each time, never `xgb_model=` to continue training | No real incremental learning in XGBoost — it only adds boosting rounds, doesn't relearn old patterns properly |

## Champion/challenger gate

Implemented in `run_train.py` + `src/models/gate.py`. Design:

- Every training run produces a **challenger**, trained fresh on this run's `train`/`test` split. It's always saved as a timestamped versioned artifact (`revenue_model_<timestamp>.json`, `metrics_<timestamp>.json`, `test_set_<timestamp>.parquet`) regardless of gate outcome — this is the audit trail.
- The **champion** is a separate, stable pointer: `revenue_model_champion.json` / `metrics_champion.json`. `run_predict.py` only ever reads this pointer — never a timestamped or `_latest` artifact directly.
- Gate logic: load champion, call `model.predict()` on **this run's already-built `test` dataframe** — no re-fetch from Athena, no re-running `build_training_features` for champion. This is deliberate: champion and challenger must be scored on byte-identical feature rows, or the comparison is meaningless (see hard-rules table). Re-deriving "the same test set" via a fresh Athena query is unsafe since `training_data` is an unpartitioned full rebuild — late-arriving/corrected rows could silently change what a re-query returns.
- `test_set_<timestamp>.parquet` is persisted (post-feature-engineering, i.e. already has lag features + encoded categoricals) so a champion can, if ever needed, be re-scored later without needing Athena or redoing feature engineering — lag features can't be correctly recomputed from a test-period-only slice since they depend on trailing history.
- Promotion rule: `challenger_mape <= champion_mape * (1 - promotion_margin_pct)`, `promotion_margin_pct` in `config.yaml` under `gate:`. **Currently `0.05` (5% relative improvement) — this is an explicit placeholder, not a validated number.** There's no historical run-to-run MAPE variance data yet to derive a real margin from. Revisit once several months of real challenger/champion comparisons exist to establish an actual noise floor.
- First-ever run (no champion exists yet): challenger is promoted unconditionally — there's nothing to compare against.
- Promotion = S3 `copy_object` of the challenger's already-written versioned artifact onto the champion pointer — no re-serialization.

## sofType / cardType mapping

`sofType` in source data has more distinct values than `cardType` (many `cardType` values collapse to the same `sofType`, e.g. `HTNS PA POSB`, `NETS 2.0 (ATM)`, `NPC`, `POSB PAssion`, `UPI ATM` all → `NETS2.0`; multiple `SSS (...)` cardTypes all → `SSS`). `SOFTYPE_MAPPING` in `category_mappings.py` is keyed on `sofType`, not `cardType` — never map on `cardType`.

Confirmed real (not data-quality artifacts) and mapped: `CONCESSION`, `EZLINK`, `UNKNOWN` (business confirmed `UNKNOWN` recurs and gets its own code — not filtered, not conflated with another category). If a *new* unmapped `sofType` appears beyond this set, `encode_categoricals` will raise `ValueError` — that's intentional (see Hard rules). Add it to `SOFTYPE_MAPPING` only after confirming with a human; always append a new integer, never reuse or reorder existing codes (XGBoost treats the codes as fixed categorical identities — reordering silently changes what the model has learned).

## Data gotchas

- **Inconsistent date formats** in source data: both `M/DD/YYYY` and `YYYY-MM-DD`. Handled at Athena layer via `TRY(DATE_PARSE(...))` + `COALESCE`; Python side receives normalized `YYYY-MM-DD`.
- **`amount` is in cents**, not dollars — always divide by 100 for revenue.
- **`"NULL"` is a string**, not a real null (source DB export artifact) — compare as string, never `IS NULL` / `.isna()`.
- **Columns excluded from feature set**: `terminalId, readerId, cardId, studentId, studentName` (privacy — see Sensitive data), all network/technical columns, `errorCode/netsErrorCode` (handled via `paymentStatus`), `settlementTimestamp, offlineReconcile_*` (internal reconciliation only).
- Current training columns: `txn_date, txn_time, amount, storeId, schoolId, sofType, paymentMode, paymentStatus`.

## Fixed bugs — don't reintroduce

- `split_train_test`: `test` line once copy-pasted `<=` from `train` (should be `>`). Double-check the split condition if touching this function.
- `encode_categoricals`: return type was once `tuple[df, encoder, encoder]` while callers expected just `df` — simplified to a single return value. Don't revert to multi-value returns here.
- `s3_output` warning from `awswrangler`: not fixed, non-blocking, but always pass `s3_output` explicitly rather than relying on the default bucket.

## Run & test

- Run via `python3 -m scripts.run_train` (or `run_predict`) — **not** `python scripts/run_train.py` directly, so `src` resolves as a package (avoids `ModuleNotFoundError`).
- For testing individual functions, sample via `WHERE storeid IN (...)` on Athena. **Never `LIMIT N`** — random `LIMIT` breaks lag features since each group ends up with 1-2 rows, not enough for `shift(7)`.
- No MLflow in `run_train.py`/`run_predict.py` (SQLite is lost when the SageMaker Processing Job container exits) — save model + metrics directly to S3 as JSON, plus timestamped versions per run (`revenue_model_<timestamp>.json`, `metrics_<timestamp>.json`, `test_set_<timestamp>.parquet`).
- **`revenue_model_latest.json` / `metrics_latest.json` no longer exist / are not the served pointer.** `run_predict.py` loads `revenue_model_champion.json` — only written when a challenger passes the gate (see Champion/challenger gate below). Never point `run_predict.py` at a `_latest`/timestamped artifact directly; it must always go through the champion pointer.

## Current status — living checklist

Update when an item completes. Don't assume an item is done unless it's marked here.

| # | Item | Status |
|---|---|---|
| 1 | Confirm `category_mappings.py` is actually wired into `encode_categoricals` | ✅ Wired in `encode_categoricals`, raises `ValueError` on unmapped category |
| 2 | Champion/challenger gate (re-predict champion on same test set) merged into `run_train.py` | ✅ Merged — see Champion/challenger gate section below |
| 3 | `run_predict.py` run end-to-end, compared against old notebook results | ⏳ Never run as a script |
| 4 | Package `run_train.py`/`run_predict.py` as a SageMaker Processing Job | ⏳ Not started |
| 5 | Add `storeType` (FOOD/BOOK/DRINK) to feature set | ⏳ Value identified, not implemented |
| 6 | Decide whether to keep `mlflow.db` for notebook dev | ⏳ Undecided |

## Open decisions — do not decide unilaterally

These affect `ml/` code but are business/architecture calls, not engineering ones — ask before implementing:

- **Rolling window size** for training data (how many months) — no number set yet.
- **Athena partitioning** (`dt=YYYY-MM/`) — decision owned by infra, outside this file's scope, but implementing it changes how `load_data.py` queries (full scan → partition-scoped). If `load_data.py` needs changes for this reason, confirm with a human first.

## Sensitive data

Columns already excluded from the feature set for privacy: `studentId, studentName, cardId, terminalId, readerId`. **Never re-add** these to any future feature engineering, even if they appear to improve model performance — this is a privacy decision, not a performance one.
