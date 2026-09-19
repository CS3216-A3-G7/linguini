import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, ProgressTrail, TopBar } from "../components/ui";
import { ArrowRightIcon, CameraIcon } from "../components/icons";
import { ImageUpload } from "../components/ImageUpload";
import { createPractice } from "../lib/api";
import type { UploadedImage } from "../lib/api";
import { SceneImage } from "../components/SceneImage";
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
  const cont = async () => {
    if (starting) return;
    if (uploaded) {
      if (!activeProfile) { setStartError("Choose a learning language first."); return; }
      setStarting(true); setStartError(null);
      if (requestKey.current?.asset !== uploaded.id) requestKey.current = { asset: uploaded.id, key: crypto.randomUUID() };
      try {
        const session = await createPractice(activeProfile.id, uploaded.id, requestKey.current.key);
        navigate(`/practice/uploads/${session.session.id}/analysis`);
      } catch (e) { setStartError(e instanceof Error ? e.message : "Unable to start analysis."); }
      finally { setStarting(false); }
      return;
    }
    if (!selected) return;
    startSession(selected);
    navigate(`/practice/${selected}/analysis`);
  };

  return (
    <div className="stack">
      <TopBar
        title="Step 1: Select environment"
        onBack={() => navigate("/home")}
        help="Your photo becomes the basis of this learning session."
      />
      <ProgressTrail value={1} total={3} label="Step 1 of 3" />

      <h1>Choose your environment</h1>
      <p className="muted">Take a photo of the world around you, or start from a ready scene.</p>

      <div className="dashed-capture">
        {uploaded ? (
          <>
            <span className="thumb thumb--lg">
              <SceneImage scene={{ imageUrl: uploaded.signedUrl, title: "Uploaded photo" }} />
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
      <div className="grid-3">
        {scenes.map((scene) => (
          <button
            key={scene.id}
            type="button"
            disabled={uploading || starting}
            className={`scene-pick${selected === scene.id ? " scene-pick--selected" : ""}`}
            aria-pressed={selected === scene.id}
            onClick={() => {
              setUploaded(null);
              setSelected(scene.id);
            }}
          >
            <SceneImage scene={scene} />
            <span className="small" style={{ fontWeight: 700 }}>
              {scene.title}
            </span>
          </button>
        ))}
      </div>

      <Button block disabled={(!selected && !uploaded) || uploading || starting} onClick={cont}>
        Continue <ArrowRightIcon />
      </Button>
      {startError ? <p role="alert">{startError}</p> : null}
      {starting ? <p role="status">Starting analysis?</p> : null}
      {!selected && !uploaded ? (
        <p className="small muted center-text">Pick a scene to continue.</p>
      ) : null}
    </div>
  );
}
