from app.datasets.adapters.base import register_adapter
from app.datasets.adapters.truthfulqa import TruthfulQAAdapter

register_adapter("truthfulqa", TruthfulQAAdapter)
