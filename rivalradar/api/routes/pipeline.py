from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.schemas import User, PipelineJob, PipelineRun
from api.models import PipelineRunResponse, PipelineStatusResponse, PipelineHistoryItem
from api.routes.auth import get_current_user

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


def _run_bg(user_id: str, job_id: str):
    import asyncio
    from agents.orchestrator import run_pipeline
    asyncio.run(run_pipeline(user_id, job_id=job_id))


@router.post("/run", response_model=PipelineRunResponse)
def run_pipeline(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = PipelineJob(user_id=user.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(_run_bg, user.id, job.id)
    return PipelineRunResponse(job_id=job.id)


@router.get("/status/{job_id}", response_model=PipelineStatusResponse)
def get_status(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(PipelineJob).filter_by(id=job_id, user_id=user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return PipelineStatusResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at.isoformat() if job.created_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        error=job.error,
    )


@router.get("/history", response_model=list[PipelineHistoryItem])
def get_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    runs = (
        db.query(PipelineRun)
        .filter_by(user_id=user.id)
        .order_by(PipelineRun.created_at.desc())
        .limit(10)
        .all()
    )
    return [
        PipelineHistoryItem(
            id=r.id,
            job_id=r.job_id,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in runs
    ]
