import { LoadingScreen } from "../components/LoadingScreen";
import { useNavigate, useParams } from "react-router-dom";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getJournal, getJournalContext } from "../lib/api";
import { queryError, queryKeys } from "../lib/queryKeys";
import type { JournalEntry } from "../data/types";
import { JournalForm } from "./JournalNew";
import { Button, Card, IconButton, TopBar } from "../components/ui";
import { ChevronLeftIcon, ChevronRightIcon } from "../components/icons";
import { MediaImage } from "../components/MediaImage";
import { useAppState } from "../state/useAppState";
import { useVocabularyQuery } from "../state/queries";

export function JournalEntryPage() {
  const { entryId } = useParams();
  return <JournalEntryDetail key={entryId} entryId={entryId ?? ""} />;
}

function JournalEntryDetail({ entryId }: { entryId: string }) {
  const navigate = useNavigate();
  const { activeProfile } = useAppState();
  const { vocabulary } = useVocabularyQuery();
  const queryClient = useQueryClient();
  const { data: entry, isPending: loading, error: queryErrorValue } = useQuery({
    queryKey: queryKeys.journal(entryId),
    queryFn: ({ signal }) => getJournal(entryId, signal),
  });
  const error = queryError(queryErrorValue);
  const [editing, setEditing] = useState(false);
  const [activePhotoIndex, setActivePhotoIndex] = useState(0);
  if (loading) return <LoadingScreen label="Loading journal entry…" />;
  if (error) return <p role="alert">{error} Reload to retry.</p>;

  if (!entry) {
    return (
      <div className="stack">
        <TopBar title="Entry not found" />
        <p className="muted">That entry is no longer here.</p>
      </div>
    );
  }

  const linked = entry.languageProfileId === activeProfile?.id
    ? vocabulary.filter((record) => entry.wordsUsed.includes(record.word)) : [];
  if (editing) return <JournalEntryEditor key={entry.id} entry={entry} onSaved={(saved) => { queryClient.setQueryData(queryKeys.journal(entryId), saved); setEditing(false); }} />;
  const photoIndex = Math.min(activePhotoIndex, entry.photos.length - 1);
  const photo = entry.photos[photoIndex];
  const changePhoto = (offset: number) => setActivePhotoIndex((photoIndex + offset + entry.photos.length) % entry.photos.length);

  return (
    <div className="stack">
      <strong>{new Date(`${entry.date}T12:00:00`).toLocaleDateString("en-GB", {
          weekday: "long",
          day: "numeric",
          month: "short",
        })}</strong>
      <h1>{entry.title}</h1>
      <Button variant="secondary" onClick={() => setEditing(true)}>Edit entry</Button>
      {photo ? <div className="journal-carousel">
        <div className="scene">
          <MediaImage key={photo.mediaAssetId} assetId={photo.mediaAssetId} title={entry.title} imageUrl={photo.imageUrl} />
        </div>
        {entry.photos.length > 1 ? <>
          <IconButton className="journal-carousel__control journal-carousel__control--previous" label="Previous photo" onClick={() => changePhoto(-1)}><ChevronLeftIcon /></IconButton>
          <IconButton className="journal-carousel__control journal-carousel__control--next" label="Next photo" onClick={() => changePhoto(1)}><ChevronRightIcon /></IconButton>
          <span className="journal-carousel__count" aria-live="polite">{photoIndex + 1} of {entry.photos.length}</span>
        </> : null}
      </div> : null}
      <Card plain>
        <p style={{ whiteSpace: "pre-wrap" }}>{entry.body}</p>
      </Card>

      {linked.length ? (
        <div className="stack-2">
          <h2>From your vocabulary</h2>
          <div className="list">
            {linked.map((record) => (
              <div key={record.id} className="list__row" style={{ cursor: "default" }}>
                <div className="grow">
                  <strong>{record.word}</strong>
                  <p className="small muted">{record.translation}</p>
                </div>
                <span className={`pill pill--${record.status}`}>{record.status}</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="stack-2">
        <Button variant="secondary" block onClick={() => navigate("/journal")}>
          Back to journal
        </Button>
      </div>
    </div>
  );
}

function JournalEntryEditor({ entry, onSaved }: { entry: JournalEntry; onSaved: (entry: JournalEntry) => void }) {
  const { data, isPending: loading, error: queryErrorValue } = useQuery({
    queryKey: queryKeys.journalDayContext(entry.date),
    queryFn: ({ signal }) => getJournalContext(entry.date, signal),
  });
  const error = queryError(queryErrorValue);
  if (loading) return <LoadingScreen label="Loading journal…" />;
  if (error || !data) return <p role="alert">{error ?? "Unable to load journal."} Reload to retry.</p>;
  return <JournalForm entry={entry} date={entry.date} photoOptions={data.photoOptions} onSaved={onSaved} />;
}
