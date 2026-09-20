import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Button, Card } from "../components/ui";
import { ArrowRightIcon } from "../components/icons";
import { ScenePhoto } from "../components/ScenePhoto";
import { useScene } from "../state/useScene";
import { useAppState } from "../state/useAppState";

export function PracticeAnalysis() {
  const navigate = useNavigate();
  const scene = useScene();
  const { session, learner } = useAppState();
  const [activeItem, setActiveItem] = useState<string | null>(null);
  const base = `/practice/sessions/${scene.sessionId}`;
  if (!session) return null;
  if (session.session.status === "completed") return <Navigate to={`${base}/summary`} replace />;
  if (["abandoned", "failed"].includes(session.session.status)) return <Navigate to={`${base}/learn`} replace />;
  const preview = session.analysisMode === "placeholder";
  return <div className="stack analysis-page">
    <h1>Scene analysis</h1>
    <p className="muted">{scene.title} - {learner.language}</p>
    {preview ? <p className="small muted">Preview mode: these are sample objects and positions, not detections from your photo.</p> : null}
    <div className="analysis-photo-stage">
      <ScenePhoto scene={scene} activeItemId={activeItem}
        onMarkerClick={item => setActiveItem(item.id === activeItem ? null : item.id)} />
    </div>
    <section className="analysis-results" aria-labelledby="analysis-found-title">
      <div>
        <h2 id="analysis-found-title">{scene.items.length} {scene.items.length === 1 ? "word" : "words"} {preview ? "to preview" : "found"}</h2>
        <p className="muted">Review the words in your lesson. Tap a marker to highlight its word.</p>
      </div>
      <Card plain className="analysis-word-card">
        <div className="analysis-word-list" aria-label="Words in this scene">
          {scene.items.map(item => <div className="analysis-word-row" key={item.id}>
            <span className="analysis-word-row__marker">{item.marker}</span>
            <div className="grow"><strong>{item.word}</strong><p className="small muted">{item.translation}</p></div>
            {activeItem === item.id ? <span className="pill pill--learning">Selected</span> : null}
          </div>)}
          {!scene.items.length ? <p className="small muted">No words are available for this scene.</p> : null}
        </div>
      </Card>
    </section>
    <Button block onClick={() => navigate(`${base}/mic-test`)}>Continue <ArrowRightIcon /></Button>
  </div>;
}
