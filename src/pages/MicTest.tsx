import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../components/ui";
import { ArrowRightIcon, MicIcon } from "../components/icons";
import { getScene } from "../data/mock";
import { useAppState } from "../state/useAppState";

type MicState = "idle" | "listening" | "working" | "unavailable";

export function MicTest() {
  const navigate = useNavigate();
  const { sceneId } = useParams();
  const scene = getScene(sceneId);
  const { ensureSession, setMicReady } = useAppState();
  const [state, setState] = useState<MicState>("idle");
  const listeningTimer = useRef<number | null>(null);

  useEffect(() => {
    ensureSession(scene.id);
  }, [scene.id, ensureSession]);

  useEffect(
    () => () => {
      if (listeningTimer.current !== null) window.clearTimeout(listeningTimer.current);
    },
    [],
  );

  const listen = () => {
    if (listeningTimer.current !== null) window.clearTimeout(listeningTimer.current);
    setState("listening");
    listeningTimer.current = window.setTimeout(() => {
      setState("working");
      setMicReady(true);
      listeningTimer.current = null;
    }, 1200);
  };

  const skip = () => {
    if (listeningTimer.current !== null) {
      window.clearTimeout(listeningTimer.current);
      listeningTimer.current = null;
    }
    setState("unavailable");
    setMicReady(false);
  };

  return (
    <div className="stack mic-test-page">
      <h1>Test your mic</h1>
      <p className="muted">Say this phrase out loud.</p>

      <section className="mic-test-panel" aria-label="Microphone test">
        <div className="mic-prompt">
          <h2>“¡Hola! Vamos a empezar.”</h2>
          <span className="small muted">Hello! Let&apos;s start.</span>
        </div>

        <button
          type="button"
          className="mic-test-control"
          onClick={listen}
          disabled={state === "listening"}
          aria-label={state === "listening" ? "Listening" : "Test my microphone"}
        >
          <span className={`mic-orb${state === "listening" ? " mic-orb--live" : ""}`}>
            <MicIcon size={48} />
          </span>
          <strong>{state === "listening" ? "Listening…" : "Tap to test"}</strong>
        </button>

        {state === "working" ? (
          <p className="mic-status mic-status--success" role="status">
            Your mic is working.
          </p>
        ) : null}

        {state === "unavailable" ? (
          <p className="mic-status" role="status">
            Typing is ready instead.
          </p>
        ) : null}
      </section>

      <Button
        variant="quiet"
        className="mic-typing-action"
        block
        onClick={skip}
        disabled={state === "listening"}
      >
        Use typing instead
      </Button>

      <Button
        block
        disabled={state === "idle" || state === "listening"}
        onClick={() => navigate(`/practice/${scene.id}/learn`)}
      >
        Continue <ArrowRightIcon />
      </Button>
    </div>
  );
}
