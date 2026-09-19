import { useEffect, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { Button, Feedback, IconButton, ProgressTrail } from "../components/ui";
import { ArrowRightIcon, CheckIcon, SpeakerIcon } from "../components/icons";
import { ScenePhoto } from "../components/ScenePhoto";
import { getScene } from "../data/mock";
import { speak } from "../lib/speech";
import { useAppState } from "../state/useAppState";

export function ISpyPhase1() {
  const navigate = useNavigate();
  const { sceneId } = useParams();
  const scene = getScene(sceneId);
  const { session, ensureSession, recordRound } = useAppState();
  const [roundIndex, setRoundIndex] = useState(0);
  const [picked, setPicked] = useState<string | null>(null);
  const [showTranslation, setShowTranslation] = useState(false);

  useEffect(() => {
    ensureSession(scene.id);
  }, [scene.id, ensureSession]);

  const ready =
    session.sceneId === scene.id &&
    scene.tasks.every((task) => session.completedTaskIds.includes(task.id));

  const round = scene.rounds[roundIndex];
  const isCorrect = picked === round.answerId;
  const answered = picked !== null;

  const choose = (choiceId: string) => {
    if (answered) return;
    setPicked(choiceId);
    recordRound(round.id, choiceId === round.answerId);
  };

  const next = () => {
    if (roundIndex === scene.rounds.length - 1) {
      navigate(`/practice/${scene.id}/ispy-2`);
      return;
    }
    setRoundIndex((current) => current + 1);
    setPicked(null);
    setShowTranslation(false);
  };

  const answerItem = scene.items.find((item) => item.id === round.answerId);

  if (!ready) return <Navigate to={`/practice/${scene.id}/learn`} replace />;

  return (
    <div className="stack">
      <h2 className="text-center">I-Spy · Linguini's clues</h2>
      <p>Use the clues to find the word</p>
      <ProgressTrail
        value={roundIndex + (answered ? 1 : 0)}
        total={scene.rounds.length}
        label={`${roundIndex + 1} / ${scene.rounds.length}`}
      />

      <ScenePhoto scene={scene} activeItemId={answered && isCorrect ? round.answerId : null} />

      <div className="card card--lifted stack-2">
        <div className="spread">
          <span className="label muted">Linguini says</span>
          <IconButton label="Hear the clue" onClick={() => speak(round.clue)}>
            <SpeakerIcon />
          </IconButton>
        </div>
        <h3>{round.clue}</h3>
        {showTranslation ? (
          <p className="small muted">{round.clueTranslation}</p>
        ) : (
          <Button variant="quiet" onClick={() => setShowTranslation(true)}>
            Show English
          </Button>
        )}
      </div>

      <div className="choice-grid">
        {round.choices.map((choice) => {
          const state = !answered
            ? ""
            : choice.id === round.answerId
              ? " choice--correct"
              : choice.id === picked
                ? " choice--incorrect"
                : "";
          return (
            <button
              key={choice.id}
              type="button"
              className={`choice${state}`}
              disabled={answered}
              onClick={() => choose(choice.id)}
            >
              {answered && choice.id === round.answerId ? <CheckIcon size={16} /> : null} {choice.label}
            </button>
          );
        })}
      </div>

      {answered ? (
        <Feedback tone={isCorrect ? "good" : "warn"}>
          <div className="stack-2">
            <strong>
              {isCorrect ? "Correct" : "Almost"} — {answerItem?.word ?? round.choices[0].label}
            </strong>
            <span className="small muted">{round.encouragement}</span>
          </div>
        </Feedback>
      ) : null}

      <Button block disabled={!answered} onClick={next}>
        {roundIndex === scene.rounds.length - 1 ? "Your turn to give clues" : "Next"}{" "}
        <ArrowRightIcon />
      </Button>
    </div>
  );
}
