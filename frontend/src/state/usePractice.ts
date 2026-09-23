import { useCallback, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { analyzePractice, ApiError, completePractice, createPractice, getPractice, getSceneDetail, reviewPractice, taskAction } from "../lib/api";
import type { PracticeReview } from "../lib/api";
import type { PracticeDetail, SessionStatus, TaskAnswer, TaskActionResult } from "../lib/api";
import { applyTaskResult } from "../lib/practiceUpdates";
import { queryKeys } from "../lib/queryKeys";

const PROCESSING = ["analyzingScene", "generatingTasks"];

export function usePractice(_userId: string, profileId: string, onLearningChanged: (scope: "task" | "session") => void) {
  const queryClient = useQueryClient();
  const [session, setSession] = useState<PracticeDetail | null>(null);
  const [practiceSaving, setSaving] = useState(false);
  const [practiceError, setError] = useState<string | null>(null);
  const [practiceStalled, setStalled] = useState(false);
  const busy = useRef(false);
  const completing = useRef(false);
  const learningDirty = useRef(false);
  const [completionError, setCompletionError] = useState<string | null>(null);
  const loadVersion = useRef(0);
  const sessionLoads = useRef(new Map<string, Promise<PracticeDetail>>());
  const creation = useRef<{ asset: string; key: string } | null>(null);
  const [micReady, setMicReady] = useState(false);
  const loadSession = useCallback((id: string, initial?: PracticeDetail) => {
    const existing = sessionLoads.current.get(id);
    if (existing) return existing;
    const request = (async () => {
    const version = ++loadVersion.current;
    setStalled(false);
    let data = initial ?? await getPractice(id);
    if (data.session.status === "created") {
      try { data = await analyzePractice(id); }
      catch (error) {
        // Another request may have claimed the session; fall back to polling.
        if (!(error instanceof ApiError && error.status === 409)) throw error;
        data = await getPractice(id);
      }
    }
    // Scene analysis can take ~60s, so poll for up to a minute before stalling.
    if (version === loadVersion.current) setSession(data);
    for (let attempt = 0; attempt < 40 && PROCESSING.includes(data.session.status); attempt += 1) {
      await new Promise(resolve => setTimeout(resolve, 1500));
      if (version !== loadVersion.current) break;
      data = await getPractice(id);
      if (version === loadVersion.current) setSession(data);
    }
    if (version === loadVersion.current) {
      setSession(data);
      setStalled(PROCESSING.includes(data.session.status));
    }
    return data;
    })();
    sessionLoads.current.set(id, request);
    const clear = () => {
      if (sessionLoads.current.get(id) === request) sessionLoads.current.delete(id);
    };
    void request.then(clear, clear);
    return request;
  }, []);
  const retryProcessing = useCallback(async (id: string) => {
    setError(null);
    try { await loadSession(id); }
    catch (error) {
      setError(error instanceof Error ? error.message : "Unable to check your scene. Please retry.");
      setStalled(true);
    }
  }, [loadSession]);
  const startSession = useCallback(async (sceneId: string) => {
    const scene = await getSceneDetail(sceneId);
    if (creation.current?.asset !== scene.mediaAssetId) creation.current = { asset: scene.mediaAssetId, key: crypto.randomUUID() };
    const result = await createPractice(profileId, scene.mediaAssetId, creation.current.key);
    creation.current = null;
    return result;
  }, [profileId]);
  const actOnTask = useCallback(async (taskId: string, action: "complete" | "skip" | "attempts", answer?: TaskAnswer, key?: string): Promise<TaskActionResult | null> => {
    if (!session || busy.current) return null;
    busy.current = true; setSaving(true); setError(null);
    try {
      const result = await taskAction(taskId, action, answer ? { ...answer, idempotencyKey: key } : {});
      setSession(value => applyTaskResult(value, session.session.id, result));
      learningDirty.current = true;
      return result;
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to save task. Retry your action."); return null; }
    finally { busy.current = false; setSaving(false); }
  }, [session]);
  const flushLearningChanges = useCallback(() => {
    if (learningDirty.current) {
      learningDirty.current = false;
      onLearningChanged("session");
    }
  }, [onLearningChanged]);
  const completion = useMutation({
    mutationFn: ({ sessionId }: { sessionId: string; previousStatus: SessionStatus }) => completePractice(sessionId),
    onError: (error, { sessionId, previousStatus }) => {
      setSession(current => current?.session.id === sessionId
        ? { ...current, session: { ...current.session, status: previousStatus } }
        : current);
      setCompletionError(error instanceof Error ? error.message : "Unable to complete session.");
    },
    onSuccess: (completed, { sessionId }) => {
      setSession(current => current?.session.id === completed.id
        ? { ...current, session: { ...current.session, status: completed.status as SessionStatus } }
        : current);
      flushLearningChanges();
      void queryClient.invalidateQueries({ queryKey: queryKeys.sessionSummary(sessionId) });
    },
    onSettled: () => { completing.current = false; },
  });
  const startCompletion = useCallback(() => {
    if (!session || completing.current) return false;
    completing.current = true;
    setCompletionError(null);
    const previousStatus = session.session.status;
    // The route guard only sends /summary when status is "completed", so the
    // optimistic status must land synchronously before the caller navigates.
    setSession(current => current?.session.id === session.session.id
      ? { ...current, session: { ...current.session, status: "completed" } }
      : current);
    completion.mutate({ sessionId: session.session.id, previousStatus });
    return true;
  }, [session, completion.mutate]);
  const completeSession = startCompletion;
  const retryCompletion = useCallback(() => { startCompletion(); }, [startCompletion]);
  const saveReview = useCallback(async (review: PracticeReview) => {
    if (!session || busy.current) return false;
    busy.current = true; setSaving(true); setError(null);
    const previous = session;
    setSession(current => current?.session.id === session.session.id
      ? { ...current, session: { ...current.session, status: "generatingTasks" } }
      : current);
    try {
      const detail = await reviewPractice(session.session.id, review);
      setSession(current => current?.session.id === detail.session.id ? detail : current);
      // Poll in the background while analysis displays the translating screen.
      // SessionRoute forwards to the mic check when this resolves as ready.
      if (PROCESSING.includes(detail.session.status)) void loadSession(session.session.id);
      return true;
    } catch (error) {
      setSession(current => current?.session.id === previous.session.id ? previous : current);
      setError(error instanceof Error ? error.message : "Unable to save your words.");
      return false;
    } finally { busy.current = false; setSaving(false); }
  }, [session, loadSession]);
  return { session, practiceSaving, practiceError, practiceStalled, startSession, loadSession, retryProcessing, actOnTask, completeSession, completionPending: completion.isPending, completionError, retryCompletion, flushLearningChanges, saveReview, micReady, setMicReady };
}
