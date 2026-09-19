import { useNavigate } from "react-router-dom";
import { Button, Card, ProgressTrail } from "../components/ui";
import { ArrowRightIcon, BookIcon, CameraIcon, TrendIcon } from "../components/icons";
import { SceneArt } from "../components/SceneArt";
import { getScene } from "../data/mock";
import { useAppState } from "../state/useAppState";

export function Home() {
  const navigate = useNavigate();
  const { learner, session } = useAppState();
  const sessionScene = getScene(session.sceneId);
  const hasPracticeActivity =
    session.analysisScored || session.completedTaskIds.length > 0 || session.roundsPlayed > 0;
  const sessionIsComplete =
    session.completedTaskIds.length === sessionScene.tasks.length &&
    session.roundsPlayed >= sessionScene.rounds.length + sessionScene.prompts.length;
  const hasSessionToContinue = hasPracticeActivity && !sessionIsComplete;
  const hasWordsToUse = session.completedTaskIds.length > 0;

  return (
    <div className="stack" style={{ gap: "var(--space-6)" }}>
      <div className="stack-2">
        <span className="label muted">Your {learner.language} practice</span>
        <h1>Hello, {learner.name}</h1>
      </div>

      {hasSessionToContinue ? (
        <Card lifted>
          <div className="stack">
            <div className="stack-2">
              <span className="label muted">Ready when you are</span>
              <h2>Continue your practice</h2>
            </div>
            <div className="row">
              <span className="thumb thumb--lg">
                <SceneArt scene={sessionScene.art} />
              </span>
              <div className="grow stack-2">
                <strong>{sessionScene.title}</strong>
                <ProgressTrail
                  value={session.completedTaskIds.length}
                  total={sessionScene.tasks.length}
                  label={`${session.completedTaskIds.length} of ${sessionScene.tasks.length} learning tasks complete`}
                />
              </div>
            </div>
            <Button block onClick={() => navigate(`/practice/${sessionScene.id}/learn`)}>
              Continue learning <ArrowRightIcon />
            </Button>
          </div>
        </Card>
      ) : (
        <Card lifted>
          <div className="stack">
            <div className="home-camera-visual" aria-hidden="true">
              <CameraIcon size={82} />
            </div>
            <div className="stack-2">
              <h2>Capture a scene</h2>
              <p className="small muted">Your photo becomes today&apos;s lesson.</p>
            </div>
            <Button block onClick={() => navigate("/practice")}>
              Start learning <ArrowRightIcon />
            </Button>
          </div>
        </Card>
      )}

      {hasWordsToUse ? (
        <Card plain>
          <div className="stack-2">
            <span className="label muted">A small next step</span>
            <h2>Use today&apos;s words</h2>
            <p className="small muted">Write a few sentences while your new vocabulary is fresh.</p>
            <Button variant="secondary" block onClick={() => navigate("/journal/new")}>
              <BookIcon size={18} /> Write journal entry
            </Button>
          </div>
        </Card>
      ) : null}

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
