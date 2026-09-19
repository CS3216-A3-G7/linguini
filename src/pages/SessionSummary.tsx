import { useNavigate, useParams } from "react-router-dom";
import { Button, Card, Noodle, StatusPill, XpPill } from "../components/ui";
import { getScene } from "../data/mock";
import { useAppState } from "../state/useAppState";

export function SessionSummary() {
  const navigate = useNavigate();
  const { sceneId } = useParams();
  const scene = getScene(sceneId);
  const { session } = useAppState();

  const revisit = scene.items.slice(0, 3);

  return (
    <div className="stack">
      <div className="center-text stack-2" style={{ alignItems: "center" }}>
        <img
          className="mascot"
          src="/linguini-logo.png"
          width={120}
          height={120}
          alt="Linguini mascot"
        />
        <h1>Good job!</h1>
        <Noodle className="noodle-divider summary__noodle" />
        <p className="muted">You practised {scene.title.toLowerCase()} out today!</p>
      </div>

      <div className="stat-grid">
        <div className="stat">
          <div className="stat__value">{session.sessionXp}</div>
          <span className="stat__label">XP</span>
        </div>
        <div className="stat">
          <div className="stat__value">
            {session.correctRounds}/{session.roundsPlayed}
          </div>
          <span className="stat__label">Correct</span>
        </div>
        <div className="stat">
          <div className="stat__value">{scene.items.length}</div>
          <span className="stat__label">Words</span>
        </div>
      </div>

      <Card>
        <div className="stack-2">
          <div className="spread">
            <h2>Words to revisit</h2>
            <XpPill xp={session.sessionXp} />
          </div>
          {revisit.map((item) => (
            <div key={item.id} className="spread">
              <div>
                <strong>{item.word}</strong>
                <p className="small muted">{item.translation}</p>
              </div>
              <StatusPill status="learning" />
            </div>
          ))}
        </div>
      </Card>

      <div className="stack-2">
        <Button block onClick={() => navigate("/journal/new")}>
          Write today&apos;s journal entry
        </Button>
        <Button variant="secondary" block onClick={() => navigate("/vocabulary")}>
          Review difficult words
        </Button>
        <Button variant="quiet" block onClick={() => navigate("/home")}>
          Back home
        </Button>
      </div>
    </div>
  );
}
