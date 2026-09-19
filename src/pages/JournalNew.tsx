import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Feedback } from "../components/ui";
import { UploadIcon } from "../components/icons";
import type { JournalPhoto } from "../data/types";
import { JournalPhotoVisual } from "../components/JournalPhotoVisual";
import { SceneVisual } from "../components/SceneVisual";
import { journalWordSuggestions, scenes } from "../data/mock";
import { useAppState } from "../state/useAppState";

export function JournalNew() {
  const navigate = useNavigate();
  const { addJournalEntry } = useAppState();
  const today = new Date();
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [photos, setPhotos] = useState<JournalPhoto[]>([]);
  const [selectedWords, setSelectedWords] = useState<string[]>([]);
  const photoInput = useRef<HTMLInputElement>(null);

  const toggleWord = (word: string) =>
    setSelectedWords((current) =>
      current.includes(word) ? current.filter((item) => item !== word) : [...current, word],
    );

  const toggleScenePhoto = (art: JournalPhoto & { kind: "scene" }) => {
    setPhotos((current) => {
      const isAdded = current.some((photo) => photo.kind === "scene" && photo.art === art.art);
      return isAdded ? current.filter((photo) => photo.id !== art.id) : [...current, art];
    });
  };

  const addUploadedPhotos = (files: FileList | null) => {
    if (!files) return;
    const uploads = Array.from(files).map((file) => ({
      id: `upload-${file.name}-${file.lastModified}`,
      kind: "upload" as const,
      url: URL.createObjectURL(file),
      alt: file.name,
    }));
    setPhotos((current) => [...current, ...uploads]);
  };

  const removePhoto = (photoId: string) => {
    setPhotos((current) => current.filter((photo) => photo.id !== photoId));
  };

  const save = () => {
    addJournalEntry({
      id: `j-${today.getTime()}`,
      date: today.toISOString().slice(0, 10),
      title: title.trim() || "Today's entry",
      photos: photos.length ? photos : [{ id: "default-street", kind: "scene", art: "street" }],
      body: body.trim(),
      wordsUsed: selectedWords,
    });
    navigate("/journal");
  };

  return (
    <div className="stack">
      <h3 className="center-text">{today.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "short" })}</h3>
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
        <span className="field__label">Photos</span>
        {photos.length ? (
          <div className="photo-strip" aria-label={`${photos.length} photos added`}>
            {photos.map((photo) => (
              <div key={photo.id} className="photo-thumb">
                <JournalPhotoVisual photo={photo} />
                <button
                  type="button"
                  className="photo-thumb__remove"
                  aria-label={`Remove ${photo.kind === "upload" ? photo.alt : "scene photo"}`}
                  onClick={() => removePhoto(photo.id)}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="dashed-capture">
            <span style={{ color: "var(--teal-dark)" }}>
              <UploadIcon size={40} />
            </span>
            <p className="small muted">Add a few photos from your day</p>
          </div>
        )}
        <div className="grid-2 journal-new__scene-grid">
          {scenes.map((scene) => {
            const scenePhoto = { id: `scene-${scene.art}`, kind: "scene" as const, art: scene.art };
            const isSelected = photos.some(
              (photo) => photo.kind === "scene" && photo.art === scene.art,
            );
            return (
            <button
              key={scene.id}
              type="button"
              className={`scene-pick${isSelected ? " scene-pick--selected" : ""}`}
              aria-pressed={isSelected}
              onClick={() => toggleScenePhoto(scenePhoto)}
            >
              <SceneVisual scene={scene} />
             
            </button>
            );
          })}
        </div>
        <input
          ref={photoInput}
          className="visually-hidden"
          type="file"
          accept="image/*"
          multiple
          onChange={(event) => {
            addUploadedPhotos(event.target.files);
            event.target.value = "";
          }}
        />
        <Button className="journal-new__upload" variant="secondary" block onClick={() => photoInput.current?.click()}>
          <UploadIcon size={18} /> Add photos from device
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
