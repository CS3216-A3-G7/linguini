import { useAppState } from "../state/useAppState";

export function SceneCatalogStatus() {
  const { scenesLoading, scenesError, scenes, learner } = useAppState();
  if (scenesLoading) return <p role="status" className="small muted">Loading scenes…</p>;
  if (scenesError) return <p role="alert" className="small">{scenesError} Reload to retry.</p>;
  if (!scenes.length) return <p className="small muted">No scenes are available for {learner.language} yet. You can change your language in Profile.</p>;
  return null;
}
