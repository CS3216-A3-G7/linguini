import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Card, Feedback, IconButton, ProgressTrail, TopBar } from "../components/ui";
import { ArrowRightIcon, MicIcon } from "../components/icons";
import { ScenePhoto } from "../components/ScenePhoto";
import { getScene } from "../data/mock";
import { useAppState } from "../state/useAppState";

export function ISpyPhase2() {
  const navigate = useNavigate();
  const { sceneId } = useParams();
  const scene = getScene(sceneId);
  const { session, recordRound } = useAppState();
  const [promptIndex, setPromptIndex] = useState(0);
  const [clue, setClue] = useState("");
  const [guessed, setGuessed] = useState(false);

  const prompt = scene.prompts[promptIndex];
  const target = scene.items.find((item) => item.id === prompt.itemId);

  const send = () => {
    if (!clue.trim()) return;
    setGuessed(true);
    recordRound(true);
  };

  const next = () => {
    if (promptIndex === scene.prompts.length - 1) {
      navigate(`/practice/${scene.id}/summary`);
      return;
    }
    setPromptIndex((current) => current + 1);
    setClue("");
    setGuessed(false);
  };

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
