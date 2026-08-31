from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Index, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.timezone import utc_now
from app.models.enums import Difficulty, Rating, ReviewStage


problem_tags = Table(
    "problem_tags",
    Base.metadata,
    Column("problem_id", ForeignKey("problems.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_problem_tags_tag_id", "tag_id"),
)


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(primary_key=True)
    leetcode_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    title_en: Mapped[str | None] = mapped_column(String(200))
    leetcode_url: Mapped[str | None] = mapped_column(String(500))
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty, native_enum=False, length=20), default=Difficulty.UNKNOWN)
    rating: Mapped[Rating] = mapped_column(Enum(Rating, native_enum=False, length=20), index=True)
    review_stage: Mapped[ReviewStage] = mapped_column(Enum(ReviewStage, native_enum=False, length=30), index=True)
    mistake_reason: Mapped[str | None] = mapped_column(Text)
    my_solution: Mapped[str | None] = mapped_column(Text)
    correct_solution: Mapped[str | None] = mapped_column(Text)
    key_points: Mapped[str | None] = mapped_column(Text)
    time_complexity: Mapped[str | None] = mapped_column(String(100))
    space_complexity: Mapped[str | None] = mapped_column(String(100))
    code: Mapped[str | None] = mapped_column(Text)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    next_review_at: Mapped[date | None] = mapped_column(Date, index=True)
    review_count: Mapped[int] = mapped_column(default=0)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    tags: Mapped[list["Tag"]] = relationship(secondary=problem_tags, back_populates="problems", lazy="selectin")
    reviews: Mapped[list["ReviewRecord"]] = relationship(
        back_populates="problem", cascade="all, delete-orphan", order_by="ReviewRecord.reviewed_at"
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    problems: Mapped[list[Problem]] = relationship(secondary=problem_tags, back_populates="tags")


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"), index=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    rating: Mapped[Rating] = mapped_column(Enum(Rating, native_enum=False, length=20))
    stage_before: Mapped[ReviewStage | None] = mapped_column(Enum(ReviewStage, native_enum=False, length=30))
    stage_after: Mapped[ReviewStage] = mapped_column(Enum(ReviewStage, native_enum=False, length=30))
    scheduled_interval_days: Mapped[int | None] = mapped_column(Integer)
    next_review_at: Mapped[date | None] = mapped_column(Date)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    used_hint: Mapped[bool] = mapped_column(Boolean, default=False)
    viewed_solution: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    problem: Mapped[Problem] = relationship(back_populates="reviews")


class AppSettings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    red_interval: Mapped[int] = mapped_column(default=1)
    yellow_first_interval: Mapped[int] = mapped_column(default=3)
    yellow_repeat_interval: Mapped[int] = mapped_column(default=7)
    green_first_interval: Mapped[int] = mapped_column(default=7)
    green_second_interval: Mapped[int] = mapped_column(default=14)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    notification_time: Mapped[str] = mapped_column(String(5), default="08:00")
