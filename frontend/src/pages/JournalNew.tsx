import { LoadingScreen } from "../components/LoadingScreen";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Feedback, TopBar } from "../components/ui";
import { UploadIcon } from "../components/icons";
import { SceneArt } from "../components/SceneArt";
import type { SceneArtId } from "../components/SceneArt";
import { SceneCatalogStatus } from "../components/SceneCatalogStatus";
import { useAppState } from "../state/useAppState";
import { getTodayJournal } from "../lib/api";
import { useApiData } from "../lib/useApiData";
import type { JournalEntry } from "../data/types";

export function JournalNew() {
  const { data, loading, error } = useApiData(getTodayJournal);
  if (loading) return <LoadingScreen label="Loading today's journal…" />;
  if (error || !data) return <p role="alert">{error ?? "Unable to load journal."} Reload to retry.</p>;
  return <JournalForm key={data.entry?.id ?? "new"} entry={data.entry} date={data.date} />;
}

export function JournalForm({ entry, date, onSaved }: { entry: JournalEntry | null; date: string; onSaved?: (entry: JournalEntry) => void }) {
  const navigate = useNavigate();
  const { saveJournalEntry, journalSaving, journalSaveError, scenes, vocabulary, vocabularyError, vocabularyLoading, learner, activeProfile } = useAppState();
  const sameLanguage = !entry || entry.languageProfileId === activeProfile?.id;
  const journalWordSuggestions = sameLanguage ? vocabulary.map((item) => item.word) : [];
  const today = new Date(`${date}T12:00:00`);
  const [title, setTitle] = useState(entry?.title ?? "");
  const [body, setBody] = useState(entry?.body ?? "");
  const [art, setArt] = useState<SceneArtId | null>(entry?.art ?? null);
  const [selectedWords, setSelectedWords] = useState<string[]>(entry?.wordsUsed ?? []);

  const toggleWord = (word: string) =>
    setSelectedWords((current) =>
      current.includes(word) ? current.filter((item) => item !== word) : [...current, word],
    );

  const save = async () => {
    const saved = await saveJournalEntry({
      title: title.trim() || "Today's entry",
      art: art ?? "street",
      body: body.trim(),
      wordsUsed: selectedWords,
    }, entry?.id);
    if (saved) {
      if (onSaved) onSaved(saved);
      else navigate(`/journal/${saved.id}`);
    }
  };

  return (
    <div className="stack">
      <TopBar
        title={today.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "short" })}
        onBack={() => navigate("/journal")}
      />
      <h1>{entry ? "Edit journal entry" : "Today's journal"}</h1>

      <div className="field">
        <label className="field__label" htmlFor="entry-title">
          Title
        </label>
        <input
          id="entry-title"
          maxLength={200}
          className="input"
          placeholder="A walk downtown"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
      </div>

      <div className="stack-2">
        <span className="field__label">Illustration</span>
        {art ? (
          <div className="scene">
            <SceneArt scene={art} className="scene__art" />
          </div>
        ) : (
          <div className="dashed-capture">
            <span style={{ color: "var(--teal-dark)" }}>
              <UploadIcon size={40} />
            </span>
            <p className="small muted">Choose a scene illustration below</p>
          </div>
        )}
        <div className="grid-3">
          <SceneCatalogStatus />
          {scenes.slice(0, 3).map((scene) => (
            <button
              key={scene.id}
              type="button"
              className={`scene-pick${art === scene.art ? " scene-pick--selected" : ""}`}
              onClick={() => setArt(scene.art)}
            >
              <SceneArt scene={scene.art} />
              <span className="small">{scene.title}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="stack-2">
        <span className="field__label">Word suggestions</span>
        {!sameLanguage ? <p className="small muted">Select this entry's language in Profile to see matching word suggestions.</p> : null}
        <div className="chip-row">
          {vocabularyLoading ? <p role="status">Loading words…</p> : null}
          {vocabularyError ? <p role="alert">{vocabularyError}</p> : null}
          {!vocabularyLoading && !vocabularyError && !journalWordSuggestions.length ? <p className="small muted">No saved words for {learner.language} yet.</p> : null}
          {journalWordSuggestions.map((word) => (
            <button
              key={word}
              type="button"
              className={`chip${selectedWords.includes(word) ? " chip--selected" : ""}`}
              aria-pressed={selectedWords.includes(word)}
              onClick={() => toggleWord(word)}
            >
              {word}
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <label className="field__label" htmlFor="entry-body">
          Your entry
        </label>
        <textarea
          id="entry-body"
          maxLength={20000}
          className="textarea"
          placeholder="Hoy caminé por la calle y vi un árbol grande…"
          value={body}
          onChange={(event) => setBody(event.target.value)}
        />
        <span className="small muted">{body.trim() ? body.trim().split(/\s+/).length : 0} words</span>
      </div>

      {selectedWords.length ? (
        <Feedback>
          <div className="stack-2">
            <strong>Nice picks</strong>
            <span className="small muted">
              Try using {selectedWords.slice(0, 2).join(" and ")} in one sentence.
            </span>
          </div>
        </Feedback>
      ) : null}

      {journalSaveError ? <p role="alert">{journalSaveError}</p> : null}
      {journalSaving ? <p role="status">Saving journal…</p> : null}
      <Button block disabled={journalSaving || !body.trim()} onClick={save}>
        Save entry
      </Button>
    </div>
  );
}
