import { LoadingScreen } from "../components/LoadingScreen";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Feedback } from "../components/ui";
import { UploadIcon } from "../components/icons";
import { ImageUpload } from "../components/ImageUpload";
import { MediaImage } from "../components/MediaImage";
import { SceneVisual } from "../components/SceneVisual";
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
  const journalWordSuggestions = sameLanguage ? [...new Set(vocabulary.map((item) => item.word))] : [];
  const today = new Date(`${date}T12:00:00`);
  const [title, setTitle] = useState(entry?.title ?? "");
  const [body, setBody] = useState(entry?.body ?? "");
  const [photos, setPhotos] = useState(entry?.photos ?? []);
  const [uploading, setUploading] = useState(false);
  const [selectedWords, setSelectedWords] = useState<string[]>(entry?.wordsUsed ?? []);

  const toggleWord = (word: string) =>
    setSelectedWords((current) =>
      current.includes(word) ? current.filter((item) => item !== word) : [...current, word],
    );

  const save = async () => {
    if (journalSaving || uploading || !body.trim() || (!entry && !activeProfile)) return;
    const saved = await saveJournalEntry({
      title: title.trim() || "Today's entry",
      mediaAssetId: photos[0]?.mediaAssetId ?? null,
      photoAssetIds: photos.map(photo => photo.mediaAssetId),
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
      <h3 className="center-text">{today.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "short" })}</h3>
      <h1>{entry ? "Edit journal entry" : "Today's journal"}</h1>

      <div className="field">
        <label className="field__label" htmlFor="entry-title">
          Title
        </label>
        <input
          id="entry-title"
          disabled={journalSaving}
          maxLength={200}
          className="input"
          placeholder="A walk downtown"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
      </div>

      <div className="stack-2">
        <span className="field__label">Photos</span>
        {photos.length ? (
          <div className="photo-strip" aria-label={`${photos.length} photos added`}>
            {photos.map((photo, index) => <div key={photo.mediaAssetId} className="photo-thumb">
              <MediaImage assetId={photo.mediaAssetId} imageUrl={photo.imageUrl} title={`Journal photo ${index + 1}`} />
              <button type="button" className="photo-thumb__remove" aria-label={`Remove photo ${index + 1}`}
                disabled={journalSaving || uploading}
                onClick={() => setPhotos(current => current.filter(item => item.mediaAssetId !== photo.mediaAssetId))}>
                &times;
              </button>
            </div>)}
          </div>
        ) : <div className="dashed-capture">
          <span style={{ color: "var(--teal-dark)" }}><UploadIcon size={40} /></span>
          <p className="small muted">Add a few photos from your day</p>
        </div>}
        <SceneCatalogStatus />
        <div className="grid-2 journal-new__scene-grid">
          {scenes.map((scene) => {
            const selected = photos.some(photo => photo.mediaAssetId === scene.mediaAssetId);
            return <button key={scene.id} type="button" disabled={uploading || journalSaving}
              className={`scene-pick${selected ? " scene-pick--selected" : ""}`} aria-pressed={selected}
              onClick={() => setPhotos(current => selected
                ? current.filter(photo => photo.mediaAssetId !== scene.mediaAssetId)
                : [...current, { mediaAssetId: scene.mediaAssetId, imageUrl: scene.imageUrl, displayOrder: current.length }])}>
              <SceneVisual scene={scene} />
            </button>;
          })}
        </div>
        <div className="journal-new__upload">
          <ImageUpload cameraEnabled={learner.cameraOn} disabled={journalSaving} onBusyChange={setUploading}
            onUploaded={(image) => setPhotos(current => current.some(photo => photo.mediaAssetId === image.id) ? current
              : [...current, { mediaAssetId: image.id, imageUrl: image.signedUrl, displayOrder: current.length }])} />
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
              disabled={journalSaving}
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
          disabled={journalSaving}
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
      {!entry && !activeProfile ? <p role="alert">Choose a language in Profile before saving.</p> : null}
      <Button block disabled={journalSaving || uploading || !body.trim() || (!entry && !activeProfile)} onClick={save}>
        Save entry
      </Button>
    </div>
  );
}
