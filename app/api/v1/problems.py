from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errors import api_error
from app.core.database import get_db
from app.core.timezone import local_today
from app.models import Problem, Tag
from app.models.enums import Difficulty, Rating
from app.schemas.problem import ProblemCreate, ProblemList, ProblemRead, ProblemUpdate
from app.services.problem_service import list_problems
from app.services.review_service import create_initial_review

router = APIRouter(prefix="/problems", tags=["Problems"])
Db = Annotated[Session, Depends(get_db)]


def get_problem_or_404(db: Session, problem_id: int) -> Problem:
    problem = db.get(Problem, problem_id)
    if not problem or problem.is_archived:
        raise api_error(404, "PROBLEM_NOT_FOUND", f"Problem #{problem_id} not found.")
    return problem


def resolve_tags(db: Session, tag_ids: list[int]) -> list[Tag]:
    tags = list(db.scalars(select(Tag).where(Tag.id.in_(set(tag_ids))))) if tag_ids else []
    if len(tags) != len(set(tag_ids)):
        raise api_error(422, "TAG_NOT_FOUND", "One or more tags do not exist.")
    return tags


@router.get("", response_model=ProblemList)
def get_problems(db: Db, rating: str | None = None, difficulty: Difficulty | None = None, tag: str | None = None, due: str | None = None, search: str | None = None, sort: str = "next_review_at", order: Literal["asc", "desc"] = "asc", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    items, total = list_problems(db, today=local_today(), rating=rating, difficulty=difficulty, tag=tag, due=due, search=search, sort=sort, order=order, page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=ProblemRead, status_code=status.HTTP_201_CREATED)
def create_problem(payload: ProblemCreate, db: Db):
    if db.scalar(select(Problem.id).where(Problem.leetcode_id == payload.leetcode_id)):
        raise api_error(409, "PROBLEM_ALREADY_EXISTS", f"LeetCode problem #{payload.leetcode_id} already exists.")
    data = payload.model_dump(exclude={"initial_rating", "tag_ids", "solved_on"})
    if data.get("leetcode_url") is not None:
        data["leetcode_url"] = str(data["leetcode_url"])
    problem = Problem(**data, rating=payload.initial_rating, review_stage="RED_D1", tags=resolve_tags(db, payload.tag_ids))
    db.add(problem)
    create_initial_review(db, problem, payload.initial_rating, review_date=payload.solved_on)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise api_error(409, "PROBLEM_ALREADY_EXISTS", f"LeetCode problem #{payload.leetcode_id} already exists.")
    db.refresh(problem)
    return problem


@router.get("/{problem_id}", response_model=ProblemRead)
def get_problem(problem_id: int, db: Db):
    return get_problem_or_404(db, problem_id)


@router.patch("/{problem_id}", response_model=ProblemRead)
def update_problem(problem_id: int, payload: ProblemUpdate, db: Db):
    problem = get_problem_or_404(db, problem_id)
    changes = payload.model_dump(exclude_unset=True, exclude={"tag_ids"})
    if "leetcode_url" in changes and changes["leetcode_url"] is not None:
        changes["leetcode_url"] = str(changes["leetcode_url"])
    for field, value in changes.items():
        setattr(problem, field, value)
    if payload.tag_ids is not None:
        problem.tags = resolve_tags(db, payload.tag_ids)
    db.commit()
    db.refresh(problem)
    return problem


@router.delete("/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_problem(problem_id: int, db: Db):
    problem = get_problem_or_404(db, problem_id)
    problem.is_archived = True
    db.commit()
    return Response(status_code=204)
