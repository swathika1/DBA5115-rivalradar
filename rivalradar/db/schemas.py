import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from db.database import Base


def _now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    domain = Column(String, nullable=True)
    competitors = Column(JSON, nullable=True)  # list of str
    update_frequency = Column(String, default="weekly")
    primary_concern = Column(String, default="Pricing Threats")
    created_at = Column(DateTime(timezone=True), default=_now)
    pipeline_runs = relationship("PipelineRun", back_populates="user", cascade="all, delete")
    pipeline_jobs = relationship("PipelineJob", back_populates="user", cascade="all, delete")


class PipelineJob(Base):
    __tablename__ = "pipeline_jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending")  # pending/running/complete/failed
    created_at = Column(DateTime(timezone=True), default=_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    user = relationship("User", back_populates="pipeline_jobs")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    job_id = Column(String, ForeignKey("pipeline_jobs.id"), nullable=True)
    agent1_output = Column(JSON, nullable=True)
    agent2_output = Column(JSON, nullable=True)
    agent3_output = Column(JSON, nullable=True)
    agent4_output = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)
    user = relationship("User", back_populates="pipeline_runs")


class ScrapeCache(Base):
    __tablename__ = "scrape_cache"
    url = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)
    content_hash = Column(String, nullable=True)
