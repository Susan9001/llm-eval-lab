# app/db.py
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()


class Base(DeclarativeBase):
  pass


def get_database_url() -> str:
  user = os.getenv("POSTGRES_USER", "llm_eval")
  password = os.getenv("POSTGRES_PASSWORD", "llm_eval_password")
  host = os.getenv("POSTGRES_HOST", "localhost")
  port = os.getenv("POSTGRES_PORT", "5432")
  database = os.getenv("POSTGRES_DB", "llm_eval_db")
  res = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
  return res


def get_engine(echo: bool = False):
  return create_engine(get_database_url(), echo=echo)
