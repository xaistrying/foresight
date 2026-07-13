from src.models.train import split_train_test, train_model
from test.build_feature import df_final

train, test = split_train_test(df_final)
print(f"Train: {train.shape}, Test: {test.shape}")
print(f"Train date range: {train['date'].min()} → {train['date'].max()}")
print(f"Test date range: {test['date'].min()} → {test['date'].max()}")

model_config = {
    "n_estimators": 300,
    "max_depth": 6,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "random_state": 42,
    "early_stopping_rounds": 30,
    "n_jobs": -1,
}

model = train_model(train, test, model_config)
print(f"Best iteration: {model.best_iteration}")
