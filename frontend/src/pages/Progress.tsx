import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Tabs } from "../components/ui";
import { BookIcon } from "../components/icons";
import { scenarioProgress } from "../data/mock";
import { useAppState } from "../state/useAppState";

type ProgressRange = "week" | "month" | "all";

const rangeOptions: { id: ProgressRange; label: string }[] = [
  { id: "week", label: "This week" },
  { id: "month", label: "This month" },
  { id: "all", label: "All time" },
];

export function Progress() {
  const navigate = useNavigate();
  const { vocabulary } = useAppState();
  const [range, setRange] = useState<ProgressRange>("week");

  const totalWords = vocabulary.length;
  const totalMastered = vocabulary.filter((item) => item.status === "mastered").length;
  const totalScenes = scenarioProgress.length;

  const snapshots: Record<ProgressRange, { words: number; mastered: number; scenes: number }> = {
    week: {
      words: Math.min(totalWords, 4),
      mastered: Math.min(totalMastered, 1),
      scenes: Math.min(totalScenes, 1),
    },
    month: {
      words: Math.min(totalWords, 8),
      mastered: Math.min(totalMastered, 2),
      scenes: Math.min(totalScenes, 2),
    },
    all: {
      words: totalWords,
      mastered: totalMastered,
      scenes: totalScenes,
    },
  };

  const snapshot = snapshots[range];

  return (
    <div className="stack progress-page">
      <div className="progress-page__header">
        <h2>Progress</h2>
      </div>
      <Button
          variant="secondary"
        className="progress-page__vocabulary"
        onClick={() => navigate("/vocabulary")}
      >
          <span className="progress-page__vocabulary-icon" aria-hidden="true">
            <BookIcon size={30} />
          </span>
          <span>My Vocabulary →</span>
        </Button>
      <Tabs options={rangeOptions} value={range} onChange={setRange} />

      <section className="progress-overview" aria-live="polite">
        <div className="progress-overview__metric">
          <strong>{snapshot.words}</strong>
          <span>Words learned</span>
        </div>
        <div className="progress-overview__metric">
          <strong>{snapshot.mastered}</strong>
          <span>Mastered</span>
        </div>
        <div className="progress-overview__metric">
          <strong>{snapshot.scenes}</strong>
          <span>Scenes</span>
        </div>
      </section>
    </div>
  );
}
