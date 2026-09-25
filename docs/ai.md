# AI features

AI construction is centralized in `backend/app/ai/registry.py`. Providers are
`openai`, `gemini`, `openrouter`, and `none`. OpenRouter uses the OpenAI
compatible adapters with a different base URL. Feature services are provider
neutral and receive validated model-client seams.

## Feature configuration

| Feature | Purpose | Supported providers | Default model | Main variables | Off or unconfigured |
| --- | --- | --- | --- | --- | --- |
| Scene analysis | Find objects, normalized boxes, anchors, and relations in an uploaded photo. | OpenAI, Gemini, OpenRouter | `anthropic/claude-haiku-4.5` via OpenRouter | `AI_SCENE_ANALYSIS_PROVIDER`, `_MODEL`, `_TIMEOUT_SECONDS`, `_MAX_OUTPUT_TOKENS`, `_MAX_RETRIES` | Uses deterministic scene analysis. |
| Translation | Translate confirmed source terms and preserve object/attribute/relation keys. | OpenAI, Gemini, OpenRouter | `openai/gpt-4o-mini` via OpenRouter | `AI_SCENE_TRANSLATION_PROVIDER`, `_MODEL`, `_TIMEOUT_SECONDS`, `_MAX_OUTPUT_TOKENS`, `_MAX_RETRIES` | Uses the workflow's deterministic translation fallback. |
| Learning tasks | Generate vocabulary, grammar, syntax, and sentence-building tasks. | OpenAI, Gemini, OpenRouter | `openai/gpt-5.4-mini` via OpenRouter | `AI_LEARNING_TASK_PROVIDER`, `_MODEL`, `_TIMEOUT_SECONDS`, `_MAX_OUTPUT_TOKENS`, `_MAX_RETRIES` | Uses deterministic lesson-plan generation. |
| I-Spy clue | Generate scene-grounded clues without leaking the answer word. | OpenAI, Gemini, OpenRouter | `google/gemini-3.1-flash-lite` via OpenRouter | `AI_ISPY_CLUE_PROVIDER`, `_MODEL`, `_TIMEOUT_SECONDS`, `_MAX_OUTPUT_TOKENS`, `_MAX_RETRIES` | Uses deterministic clue rounds. |
| I-Spy guess | Evaluate a learner's text description against the scene. | OpenAI, OpenRouter | `openai/gpt-4.1-mini` via OpenRouter | `AI_ISPY_GUESS_PROVIDER`, `_MODEL`, `_TIMEOUT_SECONDS`, `_MAX_OUTPUT_TOKENS`, `_MAX_RETRIES` | Uses the deterministic evaluator path. |
| Object grounding | Refine object boxes and marker centers with a local detector. | `none`, `groundingDino` | `IDEA-Research/grounding-dino-base` when enabled | `AI_OBJECT_GROUNDING_PROVIDER`, `_MODEL`, `_THRESHOLD`, `_MAX_LABELS`, `_MAX_IMAGE_SIDE` | Model coordinates are retained. |
| Image moderation | Moderate uploaded images before accepting scene analysis. | `none`, OpenAI | `omni-moderation-latest` | `AI_IMAGE_MODERATION_PROVIDER`, `_MODEL`, `_TIMEOUT_SECONDS` | No moderation pass. If configured provider credentials are unavailable, the moderator is not built; a flagged image fails with `imageModerationFailed`. |

Every real text/vision feature also uses the corresponding provider key:
`AI_OPENAI_API_KEY`, `AI_GEMINI_API_KEY`, or `AI_OPENROUTER_API_KEY`.
`AI_API_KEY` is a general key for custom/`none` setups and is not used by the
default registry. `VISION_PROVIDER`, `VISION_MODEL_NAME`,
`VISION_TIMEOUT_SECONDS`, `VISION_MAX_OUTPUT_TOKENS`, and
`VISION_MAX_RETRIES` remain the separate legacy vision configuration surface.

## Modes and fallbacks

`AI_MODE` accepts `demo` or `real` and defaults to `demo`. Demo mode does not
construct network clients merely because models are named; absent or
unconfigured features return `None` from the registry and preserve the
deterministic workflow. Real mode validates that every enabled feature has a
model and matching provider key, and validates Langfuse keys when
observability is enabled. Invalid settings raise `AiConfigurationError` at
load time.

## Prompts, validation, and repair

Shared prompts live in `backend/app/prompts/`; feature-specific prompts and
version constants live in each `backend/app/ai/features/*/prompt.py`.
Scene analysis validates duplicate keys, normalized finite bounding boxes,
anchors, relation endpoints, confidence ranges, and relation consistency.
Translation validates that all supplied terms are returned, requires object
articles, and normalizes duplicated leading articles. Learning tasks validate
task references, question counts, answer keys, and scene grounding. I-Spy
clues validate shape, distinct answers, scene grounding, and answer leakage.

The feature services parse strict JSON schemas, then run deterministic semantic
validation. Transient provider failures and invalid responses can use the
configured retry budget (structured text features default to one repair retry
unless explicitly set to zero). Repair attempts append a correction instruction
and, for learning tasks and translation, structured repair data; a response
that still fails validation raises the feature error rather than being stored.

## Observability

`AI_OBSERVABILITY_ENABLED` enables the Langfuse tracer. Instrumentation records
feature/provider/model names, prompt and schema versions, latency, token usage,
retry count, validation result, and sanitized error codes. Tracing is
best-effort: an SDK failure falls back to a no-op tracer and never reaches the
learner.

Content capture is opt-in through `AI_OBSERVABILITY_CAPTURE_CONTENT=false`.
When false, learner text, model responses, image bytes, base64 payloads,
keys, and signed URLs are not attached. When enabled, feature generation
observations may record request/response content. The remaining variables are
`AI_OBSERVABILITY_BASE_URL`, `AI_OBSERVABILITY_PUBLIC_KEY`,
`AI_OBSERVABILITY_SECRET_KEY`, and `AI_OBSERVABILITY_ENVIRONMENT`.

## Model selection notes

[`MODEL_COMPARISON.md`](https://github.com/CS3216-A3-G7/linguini/blob/main/MODEL_COMPARISON.md)
reports repeated evaluation cases, validator acceptance, quality, latency, tokens, and cost. Its
recommendations favor Claude Haiku 4.5 for scene analysis, Mistral Small for
translation, GPT-5.4-mini for lessons, Gemini Flash-Lite for clues, and
GPT-4.1-mini for I-Spy guesses. The checked-in defaults use the current
OpenRouter routes supplied in `.env.example`; the comparison also records
known validator and provider-rate-limit caveats, so model choice remains
per-feature rather than global.
