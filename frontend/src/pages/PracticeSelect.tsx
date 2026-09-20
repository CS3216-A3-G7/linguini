import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui";
import { CameraIcon } from "../components/icons";
import { ImageUpload } from "../components/ImageUpload";
import { ActiveSessionConflict } from "../components/ActiveSessionConflict";
import { ApiError, createPractice, getActivePractice } from "../lib/api";
import { SceneVisual } from "../components/SceneVisual";
import { SceneCatalogStatus } from "../components/SceneCatalogStatus";
import { useAppState } from "../state/useAppState";

export function PracticeSelect() {
  const navigate = useNavigate();
  const { scenes, learner, activeProfile } = useAppState();
  const [uploading, setUploading] = useState(false);
  const [selected, setSelected] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conflict, setConflict] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [settling, setSettling] = useState(false);
  const busy = useRef(false);
  const request = useRef<{ asset: string; key: string } | null>(null);
  useEffect(() => {
    let cancelled = false;
    getActivePractice()
      .then(detail => { if (!cancelled && detail) setConflict(detail.session.id); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);
  useEffect(() => {
    if (!settling) return;
    const timer = setTimeout(() => setSettling(false), 400);
    return () => clearTimeout(timer);
  }, [settling]);
  const start = async (asset: string) => {
    if (busy.current || !activeProfile) return;
    busy.current = true; setSelected(true); setStarting(true); setError(null); setNotice(null);
    if (request.current?.asset !== asset) request.current = { asset, key: crypto.randomUUID() };
    try {
      const detail = await createPractice(activeProfile.id, asset, request.current.key);
      navigate(`/practice/sessions/${detail.session.id}/analysis`);
    } catch (reason) {
      if (reason instanceof ApiError && reason.code === "active_session_exists" && reason.activeSessionId) {
        setConflict(reason.activeSessionId);
        setSelected(false);
      } else {
        setError(reason instanceof Error ? reason.message : "Unable to start practice.");
      }
    }
    finally { busy.current = false; setStarting(false); }
  };
  const discarded = async () => {
    setConflict(null);
    if (request.current) { await start(request.current.asset); return; }
    setNotice("Session discarded. Pick a scene or add a photo to start.");
    setSettling(true);
  };
  return <div className="stack practice-select">
    <h1>Capture a scene</h1>
    <p className="muted">Take a photo of the world around you, or start from a ready scene.</p>
    <div className="dashed-capture">
      <span style={{ color: "var(--teal-dark)" }}><CameraIcon size={44} /></span>
      <ImageUpload compact disabled={selected || starting || settling || conflict !== null || !activeProfile} cameraEnabled={learner.cameraOn}
        onBusyChange={setUploading} onUploaded={image => void start(image.id)} />
    </div>
    {starting ? <p role="status">Starting analysis...</p> : null}
    {conflict ? <ActiveSessionConflict activeSessionId={conflict} onDiscarded={discarded} />
      : notice ? <p role="status">{notice}</p>
      : error ? <div className="stack-2"><p role="alert">{error}</p><Button disabled={starting || uploading} onClick={() => request.current && void start(request.current.asset)}>Retry</Button></div> : null}
    {!activeProfile ? <p role="alert">Choose a learning language in Profile to start.</p> : null}
    <h2>Or practise with the below</h2>
    <SceneCatalogStatus />
    <div className="grid-2">
      {scenes.map(scene => <button key={scene.id} type="button" className="scene-pick"
        disabled={selected || uploading || starting || settling || conflict !== null || !activeProfile} aria-label={`Choose ${scene.title}`} onClick={() => void start(scene.mediaAssetId)}>
        <SceneVisual scene={scene} />
        <span className="small items-center justify-center" style={{ fontWeight: 700 }}>{scene.title}</span>
      </button>)}
    </div>
  </div>;
}
