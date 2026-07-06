from fastapi import FastAPI, Depends, HTTPException, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional
import traceback

from backend.database import get_db, init_db, User, Interview, Question
from backend.auth import hash_password, verify_password, create_token, get_current_user_id
from backend.ai import generate_question, evaluate_answer, evaluate_followup, get_weak_topic

app = FastAPI(title="CodeMentor AI")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="frontend")


# ─── Error handlers ───────────────────────────────────────────────────────────

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return await http_exception_handler(request, exc)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    if request.url.path.startswith("/api/"):
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"detail": str(exc)})
    raise exc


# ─── Startup ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    init_db()


# ─── Pages ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")

@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")

@app.get("/interview", response_class=HTMLResponse)
def interview_page(request: Request):
    return templates.TemplateResponse(request, "interview.html")

@app.get("/feedback", response_class=HTMLResponse)
def feedback_page(request: Request):
    return templates.TemplateResponse(request, "feedback.html")

@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request):
    return templates.TemplateResponse(request, "history.html")


# ─── Auth ─────────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/api/signup")
def signup(data: SignupRequest, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered.")
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    user = User(name=data.name.strip(), email=data.email.lower(),
                password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user.id, user.email)
    response.set_cookie(key="access_token", value=token, httponly=True,
                        max_age=60*60*24*7, samesite="lax")
    return {"message": "Account created.", "name": user.name}

@app.post("/api/login")
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_token(user.id, user.email)
    response.set_cookie(key="access_token", value=token, httponly=True,
                        max_age=60*60*24*7, samesite="lax")
    return {"message": "Logged in.", "name": user.name}

@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out."}

@app.get("/api/me")
def get_me(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"id": user.id, "name": user.name, "email": user.email}


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.get("/api/dashboard")
def get_dashboard(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    interviews = db.query(Interview).filter(Interview.user_id == user_id).all()
    completed  = [iv for iv in interviews if iv.score is not None]
    avg_score  = round(sum(iv.score for iv in completed) / len(completed), 1) if completed else 0
    weak_topic = get_weak_topic([{"topic": iv.topic, "score": iv.score} for iv in completed])
    recent     = sorted(interviews, key=lambda x: x.started_at, reverse=True)[:5]
    return {
        "name": user.name,
        "total_interviews": len(interviews),
        "average_score": avg_score,
        "weak_topic": weak_topic,
        "recent_interviews": [
            {"id": iv.id, "company": iv.company, "topic": iv.topic,
             "difficulty": iv.difficulty, "score": iv.score,
             "started_at": iv.started_at.strftime("%b %d, %Y")}
            for iv in recent
        ]
    }


# ─── Interview ────────────────────────────────────────────────────────────────

class StartInterviewRequest(BaseModel):
    company: str
    topic: str
    difficulty: str

class SubmitAnswerRequest(BaseModel):
    interview_id: int
    question_id: int
    answer: str

class FollowUpRequest(BaseModel):
    question: str
    answer: str

@app.post("/api/interview/start")
def start_interview(data: StartInterviewRequest,
                    user_id: int = Depends(get_current_user_id),
                    db: Session = Depends(get_db)):
    valid_companies    = ["Google", "Microsoft", "Amazon", "Atlassian", "Adobe"]
    valid_topics       = ["Arrays", "Strings", "Trees", "Graphs", "Dynamic Programming",
                          "Greedy", "Binary Search", "Linked Lists", "Stacks & Queues", "Hashing"]
    valid_difficulties = ["Easy", "Medium", "Hard"]

    if data.company not in valid_companies:
        raise HTTPException(status_code=400, detail="Invalid company.")
    if data.topic not in valid_topics:
        raise HTTPException(status_code=400, detail="Invalid topic.")
    if data.difficulty not in valid_difficulties:
        raise HTTPException(status_code=400, detail="Invalid difficulty.")

    try:
        question_text = generate_question(data.company, data.topic, data.difficulty)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    interview = Interview(user_id=user_id, company=data.company,
                          topic=data.topic, difficulty=data.difficulty)
    db.add(interview)
    db.commit()
    db.refresh(interview)

    question = Question(interview_id=interview.id, question_text=question_text)
    db.add(question)
    db.commit()
    db.refresh(question)

    return {
        "interview_id": interview.id,
        "question_id":  question.id,
        "question":     question_text,
        "company":      data.company,
        "topic":        data.topic,
        "difficulty":   data.difficulty
    }


@app.post("/api/interview/submit")
def submit_answer(data: SubmitAnswerRequest,
                  user_id: int = Depends(get_current_user_id),
                  db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(
        Interview.id == data.interview_id, Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")

    question = db.query(Question).filter(
        Question.id == data.question_id,
        Question.interview_id == data.interview_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    if len(data.answer.strip()) < 20:
        raise HTTPException(status_code=400, detail="Please write a more complete answer.")

    try:
        evaluation = evaluate_answer(
            question=question.question_text,
            answer=data.answer,
            topic=interview.topic,
            difficulty=interview.difficulty
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    question.user_answer      = data.answer
    question.score            = evaluation["score"]
    question.feedback         = evaluation["overall_feedback"]
    question.correctness      = evaluation["correctness"]
    question.time_complexity  = evaluation["time_complexity"]
    question.space_complexity = evaluation["space_complexity"]
    question.optimal_solution = evaluation["optimal_solution"]

    interview.score        = float(evaluation["score"])
    interview.completed_at = datetime.utcnow()
    db.commit()

    return {"interview_id": interview.id, "question_id": question.id, "evaluation": evaluation}


@app.post("/api/followup")
def followup(data: FollowUpRequest, user_id: int = Depends(get_current_user_id)):
    if not data.answer.strip():
        raise HTTPException(status_code=400, detail="Answer cannot be empty.")
    try:
        feedback = evaluate_followup(data.question, data.answer)
        return {"feedback": feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── History ──────────────────────────────────────────────────────────────────

@app.get("/api/history")
def get_history(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    interviews = db.query(Interview).filter(
        Interview.user_id == user_id).order_by(Interview.started_at.desc()).all()
    return [
        {"id": iv.id, "company": iv.company, "topic": iv.topic,
         "difficulty": iv.difficulty, "score": iv.score,
         "started_at": iv.started_at.strftime("%b %d, %Y")}
        for iv in interviews
    ]

@app.get("/api/history/{interview_id}")
def get_interview_detail(interview_id: int,
                         user_id: int = Depends(get_current_user_id),
                         db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(
        Interview.id == interview_id, Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")
    questions = db.query(Question).filter(Question.interview_id == interview_id).all()
    return {
        "id": interview.id, "company": interview.company, "topic": interview.topic,
        "difficulty": interview.difficulty, "score": interview.score,
        "started_at": interview.started_at.strftime("%b %d, %Y at %H:%M"),
        "questions": [
            {"id": q.id, "question": q.question_text, "answer": q.user_answer,
             "score": q.score, "correctness": q.correctness,
             "time_complexity": q.time_complexity, "space_complexity": q.space_complexity,
             "feedback": q.feedback, "optimal_solution": q.optimal_solution}
            for q in questions
        ]
    }
