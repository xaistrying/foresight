import yaml
from src.data.load_data import load_training_data

config = yaml.safe_load(open("configs/config.yaml"))

print("Loading data from Athena...")
df = load_training_data(
    database=config["athena"]["database"],
    table=config["athena"]["training_table"],
    limit=10,
    s3_output=config["athena"]["s3_output"]
)

print(f"Shape: {df.shape}")
print(f"Colums: {df.columns.to_list()}")
print(df.head())
