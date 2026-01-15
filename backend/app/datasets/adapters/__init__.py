from app.datasets.adapters.base import register_adapter
from app.datasets.adapters.truthfulqa import TruthfulQAAdapter
from app.datasets.adapters.agnews_harmful import AgNewsHarmfulAdapter

register_adapter("truthfulqa", TruthfulQAAdapter)
register_adapter("agnews_harmful", AgNewsHarmfulAdapter)
