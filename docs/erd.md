# Entity relationship diagram

This ERD is generated from `backend/prisma/schema.prisma` and uses PostgreSQL
table and column names. Only identifying columns are shown; the schema file is
authoritative for every column and constraint.

## Reading the cardinality

Mermaid crow's-foot ends map to `(min,max)`:

| Symbol | Meaning | `(min,max)` |
| --- | --- | --- |
| `||` | exactly one | `(1,1)` |
| `|o` | zero or one | `(0,1)` |
| `}|` | one or more | `(1,n)` |
| `o{` | zero or more | `(0,n)` |

```mermaid
erDiagram
    exactly_one_A ||--|| exactly_one_B : "(1,1)"
    zero_or_one_A |o--o| zero_or_one_B : "(0,1)"
    one_or_more_A }|--|{ one_or_more_B : "(1,n)"
    zero_or_more_A }o--o{ zero_or_more_B : "(0,n)"
```

For example, `users ||--o{ language_profiles` means every profile has exactly
one user and a user may have zero or more profiles. A nullable foreign key
produces an optional child-side end.

## Diagram

The diagram is wider than the page; scroll it horizontally.

<div class="erd-scroll" markdown>

```mermaid
erDiagram
    users {
        uuid id PK
        text auth_provider_id UK
        varchar display_name
        varchar email
    }
    language_profiles {
        uuid id PK
        uuid user_id FK
        varchar source_language_code
        varchar target_language_code
        boolean is_active
    }
    media_assets {
        uuid id PK
        uuid owner_user_id FK "nullable"
        varchar media_type
        varchar source
        text storage_key UK
    }
    preloaded_scenes {
        uuid id PK
        uuid media_asset_id FK
        text slug UK
        varchar language_code
        text title
    }
    vocabulary_items {
        uuid id PK
        uuid pronunciation_audio_asset_id FK "nullable"
        varchar language_code
        varchar display_text
    }
    vocabulary_translations {
        uuid id PK
        uuid vocabulary_item_id FK
        varchar source_language_code
    }
    user_vocabulary_progress {
        uuid id PK
        uuid user_id FK
        uuid vocabulary_item_id FK
        varchar status
        decimal mastery_score
    }
    vocabulary_encounters {
        uuid id PK
        uuid user_id FK
        uuid vocabulary_item_id FK
        uuid session_id FK
        uuid session_task_id FK
        varchar encounter_type
        varchar outcome
    }
    sessions {
        uuid id PK
        uuid user_id
        uuid language_profile_id FK
        uuid scene_media_asset_id FK
        varchar session_status
        varchar failure_code
        varchar idempotency_key
    }
    xp_events {
        uuid id PK
        uuid user_id FK
        uuid language_profile_id FK "nullable"
        uuid session_id FK "nullable"
        varchar event_type
        int amount
    }
    scene_objects {
        uuid id PK
        uuid session_id FK
        text label
        jsonb bounding_box
        uuid vocabulary_item_id FK "nullable"
    }
    scene_object_relations {
        uuid id PK
        uuid subject_scene_object_id FK
        text relation
        uuid reference_scene_object_id FK
    }
    session_tasks {
        uuid id PK
        uuid session_id FK
        uuid vocabulary_item_id FK "nullable"
        uuid scene_object_id FK "nullable"
        varchar phase
        varchar kind
        int order_index
    }
    task_attempts {
        uuid id PK
        uuid session_task_id FK
        uuid audio_media_asset_id FK "nullable"
        int attempt_number
        boolean is_correct
    }
    task_hints {
        uuid id PK
        uuid session_task_id FK
        int hint_level
    }
    journals {
        uuid id PK
        uuid user_id
        uuid language_profile_id FK
        date local_date
        uuid current_revision_id FK "nullable"
        varchar status
    }
    journal_media {
        uuid id PK
        uuid journal_id FK
        uuid media_asset_id FK
        int display_order
    }
    journal_revisions {
        uuid id PK
        uuid journal_id FK
        int revision_number
        varchar created_by
    }
    journal_suggestions {
        uuid id PK
        uuid journal_id FK
        uuid base_revision_id FK
        varchar suggestion_type
        varchar status
    }
    journal_word_mentions {
        uuid id PK
        uuid journal_revision_id FK
        uuid vocabulary_item_id FK
        uuid source_encounter_id FK "nullable"
    }

    users ||--o{ language_profiles : owns
    users ||--o{ sessions : starts
    users ||--o{ journals : writes
    users ||--o{ vocabulary_encounters : records
    users ||--o{ user_vocabulary_progress : tracks
    users |o--o{ media_assets : owns
    users ||--o{ xp_events : earns
    language_profiles ||--o{ sessions : configures
    language_profiles ||--o{ journals : configures
    language_profiles |o--o{ xp_events : scopes
    media_assets ||--o{ preloaded_scenes : illustrates
    media_assets ||--o{ sessions : supplies
    media_assets |o--o{ vocabulary_items : voices
    media_assets |o--o{ task_attempts : records
    media_assets |o--o{ journals : records
    media_assets ||--o{ journal_media : attaches
    vocabulary_items ||--o{ vocabulary_translations : translates
    vocabulary_items ||--o{ user_vocabulary_progress : tracks
    vocabulary_items |o--o{ scene_objects : labels
    vocabulary_items |o--o{ session_tasks : targets
    vocabulary_items ||--o{ journal_word_mentions : appears
    sessions ||--o{ scene_objects : detects
    sessions ||--o{ session_tasks : contains
    sessions ||--o{ vocabulary_encounters : records
    sessions |o--o{ xp_events : rewards
    scene_objects ||--o{ scene_object_relations : "subject of"
    scene_objects ||--o{ scene_object_relations : "reference of"
    scene_objects |o--o{ session_tasks : grounds
    session_tasks ||--o{ task_attempts : receives
    session_tasks ||--o{ task_hints : explains
    session_tasks ||--o{ vocabulary_encounters : produces
    user_vocabulary_progress ||--o{ vocabulary_encounters : aggregates
    vocabulary_encounters |o--o{ journal_word_mentions : sources
    journals ||--o{ journal_media : shows
    journals ||--o{ journal_revisions : contains
    journals ||--o{ journal_suggestions : collects
    journals |o--o| journal_revisions : "current revision"
    journal_revisions ||--o{ journal_suggestions : bases
    journal_revisions ||--o{ journal_word_mentions : mentions
```

</div>

The two `scene_object_relations` edges are named Prisma relations
`RelationSubject` and `RelationReference`; both are required foreign keys to
`scene_objects`.

## Composite and owner-aware foreign keys

| Constraint/table | Foreign key columns | Parent |
| --- | --- | --- |
| `sessions_profile_owner_fkey` | `[languageProfileId, userId]` | `language_profiles(id, user_id)` |
| `journals_profile_owner_fkey` | `[languageProfileId, userId]` | `language_profiles(id, user_id)` |
| `session_tasks_scene_object_session_fkey` | `[sceneObjectId, sessionId]` | `scene_objects(id, session_id)` |
| `vocabulary_encounters_session_owner_fkey` | `[sessionId, userId]` | `sessions(id, user_id)` |
| `vocabulary_encounters_task_session_fkey` | `[sessionTaskId, sessionId]` | `session_tasks(id, session_id)` |
| `journals_current_revision_fkey` | `[currentRevisionId, id]` | `journal_revisions(id, journal_id)` |
| `journal_suggestions_base_revision_fkey` | `[baseRevisionId, journalId]` | `journal_revisions(id, journal_id)` |
| `user_vocabulary_progress` parent | `[userId, vocabularyItemId]` | `user_vocabulary_progress(user_id, vocabulary_item_id)` |

SQL also enforces that both endpoints of a scene-object relation belong to the
same session. The current-revision pointer is deferred so a journal and first
revision can be inserted in one transaction. Deferred `NO ACTION` constraints
preserve parent history during atomic updates.

## Uniqueness worth knowing

- `users.auth_provider_id` and `media_assets.storage_key` are unique.
- Language profiles have one active profile and one case-insensitive language
  pair per user.
- `sessions` is unique per `(user_id, language_profile_id, idempotency_key)`.
- `xp_events` is unique per `(user_id, idempotency_key)`.
- Progress is unique per user and vocabulary item.
- Tasks are unique per session/order; attempts and hints are unique by
  task/attempt number and task/hint level.
- Journals are unique per user/local date; journal media and revisions have
  per-parent ordering keys.
- Journal word mentions are unique per revision, vocabulary item, and offset.
