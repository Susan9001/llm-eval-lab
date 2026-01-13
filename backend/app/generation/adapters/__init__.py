from app.generation.adapters.base import register_adapter
from app.generation.adapters.mock_adapter import MockAdapter

register_adapter("mock", MockAdapter())
