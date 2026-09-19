import { practiceScene } from "../lib/practiceScene";
import { useCallback } from "react";
import { Link, Outlet, useParams } from "react-router-dom";
import { getMedia } from "../lib/api";
import { useApiData } from "../lib/useApiData";
import { useAppState } from "../state/useAppState";
import type { Scene } from "../data/types";
import { LoadingScreen } from "./LoadingScreen";

export function SessionRoute() {
  const { sessionId = "" } = useParams();
  return <SessionLoader key={sessionId} id={sessionId} />;
}
function SessionLoader({ id }: { id: string }) {
  const { loadSession, learner } = useAppState();
  const load = useCallback(async (): Promise<Scene> => {
    const detail = await loadSession(id);
    const media = await getMedia(detail.mediaAsset.id);
    return practiceScene(detail, media, learner.language);
  }, [id, loadSession, learner.language]);
  const { data, loading, error } = useApiData(load);
  if (loading) return <LoadingScreen label="Analysing your scene..." />;
  if (!data || error) return <div className="stack"><p role="alert">{error ?? "Session unavailable."}</p><button onClick={() => window.location.reload()}>Retry</button><Link to="/practice">Choose an image</Link></div>;
  return <Outlet context={data} />;
}
