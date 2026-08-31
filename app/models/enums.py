from enum import StrEnum


class Rating(StrEnum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


class ReviewStage(StrEnum):
    RED_D1 = "RED_D1"
    YELLOW_D3 = "YELLOW_D3"
    YELLOW_D7 = "YELLOW_D7"
    GREEN_D7 = "GREEN_D7"
    GREEN_D14 = "GREEN_D14"
    MASTERED = "MASTERED"


class Difficulty(StrEnum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    UNKNOWN = "UNKNOWN"

