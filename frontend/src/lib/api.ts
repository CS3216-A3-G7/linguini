import type { LeaderboardRow, ScenarioProgress, VocabRecord, VocabStatus, WordClass } from "../data/types";
import type { Scene, SceneSummary } from "../data/types";
import type { JournalEntry } from "../data/types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, "");

// Matches the camelCase User response from GET /api/v1/me.
export interface User {
  learningGoal: string;
  microphoneEnabled: boolean;
  cameraEnabled: boolean;
  id: string;
  createdAt: string;
  updatedAt: string;
  authProviderId: string;
  displayName: string;
  email: string | null;
  timezone: string;
  onboardingCompleted: boolean;
}

async function request<T>(path: string, signal?: AbortSignal, options?: RequestInit): Promise<T> {
  if (!apiBaseUrl) {
    throw new Error("Set VITE_API_BASE_URL in frontend/.env.local and restart Vite.");
  }

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, { ...options, signal });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new Error("Cannot reach the API. Check that the backend is running and CORS allows this origin.");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = typeof body?.detail?.message === "string" ? body.detail.message : "Request failed.";
    throw new Error(`${message} (HTTP ${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function getCurrentUser(signal?: AbortSignal): Promise<User> {
  return request<User>("/api/v1/me", signal);
}

export interface LanguageProfile {
  id: string;
  userId: string;
  sourceLanguageCode: string;
  targetLanguageCode: string;
  proficiencyLevel: "A1" | "A2" | "B1" | "B2" | "C1" | "C2";
  isActive: boolean;
  dailyGoalMinutes: number | null;
  preferredInputMode: "speech" | "text" | "both";
}

export type UserPatch = Partial<Pick<User, "displayName" | "timezone" | "onboardingCompleted" | "learningGoal" | "microphoneEnabled" | "cameraEnabled">>;
export type LanguageProfilePatch = Partial<Pick<LanguageProfile, "proficiencyLevel" | "isActive" | "dailyGoalMinutes" | "preferredInputMode">>;

function write<T>(path: string, method: string, body: unknown): Promise<T> {
  return request(path, undefined, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
}

export const getLanguageProfiles = (signal?: AbortSignal) => request<LanguageProfile[]>("/api/v1/me/language-profiles", signal);
export const updateUser = (patch: UserPatch) => write<User>("/api/v1/me", "PATCH", patch);
export const updateLanguageProfile = (id: string, patch: LanguageProfilePatch) => write<LanguageProfile>(`/api/v1/me/language-profiles/${id}`, "PATCH", patch);
export const createLanguageProfile = (code: string, minutes = 10) => write<LanguageProfile>("/api/v1/me/language-profiles", "POST", {
  sourceLanguageCode: "en", targetLanguageCode: code, proficiencyLevel: "A1", dailyGoalMinutes: minutes,
});

export interface ProgressResponse {
  xp: number;
  scenarios: ScenarioProgress[];
  leaderboard: LeaderboardRow[];
}

interface DailyVocabularyItem {
  vocabulary: {
    id: string;
    displayText: string;
    partOfSpeech: WordClass;
    gender: string | null;
    exampleSentence: string | null;
  };
  translation: { translatedText: string } | null;
  progress: { status: VocabStatus } | null;
  sceneId: string | null;
  topic: string | null;
}

export function getProgress(signal?: AbortSignal): Promise<ProgressResponse> {
  return request<ProgressResponse>("/api/v1/me/progress", signal);
}

interface PreloadedScene {
  imageUrl?: string | null;
  mediaAsset: { id: string };
  languageCode: string;
  sceneId: string;
  title: string;
  description: string | null;
  language: string;
}

function sceneSummary(row: PreloadedScene): SceneSummary {
  return { id: row.sceneId, mediaAssetId: row.mediaAsset.id, imageUrl: row.imageUrl ?? null, title: row.title, blurb: row.description ?? "", language: row.language, languageCode: row.languageCode };
}

export async function getScenes(signal?: AbortSignal): Promise<SceneSummary[]> {
  const rows = await request<PreloadedScene[]>("/api/v1/preloaded-scenes", signal);
  return rows.map(sceneSummary);
}

export async function getSceneDetail(id: string, signal?: AbortSignal): Promise<Scene> {
  const row = await request<PreloadedScene & Pick<Scene, "items" | "tasks" | "rounds" | "prompts">>(
    `/api/v1/preloaded-scenes/${encodeURIComponent(id)}`, signal,
  );
  return { ...sceneSummary(row), items: row.items, tasks: row.tasks, rounds: row.rounds, prompts: row.prompts };
}

export async function getVocabulary(signal?: AbortSignal): Promise<VocabRecord[]> {
  const items: DailyVocabularyItem[] = [];
  let cursor: string | null = null;
  do {
    const query = cursor ? `?cursor=${encodeURIComponent(cursor)}` : "";
    const page: { items: DailyVocabularyItem[]; nextCursor: string | null } =
      await request(`/api/v1/me/vocabulary${query}`, signal);
    items.push(...page.items);
    cursor = page.nextCursor;
  } while (cursor);
  return items.map((item) => ({
    id: item.vocabulary.id,
    word: item.vocabulary.displayText,
    translation: item.translation?.translatedText ?? "Translation unavailable",
    wordClass: item.vocabulary.partOfSpeech,
    gender: item.vocabulary.gender === "la" || item.vocabulary.gender === "el" ? item.vocabulary.gender : null,
    status: item.progress?.status ?? "new",
    topic: item.topic ?? "Uncategorised",
    sceneId: item.sceneId ?? "",
    example: item.vocabulary.exampleSentence ?? "",
  }));
}

interface JournalRecord {
  id: string; languageProfileId: string; localDate: string; title: string;
  selectedWords: string[]; currentRevisionId: string | null;
}
interface JournalDetail {
  media: { mediaAssetId: string; displayOrder: number }[];
  imageUrl?: string | null;
  journal: JournalRecord;
  revisions: { id: string; content: string }[];
}
function journalEntry(detail: JournalDetail): JournalEntry {
  const row = detail.journal;
  return { id: row.id, languageProfileId: row.languageProfileId, date: row.localDate,
    title: row.title, mediaAssetId: [...detail.media].sort((a, b) => a.displayOrder - b.displayOrder)[0]?.mediaAssetId ?? null, imageUrl: detail.imageUrl ?? null, wordsUsed: row.selectedWords,
    body: detail.revisions.find((revision) => revision.id === row.currentRevisionId)?.content ?? "" };
}
export async function getJournals(signal?: AbortSignal): Promise<JournalEntry[]> {
  return (await request<JournalDetail[]>("/api/v1/journals", signal)).map(journalEntry);
}
export async function getJournal(id: string, signal?: AbortSignal): Promise<JournalEntry> {
  return journalEntry(await request<JournalDetail>(`/api/v1/journals/${id}`, signal));
}
export async function getTodayJournal(signal?: AbortSignal) {
  const context = await request<{ localDate: string; journal: JournalRecord | null }>("/api/v1/journal/today/context", signal);
  return { date: context.localDate, entry: context.journal ? await getJournal(context.journal.id, signal) : null };
}
export type JournalDraft = Pick<JournalEntry, "title" | "mediaAssetId" | "body" | "wordsUsed">;
export async function saveJournal(draft: JournalDraft, profileId: string, id?: string) {
  const body = { title: draft.title, mediaAssetId: draft.mediaAssetId, content: draft.body, selectedWords: draft.wordsUsed };
  const row = id ? await write<JournalRecord>(`/api/v1/journals/${id}`, "PATCH", body)
    : await write<JournalRecord>("/api/v1/journal/today", "PUT", { ...body, languageProfileId: profileId });
  return getJournal(row.id);
}

export interface PracticeDetail {
  session: { id: string; status: string };
  demoState: {
    answers: Record<string, string>; clues: Record<string, string>;
    sceneId: string; completedTaskIds: string[]; scoredRoundIds: string[];
    analysisScored: boolean; roundsPlayed: number; correctRounds: number; sessionXp: number; micReady: boolean;
  };
}
export interface PracticeEvent { kind: "analysis" | "task" | "round" | "clue"; itemId?: string; answerId?: string; text?: string }
export const getPractice = (id: string) => request<PracticeDetail>(`/api/v1/sessions/${id}`);
export const getActivePractice = () => request<PracticeDetail | null>("/api/v1/sessions/active");
export const createPractice = (profileId: string, assetId: string, key: string) => write<PracticeDetail>("/api/v1/sessions", "POST", {
  languageProfileId: profileId, mediaAssetId: assetId, idempotencyKey: key,
});
export const recordPractice = (id: string, event: PracticeEvent) => write<PracticeDetail>(`/api/v1/sessions/${id}/demo-events`, "POST", event);
export const completePractice = (id: string) => write<{ id: string; status: string }>(`/api/v1/sessions/${id}/complete`, "POST", {});
