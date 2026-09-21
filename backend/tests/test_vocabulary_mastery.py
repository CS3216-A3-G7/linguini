"""Pure unit tests for evidence-based vocabulary mastery derivation."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.vocabulary_mastery import Evidence, derive_progress

NOW = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)


def ev(day_offset, outcome="correct", encounter_type="practised", hour=12):
    return Evidence(
        occurred_at=datetime(2026, 6, 1, hour, tzinfo=UTC) + timedelta(days=day_offset),
        encounter_type=encounter_type,
        outcome=outcome,
    )


def test_no_evidence_is_new():
    derived = derive_progress([], now=NOW)
    assert derived.status == "new"
    assert derived.mastery_score == Decimal("0")
    assert derived.exposure_count == derived.correct_attempt_count == 0
    assert derived.first_learned_at is None and derived.last_practised_at is None


def test_unevaluated_evidence_only_is_learning():
    evidence = [ev(day, outcome="completed") for day in range(10)]
    derived = derive_progress(evidence, now=NOW)
    assert derived.status == "learning"
    assert derived.mastery_score == Decimal("0.25")
    assert derived.exposure_count == 10 and derived.correct_attempt_count == 0


def test_introduced_does_not_count_as_practised():
    introduced = ev(0, outcome="completed", encounter_type="introduced")
    practised = ev(1, outcome="correct")
    derived = derive_progress([practised, introduced], now=NOW)
    assert derived.first_learned_at == introduced.occurred_at
    assert derived.last_practised_at == practised.occurred_at
    # Still learning: one evaluated attempt and one practice day.
    assert derived.status == "learning"


def test_familiar_boundary_requires_three_attempts_two_days_and_accuracy():
    # Two evaluated attempts on two days: not enough attempts.
    assert derive_progress([ev(0), ev(1)], now=NOW).status == "learning"
    # Three attempts on one day: not enough days.
    assert derive_progress([ev(0), ev(0, hour=14), ev(0, hour=16)], now=NOW).status == "learning"
    # Three attempts, two days, 2/3 accuracy is below 0.70.
    below = [ev(0), ev(0, hour=14), ev(1, outcome="incorrect")]
    assert derive_progress(below, now=NOW).status == "learning"
    # Three attempts, two days, 3/3 accuracy: familiar.
    assert derive_progress([ev(0), ev(0, hour=14), ev(1)], now=NOW).status == "familiar"


def test_familiar_accuracy_boundary_is_inclusive():
    # 7/10 = exactly 0.70 across two days.
    evidence = [
        ev(0 if i < 5 else 1, outcome="correct" if i < 7 else "incorrect")
        for i in range(10)
    ]
    derived = derive_progress(evidence, now=NOW)
    assert derived.status == "familiar"
    assert derived.mastery_score == Decimal("0.6")
    assert derived.correct_attempt_count == 7


def test_mastered_requires_five_attempts_three_days_accuracy_and_recent():
    mastered = [ev(0), ev(0, hour=14), ev(1), ev(2), ev(2, hour=14)]
    derived = derive_progress(mastered, now=NOW)
    assert derived.status == "mastered"
    assert derived.mastery_score == Decimal("1")

    # Five attempts over only two days cannot be mastered.
    two_days = [ev(0), ev(0, hour=13), ev(0, hour=14), ev(1), ev(1, hour=13)]
    assert derive_progress(two_days, now=NOW).status == "familiar"


def test_mastered_accuracy_boundary_is_inclusive():
    # 17/20 = exactly 0.85 across three days; the misses come first so the
    # recent window is all correct.
    evidence = [
        ev(i % 3, outcome="incorrect" if i < 3 else "correct", hour=6 + i % 12)
        for i in range(20)
    ]
    derived = derive_progress(evidence, now=NOW)
    assert derived.correct_attempt_count == 17
    assert derived.status == "mastered"

    # 5/6 = 0.833 is under 0.85 even with three days and correct recency.
    under = [ev(day, outcome="correct") for day in range(5)] + [ev(2, outcome="incorrect")]
    assert derive_progress(under, now=NOW).status == "familiar"


def test_mastered_requires_two_of_last_three_evaluated_correct():
    # High accuracy and three days, but the last three hold only one correct.
    evidence = [ev(day) for day in range(5)] + [
        ev(5, outcome="incorrect"),
        ev(6, outcome="incorrect"),
    ]
    derived = derive_progress(evidence, now=NOW)
    assert derived.status == "familiar"  # 5/7 = 0.714 accuracy
    # Flipping the tail back to mostly correct restores mastered.
    repaired = evidence[:5] + [ev(5, outcome="incorrect"), ev(6), ev(7)]
    assert derive_progress(repaired, now=NOW).status == "mastered"


def test_days_count_in_the_user_timezone():
    # Same UTC calendar day (Jan 2) but two local days in New York (UTC-5).
    evidence = [
        Evidence(datetime(2026, 1, 2, 2, 0, tzinfo=UTC), "practised", "correct"),
        Evidence(datetime(2026, 1, 2, 3, 0, tzinfo=UTC), "practised", "correct"),
        Evidence(datetime(2026, 1, 2, 6, 0, tzinfo=UTC), "practised", "correct"),
    ]
    near = datetime(2026, 1, 3, tzinfo=UTC)
    assert derive_progress(evidence, timezone="UTC", now=near).status == "learning"
    assert (
        derive_progress(evidence, timezone="America/New_York", now=near).status == "familiar"
    )
    # An unknown timezone falls back to UTC rather than failing.
    assert derive_progress(evidence, timezone="Not/AZone", now=near).status == "learning"


def test_decay_demotes_one_rank_without_recent_correct():
    mastered = [ev(day) for day in range(5)] + [ev(5), ev(6)]
    assert derive_progress(mastered, now=NOW).status == "mastered"
    # Same history observed 40 days later: mastered decays to familiar only.
    later = NOW + timedelta(days=40)
    decayed = derive_progress(mastered, now=later)
    assert decayed.status == "familiar"
    # And a familiar history decays to learning.
    familiar = [ev(0), ev(0, hour=14), ev(1)]
    assert derive_progress(familiar, now=later).status == "learning"
    # Evidence that never qualified still cannot regress below learning.
    sparse = [ev(0)]
    assert derive_progress(sparse, now=later).status == "learning"


def test_unsorted_evidence_is_ordered_before_rules_apply():
    ordered = [ev(0), ev(1), ev(2), ev(3), ev(4)]
    shuffled = [ordered[3], ordered[0], ordered[4], ordered[1], ordered[2]]
    assert derive_progress(shuffled, now=NOW) == derive_progress(ordered, now=NOW)
