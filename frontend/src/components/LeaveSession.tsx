import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "./ui";
import { abandonPractice } from "../lib/api";

export function LeaveSession({ sessionId, warning }: { sessionId: string; warning: string }) {
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  if (!expanded) {
    return <Button variant="quiet" onClick={() => setExpanded(true)}>Leave this session</Button>;
  }
  const leave = async () => {
    setLeaving(true);
    setError(null);
    try {
      await abandonPractice(sessionId);
      navigate("/practice", { replace: true });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to leave the session.");
    } finally {
      setLeaving(false);
    }
  };
  return (
    <div className="stack-2">
      <p role="status">{warning}</p>
      {error ? <p role="alert">{error}</p> : null}
      <Button variant="secondary" disabled={leaving} onClick={() => void leave()}>
        Leave and start over
      </Button>
      <Button variant="quiet" disabled={leaving} onClick={() => setExpanded(false)}>
        Keep this session
      </Button>
    </div>
  );
}
