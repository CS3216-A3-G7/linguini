import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Button, Card, Feedback, IconButton, ProgressTrail, TopBar } from "../components/ui";
import { ArrowRightIcon, MicIcon } from "../components/icons";
import { ScenePhoto } from "../components/ScenePhoto";
import { useScene } from "../state/useScene";
import { useAppState } from "../state/useAppState";

export function ISpyPhase2() {
  const navigate = useNavigate();
  const scene = useScene();
  const { session, ensureSession, recordClue } = useAppState();
  const [promptIndex, setPromptIndex] = useState(() => {
    const next = scene.prompts.findIndex((prompt) => !session.scoredRoundIds.includes(`clue:${prompt.id}`));
    return next < 0 ? scene.prompts.length - 1 : next;
  });
  const [clue, setClue] = useState(session.clues[scene.prompts[promptIndex].id] ?? "");
  const guessed = session.scoredRoundIds.includes(`clue:${scene.prompts[promptIndex].id}`);

  useEffect(() => {
    ensureSession(scene.id);
  }, [scene.id, ensureSession]);

  const ready =
    session.sceneId === scene.id &&
    scene.tasks.every((task) => session.completedTaskIds.includes(task.id));

  const prompt = scene.prompts[promptIndex];
  const target = scene.items.find((item) => item.id === prompt.itemId);

  const send = async () => {
    if (!clue.trim()) return;
    await recordClue(prompt.id, clue);
  };

  const next = () => {
    if (promptIndex === scene.prompts.length - 1) {
      navigate(`/practice/${scene.id}/summary`);
      return;
    }
    setPromptIndex((current) => current + 1);
    setClue("");
  };

  if (!ready) return <Navigate to={`/practice/${scene.id}/learn`} replace />;

  return (
    <div className="stack">
      <TopBar title="I-Spy · Your clues" help="Describe the highlighted item and let Linguini guess." />
      <ProgressTrail
        value={promptIndex + (guessed ? 1 : 0)}
        total={scene.prompts.length}
        label={`${promptIndex + 1} / ${scene.prompts.length}`}
      />

      <ScenePhoto scene={scene} items={target ? [target] : []} activeItemId={target?.id ?? null} />

      <Card>
        <div className="stack-2">
          <span className="label muted">Describe this</span>
          <h2>{target?.word}</h2>
          <span className="small muted">{target?.translation}</span>
        </div>
      </Card>

      <div className="stack-2">
        <span className="label muted">Word suggestions</span>
        <div className="chip-row">
          {prompt.suggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              className="chip"
              onClick={() => setClue((current) => `${current} ${suggestion}`.trim())}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <label className="field__label" htmlFor="clue">
          I spy with my little eye…
        </label>
        <div className="row">
          <input
            id="clue"
            className="input"
            placeholder="Es grande y verde…"
            value={clue}
            disabled={guessed}
            onChange={(event) => setClue(event.target.value)}
          />
          <IconButton
            label={session.micReady ? "Speak your clue" : "Microphone is off — type instead"}
            onClick={() => setClue((current) => current || "Es grande y verde")}
          >
            <MicIcon />
          </IconButton>
        </div>
        <span className="small muted">
          {session.micReady ? "Speak or type — both count." : "Mic is off, so typing is fine."}
        </span>
      </div>

      {guessed ? (
        <Feedback>
          <div className="stack-2">
            <strong>Linguini guesses: {prompt.llmGuess}</strong>
            <span className="small muted">{prompt.feedback}</span>
          </div>
        </Feedback>
      ) : null}

      {guessed ? (
        <Button block onClick={next}>
          {promptIndex === scene.prompts.length - 1 ? "Finish session" : "Next item"} <ArrowRightIcon />
        </Button>
      ) : (
        <Button block disabled={!clue.trim()} onClick={send}>
          Send my clue
        </Button>
      )}
    </div>
  );
}
