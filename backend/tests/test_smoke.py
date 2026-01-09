from sqlalchemy.orm import Session
from app.db import EvalRun, create_engine_and_tables, insert_dummy_run


def test_insert_dummy_run_and_query_back() -> None:
  """最小 smoke test:
  1. 建表
  2. 插入一条 dummy run
  3. 用 run_id 把它查出来
  4. 删掉这条记录
  """

  engine = create_engine_and_tables()

  run_id = insert_dummy_run(engine)

  with Session(engine) as session:
    eval_run = session.query(EvalRun).filter(EvalRun.run_id == run_id).one()

    assert eval_run.run_id == run_id
    assert eval_run.status == "CREATED"
    assert eval_run.id is not None

    # 清理: 删除这条 dummy 数据
    session.delete(eval_run)
    session.commit()
