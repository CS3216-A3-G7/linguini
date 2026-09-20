import { LoadingScreen } from "../components/LoadingScreen";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Feedback } from "../components/ui";
import { UploadIcon } from "../components/icons";
import { ImageUpload } from "../components/ImageUpload";
import { MediaImage } from "../components/MediaImage";
import { useAppState } from "../state/useAppState";
import { getJournalContext } from "../lib/api";
import type { JournalPhotoOption } from "../lib/api";
import { queryError, queryKeys } from "../lib/queryKeys";
import { useQuery } from "@tanstack/react-query";
import type { JournalEntry } from "../data/types";

export function JournalNew() {
  const { date } = useParams<{ date?: string }>();
  const { data, isPending: loading, error: queryErrorValue } = useQuery({
    queryKey: queryKeys.journalDayContext(date ?? "today"),
    queryFn: ({ signal }) => getJournalContext(date, signal),
  });
  const error = queryError(queryErrorValue);
  if (loading) return <LoadingScreen label="Loading journal…" />;
  if (error || !data) return <p role="alert">{error ?? "Unable to load journal."} Reload to retry.</p>;
  return <JournalForm key={data.entry?.id ?? `new-${data.date}`} entry={data.entry} date={data.date} photoOptions={data.photoOptions} />;
}

export function JournalForm({ entry, date, photoOptions, onSaved }: { entry: JournalEntry | null; date: string; photoOptions: JournalPhotoOption[]; onSaved?: (entry: JournalEntry) => void }) {
  const navigate = useNavigate();
  const { saveJournalEntry, journalSaving, journalSaveError, vocabulary, vocabularyError, vocabularyLoading, learner, activeProfile } = useAppState();
  const sameLanguage = !entry || entry.languageProfileId === activeProfile?.id;
  const journalWordSuggestions = sameLanguage ? [...new Set(vocabulary.map((item) => item.word))] : [];
  const shownDate = new Date(`${date}T12:00:00`);
  const isToday = date === new Date().toLocaleDateString("en-CA");
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
    }, entry?.id, date);
    if (saved) {
      if (onSaved) onSaved(saved);
      else navigate(`/journal/${saved.id}`);
    }
  };

  return (
    <div className="stack">
      <h3 className="center-text">{shownDate.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "short" })}</h3>
      <h1>{entry ? "Edit journal entry" : isToday ? "Today's journal" : "Journal entry"}</h1>

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
        {photoOptions.length ? (
          <div className="grid-2 journal-new__scene-grid">
            {photoOptions.map((option) => {
              const selected = photos.some(photo => photo.mediaAssetId === option.mediaAssetId);
              return <button key={option.mediaAssetId} type="button" disabled={uploading || journalSaving}
                className={`scene-pick${selected ? " scene-pick--selected" : ""}`} aria-pressed={selected}
                onClick={() => setPhotos(current => selected
                  ? current.filter(photo => photo.mediaAssetId !== option.mediaAssetId)
                  : [...current, { mediaAssetId: option.mediaAssetId, imageUrl: option.imageUrl, displayOrder: current.length }])}>
                <MediaImage assetId={option.mediaAssetId} imageUrl={option.imageUrl} title="Photo from your practice session" />
              </button>;
            })}
          </div>
        ) : <p className="small muted">No photos from completed sessions on this day — add one from your camera or gallery below.</p>}
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
