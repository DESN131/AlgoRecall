from pydantic import BaseModel


class TagStatistic(BaseModel):
    name: str
    total: int
    mastered: int
    mastery_rate: float
    weak_score: int


class StatisticsOverview(BaseModel):
    total: int
    red: int
    yellow: int
    green: int
    mastered: int
    due_today: int
    overdue: int
    reviews_7d: int
    reviews_30d: int
    tags: list[TagStatistic] = []

