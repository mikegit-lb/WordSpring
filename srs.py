"""Modified SM-2 scheduling rules for WordSpring."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum


class Rating(str, Enum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


@dataclass(frozen=True, slots=True)
class ReviewState:
    ease_factor: float = 2.5
    interval: float = 0.0  # days; fractional values allow the one-minute Again step
    repetitions: int = 0


@dataclass(frozen=True, slots=True)
class Schedule:
    ease_factor: float
    interval: float
    repetitions: int
    next_review: str


def schedule_review(
    state: ReviewState,
    rating: Rating | str,
    now: datetime | None = None,
) -> Schedule:
    """Return the next SM-2-like state without mutating the supplied state.

    First-pass intervals match the app's study buttons: Hard 1 day, Good 3
    days, Easy 5 days. Later successful reviews grow from the previous interval
    and ease factor. Again schedules one minute from now and resets the
    repetition count. The classic SM-2 ease adjustment is clamped to 1.3.
    """
    rating = Rating(rating)
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    now = now.astimezone(UTC)

    quality = {
        Rating.AGAIN: 2,
        Rating.HARD: 3,
        Rating.GOOD: 4,
        Rating.EASY: 5,
    }[rating]
    delta = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    ease = min(3.0, max(1.3, float(state.ease_factor) + delta))

    if rating is Rating.AGAIN:
        interval = 1.0 / 1440.0
        repetitions = 0
        due = now + timedelta(minutes=1)
    else:
        repetitions = max(0, int(state.repetitions)) + 1
        first_interval = {
            Rating.HARD: 1.0,
            Rating.GOOD: 3.0,
            Rating.EASY: 5.0,
        }[rating]
        if state.repetitions <= 0 or state.interval <= 0:
            interval = first_interval
        else:
            growth = {
                Rating.HARD: 0.8,
                Rating.GOOD: 1.0,
                Rating.EASY: 1.3,
            }[rating]
            interval = max(first_interval, math.ceil(state.interval * ease * growth))
        due = now + timedelta(days=interval)

    return Schedule(
        ease_factor=round(ease, 3),
        interval=round(interval, 6),
        repetitions=repetitions,
        next_review=due.isoformat(timespec="seconds"),
    )
