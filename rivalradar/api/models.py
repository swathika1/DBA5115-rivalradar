from pydantic import BaseModel
from typing import Any, Optional


# Auth
class SignupRequest(BaseModel):
    email: str
    password: str
    company_name: Optional[str] = None
    domain: Optional[str] = None
    competitors: Optional[list[str]] = None
    update_frequency: str = "weekly"
    primary_concern: str = "Pricing Threats"


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Dashboard
class DashboardResponse(BaseModel):
    status: Optional[str] = None
    agent1_output: Optional[Any] = None
    agent2_output: Optional[Any] = None
    agent3_output: Optional[Any] = None
    agent4_output: Optional[Any] = None
    created_at: Optional[str] = None


# Pipeline
class PipelineRunResponse(BaseModel):
    job_id: str


class PipelineStatusResponse(BaseModel):
    job_id: str
    status: str
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class PipelineHistoryItem(BaseModel):
    id: str
    job_id: Optional[str] = None
    created_at: str


# Settings
class SettingsUpdateRequest(BaseModel):
    update_frequency: Optional[str] = None
    primary_concern: Optional[str] = None
    competitors: Optional[list[str]] = None


class SettingsUpdateResponse(BaseModel):
    success: bool


# Chat
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
