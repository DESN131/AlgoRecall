from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.v1.problems import get_problem_or_404
from app.core.database import get_db
from app.core.timezone import local_today
from app.models import Problem, ReviewRecord
from app.models.enums import ReviewStage
from app.schemas.problem import ProblemRead
from app.schemas.review import ReviewCreate, ReviewRead, ScheduleCreate
from app.services.review_service import record_review

router = APIRouter(tags=["Reviews"])
Db = Annotated[Session, Depends(get_db)]


@router.get("/reviews/due", response_model=list[ProblemRead])
def due_reviews(db: Db, limit: int = Query(100, ge=1, le=500)):
    stmt = select(Problem).where(Problem.is_archived.is_(False), Problem.next_review_at <= local_today(), Problem.review_stage != ReviewStage.MASTERED).order_by(Problem.next_review_at.asc()).limit(limit)
    return list(db.scalars(stmt).unique())


@router.post("/problems/{problem_id}/reviews", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def submit_review(problem_id: int, payload: ReviewCreate, db: Db):
    problem = get_problem_or_404(db, problem_id)
    record = record_review(db, problem, payload.rating, duration_minutes=payload.duration_minutes, used_hint=payload.used_hint, viewed_solution=payload.viewed_solution, note=payload.note)
    db.commit()
    db.refresh(record)
    return record


@router.get("/problems/{problem_id}/reviews", response_model=list[ReviewRead])
def review_history(problem_id: int, db: Db):
    get_problem_or_404(db, problem_id)
    return list(db.scalars(select(ReviewRecord).where(ReviewRecord.problem_id == problem_id).order_by(ReviewRecord.reviewed_at.desc())))


@router.post("/problems/{problem_id}/schedule", response_model=ProblemRead)
def schedule_review(problem_id: int, payload: ScheduleCreate, db: Db):
    problem = get_problem_or_404(db, problem_id)
    problem.next_review_at = payload.next_review_at
    db.commit()
    db.refresh(problem)
    return problem

