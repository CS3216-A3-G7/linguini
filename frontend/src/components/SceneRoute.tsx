import { LoadingScreen } from "./LoadingScreen";
import { useCallback, useEffect } from "react";
import { Link, Outlet, useParams } from "react-router-dom";
import { getSceneDetail } from "../lib/api";
import { useApiData } from "../lib/useApiData";
import { useAppState } from "../state/useAppState";
import type { Scene } from "../data/types";

export function SceneRoute() {
  const { sceneId } = useParams();
  return <SceneLoader key={sceneId} sceneId={sceneId ?? ""} />;
}

function SceneLoader({ sceneId }: { sceneId: string }) {
  const load = useCallback((signal?: AbortSignal) => getSceneDetail(sceneId, signal), [sceneId]);
  const { data: scene, error, loading } = useApiData(load);
  if (loading) return <LoadingScreen label="Loading scene…" />;
  if (error || !scene) {
    return <div className="stack"><h1>Scene unavailable</h1><p role="alert">{error ?? "Scene not found."} Reload to retry.</p><Link to="/practice">Choose another scene</Link></div>;
  }
  return <SessionReady scene={scene} />;
}

function SessionReady({ scene }: { scene: Scene }) {
  const { session, ensureSession, sessionLoading, practiceError, practiceSaving, retryPracticeSave } = useAppState();
  useEffect(() => { void ensureSession(scene.id); }, [scene.id, ensureSession]);
  if (sessionLoading || session.sceneId !== scene.id) {
    if (!practiceError) return <LoadingScreen label="Loading saved practice…" />;
    return <div className="stack"><p role={practiceError ? "alert" : "status"}>{practiceError ?? "Loading saved practice…"}</p>
      {practiceError ? <button className="btn btn--secondary" onClick={() => void ensureSession(scene.id)}>Retry loading</button> : null}</div>;
  }
  return <>
    {practiceSaving ? <p role="status">Saving practice and XP…</p> : null}
    {practiceError ? <p role="alert">{practiceError} <button className="btn btn--quiet" disabled={practiceSaving} onClick={() => void retryPracticeSave()}>Retry save</button></p> : null}
    <Outlet context={scene} />
  </>;
}
