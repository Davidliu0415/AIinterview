from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models import Interview, InterviewMessage, Resume


def _dt(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def message_to_dict(message: InterviewMessage) -> dict[str, Any]:
    return {
        "id": message.id,
        "interview_id": message.interview_id,
        "role": message.role,
        "message_type": message.message_type,
        "content": message.content,
        "meta": message.meta_json or {},
        "created_at": _dt(message.created_at),
    }


def resume_to_dict(resume: Resume) -> dict[str, Any]:
    return {
        "id": resume.id,
        "filename": resume.filename,
        "file_type": resume.file_type,
        "raw_text": resume.raw_text,
        "analysis": resume.analysis_json or {},
        "created_at": _dt(resume.created_at),
    }


def resume_summary_to_dict(resume: Resume) -> dict[str, Any]:
    analysis = resume.analysis_json or {}
    return {
        "id": resume.id,
        "filename": resume.filename,
        "file_type": resume.file_type,
        "candidate_summary": analysis.get("candidate_summary", ""),
        "created_at": _dt(resume.created_at),
    }


def interview_to_dict(interview: Interview, include_resume: bool = False) -> dict[str, Any]:
    data = {
        "id": interview.id,
        "resume_id": interview.resume_id,
        "level": interview.level,
        "status": interview.status,
        "summary": interview.summary_json or {},
        "created_at": _dt(interview.created_at),
        "updated_at": _dt(interview.updated_at),
        "messages": [message_to_dict(message) for message in interview.messages],
    }
    if include_resume and interview.resume:
        data["resume"] = resume_summary_to_dict(interview.resume)
    return data
