# API reference

The backend mounts every router below `/api/v1`. Response models are the
Pydantic classes named in the route declarations. Authenticated routes resolve
the current user from a Supabase bearer token or, when `AUTH_MODE=demo`, from
`DEMO_USER_ID`; repository queries scope records to that user.

## Health

| Method | Path | Response | Purpose | Auth and ownership |
| --- | --- | --- | --- | --- |
| `GET` | `/health` | `HealthResponse` | Liveness check returning `{"status":"ok"}`. | Public. |

## Home

| Method | Path | Response | Purpose | Auth and ownership |
| --- | --- | --- | --- | --- |
| `GET` | `/home` | `HomeResponse` | Intended home summary. | Route currently returns HTTP 501 through `service_not_implemented`. |

## Users and language profiles

| Method | Path | Response | Purpose | Auth and ownership |
| --- | --- | --- | --- | --- |
| `GET` | `/me` | `User` | Read the current account. | Current user only. |
| `PATCH` | `/me` | `User` | Update account settings and onboarding fields. | Current user only. |
| `GET` | `/me/language-profiles` | `list[LanguageProfile]` | List the user's language profiles. | Current user only. |
| `POST` | `/me/language-profiles` | `LanguageProfile` | Create a source/target language profile. | Current user only; `201`. |
| `PATCH` | `/me/language-profiles/{profile_id}` | `LanguageProfile` | Update proficiency, input mode, daily goal, or active state. | Profile must belong to current user. |

## Media and preloaded scenes

| Method | Path | Response | Purpose | Auth and ownership |
| --- | --- | --- | --- | --- |
| `GET` | `/media/{asset_id}` | `MediaAssetResponse` | Read media metadata and a signed URL. | Current user's asset or a preloaded asset. |
| `GET` | `/media/{asset_id}/image` | binary WebP | Serve a derivative at width `320`, `640`, or `1280`; supports `ETag` and `304`. | Current user's asset or a preloaded asset. |
| `POST` | `/media/upload-url` | `CreateUploadUrlResponse` | Allocate an owned image key and signed upload URL. | Current user; `201` is not used. |
| `POST` | `/media/confirm-upload` | `MediaAssetResponse` | Validate the uploaded object and persist metadata. | Key must match the current user's asset prefix; `201`. |
| `GET` | `/preloaded-scenes` | `list[PreloadedScene]` | List active scenes for the active target language. | Current user with an active language profile. |
| `GET` | `/preloaded-scenes/{scene_id}` | `PreloadedSceneCatalogDetail` | Read public catalog metadata and items. | Current user's active language; answer-bearing private fields are omitted. |

The upload contract accepts JPEG, PNG, or WebP, a non-empty filename up to 255
characters, and `1..10 MiB` of bytes. Confirmation downloads the object from
Storage, checks the real image format and dimensions, and deletes invalid
objects. The client flow is:

1. `POST /api/v1/media/upload-url` with filename, byte size, MIME type, and
   source (`camera` or `userUpload`).
2. `PUT` the file bytes to the returned Supabase signed upload URL.
3. `POST /api/v1/media/confirm-upload` with `assetId`, `storageKey`, and source.

The upload URL expires in 7200 seconds. Signed read URLs default to a
3600-second expiry. Image derivatives accept only the three widths above.

## Sessions

| Method | Path | Response | Purpose | Auth and ownership |
| --- | --- | --- | --- | --- |
| `POST` | `/sessions` | `SessionDetailResponse` | Create or resume a practice session for an image. | Current user and active language profile; `202`. |
| `GET` | `/sessions/active` | `SessionDetailResponse \| None` | Return the most recent unfinished session for the active profile. | Current user and active profile. |
| `GET` | `/sessions/{session_id}` | `SessionDetailResponse` | Read session, scene objects, vocabulary, tasks, and progress. | Session must belong to current user/profile. |
| `POST` | `/sessions/{session_id}/analyze` | `SessionDetailResponse` | Start uploaded-scene analysis. | Current user's session. |
| `POST` | `/sessions/{session_id}/generate-plan` | `SessionDetailResponse` | Compatibility endpoint that delegates to analysis. | Current user's session; `202`. |
| `GET` | `/sessions/{session_id}/tasks` | `list[SessionTaskPublic]` | List public task content. | Current user's session. |
| `PUT` | `/sessions/{session_id}/review` | `SessionDetailResponse` | Confirm objects, relations, attributes, positions, and title. | Current user's editable session. |
| `GET` | `/sessions/{session_id}/summary` | `SessionSummaryResponse` | Return progress, learned vocabulary, I-Spy counts, and XP. | Current user's session. |
| `POST` | `/sessions/{session_id}/complete` | `Session` | Complete a session after task completion. | Current user's session. |
| `POST` | `/sessions/{session_id}/abandon` | `Session` | Abandon an unfinished session. | Current user's session. |
| `GET` | `/sessions/{session_id}/review-word?label=...` | JSON object | Check a vocabulary review word; returns `{"available": true}` when it is in the active language catalog. | Current user's session; label length is 1–200. |

`CreateSessionRequest.idempotencyKey` is optional but must be 8–200
characters when supplied. For the same user, language profile, and key, a
retry returns the original session if it names the same image; reusing the key
for another image returns `409 practice_conflict`. Selecting the same image
without a key also resumes its unfinished session. At most three unfinished
sessions are allowed per active profile.

## Tasks

| Method | Path | Response | Purpose | Auth and ownership |
| --- | --- | --- | --- | --- |
| `GET` | `/tasks/{task_id}` | `SessionTaskPublic` | Read public task content. | Task's session must belong to current user. |
| `POST` | `/tasks/{task_id}/start` | `TaskActionResponse` | Start a task. | Current user's active task. |
| `POST` | `/tasks/{task_id}/attempts` | `TaskActionResponse` | Submit an evaluated answer. | Current user's task; request key supports retry idempotency. |
| `POST` | `/tasks/{task_id}/check-vocabulary-answer` | `CheckVocabularyAnswerResponse` | Check a vocabulary multiple-choice option without recording completion. | Current user's vocabulary task. |
| `POST` | `/tasks/{task_id}/hints` | `TaskHint` | Intended hint request. | Currently returns HTTP 501. |
| `POST` | `/tasks/{task_id}/complete` | `TaskActionResponse` | Complete a task. | Current user's task. |
| `POST` | `/tasks/{task_id}/skip` | `TaskActionResponse` | Skip a task with a reason. | Current user's task. |

## Vocabulary and progress

| Method | Path | Response | Purpose | Auth and ownership |
| --- | --- | --- | --- | --- |
| `GET` | `/me/vocabulary` | `CursorPage[DailyVocabularyItem]` | List vocabulary for the active target language. | Current user; `limit` is 1–500. |
| `GET` | `/me/vocabulary/daily` | `DailyVocabularyResponse` | Intended daily vocabulary endpoint. | Currently returns HTTP 501. |
| `GET` | `/me/vocabulary/{vocabulary_item_id}` | `DailyVocabularyItem` | Intended single-item endpoint. | Currently returns HTTP 501. |
| `GET` | `/me/progress` | `ProgressResponse` | Return XP, scenarios, leaderboard, and streak. | Current user and active language. |

## Journals

| Method | Path | Response | Purpose | Auth and ownership |
| --- | --- | --- | --- | --- |
| `GET` | `/journals` | `list[JournalDetailResponse]` | List journal entries, up to 365. | Current user. |
| `GET` | `/journal/today/context` | `JournalTodayContextResponse` | Load today's journal, eligible photos, words, and creation state. | Current user and active profile. |
| `PUT` | `/journal/today` | `Journal` | Create or update today's entry. | Current user's active profile. |
| `GET` | `/journal/{local_date}/context` | `JournalTodayContextResponse` | Load a journal day context. | Current user; date is ISO format. |
| `PUT` | `/journal/{local_date}` | `Journal` | Create or update a dated entry. | Current user's active profile. |
| `GET` | `/journals/{journal_id}` | `JournalDetailResponse` | Read an entry with media, revisions, suggestions, and word mentions. | Current user only. |
| `PATCH` | `/journals/{journal_id}` | `Journal` | Update entry metadata/content. | Current user only. |
| `POST` | `/journals/{journal_id}/media` | `JournalMedia` | Attach a media asset; `201`. | Current user's journal and asset. |
| `DELETE` | `/journals/{journal_id}/media/{media_asset_id}` | empty `204` | Remove an attachment. | Current user's journal. |
| `POST` | `/journals/{journal_id}/revisions` | `JournalRevision` | Add a revision; `201`. | Current user's journal. |
| `POST` | `/journals/{journal_id}/suggestions` | `list[JournalSuggestion]` | Intended suggestion generation. | Currently returns HTTP 501; declared status is `202`. |
| `POST` | `/journal-suggestions/{suggestion_id}/accept` | `JournalSuggestion` | Accept a suggestion. | Suggestion must belong to current user. |
| `POST` | `/journal-suggestions/{suggestion_id}/reject` | `JournalSuggestion` | Reject a suggestion. | Suggestion must belong to current user. |
| `POST` | `/journals/{journal_id}/complete` | `Journal` | Complete against a revision ID. | Current user's journal. |

## Error contract

Domain errors are returned as:

```json
{
  "detail": {
    "code": "practice_conflict",
    "message": "This practice action is not valid for the current session."
  }
}
```

`ActiveSessionExistsError` returns `409` with
`code: "active_session_exists"` and adds `activeSessionId`. `PracticeConflictError`
returns `409` with `code: "practice_conflict"` and the exception's message.
Other representative mappings include `401 unauthenticated`, `404
practice_not_found`/`scene_not_found`, `409 active_session_limit_reached`,
`502 scene_analysis_failed` and `502 learning_task_generation_failed`, `503
media_url_error`, and `500` storage errors. Invalid image uploads are `422
invalid_image_upload`; missing uploaded objects are `404 upload_not_found`.
FastAPI validation errors remain FastAPI's standard validation response.

Task attempts, session creation, vocabulary evidence, and XP awards use stable
keys in their persistence layer. Repeating an attempt with the same request
key or repeating an event with the same ledger key is a no-op/replay rather
than a second credit. Session creation has the key behavior described above.
