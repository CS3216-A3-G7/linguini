import { useNavigate, useParams } from "react-router-dom";
import { Button, Card, Mascot, Noodle, StatusPill, TopBar, XpPill } from "../components/ui";
import { getScene } from "../data/mock";
import { useAppState } from "../state/useAppState";

export function SessionSummary() {
  const navigate = useNavigate();
  const { sceneId } = useParams();
  const scene = getScene(sceneId);
  const { session, replayGame } = useAppState();

  const revisit = scene.items.slice(0, 3);

  return (
    <div className="stack">
      <TopBar title="Session complete" onBack={() => navigate("/home")} />
      <div className="center-text stack-2" style={{ alignItems: "center" }}>
        <Mascot size={120} />
        <h1>Good job!</h1>
        <Noodle />
        <p className="muted">You practised {scene.title.toLowerCase()} out loud today.</p>
      </div>

      <div className="stat-grid">
        <div className="stat">
          <div className="stat__value">{session.sessionXp}</div>
          <span className="small muted">XP earned</span>
        </div>
        <div className="stat">
          <div className="stat__value">
            {session.correctRounds}/{session.roundsPlayed}
          </div>
          <span className="small muted">I-Spy correct</span>
        </div>
        <div className="stat">
          <div className="stat__value">{scene.items.length}</div>
          <span className="small muted">Items found</span>
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
        <Button
          variant="secondary"
          block
          onClick={() => {
            replayGame();
            navigate(`/practice/${scene.id}/ispy-1`);
          }}
        >
          Replay I-Spy
        </Button>
        <Button variant="quiet" block onClick={() => navigate("/home")}>
          Back home
        </Button>
      </div>
    </div>
  );
}
