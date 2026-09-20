import { useCallback, useRef, useState } from "react";
import { analyzePractice, completePractice, createPractice, getPractice, getProgress, getSceneDetail, reviewPractice, taskAction } from "../lib/api";
import type { PracticeReview } from "../lib/api";
import type { PracticeDetail, ProgressResponse, TaskAnswer, TaskActionResult } from "../lib/api";
import { applyTaskResult } from "../lib/practiceUpdates";

export function usePractice(_userId: string, profileId: string, updateProgress: (data: ProgressResponse) => void) {
  const [session, setSession] = useState<PracticeDetail | null>(null);
  const [practiceSaving, setSaving] = useState(false);
  const [practiceError, setError] = useState<string | null>(null);
  const busy = useRef(false);
  const loadVersion = useRef(0);
  const creation = useRef<{ asset: string; key: string } | null>(null);
  const [micReady, setMicReady] = useState(false);
  const loadSession = useCallback(async (id: string) => {
    const version = ++loadVersion.current;
    let data = await getPractice(id);
    if (!data.session.planVersion && !["completed", "abandoned", "failed"].includes(data.session.status)) data = await analyzePractice(id);
    if (version === loadVersion.current) setSession(data);
    return data;
  }, []);
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
      try { updateProgress(await getProgress()); }
      catch { setError("Your task was saved. Reload to refresh the progress totals."); }
      return result;
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to save task. Retry your action."); return null; }
    finally { busy.current = false; setSaving(false); }
  }, [session, updateProgress]);
  const completeSession = useCallback(async () => {
    if (!session || busy.current) return false;
    busy.current = true; setSaving(true); setError(null);
    try {
      await completePractice(session.session.id);
      const completed = await getPractice(session.session.id);
      setSession(value => value?.session.id === completed.session.id ? completed : value);
      updateProgress(await getProgress());
      return true;
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to complete session."); return false; }
    finally { busy.current = false; setSaving(false); }
  }, [session, updateProgress]);
  const saveReview = useCallback(async (review: PracticeReview) => {
    if (!session || busy.current) return false;
    busy.current = true; setSaving(true); setError(null);
    try {
      const detail = await reviewPractice(session.session.id, review);
      setSession(current => current?.session.id === detail.session.id ? detail : current);
      return true;
    } catch (error) {
      setError(error instanceof Error ? error.message : "Unable to save your words.");
      return false;
    } finally { busy.current = false; setSaving(false); }
  }, [session]);
  return { session, practiceSaving, practiceError, startSession, loadSession, actOnTask, completeSession, saveReview, micReady, setMicReady };
}
