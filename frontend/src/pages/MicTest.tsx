import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Card, Feedback, ProgressTrail, TopBar } from "../components/ui";
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

  useEffect(() => {
    ensureSession(scene.id);
  }, [scene.id, ensureSession]);

  const listen = () => {
    setState("listening");
    window.setTimeout(() => {
      setState("working");
      setMicReady(true);
    }, 1200);
  };

  const skip = () => {
    setState("unavailable");
    setMicReady(false);
  };

  return (
    <div className="stack">
      <TopBar
        title="Step 3: Mic test"
        help="A quick check so speaking practice does not surprise you later."
      />
      <ProgressTrail value={3} total={3} label="Step 3 of 3" />

      <h1>Test your mic</h1>
      <p className="muted">Read the prompt out loud. You can also type instead — nothing is blocked.</p>

      <Card>
        <div className="stack-2 center-text">
          <span className="label muted">Test prompt</span>
          <h2>“¡Hola! Vamos a empezar.”</h2>
          <span className="small muted">Hello! Let&apos;s start.</span>
        </div>
      </Card>

      <div className={`mic-orb${state === "listening" ? " mic-orb--live" : ""}`}>
        <span style={{ color: "var(--teal-dark)" }}>
          <MicIcon size={52} />
        </span>
      </div>

      {state === "working" ? (
        <Feedback>
          <div className="stack-2">
            <strong>Mic detected and working</strong>
            <span className="small muted">We heard you clearly. Ready when you are.</span>
          </div>
        </Feedback>
      ) : null}

      {state === "unavailable" ? (
        <Feedback tone="warn">
          <div className="stack-2">
            <strong>No problem — we&apos;ll use typing</strong>
            <span className="small muted">
              You can switch the mic back on any time from your profile.
            </span>
          </div>
        </Feedback>
      ) : null}

      <div className="stack-2">
        <Button block onClick={listen} disabled={state === "listening"}>
          {state === "listening" ? "Listening…" : "Test my mic"}
        </Button>
        <Button variant="secondary" block onClick={skip}>
          My mic isn&apos;t working — continue with typing
        </Button>
      </div>

      <Button
        block
        disabled={state === "idle" || state === "listening"}
        onClick={() => navigate(`/practice/${scene.id}/learn`)}
      >
        Start practice <ArrowRightIcon />
      </Button>
    </div>
  );
}
