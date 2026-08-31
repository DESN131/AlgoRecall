from datetime import date, timedelta

import pytest

from app.models.enums import Rating, ReviewStage
from app.services.review_service import calculate_next_review


@pytest.mark.parametrize(
    ("current", "rating", "expected_stage", "days"),
    [
        (ReviewStage.RED_D1, Rating.RED, ReviewStage.RED_D1, 1),
        (ReviewStage.RED_D1, Rating.YELLOW, ReviewStage.YELLOW_D3, 3),
        (ReviewStage.RED_D1, Rating.GREEN, ReviewStage.GREEN_D7, 7),
        (ReviewStage.YELLOW_D3, Rating.RED, ReviewStage.RED_D1, 1),
        (ReviewStage.YELLOW_D3, Rating.YELLOW, ReviewStage.YELLOW_D7, 7),
        (ReviewStage.YELLOW_D3, Rating.GREEN, ReviewStage.GREEN_D7, 7),
        (ReviewStage.YELLOW_D7, Rating.RED, ReviewStage.RED_D1, 1),
        (ReviewStage.YELLOW_D7, Rating.YELLOW, ReviewStage.YELLOW_D7, 7),
        (ReviewStage.YELLOW_D7, Rating.GREEN, ReviewStage.GREEN_D7, 7),
        (ReviewStage.GREEN_D7, Rating.RED, ReviewStage.RED_D1, 1),
        (ReviewStage.GREEN_D7, Rating.YELLOW, ReviewStage.YELLOW_D3, 3),
        (ReviewStage.GREEN_D7, Rating.GREEN, ReviewStage.GREEN_D14, 14),
        (ReviewStage.GREEN_D14, Rating.RED, ReviewStage.RED_D1, 1),
        (ReviewStage.GREEN_D14, Rating.YELLOW, ReviewStage.YELLOW_D3, 3),
        (ReviewStage.GREEN_D14, Rating.GREEN, ReviewStage.MASTERED, None),
        (ReviewStage.MASTERED, Rating.RED, ReviewStage.RED_D1, 1),
        (ReviewStage.MASTERED, Rating.YELLOW, ReviewStage.YELLOW_D3, 3),
        (ReviewStage.MASTERED, Rating.GREEN, ReviewStage.MASTERED, None),
    ],
)
def test_all_state_transitions(current, rating, expected_stage, days):
    reviewed = date(2026, 8, 31)
    result = calculate_next_review(current, rating, reviewed)
    assert result.stage == expected_stage
    assert result.interval_days == days
    assert result.next_review_at == (reviewed + timedelta(days=days) if days else None)
