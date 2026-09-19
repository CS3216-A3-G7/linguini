import { useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, Mascot, Noodle, StatusPill, TopBar, XpPill } from "../components/ui";
import { useScene } from "../state/useScene";
import { useAppState } from "../state/useAppState";
import { createPractice, getPracticeSummary } from "../lib/api";
import { useApiData } from "../lib/useApiData";

export function SessionSummary() {
  const navigate = useNavigate();
  const scene = useScene();
  const { session, activeProfile, vocabulary } = useAppState();
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const requestKey = useRef(crypto.randomUUID());
  const load = useCallback(() => getPracticeSummary(scene.sessionId!), [scene.sessionId]);
  const { data, error, loading } = useApiData(load);
  const completed = session?.session.status === "completed";
  const revisit = scene.items.filter(item => data?.learnedVocabularyIds.includes(
    session?.sceneObjects.find(object => object.id === item.id)?.vocabularyItemId ?? ""
  )).slice(0, 3);
  const practiseAgain = async () => {
    if (starting || !activeProfile) return;
    setStarting(true); setStartError(null);
    try {
      const next = await createPractice(activeProfile.id, scene.mediaAssetId, requestKey.current);
      navigate("/practice/sessions/" + next.session.id + "/analysis");
    } catch (error) { setStartError(error instanceof Error ? error.message : "Unable to start practice."); }
    finally { setStarting(false); }
  };
  return <div className="stack">
    <TopBar title="Session summary" onBack={() => navigate("/home")} />
    <p className="small muted">{completed ? "Session and XP saved." : "XP is saved after each action."}</p>
    {session?.session.status === "inProgress" ? <Button onClick={() => navigate("/practice/sessions/" + scene.sessionId + "/learn")}>Continue unfinished practice</Button> : null}
    <div className="center-text stack-2" style={{ alignItems: "center" }}>
      <Mascot size={120} /><h1>{completed ? "Good job!" : "Your session"}</h1><Noodle />
      <p className="muted">You practised {scene.title.toLowerCase()} today.</p>
    </div>
    {loading ? <p role="status">Loading your results...</p> : null}
    {error || startError ? <p role="alert">{error || startError}</p> : null}
    {data ? <>
      <div className="stat-grid">
        <div className="stat"><div className="stat__value">{data.xpEarned}</div><span className="small muted">XP earned</span></div>
        <div className="stat"><div className="stat__value">{data.ispyCorrectCount}/{data.ispyAttemptCount}</div><span className="small muted">I-Spy correct</span></div>
        <div className="stat"><div className="stat__value">{scene.items.length}</div><span className="small muted">Items found</span></div>
      </div>
      <Card><div className="stack-2">
        <div className="spread"><h2>Words to revisit</h2><XpPill xp={data.xpEarned} /></div>
        {revisit.map(item => {
          const vocabularyId = session?.sceneObjects.find(object => object.id === item.id)?.vocabularyItemId;
          return <div key={item.id} className="spread"><div><strong>{item.word}</strong><p className="small muted">{item.translation}</p></div><StatusPill status={vocabulary.find(word => word.id === vocabularyId)?.status ?? "learning"} /></div>;
        })}
        {revisit.length === 0 ? <p className="small muted">No vocabulary practised in this session.</p> : null}
      </div></Card>
    </> : null}
    <div className="stack-2">
      <Button block onClick={() => navigate("/journal/new")}>Write today&apos;s journal entry</Button>
      <Button variant="secondary" block onClick={() => navigate("/vocabulary")}>Review difficult words</Button>
      <Button variant="secondary" block disabled={starting || !activeProfile} onClick={() => void practiseAgain()}>Practise again</Button>
      <Button variant="quiet" block onClick={() => navigate("/home")}>Back home</Button>
    </div>
  </div>;
}
