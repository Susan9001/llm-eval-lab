from __future__ import annotations

import os
import sys
import textwrap
from app.report.render_markdown import build_report_markdown

# Allow running this file directly: python backend/tests/test_render_markdown.py
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
  sys.path.append(BACKEND_DIR)


# This expected string is intentionally verbose and human-readable.
# It serves as a "golden snapshot" to show the report rendering style.
EXPECTED_MARKDOWN = textwrap.dedent(
  """\
  # Demo Report

  ## Run Info
  | Key | Value |
  | --- | --- |
  | `dataset_group_uid` | "agnews_harmful" |
  | `dataset_version` | "v1" |
  | `split` | "test" |
  | `adapter_name` | "agnews_harmful_adapter" |
  | `dataset_display_name` | "AGNews Harmful" |
  | `input_path` | "data/agnews_harmful.csv" |
  | `file_format` | "csv" |
  | `num_samples` | 3 |
  | `sampling` | {"limit": 3, "seed": 42, "should_random_sample": false} |
  | `created_at` | "2026-01-16T00:00:00Z" |
  | `prompt_group_uid` | "agnews_harmful" |
  | `prompt_version` | "v1" |
  | `provider` | "openai" |
  | `model_name` | "gpt-4o-mini" |
  | `judge_type` | "RULE" |
  | `judge_name` | "harmful_rule" |
  | `judge_version` | "v1" |

  ## Metrics
  ### Metrics Meta
  | Key | Value |
  | --- | --- |
  | `binary_label_key` | "is_harmful" |
  | `generated_at` | "2026-01-16T00:01:00Z" |
  | `include_curves` | false |
  | `primary_score_rule` | "v1.rule" |
  | `threshold` | 0.5 |

  ### Metrics Summary Overall
  | Key | Value |
  | --- | --- |
  | `avg_score` | 0.23 |
  | `num_over_threshold` | 1 |
  | `num_primary_scored` | 3 |
  | `num_total` | 3 |
  | `over_threshold_rate` | 0.3333 |

  ### Curves Overall
  _Curves is null._

  ## Top Samples
  ### Top Samples Config
  | Key | Value |
  | --- | --- |
  | `k_low` | 2 |
  | `k_high` | 2 |
  | `k_near` | 0 |

  ### Top Low Score

  | source_sample_id | score | rationale |
  | --- | --- | --- |
  | `s2` | 0.12 | too harmful \\| with pipe |
  | `s3` | 0.22 |  |

  ### Top High Score

  | source_sample_id | score | rationale |
  | --- | --- | --- |
  | `s1` | 0.99 | great multiline |
  | `s3` | 0.22 |  |

  ### Near Threshold

  | source_sample_id | score | rationale |
  | --- | --- | --- |
  |  |  |  |
  """
)


def test_build_report_markdown_golden_snapshot() -> None:
  run_info_section = {
    "dataset_group_uid": "agnews_harmful",
    "dataset_version": "v1",
    "split": "test",
    "adapter_name": "agnews_harmful_adapter",
    "dataset_display_name": "AGNews Harmful",
    "input_path": "data/agnews_harmful.csv",
    "file_format": "csv",
    "num_samples": 3,
    "sampling": {"limit": 3, "seed": 42, "should_random_sample": False},
    "created_at": "2026-01-16T00:00:00Z",
    "prompt_group_uid": "agnews_harmful",
    "prompt_version": "v1",
    "provider": "openai",
    "model_name": "gpt-4o-mini",
    "judge_type": "RULE",
    "judge_name": "harmful_rule",
    "judge_version": "v1",
  }

  # For this test, keep metrics_json minimal and deterministic.
  # It also includes keys we do not want to render (by_model_name/by_prompt_version),
  # so the expected snapshot implicitly documents what is shown by default.
  metrics_json = {
    "meta": {
      "generated_at": "2026-01-16T00:01:00Z",
      "primary_score_rule": "v1.rule",
      "threshold": 0.5,
      "binary_label_key": "is_harmful",
      "include_curves": False,
    },
    "summary": {
      "overall": {
        "avg_score": 0.23,
        "num_total": 3,
        "num_primary_scored": 3,
        "num_over_threshold": 1,
        "over_threshold_rate": 0.3333,
      },
      "by_model_name": {"gpt-4o-mini": {"avg_score": 0.23}},
      "by_prompt_version": {"v1": {"avg_score": 0.23}},
    },
    "curves": None,
  }

  top_samples_section = {
    "k_low": 2,
    "k_high": 2,
    "k_near": 0,
    "top_low_score": [
      {
        "source_sample_id": "s2",
        "score": 0.12,
        "rationale": "too harmful | with pipe",
      },
      {"source_sample_id": "s3", "score": 0.22, "rationale": None},
    ],
    "top_high_score": [
      {
        "source_sample_id": "s1",
        "score": 0.99,
        "rationale": "great\nmultiline",
      },
      {"source_sample_id": "s3", "score": 0.22, "rationale": ""},
    ],
    "near_threshold": [],
  }

  markdown = build_report_markdown(
    run_info_section=run_info_section,
    metrics_json=metrics_json,
    top_samples_section=top_samples_section,
    title="Demo Report",
  )

  assert markdown == EXPECTED_MARKDOWN


if __name__ == "__main__":
  # Simple direct-run mode, helpful when you do not want to invoke pytest.
  test_build_report_markdown_golden_snapshot()
  print("PASS: test_build_report_markdown_golden_snapshot")
