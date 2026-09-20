import { useCallback, useState } from "react";
import { Navigate, useParams } from "react-router-dom";
import { useApiData } from "../lib/useApiData";
import { ApiError, getActivePractice } from "../lib/api";
import type { PracticeDetail } from "../lib/api";
import { sessionDestination } from "../lib/sessionRoute";
import { useAppState } from "../state/useAppState";
import { LoadingScreen } from "./LoadingScreen";

export function SceneRoute() {
  const { sceneId = "" } = useParams();
  const { startSession } = useAppState();
  const [resume, setResume] = useState<PracticeDetail | null>(null);
  const load = useCallback(async () => {
    try {
      const active = await getActivePractice();
      return active?.sceneId === sceneId ? active : await startSession(sceneId);
    } catch (reason) {
      if (reason instanceof ApiError && reason.code === "active_session_exists" && reason.activeSessionId) {
        const existing = await getActivePractice().catch(() => null);
        if (existing) { setResume(existing); return null; }
      }
      throw reason;
    }
  }, [sceneId, startSession]);
  const { data, error } = useApiData(load);
  if (resume) {
    const dest = sessionDestination(resume);
    return <Navigate replace to={dest.path} state={dest.notice ? { practiceNotice: dest.notice } : undefined} />;
  }
  if (error) return <p role="alert">{error}</p>;
  if (!data) return <LoadingScreen label="Loading session..." />;
  return <Navigate replace to={sessionDestination(data).path} />;
}
