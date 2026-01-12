from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.schema import Prompt


_ALLOWED_PURPOSES = {"GENERATION", "JUDGE"}


def upsert_prompt(
  session: Session,
  *,
  prompt_group_uid: str,
  version: str,
  purpose: str,
  template_text: str,
  display_name: str | None = None,
  description: str | None = None,
) -> int:
  """
  Insert or update a prompt row, and return prompt_id.

  Uniqueness:
    (prompt_group_uid, version)

  Raises:
    ValueError: if purpose is not allowed.
  """
  if purpose not in _ALLOWED_PURPOSES:
    raise ValueError(
      f"Invalid purpose: {purpose}. Allowed: {sorted(_ALLOWED_PURPOSES)}"
    )

  prompt = session.execute(
    select(Prompt).where(
      Prompt.prompt_group_uid == prompt_group_uid,
      Prompt.version == version,
    )
  ).scalar_one_or_none()

  if prompt is None:
    prompt = Prompt(
      prompt_group_uid=prompt_group_uid,
      version=version,
      purpose=purpose,
      template_text=template_text,
      display_name=display_name,
      description=description,
    )
    session.add(prompt)
  else:
    prompt.purpose = purpose
    prompt.template_text = template_text
    prompt.display_name = display_name
    prompt.description = description

  session.commit()
  session.refresh(prompt)
  return int(prompt.prompt_id)
