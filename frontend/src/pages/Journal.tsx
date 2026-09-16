import { useNavigate } from "react-router-dom";
import { Button, Card, Mascot } from "../components/ui";
import { PlusIcon } from "../components/icons";
import { SceneArt } from "../components/SceneArt";
import { useAppState } from "../state/useAppState";

function formatDate(date: string) {
  return new Date(date).toLocaleDateString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

function monthOf(date: string) {
  return new Date(date).toLocaleDateString("en-GB", { month: "long", year: "numeric" });
}

export function Journal() {
  const navigate = useNavigate();
  const { journal, journalLoading, journalError } = useAppState();
  if (journalLoading) return <p role="status">Loading journal history…</p>;
  if (journalError) return <p role="alert">{journalError} Reload to retry.</p>;

  const months = journal.reduce<Record<string, typeof journal>>((groups, entry) => {
    const key = monthOf(entry.date);
    groups[key] = [...(groups[key] ?? []), entry];
    return groups;
  }, {});

  return (
    <div className="stack">
      <h1>My journal</h1>
      <p className="muted">Practice writing about your day</p>

      <Button block onClick={() => navigate("/journal/new")}>
        <PlusIcon size={18} /> Write today&apos;s entry
      </Button>

      {journal.length === 0 ? (
        <Card>
          <div className="stack-2 center-text" style={{ alignItems: "center" }}>
            <Mascot size={96} />
            <strong>No entries yet</strong>
            <p className="small muted">A few sentences a day goes a long way.</p>
          </div>
        </Card>
      ) : null}

      {Object.entries(months).map(([month, entries]) => (
        <div key={month} className="stack-2">
          <h2>{month}</h2>
          <div className="list">
            {entries.map((entry) => (
              <button
                key={entry.id}
                type="button"
                className="list__row"
                onClick={() => navigate(`/journal/${entry.id}`)}
              >
                <span className="thumb thumb--lg">
                  <SceneArt scene={entry.art} />
                </span>
                <span className="grow stack-2">
                  <strong>{entry.title}</strong>
                  <span className="small muted align-middle">{formatDate(entry.date)}</span>
                  <span className="small muted">{entry.wordsUsed.length} words used</span>
                </span>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
