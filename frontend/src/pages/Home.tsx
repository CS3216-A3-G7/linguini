
import { useNavigate } from "react-router-dom";
import { Button, Card, Noodle, ProgressTrail } from "../components/ui";
import { ArrowRightIcon, BookIcon, CameraIcon, MicIcon, TrendIcon } from "../components/icons";
import { SceneArt } from "../components/SceneArt";
import { SceneCatalogStatus } from "../components/SceneCatalogStatus";
import { useAppState } from "../state/useAppState";


export function Home() {
  const navigate = useNavigate();
  const { startSession, progress, progressLoading, progressError, scenes, user, learner } = useAppState();
  const resume = progress?.scenarios.find((item) => item.status === "in-progress");
  const resumeScene = scenes.find((scene) => scene.id === resume?.sceneId);
  const suggestions = scenes.slice(0, 3);

  const begin = (sceneId?: string) => {
    if (sceneId) {
      startSession(sceneId);
      navigate(`/practice/${sceneId}/analysis`);
      return;
    }
    navigate("/practice");
  };

  return (
    <div className="stack">
      <div className="stack-2">
        {user ? <h1>Hello, {user.displayName}!</h1> : <h1>Welcome</h1>}
        <p className="small muted">Learning {learner.language} · {learner.dailyMinutes ?? "No"} min daily goal</p>
      </div>

      <Card lifted>
        <div className="stack">
          <div className="spread">
            <div>
              <h2>Start a new practice</h2>
              <p className="small muted">Snap a scene, learn the words, then play I-Spy.</p>
            </div>
            <span aria-hidden="true" className="row" style={{ color: "var(--teal-dark)" }}>
              <MicIcon />
              <CameraIcon />
            </span>
          </div>
          <Button block onClick={() => begin()}>
            Choose an environment <ArrowRightIcon />
          </Button>
        </div>
      </Card>

      {progressLoading ? <p role="status" className="small muted">Loading your active scenario…</p> : null}
      {progressError ? <p role="alert" className="small">{progressError} Reload to retry.</p> : null}
      {resumeScene && resume ? (
        <Card plain>
          <div className="stack-2">
            <span className="label muted">Pick up where you left off</span>
            <div className="row">
              <span className="thumb">
                <SceneArt scene={resumeScene.art} />
              </span>
              <div className="grow stack-2">
                <strong>{resumeScene.title}</strong>
                <ProgressTrail
                  value={resume.spokenItems}
                  total={resume.totalItems}
                  label={`${resume.spokenItems} / ${resume.totalItems} items found`}
                />
              </div>
            </div>
            <Button variant="secondary" onClick={() => begin(resumeScene.id)}>
              Continue scenario
            </Button>
          </div>
        </Card>
      ) : null}

      <Noodle />

      <div className="stack-2">
        <h2>Or practise with a ready scene</h2>
        <SceneCatalogStatus />
        <div className="grid-3">
          {suggestions.map((scene) => (
            <button
              key={scene.id}
              type="button"
              className="scene-pick"
              onClick={() => begin(scene.id)}
            >
              <SceneArt scene={scene.art} />
              <span className="small" style={{ fontWeight: 700 }}>
                {scene.title}
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className="grid-2">
        <Button variant="secondary" onClick={() => navigate("/vocabulary")}>
          <BookIcon size={18} /> Vocabulary
        </Button>
        <Button variant="secondary" onClick={() => navigate("/progress")}>
          <TrendIcon size={18} /> Progress
        </Button>
      </div>
    </div>
  );
}
