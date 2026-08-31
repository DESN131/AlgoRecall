from datetime import date

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.models import Problem, Tag
from app.models.enums import Difficulty, Rating, ReviewStage


SORT_COLUMNS = {
    "leetcode_id": Problem.leetcode_id,
    "created_at": Problem.created_at,
    "updated_at": Problem.updated_at,
    "last_reviewed_at": Problem.last_reviewed_at,
    "next_review_at": Problem.next_review_at,
    "review_count": Problem.review_count,
}


def problem_query(*, rating=None, difficulty=None, tag=None, due=None, search=None, today: date):
    stmt = select(Problem).where(Problem.is_archived.is_(False))
    if rating == "MASTERED":
        stmt = stmt.where(Problem.review_stage == ReviewStage.MASTERED)
    elif rating:
        stmt = stmt.where(Problem.rating == rating, Problem.review_stage != ReviewStage.MASTERED)
    if difficulty:
        stmt = stmt.where(Problem.difficulty == difficulty)
    if tag:
        stmt = stmt.where(Problem.tags.any(or_(Tag.name == tag, Tag.id == int(tag) if str(tag).isdigit() else False)))
    if due == "today":
        stmt = stmt.where(Problem.next_review_at == today)
    elif due == "overdue":
        stmt = stmt.where(Problem.next_review_at < today)
    elif due == "future":
        stmt = stmt.where(Problem.next_review_at > today)
    elif due == "mastered":
        stmt = stmt.where(Problem.review_stage == ReviewStage.MASTERED)
    elif due == "due":
        stmt = stmt.where(Problem.next_review_at <= today)
    if search:
        pattern = f"%{search.strip()}%"
        clauses = [Problem.title.ilike(pattern), Problem.title_en.ilike(pattern)]
        if search.strip().isdigit():
            clauses.append(Problem.leetcode_id == int(search.strip()))
        stmt = stmt.where(or_(*clauses))
    return stmt


def list_problems(db: Session, *, today: date, rating=None, difficulty=None, tag=None, due=None, search=None, sort="next_review_at", order="asc", page=1, page_size=20):
    stmt = problem_query(rating=rating, difficulty=difficulty, tag=tag, due=due, search=search, today=today)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    column = SORT_COLUMNS.get(sort, Problem.next_review_at)
    direction = column.desc() if order == "desc" else column.asc()
    if sort == "next_review_at":
        stmt = stmt.order_by(case((Problem.next_review_at.is_(None), 1), else_=0), direction)
    else:
        stmt = stmt.order_by(direction)
    items = list(db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).unique())
    return items, total

