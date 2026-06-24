from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Interview, InterviewMessage, Resume
from app.services.llm import DeepSeekInterviewAgent
from app.services.serializers import message_to_dict


def _question_count(interview: Interview) -> int:
    return sum(
        1
        for message in interview.messages
        if message.role == "assistant" and message.message_type == "question"
    )


def _feedback_content(feedback: dict[str, Any]) -> str:
    score = feedback.get("score", "-")
    comment = feedback.get("comment", "")
    return f"本题评分：{score}。{comment}".strip()


def start_interview(db: Session, resume: Resume, level: str = "campus_junior") -> Interview:
    agent = DeepSeekInterviewAgent()
    opening = agent.create_opening_question(resume.analysis_json or {}, level)

    interview = Interview(resume_id=resume.id, level=level, status="active")
    db.add(interview)
    db.flush()

    opening_message = opening.get("opening_message", "")
    question = opening.get("question") or "请介绍一个你最熟悉的 Java 后端项目。"
    content = f"{opening_message}\n\n{question}".strip()
    db.add(
        InterviewMessage(
            interview_id=interview.id,
            role="assistant",
            message_type="question",
            content=content,
            meta_json=opening,
        )
    )
    db.commit()
    db.refresh(interview)
    return interview


def answer_interview(db: Session, interview: Interview, answer: str) -> dict[str, Any]:
    if interview.status != "active":
        raise ValueError("面试已结束，不能继续提交回答。")

    settings = get_settings()
    answer_message = InterviewMessage(
        interview_id=interview.id,
        role="user",
        message_type="answer",
        content=answer.strip(),
        meta_json={},
    )
    db.add(answer_message)
    db.flush()
    db.refresh(interview)

    messages = [message_to_dict(message) for message in interview.messages]
    question_count = _question_count(interview)
    agent = DeepSeekInterviewAgent()
    result = agent.evaluate_answer(
        interview.resume.analysis_json or {},
        messages,
        question_count,
        settings.max_interview_questions,
    )

    if question_count >= settings.max_interview_questions:
        result["next_action"] = "finish"
        result["next_question"] = ""

    feedback = result.get("feedback") or {}
    db.add(
        InterviewMessage(
            interview_id=interview.id,
            role="assistant",
            message_type="feedback",
            content=_feedback_content(feedback),
            meta_json=feedback,
        )
    )

    next_question = (result.get("next_question") or "").strip()
    if result.get("next_action") != "finish" and next_question:
        db.add(
            InterviewMessage(
                interview_id=interview.id,
                role="assistant",
                message_type="question",
                content=next_question,
                meta_json={
                    "focus_area": result.get("focus_area", ""),
                    "expected_points": result.get("expected_points", []),
                    "next_action": result.get("next_action", "ask_next"),
                },
            )
        )

    db.commit()
    db.refresh(interview)
    return result


def finish_interview(db: Session, interview: Interview) -> Interview:
    if interview.summary_json:
        return interview

    agent = DeepSeekInterviewAgent()
    messages = [message_to_dict(message) for message in interview.messages]
    summary = agent.summarize(interview.resume.analysis_json or {}, messages)

    interview.status = "completed"
    interview.summary_json = summary
    db.add(
        InterviewMessage(
            interview_id=interview.id,
            role="assistant",
            message_type="summary",
            content="面试总结已生成。",
            meta_json=summary,
        )
    )
    db.commit()
    db.refresh(interview)
    return interview
