import awswrangler as wr
import pandas as pd


def load_training_data(
        database: str,
        table: str,
        limit: int | None = None,
        s3_output: str | None = None,
    ) -> pd.DataFrame:
    limit_clause = f"LIMIT {limit}" if limit else ""
    df = wr.athena.read_sql_query(
        sql=f"SELECT * FROM {database}.{table} {limit_clause}",
        database=database,
        ctas_approach=False,
        s3_output=s3_output
    )
    df["date"] = pd.to_datetime(df["date"])
    return df
