# Frontend

The frontend is a React 19/Vite/TypeScript SPA. The route tree is defined in
`frontend/src/App.tsx`.

## Routes and shells

| Route | Component | Shell and access |
| --- | --- | --- |
| `/` | `Welcome` | `FocusShell`, public. |
| `/login` | `Login` | `FocusShell`, public. |
| `/onboarding` | `Onboarding` via `OnboardingRoute` | `FocusShell`; requires a Supabase session. |
| `/practice/sessions/:sessionId/analysis` | `PracticeAnalysis` | `RequireAuth` + `AuthenticatedApp` + `FocusShell` + `SessionRoute`. |
| `/practice/sessions/:sessionId/mic-test` | `MicTest` | Same session shell. |
| `/practice/sessions/:sessionId/learn` | `Learn` | Same session shell. |
| `/practice/sessions/:sessionId/learn/:taskId` | `LearningTaskPage` | Same session shell. |
| `/practice/sessions/:sessionId/ispy-1` | `ISpyPhase1` | Same session shell. |
| `/practice/sessions/:sessionId/ispy-2` | `ISpyPhase2` | Same session shell. |
| `/practice/sessions/:sessionId/summary` | `SessionSummary` | Same session shell. |
| `/practice/:sceneId/*` | `SceneRoute` | `RequireAuth` + `FocusShell`. |
| `/home` | `Home` | `RequireAuth` + `AppShell`. |
| `/practice` | `PracticeSelect` | `RequireAuth` + `AppShell`. |
| `/progress` | `Progress` | `RequireAuth` + `AppShell`. |
| `/vocabulary` | `Vocabulary` | `RequireAuth` + `AppShell`. |
| `/journal` | `Journal` | `RequireAuth` + `AppShell`. |
| `/journal/new` and `/journal/new/:date` | `JournalNew` | `RequireAuth` + `AppShell`. |
| `/journal/:entryId` | `JournalEntryPage` | `RequireAuth` + `AppShell`. |
| `/profile` | `Profile` | `RequireAuth` + `AppShell`. |
| `/profile/edit` | `ProfileEdit` | `RequireAuth` + `AppShell`. |
| `*` | redirect to `/home` | React Router fallback. |

`RequireAuth` permits the route tree during Vite development, waits for
`AuthProvider` in production, and redirects unauthenticated users to
`/login`. `OnboardingRoute` has its own session check and sends unauthenticated
users to `/login?mode=signup`.

## Auth and server state

`frontend/src/state/Auth.tsx` wraps Supabase's `getSession` and
`onAuthStateChange`. It clears the TanStack Query cache after auth changes.
`frontend/src/lib/supabase.ts` creates a browser client only when
`VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are present; `getAccessToken`
supplies the bearer token to API requests.

`frontend/src/state/queries.ts` defines TanStack Query hooks for scenes,
vocabulary, and journals. `frontend/src/lib/queryKeys.ts` centralizes keys for
account, profile-scoped vocabulary/progress/journals, active sessions, journal
contexts, and session summaries. `frontend/src/lib/api.ts` is the HTTP
boundary: it builds `/api/v1` URLs, adds the access token, performs the
upload-url/PUT/confirm sequence, and maps API errors to friendly messages.

## Session routing

`SessionRoute` loads session detail and uses `frontend/src/lib/sessionRoute.ts`
to map status and task completion to the canonical screen. The helper sends
`created`, `analyzingScene`, and `awaitingObjectReview` to analysis; `ready` to
the microphone check; unfinished learning tasks to `/learn`; unfinished clue
tasks to `/ispy-1`; the description phase to `/ispy-2`; completed sessions to
summary; and abandoned/failed sessions back to practice with a notice. It also
allows transitional paths while task generation is publishing its first
vocabulary task.

`SceneRoute` provides the preloaded-scene route entry point and starts/resumes
the corresponding session.

## Media and design system

`MediaImage` turns an asset ID into the backend derivative URL and delegates
rendering to `SceneImage`. `lib/api.ts` downscales large uploads before sending
them, while the backend remains authoritative for MIME and byte validation.

Shared controls and layout primitives live in `frontend/src/components/ui.tsx`
and `ui.css`, including buttons, cards, top bars, brand bars, progress trails,
status pills, and XP pills. `frontend/design.md` documents the product loop,
palette, typography, spacing, and interaction principles. It is a navigation
reference for the visual system rather than an additional runtime layer.
