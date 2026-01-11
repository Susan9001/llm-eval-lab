# backend/tests/test_smoke_db_seed.py
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models.schema import (
  Dataset,
  Sample,
  Prompt,
  ModelOutput,
  EvalRun,
  EvalResult,
)


@contextmanager
def session_with_rollback():
  engine = get_engine()
  connection = engine.connect()
  transaction = connection.begin()
  session = Session(bind=connection)
  try:
    yield session
  finally:
    session.close()
    transaction.rollback()
    connection.close()


def count_rows(session: Session, model) -> int:
  res = session.scalar(select(func.count()).select_from(model))
  return int(res or 0)


def test_smoke_db_seed_6_tables_and_rollback() -> None:
  run_uid = uuid.uuid4().hex[:16]
  now = datetime.now(timezone.utc)

  dataset_group_uid = "smoke_dataset"
  dataset_version = run_uid
  split = "test"

  generation_prompt_group_uid = "smoke_generation_prompt"
  judge_prompt_group_uid = "smoke_judge_prompt"
  prompt_version = run_uid

  with session_with_rollback() as session:
    baseline = {
      "datasets": count_rows(session, Dataset),
      "samples": count_rows(session, Sample),
      "prompts": count_rows(session, Prompt),
      "model_outputs": count_rows(session, ModelOutput),
      "eval_runs": count_rows(session, EvalRun),
      "eval_results": count_rows(session, EvalResult),
    }

    dataset = Dataset(
      dataset_group_uid=dataset_group_uid,
      display_name="Smoke Dataset",
      version=dataset_version,
      split=split,
      source="local",
      sampling_spec={"note": "pytest smoke seed"},
    )
    session.add(dataset)
    session.flush()  # insert but not commit

    sample = Sample(
      dataset_id=dataset.dataset_id,
      source_sample_id=123,
      input_text="What is 2 + 2?",
      reference_output="4",
      metadata_json={"category": "math"},
    )
    session.add(sample)
    session.flush()

    generation_prompt = Prompt(
      prompt_group_uid=generation_prompt_group_uid,
      purpose="GENERATION",
      version=prompt_version,
      display_name="Smoke Generation Prompt",
      template_text="Question: {input}\nAnswer:",
      metadata_json={"format": "plain"},
    )
    judge_prompt = Prompt(
      prompt_group_uid=judge_prompt_group_uid,
      purpose="JUDGE",
      version=prompt_version,
      display_name="Smoke Judge Prompt",
      template_text="Question: {input}\nAnswer: {output}\nReturn JSON {overall: float}.",
      metadata_json={"format": "json"},
    )
    session.add_all([generation_prompt, judge_prompt])
    session.flush()

    model_output = ModelOutput(
      sample_id=sample.sample_id,
      generation_prompt_id=generation_prompt.prompt_id,
      provider="mock",
      model_name="mock-001",
      generation_params={"temperature": 0.0, "max_tokens": 16},
      generation_status="SUCCEEDED",
      output_text="4",
      started_at=now,
      finished_at=now,
    )
    session.add(model_output)
    session.flush()

    eval_run = EvalRun(
      run_uid=run_uid,
      dataset_id=dataset.dataset_id,
      judge_prompt_id=judge_prompt.prompt_id,
      eval_name="llm_judge",
      eval_params={"judge_model": "mock-judge-001", "temperature": 0.0},
      run_status="SUCCEEDED",
      config_name="smoke",
      started_at=now,
      finished_at=now,
    )
    session.add(eval_run)
    session.flush()

    eval_result = EvalResult(
      run_id=eval_run.run_id,
      output_id=model_output.output_id,
      eval_status="SUCCEEDED",
      scores={"overall": 1.0},
      rationale="Correct answer.",
      eval_error_message=None,
      started_at=now,
      finished_at=now,
    )
    session.add(eval_result)
    session.flush()

    assert count_rows(session, Dataset) == baseline["datasets"] + 1
    assert count_rows(session, Sample) == baseline["samples"] + 1
    assert count_rows(session, Prompt) == baseline["prompts"] + 2
    assert count_rows(session, ModelOutput) == baseline["model_outputs"] + 1
    assert count_rows(session, EvalRun) == baseline["eval_runs"] + 1
    assert count_rows(session, EvalResult) == baseline["eval_results"] + 1

    fetched_result = session.scalar(
      select(EvalResult).where(EvalResult.result_id == eval_result.result_id)
    )
    assert fetched_result is not None
    assert fetched_result.eval_run.run_uid == run_uid
    assert fetched_result.model_output.sample_id == sample.sample_id

  with session_with_rollback() as session:
    res = session.scalar(
      select(func.count())
      .select_from(EvalRun)
      .where(EvalRun.run_uid == run_uid)
    )
    assert int(res or 0) == 0
