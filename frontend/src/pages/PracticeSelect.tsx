import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui";
import { ArrowRightIcon, CameraIcon } from "../components/icons";
import { ImageUpload } from "../components/ImageUpload";
import { createPractice } from "../lib/api";
import type { UploadedImage } from "../lib/api";
import { SceneVisual } from "../components/SceneVisual";
import { SceneCatalogStatus } from "../components/SceneCatalogStatus";
import { useAppState } from "../state/useAppState";

export function PracticeSelect() {
  const navigate = useNavigate();
  const { startSession, scenes, learner, activeProfile } = useAppState();
  const [selected, setSelected] = useState<string | null>(null);
  const [uploaded, setUploaded] = useState<UploadedImage | null>(null);
  const [uploading, setUploading] = useState(false);

  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const requestKey = useRef<{ asset: string; key: string } | null>(null);
  const busy = useRef(false);
  const cont = async (sceneId = selected) => {
    if (busy.current || starting || uploading) return;
    if (!activeProfile) { setStartError("Choose a learning language first."); return; }
    if (uploaded && !sceneId) {
      if (!activeProfile) { setStartError("Choose a learning language first."); return; }
      busy.current = true; setStarting(true); setStartError(null);
      if (requestKey.current?.asset !== uploaded.id) requestKey.current = { asset: uploaded.id, key: crypto.randomUUID() };
      try {
        const session = await createPractice(activeProfile.id, uploaded.id, requestKey.current.key);
        navigate(`/practice/sessions/${session.session.id}/analysis`);
      } catch (e) { setStartError(e instanceof Error ? e.message : "Unable to start analysis."); }
      finally { busy.current = false; setStarting(false); }
      return;
    }
    if (!sceneId) return;
    busy.current = true; setStarting(true); setStartError(null);
    try {
      const detail = await startSession(sceneId);
      navigate(`/practice/sessions/${detail.session.id}/analysis`);
    } catch (e) { setStartError(e instanceof Error ? e.message : "Unable to start session."); }
    finally { busy.current = false; setStarting(false); }
  };

  return (
    <div className="stack practice-select">
      <h1>Capture a scene</h1>
      <p className="muted">Take a photo of the world around you, or start from a ready scene.</p>

      <div className="dashed-capture">
        {uploaded ? (
          <>
            <span className="thumb thumb--lg">
              <SceneVisual scene={{ imageUrl: uploaded.signedUrl, title: "Uploaded photo" }} />
            </span>
            <p className="small muted">Image uploaded. Continue to analyse your photo.</p>
          </>
        ) : (
          <>
            <span style={{ color: "var(--teal-dark)" }}>
              <CameraIcon size={44} />
            </span>
            <p className="small muted center-text">Your photo goes here</p>
          </>
        )}
        <ImageUpload disabled={starting} cameraEnabled={learner.cameraOn} onBusyChange={setUploading}
          onUploaded={(image) => { setUploaded(image); setSelected(null); }} />
      </div>

      <h2>Or practise with the below</h2>
      <SceneCatalogStatus />
      <div className="grid-2">
        {scenes.map((scene) => (
          <button
            key={scene.id}
            type="button"
            disabled={uploading || starting || !activeProfile}
            aria-label={`Choose ${scene.title}`}
            className={`scene-pick${selected === scene.id ? " scene-pick--selected" : ""}`}
            aria-pressed={selected === scene.id}
            onClick={() => {
              setUploaded(null);
              setSelected(scene.id);
              void cont(scene.id);
            }}
          >
            <SceneVisual scene={scene} />
            <span className="small" style={{ fontWeight: 700 }}>
              {scene.title}
            </span>
          </button>
        ))}
      </div>

      {uploaded || selected ? <Button block disabled={(!selected && !uploaded) || uploading || starting || !activeProfile} onClick={() => void cont()}>
        {startError ? "Retry" : "Continue"} <ArrowRightIcon />
      </Button> : null}
      {startError ? <p role="alert">{startError}</p> : null}
      {starting ? <p role="status">Starting analysis...</p> : null}
      {!activeProfile ? <p role="alert">Choose a learning language in Profile to start.</p> : null}
      {!selected && !uploaded ? (
        <p className="small muted center-text">Pick a scene to continue.</p>
      ) : null}
    </div>
  );
}
