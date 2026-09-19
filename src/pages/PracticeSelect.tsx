import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui";
import { CameraIcon, UploadIcon } from "../components/icons";
import { SceneVisual } from "../components/SceneVisual";
import { scenes } from "../data/mock";
import { useAppState } from "../state/useAppState";

export function PracticeSelect() {
  const navigate = useNavigate();
  const { startSession } = useAppState();

  const chooseScene = (sceneId: string) => {
    startSession(sceneId);
    navigate(`/practice/${sceneId}/analysis`);
  };

  return (
    <div className="stack">
      <h1>Capture a Scene</h1>
      <p className="muted">Take a photo of the world around you, or start from a ready scene.</p>

      <div className="dashed-capture">
        <span style={{ color: "var(--teal-dark)" }}>
          <CameraIcon size={44} />
        </span>
        <div className="row">
          <Button onClick={() => chooseScene(scenes[0].id)}>
            <CameraIcon size={18} /> Click
          </Button>
          <Button variant="secondary" onClick={() => chooseScene(scenes[0].id)}>
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
            className="scene-pick"
            aria-label={`Choose ${scene.title}`}
            onClick={() => chooseScene(scene.id)}
          >
            <SceneVisual scene={scene} />
            <span className="small items-center justify-center" style={{ fontWeight: 700 }}>
              {scene.title}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
