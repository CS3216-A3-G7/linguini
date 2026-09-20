import { useCallback } from "react";
import { Navigate, useParams } from "react-router-dom";
import { useApiData } from "../lib/useApiData";
import { getActivePractice } from "../lib/api";
import { useAppState } from "../state/useAppState";
import { LoadingScreen } from "./LoadingScreen";
export function SceneRoute() {
  const { sceneId = "" } = useParams();
  const { startSession } = useAppState();
  const load = useCallback(async () => {
    const active = await getActivePractice();
    return active?.sceneId === sceneId ? active : startSession(sceneId);
  }, [sceneId, startSession]);
  const { data, error } = useApiData(load);
  if (error) return <p role="alert">{error}</p>;
  if (!data) return <LoadingScreen label="Loading session..." />;
  return <Navigate replace to={`/practice/sessions/${data.session.id}/analysis`} />;
}
