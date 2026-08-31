from datetime import date, datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator
from app.models.enums import Difficulty, Rating, ReviewStage
from app.schemas.tag import TagRead
from app.core.timezone import local_today


class ProblemCreate(BaseModel):
    leetcode_id: Annotated[int, Field(gt=0)]
    title: Annotated[str, Field(min_length=1, max_length=200)]
    title_en: str | None = Field(default=None, max_length=200)
    leetcode_url: HttpUrl | None = None
    difficulty: Difficulty = Difficulty.UNKNOWN
    initial_rating: Rating
    solved_on: date = Field(default_factory=local_today)
    tag_ids: list[int] = []
    mistake_reason: str | None = None
    my_solution: str | None = None
    correct_solution: str | None = None
    key_points: str | None = None
    time_complexity: str | None = Field(default=None, max_length=100)
    space_complexity: str | None = Field(default=None, max_length=100)
    code: str | None = None

    @field_validator("solved_on")
    @classmethod
    def solved_on_cannot_be_in_future(cls, value: date) -> date:
        if value > local_today():
            raise ValueError("solved_on cannot be in the future")
        return value


class ProblemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    title_en: str | None = Field(default=None, max_length=200)
    leetcode_url: HttpUrl | None = None
    difficulty: Difficulty | None = None
    tag_ids: list[int] | None = None
    mistake_reason: str | None = None
    my_solution: str | None = None
    correct_solution: str | None = None
    key_points: str | None = None
    time_complexity: str | None = Field(default=None, max_length=100)
    space_complexity: str | None = Field(default=None, max_length=100)
    code: str | None = None


class ProblemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    leetcode_id: int
    title: str
    title_en: str | None
    leetcode_url: str | None
    difficulty: Difficulty
    rating: Rating
    review_stage: ReviewStage
    mistake_reason: str | None
    my_solution: str | None
    correct_solution: str | None
    key_points: str | None
    time_complexity: str | None
    space_complexity: str | None
    code: str | None
    last_reviewed_at: datetime | None
    next_review_at: date | None
    review_count: int
    tags: list[TagRead]
    created_at: datetime
    updated_at: datetime


class ProblemList(BaseModel):
    items: list[ProblemRead]
    total: int
    page: int
    page_size: int
