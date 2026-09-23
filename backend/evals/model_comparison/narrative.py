"""Prose for MODEL_COMPARISON.md. Tables around it are generated from results.

Keeping the wording here means the document can be rebuilt after a re-run
without hand-editing Markdown, and the claims stay beside the harness that
produced the numbers.
"""

HEADER = """# Model and provider comparison

Which model Linguini should use for each of its five AI calls, measured rather
than assumed. Every candidate ran through the app's own services — the same
prompts, JSON schemas and validators that ship — so a number here is what a
learner would have got.

Regenerate this file with:

```powershell
.\\.venv\\Scripts\\python.exe -m evals.model_comparison.report --out ..\\MODEL_COMPARISON.md
```
"""

METHOD = """## How the measurements were taken

**Three providers.** OpenAI and Gemini are called directly. Everything else —
Anthropic, Qwen, DeepSeek, Meta, Mistral — is called through OpenRouter, which
serves them behind an OpenAI-compatible Responses API. OpenRouter adds a
routing hop, so its latencies are not strictly comparable with direct calls;
that is called out where it matters.

**Production code, not a copy of it.** Each candidate is built through
`app.ai.registry` and handed to the real feature service
(`SceneTranslationService`, `LearningTaskService`, `ISpyClueService`,
`UploadedSceneAnalyzer`) or, for I-Spy guessing, the real adapter. A recorder
wraps the model client to capture latency, tokens and the raw response, which
the services otherwise discard.

**Two different questions.** *Accepted by the app* is whether the output passed
the production validator — what the learner would actually receive. *Quality*
is scored from the raw response, so a rejected answer can still be diagnosed
rather than counted as a flat zero.

**Cases.** 14 labelled photos (clean, blurred, low-light, cropped, noisy, and
one deliberately unusable), 13 Spanish/French translation cases with a gold
lexicon, 4 Japanese/Korean probes, 6 hand-written scenes across four languages
for lessons and clues, and 22 learner descriptions whose intended object is
known, including directional traps, deliberate contradictions and off-topic
text.

**Repeat runs.** Models are not deterministic, so the shortlist runs each case
two or three times. *Run-to-run spread* is the standard deviation of the
overall score across repeats of the same case: treat any gap between models
smaller than that as noise.

**Judging.** Lesson quality and whether a clue can actually be solved have no
reference answer, so `anthropic/claude-sonnet-5` grades them against an
anchored rubric, and is never told which model produced the output. It is not
a candidate for any call. It does share a family with the
`anthropic/claude-haiku-4.5` candidate, so treat Haiku's judged scores with
more caution than the deterministic ones.

**Cost.** Computed from recorded tokens at the OpenRouter catalogue price,
which is the provider list price, so direct and routed calls are priced the
same way. Cost per 1,000 sessions assumes one scene analysis, one translation,
one lesson and one clue set per session, plus three learner descriptions.
"""

PARAMETERS = """## What was measured

| Parameter | Meaning |
|---|---|
| Overall quality | 0–1 composite, for ranking only; the columns beside it carry the argument |
| Output usable by app | Share of calls whose output passed the production validator |
| API errors | Share failing at the provider: timeout, overload, refusal, bad response |
| Run-to-run spread | Standard deviation of the overall score across repeat runs of one case |
| Identical repeat runs | How often repeats returned byte-identical output |
| Rate-limit retries | Our own quota retries; a property of the account, not the model |
| Latency p50 / p95 | Typical and near-worst wall-clock time for one call |
| Input / output tokens | Mean tokens per call, including image tokens and any reasoning tokens |
| Cost per call / per 1,000 sessions | Recorded tokens at list price |
| Context window, max output | Published limits, from the catalogue snapshot |
| Vision, temperature, reasoning | Takes images; accepts a temperature; is a reasoning model |

Call-specific quality columns (anchor recall, article accuracy, answer-key
errors, clue solvability, guess accuracy and so on) are defined in the section
for each call.
"""

RECOMMENDATIONS = """## Recommendations

Filled in once the full stage and the parameter sweep have run.
"""

PER_CALL_NOTES = {
    "scene_analysis": (
        "Finds the objects a learner will practise, from an uploaded photo."
        " Anchor recall is how many of the objects a labeller marked as"
        " unmissable the model found; supported precision is how much of what"
        " it returned is actually in the photo. The unusable photo is a"
        " trap: the right behaviour is to return nothing."
    ),
    "translation": (
        "Translates the confirmed English vocabulary into the learner's"
        " language, with the definite article and grammatical gender. The"
        " Japanese and Korean cases are a probe: the shipped prompt only"
        " claims French and Spanish."
    ),
    "learning_tasks": (
        "Writes the grammar lesson: four task types, each with two to four"
        " multiple-choice or sentence-building questions, restricted to the"
        " approved scene vocabulary. The per-scene JSON schema is large, which"
        " some providers refuse outright."
    ),
    "ispy_clues": (
        "Writes one or two I-Spy clues that describe an object without naming"
        " it. A clue that contains the answer word scores zero."
    ),
    "ispy_guess": (
        "Reads the learner's own description and infers which object they"
        " meant, without being told the answer, then gives short feedback."
    ),
}

FOOTER = """## Limitations

- Small datasets: 14 photos, 17 translation cases, 6 scenes, 22 descriptions.
  A few points between models is within run-to-run noise.
- The judge is one model with one rubric, and shares a family with one
  candidate. Its scores are reported separately from the deterministic ones.
- Gemini was called on a free-tier key whose quota was exhausted during the
  runs; rate-limit retries are excluded from quality but the daily cap is a
  real deployment constraint.
- OpenRouter latency includes its routing hop, and it may route the same model
  to different hosts between calls.
- Prices are list prices at the date of the catalogue snapshot.
"""
