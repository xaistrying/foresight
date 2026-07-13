import awswrangler as wr
import pandas as pd
from src.features.build_features import filter_outliers, add_time_features, encode_categoricals, add_lag_features

df = wr.athena.read_sql_query(
    sql="""
        SELECT * FROM txn_db.training_data
        WHERE storeid IN ('FTPS.005', 'CCKPS.006')
    """,
    database="txn_db",
    ctas_approach=False,
)
df["date"] = pd.to_datetime(df["date"])
print(f"Shape: {df.shape}")

df_clean = filter_outliers(df, 0.99)
df_time = add_time_features(df_clean, peak_hours=[9, 13], weekend_days=[6, 7])
df_encoded = encode_categoricals(df_time)
df_lag = add_lag_features(df_encoded, group_cols=['storeid', 'hour', 'softype'])

print(f"Shape before dropna: {df_lag.shape}")
df_final = df_lag.dropna()
print(f"Shape after dropna: {df_final.shape}")
print(df_final[['storeid', 'hour', 'softype', 'date', 'total_revenue', 'revenue_lag_1d', 'revenue_lag_7d', 'revenue_rolling_7d']].head(10))