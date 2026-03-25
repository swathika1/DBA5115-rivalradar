import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from db.database import get_db
from db.schemas import User
from api.models import SignupRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer = HTTPBearer()

SECRET = os.getenv("JWT_SECRET_KEY", "changeme")
ALGORITHM = "HS256"
EXPIRE_DAYS = 7


def _make_token(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=EXPIRE_DAYS)
    return jwt.encode({"sub": user_id, "exp": exp}, SECRET, algorithm=ALGORITHM)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(creds.credentials, SECRET, algorithms=[ALGORITHM])
        user_id: str = payload["sub"]
    except (JWTError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/signup", response_model=TokenResponse)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter_by(email=req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    # Bcrypt has a 72-byte limit; truncate if necessary
    pwd_to_hash = req.password[:72]
    user = User(
        email=req.email,
        hashed_password=_pwd.hash(pwd_to_hash),
        company_name=req.company_name,
        domain=req.domain,
        competitors=req.competitors,
        update_frequency=req.update_frequency,
        primary_concern=req.primary_concern,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Enqueue background pipeline (no job_id — signup flow)
    from api.main import background_tasks_store
    background_tasks_store.add_task(_run_pipeline_bg, user.id)
    return TokenResponse(access_token=_make_token(user.id))


def _run_pipeline_bg(user_id: str):
    import asyncio
    from agents.orchestrator import run_pipeline
    asyncio.run(run_pipeline(user_id, job_id=None))


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=req.email).first()
    pwd_to_verify = req.password[:72]
    if not user or not _pwd.verify(pwd_to_verify, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=_make_token(user.id))
