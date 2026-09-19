import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, Feedback, ProgressTrail, TopBar } from "../components/ui";
import { ArrowRightIcon, CheckIcon } from "../components/icons";
import { ScenePhoto } from "../components/ScenePhoto";
import { useScene } from "../state/useScene";
import { useAppState } from "../state/useAppState";

export function PracticeAnalysis() {
  const navigate = useNavigate();
  const scene = useScene();
  const { learner } = useAppState();
  const [done, setDone] = useState(Boolean(scene.uploadedSessionId));
  const [activeItem, setActiveItem] = useState<string | null>(null);

  useEffect(() => {
    if (scene.uploadedSessionId) return;
    const timer = window.setTimeout(() => setDone(true), 1400);
    return () => window.clearTimeout(timer);
  }, [scene.id, scene.uploadedSessionId]);

  const nouns = scene.items.filter((item) => item.wordClass === "noun").length;
  const others = scene.items.length - nouns;

  return (
    <div className="stack">
      <TopBar
        title="Step 2: Analyse"
        help="Review the objects in your scene before continuing."
      />
      <ProgressTrail value={2} total={3} label="Step 2 of 3" />

      <div className="spread">
        <h1>{scene.title}</h1>
        <span className="pill pill--new">
          {learner.languageFlag} {learner.language}
        </span>
      </div>

      {scene.uploadedSessionId ? <p className="small muted">Preview mode: these are sample objects and positions, not detections from your photo.</p> : null}

      <ScenePhoto
        scene={scene}
        activeItemId={activeItem}
        onMarkerClick={(item) => setActiveItem(item.id === activeItem ? null : item.id)}
      />

      {activeItem ? (
        <Card plain>
          {(() => {
            const item = scene.items.find((entry) => entry.id === activeItem);
            if (!item) return null;
            return (
              <div className="stack-2">
                <span className="label muted">Marker {item.marker}</span>
                <strong>{item.word}</strong>
                <span className="small muted">{item.translation}</span>
              </div>
            );
          })()}
        </Card>
      ) : (
        <p className="small muted">Tap a numbered marker to preview what Linguini found.</p>
      )}

      {done ? (
        <Feedback>
          <span style={{ color: "var(--teal-dark)" }}>
            <CheckIcon />
          </span>
          <div className="stack-2">
            <strong>Analysis complete — {scene.items.length} items found</strong>
            <span className="small muted">
              {nouns} nouns, {others} describing and position words.
            </span>
          </div>
        </Feedback>
      ) : (
        <Card>
          <div className="stack-2">
            <strong>Looking at your scene…</strong>
            <ProgressTrail value={1} total={3} label="Finding objects" />
          </div>
        </Card>
      )}

      <Button block disabled={!done} onClick={() => navigate(scene.uploadedSessionId ? `/practice/uploads/${scene.uploadedSessionId}/mic-test` : `/practice/${scene.id}/mic-test`)}>
        Continue to mic test <ArrowRightIcon />
      </Button>
    </div>
  );
}
