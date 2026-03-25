import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.schemas import PipelineRun, PipelineJob, User
from agents.agent1_collector import Agent1
from agents.agent2_analyzer import Agent2
from agents.agent3_forecaster import Agent3
from agents.agent4_strategist import Agent4

logger = logging.getLogger(__name__)


async def run_pipeline(user_id: str, job_id: str | None = None) -> dict:
    """Run the full 4-agent pipeline asynchronously."""
    db: Session = SessionLocal()
    try:
        # Mark job running
        if job_id:
            job = db.query(PipelineJob).filter_by(id=job_id).first()
            if job:
                job.status = "running"
                db.commit()

        # Load user
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        domain = user.domain or "saas_b2b"
        frequency = user.update_frequency or "weekly"
        competitors = user.competitors or []

        # Agent 1 — Collector
        agent1 = Agent1(db=db, user_id=user_id)
        agent1_out = await agent1.collect(domain, frequency, competitors)

        profiles = agent1_out.get("structured_profiles", [])

        # Agent 2 — Analyzer
        agent2 = Agent2()
        agent2_out = agent2.analyze(profiles)

        # Agent 3 — Forecaster
        agent3 = Agent3()
        agent3_out = agent3.forecast(agent2_out, profiles)

        # Agent 4 — Strategist
        agent4 = Agent4()
        agent4_out = agent4.strategize(agent2_out, agent3_out)

        # Save run
        run = PipelineRun(
            user_id=user_id,
            job_id=job_id,
            agent1_output=agent1_out,
            agent2_output=agent2_out,
            agent3_output=agent3_out,
            agent4_output=agent4_out,
        )
        db.add(run)

        # Mark job complete
        if job_id:
            job = db.query(PipelineJob).filter_by(id=job_id).first()
            if job:
                job.status = "complete"
                job.completed_at = datetime.now(timezone.utc)

        db.commit()

        return {
            "agent1_output": agent1_out,
            "agent2_output": agent2_out,
            "agent3_output": agent3_out,
            "agent4_output": agent4_out,
        }

    except Exception as exc:
        logger.error("Pipeline failed for user %s: %s", user_id, exc)
        if job_id:
            job = db.query(PipelineJob).filter_by(id=job_id).first()
            if job:
                job.status = "failed"
                job.error = str(exc)
                job.completed_at = datetime.now(timezone.utc)
            db.commit()
        raise
    finally:
        db.close()
