import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "../components/ui";
import { CameraIcon } from "../components/icons";
import { ImageUpload } from "../components/ImageUpload";
import { ApiError, createPractice, getActivePractice } from "../lib/api";
import type { PracticeDetail } from "../lib/api";
import { SceneVisual } from "../components/SceneVisual";
import { SceneCatalogStatus } from "../components/SceneCatalogStatus";
import { sessionDestination } from "../lib/sessionRoute";
import { useAppState } from "../state/useAppState";

export function PracticeSelect() {
  const navigate = useNavigate();
  const notice = (useLocation().state as { practiceNotice?: string } | null)?.practiceNotice;
  const { scenes, learner, activeProfile } = useAppState();
  const activeProfileId = activeProfile?.id;
  const [uploading, setUploading] = useState(false);
  const [selected, setSelected] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSession, setActiveSession] = useState<PracticeDetail | null>(null);
  const [activeCheckLoading, setActiveCheckLoading] = useState(true);
  const [activeCheckError, setActiveCheckError] = useState<string | null>(null);
  const busy = useRef(false);
  const request = useRef<{ asset: string; key: string } | null>(null);
  useEffect(() => {
    let cancelled = false;
    if (!activeProfileId) {
      setActiveSession(null);
      setActiveCheckLoading(false);
      return () => { cancelled = true; };
    }
    setActiveSession(null);
    setActiveCheckLoading(true);
    setActiveCheckError(null);
    getActivePractice()
      .then(session => { if (!cancelled) setActiveSession(session); })
      .catch(reason => {
        if (!cancelled) setActiveCheckError(reason instanceof Error ? reason.message : "Unable to check active practice.");
      })
      .finally(() => { if (!cancelled) setActiveCheckLoading(false); });
    return () => { cancelled = true; };
  }, [activeProfileId]);
  const interactionDisabled = selected || starting || activeCheckLoading || !!activeSession || !!activeCheckError || !activeProfile;
  const start = async (asset: string) => {
    if (busy.current || !activeProfile || activeCheckLoading || activeSession || activeCheckError) return;
    busy.current = true; setSelected(true); setStarting(true); setError(null);
    if (request.current?.asset !== asset) request.current = { asset, key: crypto.randomUUID() };
    try {
      const detail = await createPractice(activeProfile.id, asset, request.current.key);
      navigate(sessionDestination(detail).path);
    } catch (reason) {
      if (reason instanceof ApiError && reason.code === "active_session_exists" && reason.activeSessionId) {
        setSelected(false);
        const existing = await getActivePractice().catch(() => null);
        if (existing) setActiveSession(existing);
        navigate(existing ? sessionDestination(existing).path : `/practice/sessions/${reason.activeSessionId}/analysis`);
        return;
      }
      setError(reason instanceof Error ? reason.message : "Unable to start practice.");
    }
    finally { busy.current = false; setStarting(false); }
  };
  const continueActive = async () => {
    try {
      const fresh = await getActivePractice();
      if (!fresh) { setActiveSession(null); return; }
      setActiveSession(fresh);
      navigate(sessionDestination(fresh).path);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to load your practice."); }
  };
  return <div className="stack practice-select">
    <h1>Capture a scene</h1>
    {notice ? <p role="alert">{notice}</p> : null}
    <p className="muted">Take a photo of the world around you, or start from a ready scene.</p>
    {activeCheckLoading ? <p role="status">Checking your current practice...</p> : null}
    {activeCheckError ? <p role="alert">{activeCheckError} Reload to check before starting a new practice.</p> : null}
    {activeSession ? <div className="practice-select__active" role="status">
      <div>
        <strong>You already have an active practice</strong>
        <p className="small muted">Continue it before starting another session.</p>
      </div>
      <Button variant="secondary" onClick={() => void continueActive()}>
        Continue practice
      </Button>
    </div> : null}
    <div className="dashed-capture">
      <span style={{ color: "var(--teal-dark)" }}><CameraIcon size={44} /></span>
      <ImageUpload compact disabled={interactionDisabled} cameraEnabled={learner.cameraOn}
        onBusyChange={setUploading} onUploaded={image => void start(image.id)} />
    </div>
    {starting ? <p role="status">Starting analysis...</p> : null}
    {error ? <div className="stack-2"><p role="alert">{error}</p><Button disabled={starting || uploading} onClick={() => request.current && void start(request.current.asset)}>Retry</Button></div> : null}
    {!activeProfile ? <p role="alert">Choose a learning language in Profile to start.</p> : null}
    <h2>Or practise with the below</h2>
    <SceneCatalogStatus />
    <div className="grid-2">
      {scenes.map(scene => <button key={scene.id} type="button" className="scene-pick"
        disabled={interactionDisabled || uploading} aria-label={`Choose ${scene.title}`} onClick={() => void start(scene.mediaAssetId)}>
        <SceneVisual scene={scene} />
        <span className="small items-center justify-center" style={{ fontWeight: 700 }}>{scene.title}</span>
      </button>)}
    </div>
  </div>;
}
