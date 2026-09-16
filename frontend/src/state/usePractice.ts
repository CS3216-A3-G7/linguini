import { useCallback, useRef, useState } from "react";
import { completePractice, createPractice, getActivePractice, getPractice, getProgress, getSceneDetail, recordPractice } from "../lib/api";
import type { PracticeDetail, PracticeEvent, ProgressResponse } from "../lib/api";

const empty = { id: "", status: "", sceneId: "", completedTaskIds: [] as string[], scoredRoundIds: [] as string[], analysisScored: false, roundsPlayed: 0, correctRounds: 0, sessionXp: 0, micReady: false, answers: {} as Record<string, string>, clues: {} as Record<string, string> };

export function usePractice(userId: string, profileId: string, updateProgress: (data: ProgressResponse) => void) {
  const [session, setSession] = useState(empty);
  const current = useRef(empty);
  const loading = useRef<Promise<boolean> | null>(null);
  const [sessionLoading, setLoading] = useState(false);
  const [practiceSaving, setSaving] = useState(false);
  const [practiceError, setError] = useState<string | null>(null);
  const queue = useRef(Promise.resolve(true));
  const retry = useRef<(() => Promise<boolean>) | null>(null);
  const storageKey = `linguini-session:${userId}:${profileId}`;
  const accept = useCallback((data: PracticeDetail) => {
    const value = { ...data.demoState, id: data.session.id, status: data.session.status };
    current.current = value;
    setSession(value);
    try { sessionStorage.setItem(storageKey, value.id); } catch { /* Server active session remains available. */ }
  }, [storageKey]);

  const load = useCallback(function loadScene(sceneId: string, force = false): Promise<boolean> {
    if (loading.current) return loading.current.then(() => loadScene(sceneId, force));
    if (!force && current.current.sceneId === sceneId && current.current.id) return Promise.resolve(true);
    setLoading(true);
    setError(null);
    loading.current = (async () => {
      try {
        let found: PracticeDetail | null = null;
        if (!force) {
          let saved: string | null = null;
          try { saved = sessionStorage.getItem(storageKey); } catch { /* Use the server's active session. */ }
          if (saved) {
            try { found = await getPractice(saved); } catch (error) {
              if (!(error instanceof Error && error.message.includes("HTTP 404"))) throw error;
            }
          }
          if (!found || found.demoState.sceneId !== sceneId) found = await getActivePractice();
        }
        if (!found || found.demoState.sceneId !== sceneId || found.session.status === "abandoned") {
          const scene = await getSceneDetail(sceneId);
          found = await createPractice(profileId, scene.mediaAssetId, crypto.randomUUID());
        }
        accept(found);
        return true;
      } catch (error) {
        setError(error instanceof Error ? error.message : "Unable to load practice.");
        return false;
      } finally { loading.current = null; setLoading(false); }
    })();
    return loading.current;
  }, [accept, profileId, storageKey]);

  const enqueue = useCallback((action: () => Promise<void>): Promise<boolean> => {
    const perform = async () => {
      setSaving(true);
      setError(null);
      try {
        await action();
        updateProgress(await getProgress());
        retry.current = null;
        return true;
      } catch (error) {
        setError(error instanceof Error ? error.message : "Unable to save practice.");
        retry.current = perform;
        return false;
      } finally { setSaving(false); }
    };
    const next = queue.current.then(perform);
    queue.current = next;
    return next;
  }, [updateProgress]);
  const record = useCallback((event: PracticeEvent) => {
    const id = current.current.id;
    return enqueue(async () => {
      if (!id) throw new Error("Wait for the session to load.");
      accept(await recordPractice(id, event));
    });
  }, [accept, enqueue]);
  const ensureSession = useCallback((sceneId: string) => load(sceneId), [load]);
  const startSession = useCallback((sceneId: string) => load(sceneId, true), [load]);
  const awardAnalysis = useCallback(() => record({ kind: "analysis" }), [record]);
  const completeTask = useCallback((id: string) => record({ kind: "task", itemId: id }), [record]);
  const recordRound = useCallback((id: string, answer: string) => record({ kind: "round", itemId: id, answerId: answer }), [record]);
  const recordClue = useCallback((id: string, text: string) => record({ kind: "clue", itemId: id, text }), [record]);
  const completeSession = useCallback(() => enqueue(async () => {
    const id = current.current.id;
    if (!id) throw new Error("Wait for the session to load.");
    await completePractice(id);
    accept(await getPractice(id));
  }), [accept, enqueue]);
  const setMicReady = useCallback((ready: boolean) => setSession((value) => ({ ...value, micReady: ready })), []);
  const retryPracticeSave = useCallback(() => retry.current?.() ?? Promise.resolve(false), []);
  return { session, sessionLoading, practiceSaving, practiceError, ensureSession, startSession,
    awardAnalysis, completeTask, recordRound, recordClue, completeSession, setMicReady, retryPracticeSave };
}
