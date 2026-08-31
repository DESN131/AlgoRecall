from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Problem, ReviewRecord, Tag
from app.models.enums import Rating, ReviewStage


def overview(db: Session, today: date) -> dict:
    active = Problem.is_archived.is_(False)
    def count_where(*conditions) -> int:
        return db.scalar(select(func.count(Problem.id)).where(active, *conditions)) or 0

    total = count_where()
    mastered = count_where(Problem.review_stage == ReviewStage.MASTERED)
    since_7 = datetime.combine(today - timedelta(days=6), time.min)
    since_30 = datetime.combine(today - timedelta(days=29), time.min)
    tags = []
    for tag in db.scalars(select(Tag).order_by(Tag.name)):
        problems = [p for p in tag.problems if not p.is_archived]
        tag_total = len(problems)
        tag_mastered = sum(p.review_stage == ReviewStage.MASTERED for p in problems)
        weak = sum(3 if p.rating == Rating.RED else 2 if p.rating == Rating.YELLOW else 1 for p in problems if p.review_stage != ReviewStage.MASTERED)
        tags.append({"name": tag.name, "total": tag_total, "mastered": tag_mastered, "mastery_rate": round(tag_mastered / tag_total * 100, 1) if tag_total else 0, "weak_score": weak})
    tags.sort(key=lambda x: (-x["weak_score"], x["name"]))
    return {
        "total": total,
        "red": count_where(Problem.rating == Rating.RED, Problem.review_stage != ReviewStage.MASTERED),
        "yellow": count_where(Problem.rating == Rating.YELLOW, Problem.review_stage != ReviewStage.MASTERED),
        "green": count_where(Problem.rating == Rating.GREEN, Problem.review_stage != ReviewStage.MASTERED),
        "mastered": mastered,
        "due_today": count_where(Problem.next_review_at <= today, Problem.review_stage != ReviewStage.MASTERED),
        "overdue": count_where(Problem.next_review_at < today, Problem.review_stage != ReviewStage.MASTERED),
        "reviews_7d": db.scalar(select(func.count(ReviewRecord.id)).where(ReviewRecord.reviewed_at >= since_7)) or 0,
        "reviews_30d": db.scalar(select(func.count(ReviewRecord.id)).where(ReviewRecord.reviewed_at >= since_30)) or 0,
        "tags": tags,
    }

