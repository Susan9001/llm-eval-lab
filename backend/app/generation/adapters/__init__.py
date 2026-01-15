from app.generation.adapters.base import register_adapter
from app.generation.adapters.harmful_score_adapter import HarmfulScoreAdapter
from app.generation.adapters.mock_adapter import MockAdapter

register_adapter("mock", MockAdapter())
register_adapter("harmful_score", HarmfulScoreAdapter())
