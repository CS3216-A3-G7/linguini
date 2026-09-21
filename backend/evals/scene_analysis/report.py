"""Aggregate per-case scores into a scorecard.

The aggregate deliberately refuses to collapse into a single number. A model
that hallucinates objects in an unreadable photo and a model that misses a
chair are not separated by one score, and a leaderboard that pretends otherwise
would pick the wrong model. The report keeps accuracy, rule compliance and cost
side by side and leaves the trade-off visible.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from statistics import mean

from .scoring import CaseScore


def _mean_of(values: Iterable[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    return mean(present) if present else None


def _pct(value: float | None) -> str:
    return "--" if value is None else f"{value * 100:.0f}%"


def _num(value: float | None, digits: int = 2) -> str:
    return "--" if value is None else f"{value:.{digits}f}"


@dataclass
class Scorecard:
    model_name: str
    provider: str
    cases: int = 0

    valid_rate: float | None = None
    anchor_recall: float | None = None
    supported_precision: float | None = None
    title_accuracy: float | None = None
    mean_iou: float | None = None
    relation_recall: float | None = None

    clean_rate: float | None = None
    person_violations: int = 0
    brand_violations: int = 0
    adjective_violations: int = 0
    plural_violations: int = 0
    duplicate_violations: int = 0

    empty_cases: int = 0
    empty_handled: int = 0
    hallucinated_in_empty: int = 0

    confidence_capped_rate: float | None = None
    count_compliance: float | None = None
    max_pairwise_overlap: float | None = None

    median_latency_ms: float | None = None
    mean_input_tokens: float | None = None
    mean_output_tokens: float | None = None

    issue_codes: dict[str, int] = field(default_factory=dict)
    by_difficulty: dict[str, float | None] = field(default_factory=dict)


def build_scorecard(
    model_name: str, provider: str, scores: Sequence[CaseScore]
) -> Scorecard:
    card = Scorecard(model_name=model_name, provider=provider, cases=len(scores))
    if not scores:
        return card

    card.valid_rate = sum(1 for score in scores if score.parsed) / len(scores)
    card.clean_rate = sum(1 for score in scores if score.clean) / len(scores)

    card.anchor_recall = _mean_of(score.anchor_recall for score in scores)
    card.supported_precision = _mean_of(score.supported_precision for score in scores)
    card.title_accuracy = _mean_of(
        float(score.title_match) for score in scores if score.title_match is not None
    )
    card.mean_iou = _mean_of(score.mean_iou for score in scores)
    card.relation_recall = _mean_of(score.relation_recall for score in scores)
    card.confidence_capped_rate = _mean_of(
        float(score.confidence_within_cap)
        for score in scores
        if score.confidence_within_cap is not None
    )
    card.count_compliance = _mean_of(
        float(score.count_within_range)
        for score in scores
        if score.count_within_range is not None
    )
    overlaps = [s.max_pairwise_overlap for s in scores if s.max_pairwise_overlap is not None]
    card.max_pairwise_overlap = max(overlaps) if overlaps else None

    card.person_violations = sum(len(score.person_labels) for score in scores)
    card.brand_violations = sum(len(score.brand_labels) for score in scores)
    card.adjective_violations = sum(len(score.adjective_labels) for score in scores)
    card.plural_violations = sum(len(score.plural_labels) for score in scores)
    card.duplicate_violations = sum(len(score.duplicate_labels) for score in scores)

    empty = [score for score in scores if score.empty_as_required is not None]
    card.empty_cases = len(empty)
    card.empty_handled = sum(1 for score in empty if score.empty_as_required)
    card.hallucinated_in_empty = sum(len(score.hallucinated_objects) for score in empty)

    latencies = sorted(s.latency_ms for s in scores if s.latency_ms is not None)
    if latencies:
        card.median_latency_ms = latencies[len(latencies) // 2]
    card.mean_input_tokens = _mean_of(
        float(s.input_tokens) for s in scores if s.input_tokens is not None
    )
    card.mean_output_tokens = _mean_of(
        float(s.output_tokens) for s in scores if s.output_tokens is not None
    )

    counts: dict[str, int] = {}
    for score in scores:
        for code in score.issue_codes:
            counts[code] = counts.get(code, 0) + 1
    card.issue_codes = dict(sorted(counts.items(), key=lambda item: -item[1]))

    for difficulty in ("easy", "medium", "hard", "unusable"):
        subset = [score for score in scores if score.difficulty == difficulty]
        card.by_difficulty[difficulty] = (
            _mean_of(score.anchor_recall for score in subset) if subset else None
        )

    return card


def render_comparison(cards: Sequence[Scorecard]) -> str:
    """Markdown scorecard, ready to paste into the report."""
    if not cards:
        return "_No results._\n"

    lines: list[str] = []
    lines.append("## Scene analysis: model comparison\n")
    lines.append(f"_{cards[0].cases} cases._\n")

    header = ["Metric", *(f"{card.model_name}" for card in cards)]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "---|" * len(header))

    def row(label: str, render) -> None:
        lines.append("| " + " | ".join([label, *(render(card) for card in cards)]) + " |")

    lines.append("| **Accuracy** |" + " |" * len(cards))
    row("Anchor recall", lambda c: _pct(c.anchor_recall))
    row("Supported precision", lambda c: _pct(c.supported_precision))
    row("Scene title accuracy", lambda c: _pct(c.title_accuracy))
    row("Mean box IoU", lambda c: _num(c.mean_iou))
    row("Relation recall", lambda c: _pct(c.relation_recall))

    lines.append("| **Reliability** |" + " |" * len(cards))
    row("Schema-valid responses", lambda c: _pct(c.valid_rate))
    row("Object count in 3-6", lambda c: _pct(c.count_compliance))
    row("Confidence within cap", lambda c: _pct(c.confidence_capped_rate))
    row(
        "Unusable image handled",
        lambda c: "--" if not c.empty_cases else f"{c.empty_handled}/{c.empty_cases}",
    )

    lines.append("| **Rule violations** (lower is better) |" + " |" * len(cards))
    row("People named", lambda c: str(c.person_violations))
    row("Brands named", lambda c: str(c.brand_violations))
    row("Adjective in label", lambda c: str(c.adjective_violations))
    row("Plural label", lambda c: str(c.plural_violations))
    row("Duplicate object", lambda c: str(c.duplicate_violations))
    row("Objects invented in unusable image", lambda c: str(c.hallucinated_in_empty))
    row("Fully clean responses", lambda c: _pct(c.clean_rate))

    lines.append("| **Cost and speed** |" + " |" * len(cards))
    row("Median latency", lambda c: "--" if c.median_latency_ms is None
        else f"{c.median_latency_ms / 1000:.1f}s")
    row("Mean input tokens", lambda c: _num(c.mean_input_tokens, 0))
    row("Mean output tokens", lambda c: _num(c.mean_output_tokens, 0))

    lines.append("| **Anchor recall by difficulty** |" + " |" * len(cards))
    for difficulty in ("easy", "medium", "hard"):
        row(f"  {difficulty}", lambda c, d=difficulty: _pct(c.by_difficulty.get(d)))

    lines.append("")
    for card in cards:
        if card.issue_codes:
            codes = ", ".join(f"{code} x{count}" for code, count in card.issue_codes.items())
            lines.append(f"- **{card.model_name}** validation failures: {codes}")
    lines.append("")
    return "\n".join(lines)
