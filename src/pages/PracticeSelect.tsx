import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui";
import { ArrowRightIcon, CameraIcon, UploadIcon } from "../components/icons";
import { SceneVisual } from "../components/SceneVisual";
import { scenes } from "../data/mock";
import { useAppState } from "../state/useAppState";

export function PracticeSelect() {
  const navigate = useNavigate();
  const { startSession } = useAppState();
  const [selected, setSelected] = useState<string | null>(null);
  const [captured, setCaptured] = useState(false);

  const capture = () => {
    setCaptured(true);
    setSelected(scenes[0].id);
  };

  const cont = () => {
    if (!selected) return;
    startSession(selected);
    navigate(`/practice/${selected}/analysis`);
  };

  return (
    <div className="stack">
      <h1>Capture a Scene</h1>
      <p className="muted">Take a photo of the world around you, or start from a ready scene.</p>

      <div className="dashed-capture">
        {captured ? (
          <>
            <span className="thumb thumb--lg">
              <SceneVisual scene={scenes[0]} />
            </span>
            <p className="small muted">Photo captured — {scenes[0].title}</p>
          </>
        ) : (
          <>
            <span style={{ color: "var(--teal-dark)" }}>
              <CameraIcon size={44} />
            </span>
          </>
        )}
        <div className="row">
          <Button onClick={capture}>
            <CameraIcon size={18} /> Click
          </Button>
          <Button variant="secondary" onClick={capture}>
            <UploadIcon size={18} /> Upload
          </Button>
        </div>
      </div>

      <h2>Or practise with the below</h2>
      <div className="grid-2">
        {scenes.map((scene) => (
          <button
            key={scene.id}
            type="button"
            className={`scene-pick${selected === scene.id ? " scene-pick--selected" : ""}`}
            aria-pressed={selected === scene.id}
            onClick={() => {
              setCaptured(false);
              setSelected(scene.id);
            }}
          >
            <SceneVisual scene={scene} />
            <span className="small items-center justify-center" style={{ fontWeight: 700 }}>
              {scene.title}
            </span>
          </button>
        ))}
      </div>

      <Button block disabled={!selected} onClick={cont}>
        Continue <ArrowRightIcon />
      </Button>
      {!selected ? (
        <p className="small muted center-text">Pick a scene to continue.</p>
      ) : null}
    </div>
  );
}
