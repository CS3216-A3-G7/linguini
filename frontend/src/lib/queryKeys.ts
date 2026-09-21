export const queryKeys = {
  account: ["account"] as const,
  scenes: ["scenes"] as const,
  vocabulary: (profileId: string) => ["vocabulary", profileId] as const,
  progress: (profileId: string) => ["progress", profileId] as const,
  journals: (profileId: string) => ["journals", profileId] as const,
  activeSession: (profileId: string) => ["session", "active", profileId] as const,
  journal: (id: string) => ["journal", id] as const,
  journalDayContext: (date: string) => ["journal", "day", date] as const,
  media: (assetId: string, width?: number) =>
    width === undefined ? (["media", assetId] as const) : (["media", assetId, width] as const),
  sessionScene: (sessionId: string) => ["session", sessionId, "scene"] as const,
  sceneSession: (sceneId: string) => ["scene", sceneId, "session"] as const,
  sessionSummary: (sessionId: string) => ["session", sessionId, "summary"] as const,
};

export function queryError(error: unknown): string | null {
  return error instanceof Error ? error.message : error ? "Unable to load data." : null;
}
