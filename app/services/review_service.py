from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.timezone import local_date_midday_to_utc_naive, local_today, utc_now
from app.models import Problem, ReviewRecord
from app.models.enums import Rating, ReviewStage


@dataclass(frozen=True)
class ReviewSchedule:
    stage: ReviewStage
    interval_days: int | None
    next_review_at: date | None


def calculate_next_review(current_stage: ReviewStage | None, rating: Rating, review_date: date) -> ReviewSchedule:
    if rating == Rating.RED:
        stage, interval = ReviewStage.RED_D1, 1
    elif rating == Rating.YELLOW:
        if current_stage in (ReviewStage.YELLOW_D3, ReviewStage.YELLOW_D7):
            stage, interval = ReviewStage.YELLOW_D7, 7
        else:
            stage, interval = ReviewStage.YELLOW_D3, 3
    elif current_stage == ReviewStage.GREEN_D7:
        stage, interval = ReviewStage.GREEN_D14, 14
    elif current_stage in (ReviewStage.GREEN_D14, ReviewStage.MASTERED):
        stage, interval = ReviewStage.MASTERED, None
    else:
        stage, interval = ReviewStage.GREEN_D7, 7

    return ReviewSchedule(stage, interval, review_date + timedelta(days=interval) if interval else None)


def record_review(
    db: Session,
    problem: Problem,
    rating: Rating,
    *,
    reviewed_at: datetime | None = None,
    review_date: date | None = None,
    duration_minutes: int | None = None,
    used_hint: bool = False,
    viewed_solution: bool = False,
    note: str | None = None,
) -> ReviewRecord:
    effective_review_date = review_date or (reviewed_at.date() if reviewed_at else local_today())
    if reviewed_at is None:
        reviewed_at = (
            utc_now()
            if effective_review_date == local_today()
            else local_date_midday_to_utc_naive(effective_review_date)
        )
    schedule = calculate_next_review(problem.review_stage, rating, effective_review_date)
    record = ReviewRecord(
        problem=problem,
        reviewed_at=reviewed_at,
        rating=rating,
        stage_before=problem.review_stage,
        stage_after=schedule.stage,
        scheduled_interval_days=schedule.interval_days,
        next_review_at=schedule.next_review_at,
        duration_minutes=duration_minutes,
        used_hint=used_hint,
        viewed_solution=viewed_solution,
        note=note.strip() if note else None,
    )
    problem.rating = rating
    problem.review_stage = schedule.stage
    problem.last_reviewed_at = reviewed_at
    problem.next_review_at = schedule.next_review_at
    problem.review_count += 1
    db.add(record)
    db.add(problem)
    return record


def create_initial_review(
    db: Session,
    problem: Problem,
    rating: Rating,
    *,
    review_date: date | None = None,
    reviewed_at: datetime | None = None,
    duration_minutes: int | None = None,
) -> ReviewRecord:
    problem.review_stage = None  # type: ignore[assignment]
    problem.review_count = 0
    return record_review(
        db,
        problem,
        rating,
        reviewed_at=reviewed_at,
        review_date=review_date,
        duration_minutes=duration_minutes,
    )
