from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc
from sqlalchemy.orm import Session, selectinload

from app.config import resource_path, get_settings
from app.database import get_db, init_db
from app.models import Interview, Resume
from app.schemas import AnswerRequest, StartInterviewRequest
from app.services.interview import answer_interview, finish_interview, start_interview
from app.services.llm import DeepSeekInterviewAgent
from app.services.resume_parser import ResumeParseError, parse_resume_file
from app.services.serializers import (
    interview_to_dict,
    resume_summary_to_dict,
    resume_to_dict,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI Java Backend Interview Agent", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=resource_path("app/static")), name="static")
templates = Jinja2Templates(directory=resource_path("app/templates"))


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/history", response_class=HTMLResponse)
def history(request: Request):
    return templates.TemplateResponse(request, "history.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/config")
def get_public_config():
    settings = get_settings()
    return {
        "speech_language": settings.speech_language,
        "max_interview_questions": settings.max_interview_questions,
        "model": settings.deepseek_model,
    }


@app.post("/api/resumes")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择简历文件。")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="简历文件不能超过 10MB。")

    try:
        raw_text, file_type = parse_resume_file(file.filename, content)
    except ResumeParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"简历解析失败：{exc.__class__.__name__}") from exc

    analysis = DeepSeekInterviewAgent().analyze_resume(file.filename, raw_text)
    resume = Resume(
        filename=file.filename,
        file_type=file_type,
        raw_text=raw_text,
        analysis_json=analysis,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume_to_dict(resume)


@app.get("/api/resumes")
def list_resumes(db: Session = Depends(get_db)):
    resumes = db.query(Resume).order_by(desc(Resume.created_at)).limit(50).all()
    return [resume_summary_to_dict(resume) for resume in resumes]


@app.get("/api/resumes/{resume_id}")
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.get(Resume, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="简历不存在。")
    return resume_to_dict(resume)


@app.post("/api/interviews")
def create_interview(payload: StartInterviewRequest, db: Session = Depends(get_db)):
    resume = db.get(Resume, payload.resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="简历不存在。")
    interview = start_interview(db, resume, payload.level)
    return interview_to_dict(interview, include_resume=True)


@app.get("/api/interviews")
def list_interviews(db: Session = Depends(get_db)):
    interviews = (
        db.query(Interview)
        .options(selectinload(Interview.resume), selectinload(Interview.messages))
        .order_by(desc(Interview.created_at))
        .limit(50)
        .all()
    )
    return [interview_to_dict(interview, include_resume=True) for interview in interviews]


@app.get("/api/interviews/{interview_id}")
def get_interview(interview_id: int, db: Session = Depends(get_db)):
    interview = (
        db.query(Interview)
        .options(selectinload(Interview.resume), selectinload(Interview.messages))
        .filter(Interview.id == interview_id)
        .one_or_none()
    )
    if interview is None:
        raise HTTPException(status_code=404, detail="面试不存在。")
    return interview_to_dict(interview, include_resume=True)


@app.post("/api/interviews/{interview_id}/answer")
def submit_answer(interview_id: int, payload: AnswerRequest, db: Session = Depends(get_db)):
    interview = (
        db.query(Interview)
        .options(selectinload(Interview.resume), selectinload(Interview.messages))
        .filter(Interview.id == interview_id)
        .one_or_none()
    )
    if interview is None:
        raise HTTPException(status_code=404, detail="面试不存在。")
    try:
        result = answer_interview(db, interview, payload.answer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.refresh(interview)
    return {"result": result, "interview": interview_to_dict(interview, include_resume=True)}


@app.post("/api/interviews/{interview_id}/finish")
def finish(interview_id: int, db: Session = Depends(get_db)):
    interview = (
        db.query(Interview)
        .options(selectinload(Interview.resume), selectinload(Interview.messages))
        .filter(Interview.id == interview_id)
        .one_or_none()
    )
    if interview is None:
        raise HTTPException(status_code=404, detail="面试不存在。")
    interview = finish_interview(db, interview)
    return interview_to_dict(interview, include_resume=True)
