import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui";
import { useAppState } from "../state/useAppState";

export function Login() {
  const navigate = useNavigate();
  const { learner, progress, progressLoading, progressError } = useAppState();
  const active = progress?.scenarios.find(row => row.status === "in-progress");
  return <div className="stack">
    <div className="center-text stack-2" style={{ alignItems: "center" }}>
      <img className="mascot" src="/linguini-logo.png" width={120} height={120} alt="Linguini mascot" />
      <h1>Welcome back</h1>
      <p className="muted">Continue learning with {learner.name}.</p>
      <p className="small muted">This version uses a demo account. Email and password sign-in is not available yet.</p>
    </div>
    <Button block onClick={() => navigate("/home")}>Continue to home</Button>
    {progressLoading ? <p role="status">Loading your practice...</p> : null}
    {progressError ? <p role="alert">{progressError} Reload to retry.</p> : null}
    {active ? <Button variant="secondary" block onClick={() => navigate(`/practice/sessions/${active.sessionId}/learn`)}>Resume {active.title}</Button> : null}
    <p className="small muted center-text">
      <button type="button" className="btn btn--quiet" onClick={() => navigate("/onboarding")}>Set up your learning preferences</button>
    </p>
  </div>;
}
