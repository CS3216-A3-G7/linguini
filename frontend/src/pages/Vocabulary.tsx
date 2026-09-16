import { useMemo, useState } from "react";
import { Button, Card, IconButton, StatusPill, Tabs } from "../components/ui";
import { FilterIcon, SpeakerIcon } from "../components/icons";
import { SceneArt } from "../components/SceneArt";
import { SceneCatalogStatus } from "../components/SceneCatalogStatus";
import type { VocabStatus, WordClass } from "../data/types";
import { speak } from "../lib/speech";
import { useAppState } from "../state/useAppState";

const statusLabels: { id: VocabStatus; label: string }[] = [
  { id: "new", label: "New" },
  { id: "learning", label: "Learning" },
  { id: "familiar", label: "Familiar" },
  { id: "mastered", label: "Mastered" },
];

export function Vocabulary() {
  const { vocabulary, setVocabStatus, vocabularyLoading, vocabularyError, scenes, learner } = useAppState();
  const [status, setStatus] = useState<VocabStatus>("learning");
  const [wordClass, setWordClass] = useState<WordClass | "all">("all");
  const [topic, setTopic] = useState<string>("all");
  const [showFilters, setShowFilters] = useState(false);

  const statusTabs = useMemo(
    () =>
      statusLabels.map(({ id, label }) => ({
        id,
        label: `${label} (${vocabulary.filter((item) => item.status === id).length})`,
      })),
    [vocabulary],
  );

  const topics = useMemo(
    () => ["all", ...Array.from(new Set(vocabulary.map((item) => item.topic)))],
    [vocabulary],
  );

  const rows = vocabulary.filter(
    (item) =>
      item.status === status &&
      (wordClass === "all" || item.wordClass === wordClass) &&
      (topic === "all" || item.topic === topic),
  );

  const wordClasses: (WordClass | "all")[] = ["all", ...new Set(vocabulary.map((item) => item.wordClass))];

  if (vocabularyError) {
    return <div className="stack"><h1>My vocabulary</h1><p role="alert">{vocabularyError} Reload to retry.</p></div>;
  }
  if (vocabularyLoading) {
    return <div className="stack"><h1>My vocabulary</h1><p role="status">Loading vocabulary…</p></div>;
  }

  const nextStatus: Record<VocabStatus, VocabStatus> = {
    new: "learning",
    learning: "mastered",
    familiar: "mastered",
    mastered: "new",
  };

  return (
    <div className="stack">
      <div className="spread">
        <h1>My vocabulary</h1>
        <IconButton label="Filters" onClick={() => setShowFilters((current) => !current)}>
          <FilterIcon />
        </IconButton>
      </div>
      <p className="muted">Everything you found in your own scenes.</p>
      <SceneCatalogStatus />
      <p className="small muted">Moving words changes this session only. Status resets on reload.</p>

      <Tabs options={statusTabs} value={status} onChange={setStatus} />

      {showFilters ? (
        <Card plain>
          <div className="stack-2">
            <span className="label muted">Word type</span>
            <div className="chip-row">
              {wordClasses.map((option) => (
                <button
                  key={option}
                  type="button"
                  className={`chip${option === wordClass ? " chip--selected" : ""}`}
                  onClick={() => setWordClass(option)}
                >
                  {option}
                </button>
              ))}
            </div>
            <span className="label muted">Topic</span>
            <div className="chip-row">
              {topics.map((option) => (
                <button
                  key={option}
                  type="button"
                  className={`chip${option === topic ? " chip--selected" : ""}`}
                  onClick={() => setTopic(option)}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
        </Card>
      ) : null}

      <div className="list">
        {rows.map((item) => {
          const scene = scenes.find((candidate) => candidate.id === item.sceneId);
          return (
            <div key={item.id} className="list__row" style={{ cursor: "default" }}>
              <span className="thumb">
                {scene ? <SceneArt scene={scene.art} /> : <span aria-label="Word">Aa</span>}
              </span>
              <div className="grow stack-2">
                <div className="row">
                  <strong>{item.word}</strong>
                  <IconButton label={`Hear ${item.word}`} onClick={() => speak(item.word, learner.languageCode)}>
                    <SpeakerIcon size={18} />
                  </IconButton>
                </div>
                <span className="small muted">{item.translation}</span>
                <span className="small muted">{item.example}</span>
                <div className="row">
                  <StatusPill status={item.status} />
                  <span className="pill pill--new">{item.wordClass}</span>
                  <span className="pill pill--new">{item.topic}</span>
                </div>
              </div>
              <Button
                variant="quiet"
                aria-label={`Move ${item.word} to ${nextStatus[item.status]}`}
                onClick={() => setVocabStatus(item.id, nextStatus[item.status])}
              >
                Move
              </Button>
            </div>
          );
        })}
      </div>

      {rows.length === 0 ? (
        <Card>
          <p className="small">
            No words in this list for {learner.language} yet.
          </p>
        </Card>
      ) : null}
    </div>
  );
}
