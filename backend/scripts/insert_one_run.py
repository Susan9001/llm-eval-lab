import uuid
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models.schema import Dataset, Prompt, EvalRun


def main() -> None:
  engine = get_engine()
  run_uid = uuid.uuid4().hex[:16]
  prompt_group_uid = uuid.uuid4().hex

  with Session(engine) as session:
    dataset = Dataset(
      name="smoke_dataset",
      version="v1",
      split="test",
      source="local",
      status="READY",
    )
    session.add(dataset)
    session.flush()  # create dataset.dataset_id

    prompt = Prompt(
      prompt_group_uid=prompt_group_uid,
      purpose="JUDGE",
      version="v1",
      display_name="smoke_judge_prompt",
      template_text="You are a judge. Rate the answer.",
    )
    session.add(prompt)
    session.flush()  # create prompt.prompt_id

    run = EvalRun(
      run_uid=run_uid,
      dataset_id=dataset.dataset_id,
      judge_prompt_id=prompt.prompt_id,
      evaluator_name="llm_judge",
      run_status="PENDING",
      config_name="smoke",
    )
    session.add(run)
    session.commit()

    res = run.run_id
    print(f"inserted eval_run run_id={res}, run_uid={run_uid}")


if __name__ == "__main__":
  main()
