import { practiceScene } from "../lib/practiceScene";
import { useCallback, useRef, useState } from "react";
import { Link, Navigate, Outlet, useLocation, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getPractice } from "../lib/api";
import type { PracticeDetail } from "../lib/api";
import { isSessionRouteAllowed, sessionDestination, sessionLoadingCopy } from "../lib/sessionRoute";
import { queryError, queryKeys } from "../lib/queryKeys";
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
  const [detail, setDetail] = useState<PracticeDetail | null>(null);
  const location = useLocation();
  // The guard validates every navigation against the latest canonical
  // destination, but a page whose session advanced underneath it is not
  // re-validated while the pathname stays the same — Back/Forward and every
  // in-app move change the pathname, so they are always checked.
  const checked = useRef<{ path: string; allowed: boolean } | null>(null);
  const load = useCallback(async (signal?: AbortSignal): Promise<Scene> => {
    const initial = await getPractice(id);
    const media = { id: initial.mediaAsset.id, signedUrl: initial.imageUrl ?? "" };
    if (!signal?.aborted) setPreview(practiceScene(initial, media, learner.language));
    const loaded = await loadSession(id, initial);
    setDetail(loaded);
    return practiceScene(loaded, media, learner.language);
  }, [id, loadSession, learner.language]);
  // Side-effecting session resolution: never served from or retained in cache.
  const { data, isPending: loading, error: queryErrorValue } = useQuery({
    queryKey: queryKeys.sessionScene(id),
    queryFn: ({ signal }) => load(signal),
    staleTime: 0, gcTime: 0, retry: false, refetchOnMount: "always",
  });
  const error = queryError(queryErrorValue);
  const copy = sessionLoadingCopy(location.pathname);
  if (loading) return copy.scan && preview ? <div className="stack analysis-page">
    <h1>{copy.title}</h1>
    <section className="analysis-loading" aria-live="polite" aria-busy="true">
      <div className="analysis-scan" aria-hidden="true"><ScenePhoto scene={preview} items={[]} /><span className="analysis-scan__line" /></div>
      <div className="analysis-loading__copy"><h2>{copy.heading}</h2><p className="muted">This will only take a moment.</p></div>
    </section>
  </div> : <LoadingScreen label={copy.heading} />;
  if (!data || error) return <div className="stack"><p role="alert">{error ?? "Session unavailable."}</p><button onClick={() => window.location.reload()}>Retry</button><Link to="/practice">Choose an image</Link></div>;
  const current = session?.session.id === id
    ? practiceScene(session, { id: data.mediaAssetId, signedUrl: data.imageUrl ?? "" }, learner.language)
    : data;
  const authoritative = session?.session.id === id ? session : detail;
  if (authoritative && checked.current?.path !== location.pathname) {
    checked.current = { path: location.pathname, allowed: isSessionRouteAllowed(authoritative, location.pathname) };
  }
  if (checked.current && !checked.current.allowed) {
    const dest = sessionDestination(authoritative!);
    return <Navigate to={dest.path} replace state={dest.notice ? { practiceNotice: dest.notice } : undefined} />;
  }
  return <Outlet context={current} />;
}
