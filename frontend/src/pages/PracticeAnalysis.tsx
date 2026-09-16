import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, Feedback, ProgressTrail, TopBar, XpPill } from "../components/ui";
import { ArrowRightIcon, CheckIcon } from "../components/icons";
import { ScenePhoto } from "../components/ScenePhoto";
import { useScene } from "../state/useScene";
import { useAppState } from "../state/useAppState";

const ANALYSIS_XP = 12;

export function PracticeAnalysis() {
  const navigate = useNavigate();
  const scene = useScene();
  const { learner, ensureSession, awardAnalysis } = useAppState();
  const [done, setDone] = useState(false);
  const [activeItem, setActiveItem] = useState<string | null>(null);

  useEffect(() => {
    ensureSession(scene.id);
  }, [scene.id, ensureSession]);

  useEffect(() => {
    const timer = window.setTimeout(() => setDone(true), 1400);
    return () => window.clearTimeout(timer);
  }, [scene.id]);

  useEffect(() => {
    if (done) void awardAnalysis();
  }, [done, awardAnalysis]);

  const nouns = scene.items.filter((item) => item.wordClass === "noun").length;
  const others = scene.items.length - nouns;

  return (
    <div className="stack">
      <TopBar
        title="Step 2: Analyse"
        help="Linguini only teaches what it can actually see in your photo."
      />
      <ProgressTrail value={2} total={3} label="Step 2 of 3" />

      <div className="spread">
        <h1>{scene.title}</h1>
        <span className="pill pill--new">
          {learner.languageFlag} {learner.language}
        </span>
      </div>

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
            <XpPill xp={ANALYSIS_XP} />
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

      <Button block disabled={!done} onClick={() => navigate(`/practice/${scene.id}/mic-test`)}>
        Continue to mic test <ArrowRightIcon />
      </Button>
    </div>
  );
}
