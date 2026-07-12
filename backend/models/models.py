"""
ApplyMind AI — SQLAlchemy Database Models
All tables from SRS Section 4.2
"""
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, Boolean,
    ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


class PlanEnum(str, enum.Enum):
    starter = "starter"
    pro = "pro"
    elite = "elite"


class ApplicationStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    CAPTCHA_REQUIRED = "CAPTCHA_REQUIRED"
    FORM_ERROR = "FORM_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    AUTH_FAILED = "AUTH_FAILED"
    DUPLICATE = "DUPLICATE"
    MANUAL_REQUIRED = "MANUAL_REQUIRED"
    BLOCKED = "BLOCKED"


class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    plan = Column(SAEnum(PlanEnum), default=PlanEnum.starter)
    created_at = Column(DateTime, default=datetime.utcnow)
    settings_json = Column(JSON, default={})
    daily_app_limit = Column(Integer, default=50)
    auto_apply_threshold = Column(Integer, default=65)
    is_active = Column(Boolean, default=True)

    resumes = relationship("Resume", back_populates="user", cascade="all, delete")
    job_matches = relationship("JobMatch", back_populates="user", cascade="all, delete")
    applications = relationship("Application", back_populates="user", cascade="all, delete")
    credentials = relationship("Credential", back_populates="user", cascade="all, delete")
    analytics = relationship("Analytics", back_populates="user", cascade="all, delete")


class Resume(Base):
    __tablename__ = "resumes"
    resume_id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    version = Column(Integer, default=1)
    json_data = Column(JSON, nullable=False, default={})
    pdf_path = Column(String)
    docx_path = Column(String)
    raw_text = Column(Text)
    ats_compliance_issues = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resumes")
    variants = relationship("ResumeVariant", back_populates="resume", cascade="all, delete")


class Job(Base):
    __tablename__ = "jobs"
    job_id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String)
    jd_text = Column(Text)
    salary = Column(String)
    apply_url = Column(String)
    apply_method = Column(String)   # linkedin_easy_apply | indeed | wellfound | email | company_site
    source = Column(String)
    posted_date = Column(DateTime)
    scrape_date = Column(DateTime, default=datetime.utcnow)
    dedup_hash = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    remote = Column(Boolean, default=False)
    job_type = Column(String)       # full-time, internship, contract

    matches = relationship("JobMatch", back_populates="job", cascade="all, delete")
    applications = relationship("Application", back_populates="job", cascade="all, delete")
    variants = relationship("ResumeVariant", back_populates="job", cascade="all, delete")
    cover_letters = relationship("CoverLetter", back_populates="job", cascade="all, delete")


class JobMatch(Base):
    __tablename__ = "job_matches"
    match_id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False)
    fit_score = Column(Float, nullable=False)
    gap_analysis = Column(JSON, default={})
    recommendation = Column(String)  # apply | skip | overqualified
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="job_matches")
    job = relationship("Job", back_populates="matches")


class ResumeVariant(Base):
    __tablename__ = "resume_variants"
    variant_id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False)
    resume_id = Column(String, ForeignKey("resumes.resume_id"), nullable=False)
    resume_version = Column(Integer, default=1)
    ats_score = Column(Float)
    keyword_coverage = Column(JSON, default={})
    rewritten_text = Column(Text)
    pdf_path = Column(String)
    docx_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    resume = relationship("Resume", back_populates="variants")
    job = relationship("Job", back_populates="variants")


class CoverLetter(Base):
    __tablename__ = "cover_letters"
    cl_id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False)
    variant = Column(String, default="A")   # A or B
    text = Column(Text)
    tone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="cover_letters")


class Application(Base):
    __tablename__ = "applications"
    app_id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False)
    variant_resume_id = Column(String, ForeignKey("resume_variants.variant_id"))
    cl_id = Column(String, ForeignKey("cover_letters.cl_id"))
    status = Column(SAEnum(ApplicationStatus), default=ApplicationStatus.PENDING)
    platform = Column(String)
    submitted_at = Column(DateTime)
    response_at = Column(DateTime)
    response_type = Column(String)   # interview | rejection | no_response
    submission_log = Column(JSON, default={})
    error_text = Column(Text)
    confirmation_text = Column(Text)

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")


class Credential(Base):
    __tablename__ = "credentials"
    cred_id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    platform = Column(String, nullable=False)
    encrypted_username = Column(Text)
    encrypted_password = Column(Text)
    oauth_token = Column(Text)
    token_expires = Column(DateTime)
    last_login = Column(DateTime)
    rate_limit_hits = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="credentials")


class Analytics(Base):
    __tablename__ = "analytics"
    metric_id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    submissions = Column(Integer, default=0)
    responses = Column(Integer, default=0)
    interviews = Column(Integer, default=0)
    offers = Column(Integer, default=0)
    response_rate = Column(Float, default=0.0)
    ab_winner = Column(String)
    notes = Column(Text)

    user = relationship("User", back_populates="analytics")
