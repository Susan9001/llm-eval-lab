from datetime import datetime

from sqlalchemy import (
  DateTime,
  ForeignKey,
  String,
  Integer,
  Text,
  BigInteger,
  UniqueConstraint,
  CheckConstraint,
  Index,
  text,
  func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.db import Base


class Dataset(Base):
  __tablename__ = "datasets"
  __table_args__ = (
    UniqueConstraint("dataset_group_uid", "version", "split"),
    CheckConstraint("status IN ('BUILDING', 'READY', 'DEPRECATED')"),
    Index("idx_datasets_group_uid", "dataset_group_uid"),
  )

  dataset_id: Mapped[int] = mapped_column(
    BigInteger, primary_key=True, autoincrement=True
  )
  dataset_group_uid: Mapped[str] = mapped_column(String(255), nullable=False)
  display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
  version: Mapped[str] = mapped_column(String(64), nullable=False)
  split: Mapped[str | None] = mapped_column(String(64), nullable=True)
  description: Mapped[str | None] = mapped_column(Text, nullable=True)
  source: Mapped[str | None] = mapped_column(String(255), nullable=True)
  sampling_spec: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
  content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
  num_samples: Mapped[int | None] = mapped_column(Integer, nullable=True)
  status: Mapped[str] = mapped_column(
    String(32), nullable=False, server_default=text("'READY'")
  )
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), nullable=False, server_default=func.now()
  )

  samples: Mapped[list["Sample"]] = relationship(
    "Sample", back_populates="dataset"
  )
  eval_runs: Mapped[list["EvalRun"]] = relationship(
    "EvalRun", back_populates="dataset"
  )


class Sample(Base):
  __tablename__ = "samples"
  __table_args__ = (
    UniqueConstraint("dataset_id", "source_sample_id"),
    Index("idx_samples_dataset_id", "dataset_id"),
  )

  sample_id: Mapped[int] = mapped_column(
    BigInteger, primary_key=True, autoincrement=True
  )
  dataset_id: Mapped[int] = mapped_column(
    BigInteger, ForeignKey("datasets.dataset_id"), nullable=False
  )
  source_sample_id: Mapped[str] = mapped_column(String(255), nullable=False)
  input_text: Mapped[str] = mapped_column(Text, nullable=False)
  reference_output: Mapped[str | None] = mapped_column(Text, nullable=True)
  metadata_json: Mapped[dict | None] = mapped_column(
    "metadata", JSONB, nullable=True
  )
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), nullable=False, server_default=func.now()
  )

  dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="samples")
  model_outputs: Mapped[list["ModelOutput"]] = relationship(
    "ModelOutput", back_populates="sample"
  )


class Prompt(Base):
  __tablename__ = "prompts"
  __table_args__ = (
    UniqueConstraint("prompt_group_uid", "version"),
    CheckConstraint("purpose IN ('GENERATION', 'JUDGE')"),
    Index("idx_prompts_group_uid", "prompt_group_uid"),
    Index("idx_prompts_purpose", "purpose"),
  )

  prompt_id: Mapped[int] = mapped_column(
    BigInteger, primary_key=True, autoincrement=True
  )
  prompt_group_uid: Mapped[str] = mapped_column(String(255), nullable=False)
  purpose: Mapped[str] = mapped_column(String(32), nullable=False)
  version: Mapped[str] = mapped_column(String(64), nullable=False)
  display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
  template_text: Mapped[str] = mapped_column(Text, nullable=False)
  metadata_json: Mapped[dict | None] = mapped_column(
    "metadata", JSONB, nullable=True
  )
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), nullable=False, server_default=func.now()
  )


class ModelOutput(Base):
  __tablename__ = "model_outputs"
  __table_args__ = (
    CheckConstraint(
      "generation_status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED', 'SKIPPED')"
    ),
    Index("idx_model_outputs_sample_id", "sample_id"),
    Index("idx_model_outputs_generation_status", "generation_status"),
  )

  output_id: Mapped[int] = mapped_column(
    BigInteger, primary_key=True, autoincrement=True
  )
  sample_id: Mapped[int] = mapped_column(
    BigInteger, ForeignKey("samples.sample_id"), nullable=False
  )
  generation_prompt_id: Mapped[int | None] = mapped_column(
    BigInteger, ForeignKey("prompts.prompt_id"), nullable=True
  )
  provider: Mapped[str | None] = mapped_column(Text, nullable=True)
  model_name: Mapped[str | None] = mapped_column(Text, nullable=True)
  generation_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
  generation_status: Mapped[str] = mapped_column(
    Text, nullable=False, server_default=text("'PENDING'")
  )
  output_text: Mapped[str | None] = mapped_column(Text, nullable=True)
  output_artifact_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
  generation_error_message: Mapped[str | None] = mapped_column(
    Text, nullable=True
  )
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), nullable=False, server_default=func.now()
  )
  started_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True), nullable=True
  )
  finished_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True), nullable=True
  )

  sample: Mapped["Sample"] = relationship(
    "Sample", back_populates="model_outputs"
  )
  generation_prompt: Mapped["Prompt | None"] = relationship("Prompt")
  eval_results: Mapped[list["EvalResult"]] = relationship(
    "EvalResult", back_populates="model_output"
  )


class EvalRun(Base):
  __tablename__ = "eval_runs"
  __table_args__ = (
    CheckConstraint(
      "run_status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED')"
    ),
    Index("idx_eval_runs_dataset_id", "dataset_id"),
    Index("idx_eval_runs_parent_run_id", "parent_run_id"),
    Index("idx_eval_runs_run_status", "run_status"),
  )

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
  eval_name: Mapped[str] = mapped_column(String(255), nullable=False)
  eval_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
  run_status: Mapped[str] = mapped_column(
    String(32), nullable=False, server_default=text("'PENDING'")
  )
  git_commit: Mapped[str | None] = mapped_column(String(64), nullable=True)
  config_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), nullable=False, server_default=func.now()
  )
  started_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True), nullable=True
  )
  finished_at: Mapped[datetime | None] = mapped_column(
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
  eval_results: Mapped[list["EvalResult"]] = relationship(
    "EvalResult", back_populates="eval_run"
  )


class EvalResult(Base):
  __tablename__ = "eval_results"
  __table_args__ = (
    UniqueConstraint("run_id", "output_id"),
    CheckConstraint(
      "eval_status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED', 'SKIPPED')"
    ),
    Index("idx_eval_results_run_id", "run_id"),
    Index("idx_eval_results_output_id", "output_id"),
    Index("idx_eval_results_eval_status", "eval_status"),
    Index("idx_eval_results_run_id_eval_status", "run_id", "eval_status"),
  )

  result_id: Mapped[int] = mapped_column(
    BigInteger, primary_key=True, autoincrement=True
  )

  run_id: Mapped[int] = mapped_column(
    BigInteger, ForeignKey("eval_runs.run_id"), nullable=False
  )
  output_id: Mapped[int] = mapped_column(
    BigInteger, ForeignKey("model_outputs.output_id"), nullable=False
  )
  eval_status: Mapped[str] = mapped_column(
    Text, nullable=False, server_default=text("'PENDING'")
  )
  scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
  rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
  eval_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), nullable=False, server_default=func.now()
  )
  started_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True), nullable=True
  )
  finished_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True), nullable=True
  )

  eval_run: Mapped["EvalRun"] = relationship(
    "EvalRun", back_populates="eval_results"
  )
  model_output: Mapped["ModelOutput"] = relationship(
    "ModelOutput", back_populates="eval_results"
  )
