import { useNavigate, useParams } from "react-router-dom";
import { Button, Card, TopBar } from "../components/ui";
import { PlusIcon } from "../components/icons";
import { SceneArt } from "../components/SceneArt";
import { useAppState } from "../state/useAppState";

export function JournalEntryPage() {
  const navigate = useNavigate();
  const { entryId } = useParams();
  const { journal, vocabulary } = useAppState();
  const entry = journal.find((item) => item.id === entryId);

  if (!entry) {
    return (
      <div className="stack">
        <TopBar title="Entry not found" onBack={() => navigate("/journal")} />
        <p className="muted">That entry is no longer here.</p>
      </div>
    );
  }

  const linked = vocabulary.filter((record) => entry.wordsUsed.includes(record.word));

  return (
    <div className="stack">
      <TopBar
        title={new Date(entry.date).toLocaleDateString("en-GB", {
          weekday: "long",
          day: "numeric",
          month: "short",
        })}
        onBack={() => navigate("/journal")}
      />
      <h1>{entry.title}</h1>
      <div className="scene">
        <SceneArt scene={entry.art} className="scene__art" />
      </div>
      <Card plain>
        <p>{entry.body}</p>
      </Card>

      <div className="stack-2">
        <h2>Words used</h2>
        <div className="chip-row">
          {entry.wordsUsed.map((word) => (
            <span key={word} className="chip chip--static">
              {word}
            </span>
          ))}
        </div>
      </div>

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
        <Button block onClick={() => navigate("/journal/new")}>
          <PlusIcon size={18} /> New entry
        </Button>
        <Button variant="secondary" block onClick={() => navigate("/journal")}>
          Back to journal
        </Button>
      </div>
    </div>
  );
}
