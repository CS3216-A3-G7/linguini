import { useCallback, useState } from "react";
import { Navigate, useParams } from "react-router-dom";
import { useApiData } from "../lib/useApiData";
import { ApiError, getActivePractice } from "../lib/api";
import type { PracticeDetail } from "../lib/api";
import { useAppState } from "../state/useAppState";
import { ActiveSessionConflict } from "./ActiveSessionConflict";
import { LoadingScreen } from "./LoadingScreen";

const conflictId = (reason: unknown) =>
  reason instanceof ApiError && reason.code === "active_session_exists" ? reason.activeSessionId : null;

export function SceneRoute() {
  const { sceneId = "" } = useParams();
  const { startSession } = useAppState();
  const [conflict, setConflict] = useState<string | null>(null);
  const [fatal, setFatal] = useState<string | null>(null);
  const attempt = useCallback(async (): Promise<PracticeDetail | null> => {
    const active = await getActivePractice();
    return active?.sceneId === sceneId ? active : startSession(sceneId);
  }, [sceneId, startSession]);
  const load = useCallback(async () => {
    try {
      return await attempt();
    } catch (reason) {
      const id = conflictId(reason);
      if (id) {
        setConflict(id);
        return null;
      }
      throw reason;
    }
  }, [attempt]);
  const { data, setData, error } = useApiData(load);
  const retry = async () => {
    setConflict(null);
    try {
      setData(await attempt());
    } catch (reason) {
      const id = conflictId(reason);
      if (id) setConflict(id);
      else setFatal(reason instanceof Error ? reason.message : "Unable to load data.");
    }
  };
  if (conflict) return <ActiveSessionConflict activeSessionId={conflict} onDiscarded={retry} />;
  if (fatal ?? error) return <p role="alert">{fatal ?? error}</p>;
  if (!data) return <LoadingScreen label="Loading session..." />;
  return <Navigate replace to={`/practice/sessions/${data.session.id}/analysis`} />;
}
