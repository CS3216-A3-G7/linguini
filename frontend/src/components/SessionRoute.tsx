import { practiceScene } from "../lib/practiceScene";
import { useCallback, useState } from "react";
import { Link, Navigate, Outlet, useLocation, useParams } from "react-router-dom";
import { getMedia, getPractice } from "../lib/api";
import { useApiData } from "../lib/useApiData";
import { useAppState } from "../state/useAppState";
import type { Scene } from "../data/types";
import { ScenePhoto } from "./ScenePhoto";
import { LoadingScreen } from "./LoadingScreen";

export function SessionRoute() {
  const { sessionId = "" } = useParams();
  return <SessionLoader key={sessionId} id={sessionId} />;
}
function SessionLoader({ id }: { id: string }) {
  const { loadSession, learner, session } = useAppState();
  const [preview, setPreview] = useState<Scene | null>(null);
  const location = useLocation();
  const load = useCallback(async (signal?: AbortSignal): Promise<Scene> => {
    const initial = await getPractice(id);
    const media = await getMedia(initial.mediaAsset.id);
    if (!signal?.aborted) setPreview(practiceScene(initial, media, learner.language));
    const detail = await loadSession(id);
    return practiceScene(detail, media, learner.language);
  }, [id, loadSession, learner.language]);
  const { data, loading, error } = useApiData(load);
  if (loading) return preview ? <div className="stack analysis-page">
    <h1>Scene analysis</h1>
    <section className="analysis-loading" aria-live="polite" aria-busy="true">
      <div className="analysis-scan" aria-hidden="true"><ScenePhoto scene={preview} items={[]} /><span className="analysis-scan__line" /></div>
      <div className="analysis-loading__copy"><h2>Finding objects in your image...</h2><p className="muted">This will only take a moment.</p></div>
    </section>
  </div> : <LoadingScreen label="Loading your image..." />;
  if (!data || error) return <div className="stack"><p role="alert">{error ?? "Session unavailable."}</p><button onClick={() => window.location.reload()}>Retry</button><Link to="/practice">Choose an image</Link></div>;
  const current = session?.session.id === id
    ? practiceScene(session, { id: data.mediaAssetId, signedUrl: data.imageUrl ?? "" }, learner.language)
    : data;
  if (session?.session.id === id && !session.session.planVersion && !["completed", "abandoned", "failed"].includes(session.session.status) && !location.pathname.endsWith("/analysis")) {
    return <Navigate to={`/practice/sessions/${id}/analysis`} replace />;
  }
  return <Outlet context={current} />;
}
