import { useNavigate } from "react-router-dom";
import { Button, Mascot, Noodle } from "../components/ui";

export function Welcome() {
  const navigate = useNavigate();
  return (
    <div className="stack" style={{ minHeight: "80vh", justifyContent: "center", gap: "var(--space-6)" }}>
      <div className="center-text stack-2" style={{ alignItems: "center" }}>
        <Mascot size={140} />
        <h1 style={{ color: "var(--tomato)", fontSize: "var(--text-display)" }}>Linguini</h1>
        <Noodle />
        <h2>Learn a language in an immersive way!</h2>
        <p className="muted">
          A speak-first app that turns the street, the café and your kitchen into today&apos;s lesson.
        </p>
      </div>
      <div className="stack-2">
        <Button block onClick={() => navigate("/onboarding")}>
          Get started
        </Button>
        <Button variant="secondary" block onClick={() => navigate("/login")}>
          I already have an account
        </Button>
      </div>
    </div>
  );
}
