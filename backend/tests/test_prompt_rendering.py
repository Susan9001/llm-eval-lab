import pytest

from app.prompts.prompt_template import parse_prompt_path, render_prompt


def test_parse_prompt_path_basic() -> None:
  prompt_group_uid, version = parse_prompt_path(
    "truthfulqa_generation_base/v1.txt"
  )
  assert prompt_group_uid == "truthfulqa_generation_base"
  assert version == "v1"


def test_parse_prompt_path_nested_dirs_join_with_underscore() -> None:
  prompt_group_uid, version = parse_prompt_path(
    "truthfulqa_generation_base/test_set/v2.txt"
  )
  assert prompt_group_uid == "truthfulqa_generation_base_test_set"
  assert version == "v2"


def test_parse_prompt_path_requires_parent_dir() -> None:
  with pytest.raises(ValueError):
    parse_prompt_path("v1.txt")


def test_parse_prompt_path_requires_txt_suffix() -> None:
  with pytest.raises(ValueError):
    parse_prompt_path("truthfulqa_generation_base/v1.md")


def test_parse_prompt_path_requires_lowercase_snake_case_group_uid() -> None:
  with pytest.raises(ValueError):
    parse_prompt_path("TruthfulQA/v1.txt")


def test_render_prompt_replaces_input_text() -> None:
  template_text = "Q: {input_text}\n"
  rendered = render_prompt(template_text, input_text="hello")
  assert rendered == "Q: hello\n"


def test_render_prompt_replaces_reference_output() -> None:
  template_text = "Q: {input_text}\nA: {reference_output}\n"
  rendered = render_prompt(
    template_text, input_text="hi", reference_output="there"
  )
  assert rendered == "Q: hi\nA: there\n"


def test_render_prompt_requires_reference_output_when_placeholder_exists() -> (
  None
):
  template_text = "A: {reference_output}\n"
  with pytest.raises(ValueError):
    render_prompt(template_text, input_text="x", reference_output=None)


def test_render_prompt_replaces_output_text() -> None:
  template_text = "Judge: {output_text}\n"
  rendered = render_prompt(template_text, input_text="x", output_text="ok")
  assert rendered == "Judge: ok\n"


def test_render_prompt_requires_output_text_when_placeholder_exists() -> None:
  template_text = "Judge: {output_text}\n"
  with pytest.raises(ValueError):
    render_prompt(template_text, input_text="x", output_text=None)
