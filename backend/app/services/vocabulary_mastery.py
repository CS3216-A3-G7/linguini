"""Evidence-based vocabulary mastery: status is a pure function of history."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

EVALUATED_OUTCOMES = {"correct", "incorrect"}
FAMILIAR_MIN_ATTEMPTS = 3
FAMILIAR_MIN_DAYS = 2
FAMILIAR_MIN_ACCURACY = Decimal("0.70")
MASTERED_MIN_ATTEMPTS = 5
MASTERED_MIN_DAYS = 3
MASTERED_MIN_ACCURACY = Decimal("0.85")
RECENT_WINDOW = 3
RECENT_MIN_CORRECT = 2
DECAY_AFTER = timedelta(days=30)
MASTERY_BY_STATUS = {
    "new": Decimal("0"),
    "learning": Decimal("0.25"),
    "familiar": Decimal("0.6"),
    "mastered": Decimal("1"),
}
DEMOTION = {"mastered": "familiar", "familiar": "learning"}


@dataclass(frozen=True)
class Evidence:
    """One vocabulary_encounters row."""

    occurred_at: datetime
    encounter_type: str
    outcome: str


@dataclass(frozen=True)
class DerivedProgress:
    status: str
    mastery_score: Decimal
    exposure_count: int
    correct_attempt_count: int
    first_learned_at: datetime | None
    last_practised_at: datetime | None


def derive_progress(
    evidence: Iterable[Evidence], *, timezone: str = "UTC", now: datetime
) -> DerivedProgress:
    ordered = sorted(evidence, key=lambda entry: entry.occurred_at)
    evaluated = [entry for entry in ordered if entry.outcome in EVALUATED_OUTCOMES]
    correct = [entry for entry in evaluated if entry.outcome == "correct"]
    accuracy = (
        Decimal(len(correct)) / Decimal(len(evaluated)) if evaluated else Decimal("0")
    )
    try:
        zone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        zone = ZoneInfo("UTC")
    days = {entry.occurred_at.astimezone(zone).date() for entry in evaluated}
    recent_correct = sum(
        entry.outcome == "correct" for entry in evaluated[-RECENT_WINDOW:]
    )
    if not ordered:
        status = "new"
    elif (
        len(evaluated) >= MASTERED_MIN_ATTEMPTS
        and len(days) >= MASTERED_MIN_DAYS
        and accuracy >= MASTERED_MIN_ACCURACY
        and recent_correct >= RECENT_MIN_CORRECT
    ):
        status = "mastered"
    elif (
        len(evaluated) >= FAMILIAR_MIN_ATTEMPTS
        and len(days) >= FAMILIAR_MIN_DAYS
        and accuracy >= FAMILIAR_MIN_ACCURACY
    ):
        status = "familiar"
    else:
        status = "learning"
    # Decay: a stale correct record demotes exactly one rank on recompute.
    if status in DEMOTION and not any(
        entry.occurred_at >= now - DECAY_AFTER for entry in correct
    ):
        status = DEMOTION[status]
    practised = [
        entry.occurred_at for entry in ordered if entry.encounter_type != "introduced"
    ]
    return DerivedProgress(
        status=status,
        mastery_score=MASTERY_BY_STATUS[status],
        exposure_count=len(ordered),
        correct_attempt_count=len(correct),
        first_learned_at=ordered[0].occurred_at if ordered else None,
        last_practised_at=max(practised) if practised else None,
    )
