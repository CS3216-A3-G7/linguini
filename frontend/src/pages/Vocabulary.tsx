import { useEffect, useMemo, useRef, useState } from "react";
import { Button, Card, IconButton, Tabs } from "../components/ui";
import { BookIcon, CloseIcon, FilterIcon, SpeakerIcon } from "../components/icons";
import { SceneVisual } from "../components/SceneVisual";
import { LoadingScreen } from "../components/LoadingScreen";
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
  const { vocabulary, vocabularyLoading, vocabularyError, scenes, scenesLoading, scenesError, learner } = useAppState();
  const wordClasses: (WordClass | "all")[] = ["all", ...new Set(vocabulary.map(item => item.wordClass))];
  const [view, setView] = useState<"scenes" | "list">("scenes");
  const [status, setStatus] = useState<VocabStatus>("learning");
  const [wordClass, setWordClass] = useState<WordClass | "all">("all");
  const [topic, setTopic] = useState<string>("all");
  const [showFilters, setShowFilters] = useState(false);
  const [draftWordClass, setDraftWordClass] = useState<WordClass | "all">("all");
  const [draftTopic, setDraftTopic] = useState<string>("all");
  const filterSheetRef = useRef<HTMLDivElement>(null);

  const statusTabs = statusLabels.map(({ id, label }) => ({ id, label }));

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

  const sceneGroups = useMemo(
    () =>
      scenes
        .map((scene) => ({
          scene,
          words: vocabulary.filter((item) => item.sceneId === scene.id),
        }))
        .filter((group) => group.words.length > 0),
    [vocabulary, scenes],
  );
  const ungrouped = vocabulary.filter(item => !scenes.some(scene => scene.id === item.sceneId));

  const openFilters = () => {
    setDraftWordClass(wordClass);
    setDraftTopic(topic);
    setShowFilters(true);
  };

  const closeFilters = () => setShowFilters(false);

  const applyFilters = () => {
    setWordClass(draftWordClass);
    setTopic(draftTopic);
    setShowFilters(false);
  };

  useEffect(() => {
    if (!showFilters) return;

    const previousFocus = document.activeElement as HTMLElement | null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    filterSheetRef.current?.querySelector<HTMLButtonElement>("button")?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeFilters();
      if (event.key === "Tab") {
        const buttons = filterSheetRef.current?.querySelectorAll<HTMLButtonElement>("button:not(:disabled)");
        const first = buttons?.[0];
        const last = buttons?.[buttons.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
      previousFocus?.focus();
    };
  }, [showFilters]);

  if (vocabularyLoading) return <LoadingScreen label="Loading vocabulary..." />;
  if (vocabularyError) return <p role="alert">{vocabularyError} Reload to retry.</p>;

  return (
    <div className="stack vocabulary-page">
      <div className="vocabulary-page__header">
        <div>
          <h1>Vocabulary</h1>
          <p className="small muted">Words collected from the places you explored.</p>
        </div>
      </div>

      <Button
        variant="secondary"
        className="vocabulary-page__view-toggle"
        aria-pressed={view === "list"}
        onClick={() => setView((current) => (current === "scenes" ? "list" : "scenes"))}
      >
        <span className="vocabulary-page__view-icon" aria-hidden="true">
          <BookIcon size={22} />
        </span>
        <span>{view === "scenes" ? "View Vocabulary List" : "View Words by Scene"}</span>
      </Button>

      {view === "list" ? (
        <>
          <div className="spread vocabulary-page__list-controls">
            <Tabs options={statusTabs} value={status} onChange={setStatus} />
            <IconButton
              label="Filters"
              aria-haspopup="dialog"
              aria-expanded={showFilters}
              onClick={openFilters}
            >
              <FilterIcon />
            </IconButton>
          </div>

      {showFilters && view === "list" ? (
        <div
          className="vocabulary-filter-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) closeFilters();
          }}
        >
          <div
            ref={filterSheetRef}
            className="vocabulary-filter-sheet"
            role="dialog"
            aria-modal="true"
            aria-labelledby="vocabulary-filter-title"
          >
            <span className="vocabulary-filter-sheet__handle" aria-hidden="true" />

            <div className="vocabulary-filter-sheet__header">
              <h2 id="vocabulary-filter-title">Filter vocabulary</h2>
              <IconButton label="Close filters" onClick={closeFilters}>
                <CloseIcon />
              </IconButton>
            </div>

            <fieldset className="vocabulary-filter-group">
              <legend>Word type</legend>
              <div className="chip-row">
                {wordClasses.map((option) => (
                  <button
                    key={option}
                    type="button"
                    className={`chip${option === draftWordClass ? " chip--selected" : ""}`}
                    aria-pressed={option === draftWordClass}
                    onClick={() => setDraftWordClass(option)}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </fieldset>

            <fieldset className="vocabulary-filter-group">
              <legend>Topic</legend>
              <div className="chip-row">
                {topics.map((option) => (
                  <button
                    key={option}
                    type="button"
                    className={`chip${option === draftTopic ? " chip--selected" : ""}`}
                    aria-pressed={option === draftTopic}
                    onClick={() => setDraftTopic(option)}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </fieldset>

            <Button block className="vocabulary-filter-sheet__apply" onClick={applyFilters}>
              Apply filters
            </Button>
          </div>
        </div>
      ) : null}

          <div className="list vocabulary-list">
        {rows.map((item) => (
          <article key={item.id} className="list__row vocabulary-card">
            <div className="grow vocabulary-card__content">
              <div className="vocabulary-card__heading">
                <strong className="vocabulary-card__title">{item.word}</strong>
                <div className="vocabulary-card__right">
                  <p className="vocabulary-card__translation">{item.translation}</p>
                </div>
              </div>

              <p className="vocabulary-card__example">{item.example}</p>

              <div className="vocabulary-card__footer">
                <div className="vocabulary-card__tags">
                  <span className="pill pill--new">{item.wordClass}</span>
                  <span className="pill pill--new">{item.topic}</span>
                </div>
                <IconButton
                  className="vocabulary-card__audio"
                  label={`Hear ${item.word}`}
                  onClick={() => speak(item.word, learner.languageCode)}
                >
                  <SpeakerIcon size={18} />
                </IconButton>
              </div>
            </div>
          </article>
        ))}
          </div>

      {rows.length === 0 ? (
        <Card>
          <p className="small">
            Nothing in this list yet. Play a scene and the words you meet land here.
          </p>
        </Card>
      ) : null}
        </>
      ) : (
        <div className="vocabulary-scenes">
          {scenesLoading ? <p role="status">Loading scenes...</p> : null}
          {scenesError ? <p role="alert">{scenesError} Your words are still available below.</p> : null}
          {!vocabulary.length ? <Card><p>No saved words yet. Practise a scene to collect words.</p></Card> : null}
          {ungrouped.length ? <section className="vocabulary-scene">
            <div className="vocabulary-scene__content">
              <h2>Other collected words</h2>
              <div className="vocabulary-scene__words">{ungrouped.map(item => <div key={item.id} className="vocabulary-scene__word">
                <span><strong>{item.word}</strong><small>{item.translation}</small></span>
                <IconButton label={`Hear ${item.word}`} onClick={() => speak(item.word, learner.languageCode)}><SpeakerIcon size={18} /></IconButton>
              </div>)}</div>
            </div>
          </section> : null}
          {sceneGroups.map(({ scene, words }) => (
            <section key={scene.id} className="vocabulary-scene">
              <SceneVisual scene={scene} className="vocabulary-scene__image" />
              <div className="vocabulary-scene__content">
                <div className="vocabulary-scene__heading">
                  <h2>{scene.title}</h2>
                  <span>{words.length} {words.length === 1 ? "word" : "words"}</span>
                </div>
                <div className="vocabulary-scene__words">
                  {words.map((item) => (
                    <div key={item.id} className="vocabulary-scene__word">
                      <span>
                        <strong>{item.word}</strong>
                        <small>{item.translation}</small>
                      </span>
                      <IconButton
                        label={`Hear ${item.word}`}
                        onClick={() => speak(item.word, learner.languageCode)}
                      >
                        <SpeakerIcon size={18} />
                      </IconButton>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
