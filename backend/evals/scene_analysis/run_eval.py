"""Run the scene-analysis eval against a vision model and score the results.

Usage, from ``backend/``::

    python -m evals.scene_analysis.run_eval --provider openai --model gpt-4.1-mini
    python -m evals.scene_analysis.run_eval --replay results/raw/gemini-3.8-flash
    python -m evals.scene_analysis.run_eval --compare results/*.json

The runner drives ``VisionModelClient``, the provider-independent seam that
already exists in ``app/services/vision_model.py``. Adding a provider to the
eval therefore means adding an adapter next to ``vision_openai.py`` -- no
changes here.

Every raw response is written to disk before scoring. Scoring rules will change
as the dataset grows, and saved responses mean a rule change can be re-applied
to past runs instead of costing another round of API calls.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from app.schemas.scene_analysis import SceneAnalysisModelResult
from app.services.prompts.scene_analysis_v1 import (
    SCENE_ANALYSIS_PROMPT_VERSION,
    SCENE_ANALYSIS_SYSTEM_PROMPT,
    SCENE_ANALYSIS_USER_INSTRUCTION,
)
from app.services.vision_model import (
    VisionImage,
    VisionModelClient,
    VisionModelError,
    VisionModelRequest,
    build_strict_json_schema,
)

from .ground_truth import EvalCase, load_cases
from .report import build_scorecard, render_comparison
from .scoring import CaseScore, score_case

HERE = Path(__file__).resolve().parent
CASES_DIR = HERE / "cases"
RESULTS_DIR = HERE / "results"

MIME_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
              ".webp": "image/webp"}


def build_request(case: EvalCase) -> VisionModelRequest:
    path = case.image_path(HERE)
    return VisionModelRequest(
        image=VisionImage(
            data=path.read_bytes(),
            mime_type=MIME_TYPES[path.suffix.lower()],
        ),
        system_prompt=SCENE_ANALYSIS_SYSTEM_PROMPT,
        user_instruction=SCENE_ANALYSIS_USER_INSTRUCTION,
        json_schema_name="scene_analysis",
        json_schema=build_strict_json_schema(SceneAnalysisModelResult),
        prompt_version=SCENE_ANALYSIS_PROMPT_VERSION,
    )


def run_case(
    client: VisionModelClient, case: EvalCase, raw_dir: Path | None
) -> CaseScore:
    request = build_request(case)
    started = time.perf_counter()
    try:
        response = client.generate(request)
    except VisionModelError as exc:
        elapsed = (time.perf_counter() - started) * 1000
        score = CaseScore(
            case_id=case.case_id, difficulty=case.difficulty.value, tags=list(case.tags)
        )
        score.issue_codes = [exc.code.value]
        score.error = str(exc)
        score.latency_ms = elapsed
        return score

    elapsed = (time.perf_counter() - started) * 1000
    if raw_dir is not None:
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / f"{case.case_id}.json").write_text(response.output_text, encoding="utf-8")

    return score_case(
        case,
        response.output_text,
        latency_ms=elapsed,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
    )


def run(
    client: VisionModelClient,
    cases: Sequence[EvalCase],
    raw_dir: Path | None = None,
) -> list[CaseScore]:
    scores: list[CaseScore] = []
    for index, case in enumerate(cases, start=1):
        score = run_case(client, case, raw_dir)
        scores.append(score)
        status = "ok " if score.parsed else "FAIL"
        recall = "--" if score.anchor_recall is None else f"{score.anchor_recall:.2f}"
        print(
            f"[{index:2}/{len(cases)}] {status} {case.case_id:26} "
            f"recall={recall} violations={score.violation_count}"
        )
    return scores


def replay(cases: Sequence[EvalCase], raw_dir: Path) -> list[CaseScore]:
    """Re-score responses captured by an earlier run.

    Also the way to score output produced outside this harness -- paste a
    model's JSON into ``<case_id>.json`` and the same rules apply.
    """
    scores: list[CaseScore] = []
    for case in cases:
        path = raw_dir / f"{case.case_id}.json"
        if not path.exists():
            print(f"  skipping {case.case_id}: no saved response")
            continue
        scores.append(score_case(case, path.read_text(encoding="utf-8")))
    return scores


def _write_results(
    scores: Sequence[CaseScore], model_name: str, provider: str, destination: Path
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": model_name,
        "provider": provider,
        "promptVersion": SCENE_ANALYSIS_PROMPT_VERSION,
        "scorecard": asdict(build_scorecard(model_name, provider, scores)),
        "cases": [asdict(score) for score in scores],
    }
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {destination}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--replay", type=Path, default=None,
                        help="Score saved responses instead of calling a provider.")
    parser.add_argument("--compare", nargs="+", type=Path, default=None,
                        help="Render a comparison table from saved result files.")
    parser.add_argument("--only", nargs="+", default=None, help="Limit to these case ids.")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.compare:
        from .report import Scorecard

        cards = []
        for path in args.compare:
            data = json.loads(path.read_text(encoding="utf-8"))
            cards.append(Scorecard(**data["scorecard"]))
        print(render_comparison(cards))
        return 0

    cases = load_cases(CASES_DIR)
    if args.only:
        wanted = set(args.only)
        cases = [case for case in cases if case.case_id in wanted]
    if not cases:
        parser.error("no cases selected")

    if args.replay is not None:
        model_name = args.model or args.replay.name
        provider = args.provider or "replay"
        scores = replay(cases, args.replay)
    else:
        from app.config import get_vision_model_client, get_vision_model_config

        # The client is built from the environment, so --provider/--model are
        # applied as overrides before it is constructed.
        if args.provider:
            os.environ["VISION_PROVIDER"] = args.provider
        if args.model:
            os.environ["VISION_MODEL_NAME"] = args.model

        provider = args.provider or os.getenv("VISION_PROVIDER", "openai")
        model_name = get_vision_model_config().model_name
        client = get_vision_model_client()
        scores = run(client, cases, RESULTS_DIR / "raw" / model_name)

    card = build_scorecard(model_name, provider, scores)
    print()
    print(render_comparison([card]))
    _write_results(
        scores, model_name, provider,
        args.out or RESULTS_DIR / f"{model_name.replace('/', '_')}.json",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
