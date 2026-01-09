# app/db.py
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session


load_dotenv()  # 从项目根目录或 backend 目录下的 .env 读取配置


class Base(DeclarativeBase):
    pass


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), unique=True, nullable=False)
    config_name = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False, default="CREATED")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<EvalRun id={self.id} run_id={self.run_id} status={self.status}>"
        )


def get_database_url() -> str:
    user = os.getenv("POSTGRES_USER", "llm_eval")
    password = os.getenv("POSTGRES_PASSWORD", "llm_eval_password")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "llm_eval_db")

    res = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    return res


def create_engine_and_tables():
    database_url = get_database_url()
    engine = create_engine(database_url, echo=False)

    # 建表
    Base.metadata.create_all(bind=engine)

    return engine


def insert_dummy_run(engine):
    now = datetime.utcnow()
    run_id = f"dummy-{int(now.timestamp())}"

    with Session(engine) as session:
        eval_run = EvalRun(
            run_id=run_id,
            config_name="dummy_config",
            status="CREATED",
            created_at=now,
            updated_at=now,
        )
        session.add(eval_run)
        session.commit()

    return run_id


if __name__ == "__main__":
    engine = create_engine_and_tables()
    dummy_run_id = insert_dummy_run(engine)
    print(f"Created eval_runs table and inserted dummy run: {dummy_run_id}")
