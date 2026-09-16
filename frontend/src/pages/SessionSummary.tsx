import { useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { Button, Card, Mascot, Noodle, StatusPill, TopBar, XpPill } from "../components/ui";
import { useScene } from "../state/useScene";
import { useAppState } from "../state/useAppState";

export function SessionSummary() {
  const navigate = useNavigate();
  const scene = useScene();
  const { session, startSession, completeSession, practiceSaving } = useAppState();
  const finished = scene.tasks.every((task) => session.completedTaskIds.includes(task.id))
    && scene.rounds.every((round) => session.scoredRoundIds.includes(`round:${round.id}`))
    && scene.prompts.every((prompt) => session.scoredRoundIds.includes(`clue:${prompt.id}`));
  useEffect(() => {
    if (finished && session.status === "inProgress") void completeSession();
  }, [finished, session.status, completeSession]);

  const revisit = scene.items.slice(0, 3);

  return (
    <div className="stack">
      <TopBar title="Session summary" onBack={() => navigate("/home")} />
      <p className="small muted">{session.status === "completed" ? "Session and XP saved." : "XP is saved after each action."}</p>
      {!finished ? <Button onClick={() => navigate(`/practice/${scene.id}/learn`)}>Continue unfinished practice</Button> : null}
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
          disabled={practiceSaving}
          onClick={async () => {
            if (await startSession(scene.id)) navigate(`/practice/${scene.id}/analysis`);
          }}
        >
          Practise again
        </Button>
        <Button variant="quiet" block onClick={() => navigate("/home")}>
          Back home
        </Button>
      </div>
    </div>
  );
}
