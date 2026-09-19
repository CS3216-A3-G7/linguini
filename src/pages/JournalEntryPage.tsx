import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Card, IconButton, TopBar } from "../components/ui";
import { ChevronLeftIcon, ChevronRightIcon } from "../components/icons";
import { JournalPhotoVisual } from "../components/JournalPhotoVisual";
import { useAppState } from "../state/useAppState";

export function JournalEntryPage() {
  const navigate = useNavigate();
  const { entryId } = useParams();
  const { journal, vocabulary } = useAppState();
  const [activePhotoIndex, setActivePhotoIndex] = useState(0);
  const entry = journal.find((item) => item.id === entryId);

  if (!entry) {
    return (
      <div className="stack">
        <TopBar title="Entry not found" />
        <p className="muted">That entry is no longer here.</p>
      </div>
    );
  }

  const linked = vocabulary.filter((record) => entry.wordsUsed.includes(record.word));
  const photoIndex = Math.min(activePhotoIndex, entry.photos.length - 1);
  const activePhoto = entry.photos[photoIndex];

  const changePhoto = (offset: number) => {
    setActivePhotoIndex((current) => (current + offset + entry.photos.length) % entry.photos.length);
  };

  return (
    <div className="stack">
      <strong>{new Date(entry.date).toLocaleDateString("en-GB", {
          weekday: "long",
          day: "numeric",
          month: "short",
        })}</strong>
      <h1>{entry.title}</h1>
      <div className="journal-carousel">
        <div className="scene">
          <JournalPhotoVisual photo={activePhoto} className="scene__art" />
        </div>
        {entry.photos.length > 1 ? (
          <>
            <IconButton
              className="journal-carousel__control journal-carousel__control--previous"
              label="Previous photo"
              onClick={() => changePhoto(-1)}
            >
              <ChevronLeftIcon />
            </IconButton>
            <IconButton
              className="journal-carousel__control journal-carousel__control--next"
              label="Next photo"
              onClick={() => changePhoto(1)}
            >
              <ChevronRightIcon />
            </IconButton>
            <span className="journal-carousel__count">
              {photoIndex + 1} of {entry.photos.length}
            </span>
          </>
        ) : null}
      </div>
      <Card plain>
        <p>{entry.body}</p>
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
