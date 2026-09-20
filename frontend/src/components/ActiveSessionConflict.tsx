import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "./ui";
import { abandonPractice } from "../lib/api";

export function ActiveSessionConflict({ activeSessionId, onDiscarded }: { activeSessionId: string; onDiscarded: () => void | Promise<void> }) {
  const navigate = useNavigate();
  const [discarding, setDiscarding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const discard = async () => {
    setDiscarding(true);
    setError(null);
    try {
      await abandonPractice(activeSessionId);
      await onDiscarded();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to discard the session.");
    } finally {
      setDiscarding(false);
    }
  };
  return (
    <div className="stack-2">
      <p>You have a practice session in progress.</p>
      {error ? <p role="alert">{error}</p> : null}
      <Button disabled={discarding} onClick={() => navigate(`/practice/sessions/${activeSessionId}/analysis`)}>
        Continue
      </Button>
      <Button variant="secondary" disabled={discarding} onClick={() => void discard()}>
        Discard and start new
      </Button>
    </div>
  );
}
