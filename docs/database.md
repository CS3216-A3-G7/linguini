# Database

Prisma owns PostgreSQL DDL and migration history. Runtime Python code uses
SQLAlchemy Core and psycopg; Prisma is not the application ORM.

## Models and tables

The current schema has 20 models. `@@map` names are the PostgreSQL tables.

### Identity and media

| Model (`table`) | Purpose and key columns |
| --- | --- |
| `User` (`users`) | Auth-linked learner; `id`, unique `authProviderId`, display name, email, timezone, onboarding flags. |
| `LanguageProfile` (`language_profiles`) | Source/target language and preferences; `id`, `userId`, language codes, proficiency, active flag. |
| `MediaAsset` (`media_assets`) | Metadata for objects stored outside PostgreSQL; `id`, optional `ownerUserId`, type/source, unique `storageKey`, MIME and dimensions. |
| `PreloadedScene` (`preloaded_scenes`) | Curated catalog and JSONB content; `id`, unique `slug`, language, `mediaAssetId`, title, difficulty, active/sort fields. |

### Scene and practice

| Model (`table`) | Purpose and key columns |
| --- | --- |
| `Session` (`sessions`) | Practice run; `id`, `userId`, `languageProfileId`, `sceneMediaAssetId`, status, draft/title/summary, failure code, idempotency key. |
| `SceneObject` (`scene_objects`) | Confirmable detected object; `id`, `sessionId`, label, JSONB box/anchor/attributes, confidence, optional vocabulary item. |
| `SceneObjectRelation` (`scene_object_relations`) | Directed relation between two objects; subject/reference IDs, relation, optional source key. |
| `SessionTask` (`session_tasks`) | Public learning/I-Spy task; phase/kind/order/status, public JSON, optional answer JSON and object/vocabulary links. |
| `TaskAttempt` (`task_attempts`) | Answer attempt; task ID, attempt number, input mode, response JSON, optional audio, correctness/score/feedback. |
| `TaskHint` (`task_hints`) | Requested hint level and JSON content for a task. |

### Vocabulary and progress

| Model (`table`) | Purpose and key columns |
| --- | --- |
| `VocabularyItem` (`vocabulary_items`) | Canonical target-language item; language, lemma/display text, part of speech, optional gender/pronunciation/example. |
| `VocabularyTranslation` (`vocabulary_translations`) | Source-language translation and definition. |
| `UserVocabularyProgress` (`user_vocabulary_progress`) | Per-user status, exposures, correct attempts, mastery score, first/last practice times. |
| `VocabularyEncounter` (`vocabulary_encounters`) | Evidence connecting user, item, session, task, type, outcome, and time. |
| `XpEvent` (`xp_events`) | Idempotent XP ledger row with event type, amount, key, and optional profile/session. |

### Journals

| Model (`table`) | Purpose and key columns |
| --- | --- |
| `Journal` (`journals`) | One user/profile entry per local date; selected words, status, current revision, optional audio. |
| `JournalMedia` (`journal_media`) | Ordered media attachment and caption. |
| `JournalRevision` (`journal_revisions`) | Content version with revision number and creator. |
| `JournalSuggestion` (`journal_suggestions`) | Revision-scoped suggestion and status. |
| `JournalWordMention` (`journal_word_mentions`) | Vocabulary match offsets with optional source encounter. |

## Enums

`SessionStatus`: `created`, `analyzingScene`, `awaitingObjectReview`,
`generatingTasks`, `ready`, `inProgress`, `completed`, `abandoned`, `failed`.

`SessionFailureCode`: `imageUploadFailed`, `sceneAnalysisFailed`,
`imageModerationFailed`, `noValidObjects`, `vocabularyMappingFailed`,
`taskGenerationFailed`.

## Migrations

Migration SQL lives in timestamped directories under
`backend/prisma/migrations/`. The current history includes removal of the old
`AiGenerationRun` model, creation of `xp_events`, and creation of
`scene_object_relations`; old directory names remain historical artifacts.

```sh
cd backend
npm run db:validate
npm run db:deploy
npx prisma migrate status
```

`db:validate` validates the schema. `db:deploy` applies committed migrations.
`migrate status` reports pending migrations.

## Ownership and constraints

Composite foreign keys carry ownership into child rows. For example,
`sessions_profile_owner_fkey` uses `[languageProfileId, userId]` and points to
`language_profiles(id, user_id)`; journals use the same profile-owner pattern.
Session tasks and vocabulary encounters use composite session/task keys so
objects and events cannot be attached across sessions. The current-revision
pointer uses `(currentRevisionId, id)` and is `DEFERRABLE INITIALLY DEFERRED`
in SQL so a journal and its first revision can be inserted atomically. Several
parent-preserving links use deferred `NO ACTION`.

Migrations enable Row Level Security and revoke browser-role grants from
`PUBLIC`, `anon`, and `authenticated` on application tables. The backend uses
server-side PostgreSQL access; the browser does not query these tables.

## XP and progress

`GET /api/v1/me/progress` calls `LearningService.get_progress`, which calls
`SessionBackedLearningRepository.get_progress`. That repository sums
`xp_events.amount` for the user (and target language when requested), derives a
seven-day streak from `occurred_at`, and derives scenarios from sessions and
task statuses.

XP is awarded by the idempotent `award()` helper, not by counting
`vocabulary_encounters` at read time. Current amounts are 10 for
`taskCompleted`, 15 for `ispyCorrect`, 20 for `sessionCompleted`, 10 for
`perfectSession`, and 20 for `journalEntry`. `xp_events` is active and used by
workflow, vocabulary, journal, summary, and progress code. Encounters remain
mastery/history evidence; older documentation that describes XP as a
per-encounter point count, including `backend/README.md`, is outdated.

See the [entity relationship diagram](erd.md) for current relationships,
cardinality, composite keys, and uniqueness notes.
