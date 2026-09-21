# Backend rules: vocabulary mastery, XP, and the session lifecycle

This document is the reference for the product rules the backend now enforces, and
records the decisions behind them.

## 1. Vocabulary status and mastery

Status is a **pure function of a learner's encounter history** for a word,
recomputed on every write and on every read (`app/services/vocabulary_mastery.py`).
Nothing stores a status transition; there is therefore no way for the stored value
to drift from the evidence, and regression falls out of the same function.

Definitions, per (user, vocabulary item):

- **Encounter** — a `vocabulary_encounters` row (introduced, practised, recalled).
- **Evaluated attempt** — an encounter whose outcome is `correct` or `incorrect`.
  Introductions and `completed` outcomes are exposure, not evidence of recall.
- **Accuracy** — correct evaluated attempts / evaluated attempts.
- **Day** — the local calendar date of the attempt in the learner's timezone.
- **Recent window** — the last 3 evaluated attempts by time.

| Status | Condition |
| --- | --- |
| `new` | no encounters |
| `learning` | at least one encounter, and neither rule below is met |
| `familiar` | ≥ 3 evaluated attempts, on ≥ 2 distinct days, accuracy ≥ 70% |
| `mastered` | ≥ 5 evaluated attempts, on ≥ 3 distinct days, accuracy ≥ 85%, and ≥ 2 of the last 3 evaluated attempts correct |

**Regression.** Because status is derived, a run of incorrect recalls demotes a word
automatically (the recent-window and accuracy clauses stop holding). On top of that,
a `familiar` or `mastered` word with no *correct* evaluated attempt in the last
30 days is demoted exactly one rank (`mastered → familiar`, `familiar → learning`)
each time it is recomputed. A word that has ever been seen never returns to `new`.

`mastery_score` is a display anchor for the band: 0 / 0.25 / 0.6 / 1.

**Journal usage is not an evaluated attempt.** Previously, writing a word in a
journal entry marked it `mastered` outright. Free-text matching is weak,
unsupervised evidence, so it now only refreshes recency (`last_practised_at`),
which delays decay, and never promotes a word.

**One write path.** `record_vocabulary_evidence()` is the only function that touches
`user_vocabulary_progress`. It locks the progress row, inserts the encounter
(idempotent by encounter id), reloads the full history, derives status, counters and
timestamps, and writes them. Counters are derived rather than incremented, so a
replayed or out-of-order write cannot corrupt them.

`scene_id` and `topic` are not columns on `user_vocabulary_progress`; they are
derived per response from the word's most recent session scene, and remain in the
vocabulary API payload because the vocabulary page groups by scene.

## 2. XP

XP is an append-only ledger (`xp_events`) with a unique `(user_id, idempotency_key)`
constraint, so every award is exactly-once under retries and concurrent writes; the
totals shown to the learner are a sum over the ledger, optionally filtered by
language profile. Event types and amounts:

| Event | Amount | Idempotency key |
| --- | --- | --- |
| `taskCompleted` | 5 | task id |
| `ispyCorrect` | 5 | attempt id |
| `sessionCompleted` | 20 | session id |
| `perfectSession` | 10 | session id |
| `journalEntry` | 20 | journal id |
| `vocabularyMastered` | 25 | `mastery:{vocabulary_item_id}` |

`vocabularyMastered` is new: it is awarded the first time a word's derived status
becomes `mastered`. The key is per word, so re-mastering a word after regression
does not pay out twice.

## 3. Session lifecycle

### One active session per user and language profile

Active means any status other than `completed`, `abandoned`, `failed`. Creating a
session no longer abandons the previous one:

- selecting the scene that already has an unfinished session returns that session;
- selecting any other scene, or uploading a new image, returns a conflict carrying
  the active session id, for the UI to render "You already have an unfinished
  session. Continue or discard it before starting another";
- a partial unique index (`one_active_session_per_profile`) enforces this in the
  database, not only in application code.

### State machine

```
created → analyzingScene → awaitingObjectReview → generatingTasks → ready → inProgress → completed
```

Every non-terminal state may also move to `abandoned` or `failed`; the terminal
states have no outgoing edges. No other edge exists — the previous backwards edges
and the `generatingTasks → inProgress` shortcut have been removed. Transitions are
compare-and-set on the current status, so two concurrent requests cannot both
advance a session, and re-requesting the state a session is already in is a no-op.

| State | Page |
| --- | --- |
| `created`, `analyzingScene`, `awaitingObjectReview`, `generatingTasks` | analysis |
| `ready` | mic test |
| `inProgress` | learning / I-Spy |
| `completed` | summary |
| `abandoned`, `failed` | practice landing |

Because the canonical page is derived from the stored status, an interrupted
session resumes exactly where it stopped.

### End-to-end flow

1. `POST /sessions` — idempotency and active-session checks, returns `created`.
2. `POST /sessions/:id/analyze` — `created → analyzingScene`, run the analyzer,
   validate; on failure `failed` plus a `failureCode`; on success save
   `sessionTitle`, `sessionSummary` and the validated `analysisDraft`, then
   `→ awaitingObjectReview`.
3. `POST /sessions/:id/confirm-objects` — validates the submitted selection,
   resolves every English label to a `VocabularyItem`, and in one transaction
   writes the final `SceneObject` rows, maps temporary object keys to their ids,
   writes the `SceneObjectRelation` rows, and moves `→ generatingTasks`. Task
   generation then runs, all `SessionTask` rows are inserted, the draft is cleared
   and the session moves `→ ready`. (`PUT /sessions/:id/review` remains as an alias.)
4. `POST /sessions/:id/start` — `ready → inProgress`, sets `startedAt`. A task
   action on a `ready` session performs the same transition defensively.
5. When every task is completed or skipped — `→ completed`, sets `completedAt`.

### Discard

`POST /sessions/:id/abandon` on a non-terminal session sets `status = abandoned`,
`abandonedAt = now` and `analysisDraft = null`. This is the only path to
`abandoned`: nothing abandons a session implicitly. Abandoned and failed rows are
kept in the database for the MVP, and are excluded from every active-session and
progress query.

## 4. Open items

- **Precomputed output for preloaded scenes** — scene analysis is still the
  deterministic placeholder (`DeterministicSceneAnalyzer`); no model is called, so
  there is nothing to precompute yet. When a real multimodal model is wired in,
  preloaded scenes should read a stored analysis rather than calling it.
- **Journal media** — the day context already offers only the completed-session
  images for that day, and entries can be written for past days.
- **Session cleanup** — `vocabularyEncounters` and `aiRuns` remain on the session
  model; removing them is deferred until the vocabulary work settles.
