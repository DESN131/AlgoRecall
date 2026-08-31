from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import Rating, ReviewStage


class ReviewCreate(BaseModel):
    rating: Rating
    duration_minutes: int | None = Field(default=None, ge=0, le=600)
    used_hint: bool = False
    viewed_solution: bool = False
    note: str | None = None


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    problem_id: int
    reviewed_at: datetime
    rating: Rating
    stage_before: ReviewStage | None
    stage_after: ReviewStage
    scheduled_interval_days: int | None
    next_review_at: date | None
    duration_minutes: int | None
    used_hint: bool
    viewed_solution: bool
    note: str | None


class ScheduleCreate(BaseModel):
    next_review_at: date

