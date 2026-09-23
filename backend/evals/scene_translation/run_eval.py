"""Run the scene-translation eval against a provider and score the results.

Usage, from ``backend/``::

    python -m evals.scene_translation.run_eval --provider openai --model gpt-4.1-mini
    python -m evals.scene_translation.run_eval --provider gemini --model gemini-3.8-flash
    python -m evals.scene_translation.run_eval --replay results/raw/gpt-4.1-mini
    python -m evals.scene_translation.run_eval --compare results/*.json

Both translation adapters already exist in ``app/services``, so this compares
providers today without any new integration work.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from collections.abc import Iterable, Sequence
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from typing import Any, Protocol

from .ground_truth import TranslationCase, load_cases
from .scoring import TranslationCaseScore, score_case

HERE = Path(__file__).resolve().parent
CASES_DIR = HERE / "cases"
RESULTS_DIR = HERE / "results"


class Translator(Protocol):
    def translate(self, payload: dict[str, Any]) -> Any: ...


def build_translator(provider: str, model: str) -> Translator:
    """Construct a provider adapter from the environment."""
    provider = provider.strip().lower()
    if provider == "openai":
        from app.services.openai_translation import OpenAISceneTranslator

        key = os.getenv("OPENAI_API_KEY", "").strip()
        if not key:
            raise SystemExit("OPENAI_API_KEY is not set")
        return OpenAISceneTranslator(key, model)
    if provider == "gemini":
        from app.services.gemini_translation import GeminiSceneTranslator

        key = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")).strip()
        if not key:
            raise SystemExit("GEMINI_API_KEY is not set")
        return GeminiSceneTranslator(key, model)
    raise SystemExit(f"unknown provider {provider!r}; expected openai or gemini")


def run(
    translator: Translator, cases: Sequence[TranslationCase], raw_dir: Path | None
) -> list[TranslationCaseScore]:
    scores: list[TranslationCaseScore] = []
    for index, case in enumerate(cases, start=1):
        started = time.perf_counter()
        try:
            result = translator.translate(case.payload())
        except Exception as exc:  # noqa: BLE001 - a provider failure fails one case
            score = TranslationCaseScore(
                case_id=case.case_id,
                target_language=case.target_language,
                tags=list(case.tags),
                error=f"{type(exc).__name__}: {exc}",
                latency_ms=(time.perf_counter() - started) * 1000,
            )
            scores.append(score)
            print(f"[{index:2}/{len(cases)}] FAIL {case.case_id:22} {score.error}")
            continue

        elapsed = (time.perf_counter() - started) * 1000
        payload = result.model_dump(by_alias=True)
        if raw_dir is not None:
            raw_dir.mkdir(parents=True, exist_ok=True)
            (raw_dir / f"{case.case_id}.json").write_text(
                json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
            )

        score = score_case(case, payload, latency_ms=elapsed)
        scores.append(score)
        article = "--" if score.article_accuracy is None else f"{score.article_accuracy:.2f}"
        print(
            f"[{index:2}/{len(cases)}] ok   {case.case_id:22} "
            f"noun={score.noun_accuracy or 0:.2f} article={article}"
        )
    return scores


def replay(cases: Sequence[TranslationCase], raw_dir: Path) -> list[TranslationCaseScore]:
    scores: list[TranslationCaseScore] = []
    for case in cases:
        path = raw_dir / f"{case.case_id}.json"
        if not path.exists():
            print(f"  skipping {case.case_id}: no saved response")
            continue
        scores.append(score_case(case, path.read_text(encoding="utf-8")))
    return scores


def _mean(values: Iterable[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    return mean(present) if present else None


def summarize(model: str, provider: str, scores: Sequence[TranslationCaseScore]) -> dict:
    return {
        "model": model,
        "provider": provider,
        "cases": len(scores),
        "structurallyValid": _mean([float(s.structurally_valid) for s in scores]),
        "nounAccuracy": _mean(s.noun_accuracy for s in scores),
        "articleAccuracy": _mean(s.article_accuracy for s in scores),
        "genderAccuracy": _mean(s.gender_accuracy for s in scores),
        "elisionAccuracy": _mean(s.elision_accuracy for s in scores),
        "attributeAccuracy": _mean(s.attribute_accuracy for s in scores),
        "relationAccuracy": _mean(s.relation_accuracy for s in scores),
        "cleanRate": _mean([float(s.clean) for s in scores]),
        "articlesGluedIntoTranslation": sum(len(s.articles_in_translation) for s in scores),
        "wrongArticles": sum(len(s.wrong_articles) for s in scores),
        "wrongGenders": sum(len(s.wrong_genders) for s in scores),
        "medianLatencyMs": (
            sorted(s.latency_ms for s in scores if s.latency_ms is not None)[
                len([s for s in scores if s.latency_ms is not None]) // 2
            ]
            if any(s.latency_ms is not None for s in scores)
            else None
        ),
    }


def _pct(value: float | None) -> str:
    return "--" if value is None else f"{value * 100:.0f}%"


def render(summaries: Sequence[dict]) -> str:
    rows = [
        ("Structurally valid", "structurallyValid", _pct),
        ("Noun accuracy", "nounAccuracy", _pct),
        ("Article accuracy", "articleAccuracy", _pct),
        ("Gender accuracy", "genderAccuracy", _pct),
        ("French elision accuracy", "elisionAccuracy", _pct),
        ("Attribute accuracy", "attributeAccuracy", _pct),
        ("Relation accuracy", "relationAccuracy", _pct),
        ("Fully clean cases", "cleanRate", _pct),
        ("Article glued into noun", "articlesGluedIntoTranslation", str),
        ("Wrong articles", "wrongArticles", str),
        ("Wrong genders", "wrongGenders", str),
    ]
    header = ["Metric", *(s["model"] for s in summaries)]
    lines = [
        "## Scene translation: model comparison\n",
        f"_{summaries[0]['cases']} cases, French and Spanish._\n",
        "| " + " | ".join(header) + " |",
        "|" + "---|" * len(header),
    ]
    for label, key, fmt in rows:
        lines.append(
            "| " + " | ".join([label, *(fmt(s.get(key)) for s in summaries)]) + " |"
        )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--model", default=None)
    parser.add_argument("--replay", type=Path, default=None)
    parser.add_argument("--compare", nargs="+", type=Path, default=None)
    parser.add_argument("--only", nargs="+", default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.compare:
        summaries = [
            json.loads(path.read_text(encoding="utf-8"))["summary"] for path in args.compare
        ]
        print(render(summaries))
        return 0

    cases = load_cases(CASES_DIR)
    if args.only:
        wanted = set(args.only)
        cases = [case for case in cases if case.case_id in wanted]
    if not cases:
        parser.error("no cases selected")

    if args.replay is not None:
        model = args.model or args.replay.name
        provider = "replay"
        scores = replay(cases, args.replay)
    else:
        model = args.model or "gpt-4.1-mini"
        provider = args.provider
        scores = run(build_translator(provider, model), cases, RESULTS_DIR / "raw" / model)

    summary = summarize(model, provider, scores)
    print()
    print(render([summary]))

    destination = args.out or RESULTS_DIR / f"{model.replace('/', '_')}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {"summary": summary, "cases": [asdict(s) for s in scores]},
            indent=2, ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
