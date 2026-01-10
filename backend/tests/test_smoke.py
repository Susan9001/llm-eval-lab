from sqlalchemy import text
from sqlalchemy import create_engine
from app.db import get_database_url


def test_db_connection_smoke() -> None:
  engine = create_engine(get_database_url())
  with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    assert result.scalar_one() == 1
