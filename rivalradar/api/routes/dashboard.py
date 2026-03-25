from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db.schemas import User, PipelineRun
from api.models import DashboardResponse, SettingsUpdateRequest, SettingsUpdateResponse
from api.routes.auth import get_current_user

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    run = (
        db.query(PipelineRun)
        .filter_by(user_id=user.id)
        .order_by(PipelineRun.created_at.desc())
        .first()
    )
    if not run:
        return DashboardResponse(status="pipeline_pending")
    return DashboardResponse(
        agent1_output=run.agent1_output,
        agent2_output=run.agent2_output,
        agent3_output=run.agent3_output,
        agent4_output=run.agent4_output,
        created_at=run.created_at.isoformat() if run.created_at else None,
    )


@router.patch("/user/settings", response_model=SettingsUpdateResponse)
def update_settings(
    req: SettingsUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.update_frequency is not None:
        user.update_frequency = req.update_frequency
    if req.primary_concern is not None:
        user.primary_concern = req.primary_concern
    if req.competitors is not None:
        user.competitors = req.competitors
    db.commit()
    return SettingsUpdateResponse(success=True)
