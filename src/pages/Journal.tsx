import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, IconButton } from "../components/ui";
import { ChevronLeftIcon, ChevronRightIcon, PlusIcon } from "../components/icons";
import { JournalPhotoVisual } from "../components/JournalPhotoVisual";
import { useAppState } from "../state/useAppState";

function formatDate(date: string) {
  return new Date(date).toLocaleDateString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

function monthStart(date: Date) {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function dateFromEntry(date: string) {
  const [year, month] = date.split("-").map(Number);
  return new Date(year, month - 1, 1);
}

function monthLabel(date: Date) {
  return date.toLocaleDateString("en-GB", { month: "long", year: "numeric" });
}

function isInMonth(date: string, month: Date) {
  const entryMonth = dateFromEntry(date);
  return entryMonth.getFullYear() === month.getFullYear() && entryMonth.getMonth() === month.getMonth();
}

function wordCount(text: string) {
  const count = text.trim().split(/\s+/).filter(Boolean).length;
  return `${count} ${count === 1 ? "word" : "words"}`;
}

export function Journal() {
  const navigate = useNavigate();
  const { journal } = useAppState();
  const [visibleMonth, setVisibleMonth] = useState(() =>
    monthStart(journal.length ? dateFromEntry(journal[0].date) : new Date()),
  );
  const visibleEntries = journal.filter((entry) => isInMonth(entry.date, visibleMonth));

  const changeMonth = (offset: number) => {
    setVisibleMonth((current) => new Date(current.getFullYear(), current.getMonth() + offset, 1));
  };

  return (
    <div className="stack journal-page">
      <div className="month-switcher">
        <IconButton label="Previous month" onClick={() => changeMonth(-1)}>
          <ChevronLeftIcon />
        </IconButton>
        <h1>{monthLabel(visibleMonth)}</h1>
        <IconButton label="Next month" onClick={() => changeMonth(1)}>
          <ChevronRightIcon />
        </IconButton>
      </div>

      <Button block className="journal-page__add" onClick={() => navigate("/journal/new")}>
        <PlusIcon size={18} /> Add today&apos;s entry
      </Button>

      {visibleEntries.length === 0 ? (
        <Card>
          <div className="stack-2 center-text" style={{ alignItems: "center" }}>
           
            <strong>No entries this month</strong>
            <p className="small muted">A few sentences a day goes a long way.</p>
          </div>
        </Card>
      ) : null}

      {visibleEntries.length ? (
        <div className="list">
          {visibleEntries.map((entry) => (
            <button
              key={entry.id}
              type="button"
              className="list__row journal-list-entry"
              onClick={() => navigate(`/journal/${entry.id}`)}
            >
              <span className="thumb thumb--lg">
                <JournalPhotoVisual photo={entry.photos[0]} />
              </span>
              <span className="grow journal-list-entry__details">
                <strong className="journal-list-entry__title">{entry.title}</strong>
                <span className="journal-list-entry__meta">
                  <span className="journal-list-entry__date">{formatDate(entry.date)}</span>
                </span>
                 <span className="journal-list-entry__word-count">{wordCount(entry.body)}</span>
              </span>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
