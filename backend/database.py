from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./codementor.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String, nullable=False)
    email         = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
    interviews    = relationship("Interview", back_populates="user")


class Interview(Base):
    __tablename__ = "interviews"
    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    company      = Column(String, nullable=False)
    topic        = Column(String, nullable=False)
    difficulty   = Column(String, nullable=False)
    score        = Column(Float, nullable=True)
    started_at   = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    user         = relationship("User", back_populates="interviews")
    questions    = relationship("Question", back_populates="interview")


class Question(Base):
    __tablename__ = "questions"
    id               = Column(Integer, primary_key=True, index=True)
    interview_id     = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    question_text    = Column(Text, nullable=False)
    user_answer      = Column(Text, nullable=True)
    feedback         = Column(Text, nullable=True)
    score            = Column(Float, nullable=True)
    correctness      = Column(String, nullable=True)
    time_complexity  = Column(String, nullable=True)
    space_complexity = Column(String, nullable=True)
    optimal_solution = Column(Text, nullable=True)
    asked_at         = Column(DateTime, default=datetime.utcnow)
    interview        = relationship("Interview", back_populates="questions")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
