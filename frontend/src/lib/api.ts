import type { LeaderboardRow, ScenarioProgress, VocabRecord, VocabStatus, WordClass } from "../data/types";
import type { Scene, SceneSummary } from "../data/types";
import type { JournalEntry } from "../data/types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, "");

export interface UploadedImage {
  id: string;
  signedUrl: string;
  mimeType: string;
  width: number;
  height: number;
}

export async function uploadImage(file: File, source: "camera" | "userUpload", onPhase: (phase: string) => void): Promise<UploadedImage> {
  if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) throw new Error("Choose a JPEG, PNG or WebP image.");
  if (!file.size || file.size > 10 * 1024 * 1024) throw new Error("Choose an image between 1 byte and 10 MB.");
  onPhase("Preparing uploadâ€¦");
  const upload = await write<{ assetId: string; storageKey: string; uploadUrl: string }>("/api/v1/media/upload-url", "POST", {
    fileName: file.name, fileSize: file.size, mimeType: file.type, source,
  });
  onPhase("Uploading imageâ€¦");
  const response = await fetch(upload.uploadUrl, {
    method: "PUT", headers: { "Content-Type": file.type, "x-upsert": "false" }, body: file,
  });
  if (!response.ok) throw new Error("Image upload failed. Please try again.");
  onPhase("Checking imageâ€¦");
  // Confirmation is idempotent; retry once if the server committed but its response was lost.
  const confirm = () => write<UploadedImage>("/api/v1/media/confirm-upload", "POST", {
    assetId: upload.assetId, storageKey: upload.storageKey, source,
  });
  try { return await confirm(); } catch (error) {
    if (error instanceof Error && /HTTP 4\d\d/.test(error.message)) throw error;
    return confirm();
  }
}

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

export class ApiError extends Error {
  readonly status: number;
  readonly code: string | null;
  readonly activeSessionId: string | null;
  constructor(message: string, status: number, code: string | null, activeSessionId: string | null) {
    super(message);
    this.status = status;
    this.code = code;
    this.activeSessionId = activeSessionId;
  }
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
    const code = typeof body?.detail?.code === "string" ? body.detail.code : null;
    const activeSessionId = typeof body?.detail?.activeSessionId === "string" ? body.detail.activeSessionId : null;
    throw new ApiError(`${message} (HTTP ${response.status})`, response.status, code, activeSessionId);
  }
  if (response.status === 204) return undefined as T;
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
  const row = await request<PreloadedScene & Pick<Scene, "items">>(
    `/api/v1/preloaded-scenes/${encodeURIComponent(id)}`, signal,
  );
  return { ...sceneSummary(row), items: row.items };
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
  const media = [...detail.media].sort((a, b) => a.displayOrder - b.displayOrder);
  return { id: row.id, languageProfileId: row.languageProfileId, date: row.localDate,
    photos: media.map((photo, index) => ({ ...photo, imageUrl: index === 0 ? detail.imageUrl ?? null : null })),
    title: row.title, mediaAssetId: [...detail.media].sort((a, b) => a.displayOrder - b.displayOrder)[0]?.mediaAssetId ?? null, imageUrl: detail.imageUrl ?? null, wordsUsed: row.selectedWords,
    body: detail.revisions.find((revision) => revision.id === row.currentRevisionId)?.content ?? "" };
}
export async function getJournals(signal?: AbortSignal): Promise<JournalEntry[]> {
  return (await request<JournalDetail[]>("/api/v1/journals", signal)).map(journalEntry);
}
export async function getJournal(id: string, signal?: AbortSignal): Promise<JournalEntry> {
  return journalEntry(await request<JournalDetail>(`/api/v1/journals/${id}`, signal));
}
export interface JournalPhotoOption {
  mediaAssetId: string;
  imageUrl: string | null;
  sessionId: string;
  completedAt: string;
}
export async function getJournalContext(date?: string, signal?: AbortSignal) {
  const context = await request<{ localDate: string; journal: JournalRecord | null; eligiblePhotos: JournalPhotoOption[] }>(`/api/v1/journal/${date ?? "today"}/context`, signal);
  return { date: context.localDate, entry: context.journal ? await getJournal(context.journal.id, signal) : null, photoOptions: context.eligiblePhotos };
}
export type JournalDraft = Pick<JournalEntry, "title" | "mediaAssetId" | "body" | "wordsUsed"> & { photoAssetIds?: string[] };
export async function saveJournal(draft: JournalDraft, profileId: string, id?: string, date?: string) {
  const body = { title: draft.title, ...(draft.photoAssetIds === undefined ? { mediaAssetId: draft.mediaAssetId } : {}), content: draft.body, selectedWords: draft.wordsUsed };
  const row = id ? await write<JournalRecord>(`/api/v1/journals/${id}`, "PATCH", body)
    : await write<JournalRecord>(`/api/v1/journal/${date ?? "today"}`, "PUT", { ...body, languageProfileId: profileId });
  if (draft.photoAssetIds !== undefined) {
    const desired = [...new Set(draft.photoAssetIds)];
    const current = await getJournal(row.id);
    // Remove changed positions first; the API requires unique positions and asset IDs.
    // Reading persisted attachments on every retry also recovers from a partial save.
    for (const photo of current.photos) {
      if (desired[photo.displayOrder] !== photo.mediaAssetId) {
        await request<void>(`/api/v1/journals/${row.id}/media/${photo.mediaAssetId}`, undefined, { method: "DELETE" });
      }
    }
    for (const [displayOrder, mediaAssetId] of desired.entries()) {
      if (!current.photos.some(photo => photo.mediaAssetId === mediaAssetId && photo.displayOrder === displayOrder)) {
        await write(`/api/v1/journals/${row.id}/media`, "POST", { mediaAssetId, displayOrder });
      }
    }
  }
  return getJournal(row.id);
}

export type TaskContent =
  | { kind: "vocabularyIntroduction"; title: string; words: VocabularyLearningWord[]; questions: VocabularyQuestion[]; allowTypingPractice: boolean; targetText?: string | null; translation?: string | null; partOfSpeech?: WordClass | null; exampleSentence?: string | null }
  | { kind: "pronunciationPractice"; prompt: string; targetText: string }
  | { kind: "grammarExplanation"; title: string; explanation: string; examples: string[] }
  | { kind: "grammarPractice"; prompt: string; options: string[] }
  | { kind: "syntaxExplanation"; title: string; sentencePattern: string; explanation: string; examples: string[] }
  | { kind: "sentenceBuilding"; prompt: string; sourceText: string | null; tokenBank: string[] }
  | { kind: "ispyRound"; clue: string; clueTranslation?: string | null; encouragement?: string | null; options: { optionId: string; label: string; sceneObjectId: string }[] }
  | { kind: "reflection"; prompt: string };
export interface SessionTask {
  id: string; kind: TaskContent["kind"]; phase: "learning" | "ispy";
  status: "pending" | "inProgress" | "completed" | "skipped";
  isSkippable: true; orderIndex: number; publicContent: TaskContent;
  vocabularyItemId: string | null; sceneObjectId: string | null;
}
export interface SessionProgress {
  completedTaskCount: number; skippedTaskCount: number; terminalTaskCount: number; totalTaskCount: number;
}
export type SessionStatus = "created" | "analyzingScene" | "awaitingObjectReview" | "generatingTasks" | "ready" | "inProgress" | "completed" | "abandoned" | "failed";
export interface PracticeDetail {
  session: { id: string; status: SessionStatus; sceneMediaAssetId: string; sessionTitle: string | null; sessionSummary: string | null; failureCode: "imageUploadFailed" | "sceneAnalysisFailed" | "noValidObjects" | "vocabularyMappingFailed" | "taskGenerationFailed" | null };
  mediaAsset: { id: string; source: "preloaded" | "camera" | "userUpload" };
  sceneId: string | null; title: string;
  analysisMode: "placeholder" | null;
  sceneObjects: SceneObject[];
  sceneObjectRelations: SceneObjectRelation[];
  vocabulary: { id: string; displayText: string; partOfSpeech: WordClass; gender: string | null; exampleSentence: string | null; languageCode: string }[];
  translations: { vocabularyItemId: string; translatedText: string }[];
  translationPreview: {
    objects: TranslatedTerm[];
    attributes: TranslatedTerm[];
    relationships: TranslatedTerm[];
  } | null;
  tasks: SessionTask[]; nextTaskId: string | null; progress: SessionProgress;
}
interface TranslatedTerm { key: string; source: string; translation: string }
export interface SceneObject {
  id: string; sessionId: string; label: string; vocabularyItemId: string | null;
  boundingBox: { x: number | string; y: number | string; width: number | string; height: number | string } | null;
  attributes: Record<string, unknown> | null; confidenceScore: number | string | null; sourceObjectKey: string | null;
}
export interface SceneObjectRelation {
  id: string; subjectSceneObjectId: string; relation: string;
  referenceSceneObjectId: string; sourceRelationKey: string | null;
}
export interface VocabularyLearningWord {
  learningKey: string | null; termType: "object" | "attribute" | "relationship";
  vocabularyItemId: string | null; sceneObjectId: string | null; targetText: string; translation: string;
  partOfSpeech: WordClass; gender: string | null; pluralForm: string | null; phoneticText: string | null;
  pronunciationAudioAssetId: string | null; exampleSentence: string | null;
}
export interface VocabularyQuestion { questionId: string; prompt: string; options: { optionId: string; label: string }[] }
export type TaskAnswer = { inputMode: "text"; text: string } | { inputMode: "multipleChoice"; optionId: string } | { inputMode: "objectSelection"; sceneObjectId: string } | { inputMode: "vocabularyReview"; answers: Record<string, string>; typedAnswers: Record<string, string> };
export interface TaskActionResult {
  task: SessionTask; nextTaskId: string | null; sessionProgress: SessionProgress;
  attempt: { id: string; isCorrect: boolean | null; feedback: { message?: string } | null } | null;
}
export const getMedia = (id: string) => request<UploadedImage>(`/api/v1/media/${id}`);
export const analyzePractice = (id: string) => write<PracticeDetail>(`/api/v1/sessions/${id}/analyze`, "POST", {});
export interface PracticeReview {
  acceptedObjectIds: string[];
  relations: SceneObjectRelation[];
  addedObjects: { id: string; label: string; x: number; y: number }[];
  objectAttributes: Record<string, Record<string, string>>;
}
export const reviewPractice = (id: string, review: PracticeReview) => write<PracticeDetail>(`/api/v1/sessions/${id}/review`, "PUT", review);
export const getPractice = (id: string) => request<PracticeDetail>(`/api/v1/sessions/${id}`);
export const getActivePractice = () => request<PracticeDetail | null>("/api/v1/sessions/active");
export const createPractice = (profileId: string, assetId: string, key: string) => write<PracticeDetail>("/api/v1/sessions", "POST", {
  languageProfileId: profileId, mediaAssetId: assetId, idempotencyKey: key,
});
export const taskAction = (id: string, action: "start" | "complete" | "skip" | "attempts", body: unknown = {}) => write<TaskActionResult>(`/api/v1/tasks/${id}/${action}`, "POST", body);
export const completePractice = (id: string) => write<{ id: string; status: string }>(`/api/v1/sessions/${id}/complete`, "POST", {});
export const abandonPractice = (id: string) => write<{ id: string; status: string }>(`/api/v1/sessions/${id}/abandon`, "POST", {});
export const getPracticeSummary = (id: string) => request<{ progress: SessionProgress; learnedVocabularyIds: string[]; xpEarned: number; ispyCorrectCount: number; ispyAttemptCount: number }>(`/api/v1/sessions/${id}/summary`);

export const checkPracticeWord = (id: string, label: string) => request<{ available: boolean }>(`/api/v1/sessions/${id}/review-word?label=${encodeURIComponent(label)}`);
