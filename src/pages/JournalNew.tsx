import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Feedback, TopBar } from "../components/ui";
import { CameraIcon, UploadIcon } from "../components/icons";
import { SceneArt } from "../components/SceneArt";
import type { SceneArtId } from "../components/SceneArt";
import { journalWordSuggestions, scenes } from "../data/mock";
import { useAppState } from "../state/useAppState";

export function JournalNew() {
  const navigate = useNavigate();
  const { addJournalEntry } = useAppState();
  const today = new Date();
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [art, setArt] = useState<SceneArtId | null>(null);
  const [selectedWords, setSelectedWords] = useState<string[]>([]);

  const toggleWord = (word: string) =>
    setSelectedWords((current) =>
      current.includes(word) ? current.filter((item) => item !== word) : [...current, word],
    );

  const save = () => {
    addJournalEntry({
      id: `j-${today.getTime()}`,
      date: today.toISOString().slice(0, 10),
      title: title.trim() || "Today's entry",
      art: art ?? "street",
      body: body.trim(),
      wordsUsed: selectedWords,
    });
    navigate("/journal");
  };

  return (
    <div className="stack">
      <TopBar
        title={today.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "short" })}
        onBack={() => navigate("/journal")}
      />
      <h1>Add a new entry</h1>

      <div className="field">
        <label className="field__label" htmlFor="entry-title">
          Title
        </label>
        <input
          id="entry-title"
          className="input"
          placeholder="A walk downtown"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
      </div>

      <div className="stack-2">
        <span className="field__label">Photo</span>
        {art ? (
          <div className="scene">
            <SceneArt scene={art} className="scene__art" />
          </div>
        ) : (
          <div className="dashed-capture">
            <span style={{ color: "var(--teal-dark)" }}>
              <UploadIcon size={40} />
            </span>
            <p className="small muted">Upload an image or pick one from today</p>
          </div>
        )}
        <div className="grid-3">
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
        <Button variant="secondary" onClick={() => setArt("street")}>
          <CameraIcon size={18} /> Take a photo
        </Button>
      </div>

      <div className="stack-2">
        <span className="field__label">Word suggestions</span>
        <div className="chip-row">
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

      <Button block disabled={!body.trim()} onClick={save}>
        Save entry
      </Button>
    </div>
  );
}
