from datetime import datetime, timezone

from sqlalchemy import (
  DateTime,
  ForeignKey,
  String,
  JSON,
  Integer,
  Text,
  BigInteger,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow():
  return datetime.now(timezone.utc)


class Dataset(Base):
  __tablename__ = "datasets"

  dataset_id: Mapped[int] = mapped_column(
    BigInteger, primary_key=True, autoincrement=True
  )
  name: Mapped[str] = mapped_column(String(255), nullable=False)
  version: Mapped[str] = mapped_column(String(64), nullable=False)
  split: Mapped[str | None] = mapped_column(String(64), nullable=True)
  description: Mapped[str | None] = mapped_column(Text, nullable=True)
  source: Mapped[str | None] = mapped_column(String(255), nullable=True)
  sampling_spec: Mapped[dict | None] = mapped_column(JSON, nullable=True)
  content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
  num_samples: Mapped[int | None] = mapped_column(Integer, nullable=True)
  status: Mapped[str] = mapped_column(
    String(32), nullable=False, default="READY"
  )
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), nullable=False, default=utcnow
  )

  samples: Mapped[list["Sample"]] = relationship(
    "Sample", back_populates="dataset"
  )
  eval_runs: Mapped[list["EvalRun"]] = relationship(
    "EvalRun", back_populates="dataset"
  )


class Sample(Base):
  __tablename__ = "samples"

  sample_id: Mapped[int] = mapped_column(
    BigInteger, primary_key=True, autoincrement=True
  )
  dataset_id: Mapped[int] = mapped_column(
    BigInteger, ForeignKey("datasets.dataset_id"), nullable=False
  )
  external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
  input_text: Mapped[str] = mapped_column(Text, nullable=False)
  reference_output: Mapped[str | None] = mapped_column(Text, nullable=True)
  metadata_json: Mapped[dict | None] = mapped_column(
    "metadata", JSON, nullable=True
  )
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), nullable=False, default=utcnow
  )

  dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="samples")


class Prompt(Base):
  __tablename__ = "prompts"

  prompt_id: Mapped[int] = mapped_column(
    BigInteger, primary_key=True, autoincrement=True
  )
  prompt_group_uid: Mapped[str] = mapped_column(String(255), nullable=False)
  purpose: Mapped[str] = mapped_column(String(32), nullable=False)
  version: Mapped[str] = mapped_column(String(64), nullable=False)
  display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
  template_text: Mapped[str] = mapped_column(Text, nullable=False)
  metadata_json: Mapped[dict | None] = mapped_column(
    "metadata", JSON, nullable=True
  )
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), nullable=False, default=utcnow
  )


class EvalRun(Base):
  __tablename__ = "eval_runs"

  run_id: Mapped[int] = mapped_column(
    BigInteger, primary_key=True, autoincrement=True
  )
  run_uid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
  dataset_id: Mapped[int | None] = mapped_column(
    BigInteger, ForeignKey("datasets.dataset_id"), nullable=True
  )
  judge_prompt_id: Mapped[int | None] = mapped_column(
    BigInteger, ForeignKey("prompts.prompt_id"), nullable=True
  )
  parent_run_id: Mapped[int | None] = mapped_column(
    BigInteger, ForeignKey("eval_runs.run_id"), nullable=True
  )
  evaluator_name: Mapped[str] = mapped_column(String(255), nullable=False)
  evaluator_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
  run_status: Mapped[str] = mapped_column(
    String(32), nullable=False, default="PENDING"
  )
  git_commit: Mapped[str | None] = mapped_column(String(64), nullable=True)
  config_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), nullable=False, default=utcnow
  )
  started_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), nullable=True
  )
  finished_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), nullable=True
  )

  dataset: Mapped["Dataset"] = relationship(
    "Dataset", back_populates="eval_runs"
  )
  parent_run: Mapped["EvalRun | None"] = relationship(
    "EvalRun",
    remote_side=lambda: [EvalRun.run_id],
    back_populates="child_runs",
  )

  child_runs: Mapped[list["EvalRun"]] = relationship(
    "EvalRun",
    back_populates="parent_run",
  )
