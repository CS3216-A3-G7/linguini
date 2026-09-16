import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, ProgressTrail, TopBar } from "../components/ui";
import { ArrowRightIcon, CameraIcon, UploadIcon } from "../components/icons";
import { SceneArt } from "../components/SceneArt";
import { SceneCatalogStatus } from "../components/SceneCatalogStatus";
import { useAppState } from "../state/useAppState";

export function PracticeSelect() {
  const navigate = useNavigate();
  const { startSession, scenes, learner } = useAppState();
  const [selected, setSelected] = useState<string | null>(null);
  const [captured, setCaptured] = useState(false);

  if (!scenes.length) return <div className="stack"><h1>Choose your environment</h1><SceneCatalogStatus /></div>;

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
      <TopBar
        title="Step 1: Select environment"
        onBack={() => navigate("/home")}
        help="Your photo becomes the basis of this learning session."
      />
      <ProgressTrail value={1} total={3} label="Step 1 of 3" />

      <h1>Choose your environment</h1>
      <p className="muted">Take a photo of the world around you, or start from a ready scene.</p>

      <div className="dashed-capture">
        {captured ? (
          <>
            <span className="thumb thumb--lg">
              <SceneArt scene={scenes[0].art} />
            </span>
            <p className="small muted">Photo captured — {scenes[0].title}</p>
          </>
        ) : (
          <>
            <span style={{ color: "var(--teal-dark)" }}>
              <CameraIcon size={44} />
            </span>
            <p className="small muted center-text">Your photo goes here</p>
          </>
        )}
        <div className="row">
          <Button onClick={capture} disabled={!learner.cameraOn}>
            <CameraIcon size={18} /> Open camera
          </Button>
          <Button variant="secondary" onClick={capture}>
            <UploadIcon size={18} /> Upload
          </Button>
        </div>
      </div>

      <h2>Or practise with the below</h2>
      <div className="grid-3">
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
            <SceneArt scene={scene.art} />
            <span className="small" style={{ fontWeight: 700 }}>
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
