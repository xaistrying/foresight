from src.models.metrics import evaluate_model
from test.train import model, test

metrics = evaluate_model(model, test)
print(metrics)
