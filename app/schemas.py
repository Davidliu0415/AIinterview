from __future__ import annotations

from pydantic import BaseModel, Field


class StartInterviewRequest(BaseModel):
    resume_id: int
    level: str = Field(default="campus_junior")


class AnswerRequest(BaseModel):
    answer: str = Field(min_length=1)
