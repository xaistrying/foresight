import pandas as pd

from src.models.predict import build_lag_stats, build_future_dataframe, predict
from test.build_feature import df_encoded
from test.train import model

# Lag stats from 4/2026 (last month has real data)
recent = df_encoded[df_encoded['date'] >= '2026-04-01']
lag_stats = build_lag_stats(recent, group_cols=['storeid', 'hour', 'softype'])
print(f"Lag stats shape: {lag_stats.shape}")
print(lag_stats.head())

# Create future dataframe for 5/2026
future_dates = pd.date_range(start='2026-05-01', end='2026-05-31')
future_df = build_future_dataframe(lag_stats, future_dates, peak_hours=[9, 13], weekend_days=[6, 7])
print(f"Future df shape: {future_df.shape}")

# Predict
result = predict(model, future_df)
print(result[['date', 'storeid', 'hour', 'softype', 'predicted_revenue']].head(10))
