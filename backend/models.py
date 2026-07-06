from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class StartInterviewRequest(BaseModel):
    company: str
    topic: str
    difficulty: str


class SubmitAnswerRequest(BaseModel):
    interview_id: int
    question_id: int
    answer: str


class InterviewSummary(BaseModel):
    id: int
    company: str
    topic: str
    difficulty: str
    score: Optional[float]
    started_at: datetime

    class Config:
        from_attributes = True


class DashboardData(BaseModel):
    name: str
    total_interviews: int
    average_score: float
    weak_topic: str
    recent_interviews: list
