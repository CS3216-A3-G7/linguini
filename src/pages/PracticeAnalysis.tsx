import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Card } from "../components/ui";
import { ArrowRightIcon, CloseIcon } from "../components/icons";
import { ScenePhoto } from "../components/ScenePhoto";
import { getScene } from "../data/mock";
import type { LanguageItem } from "../data/types";
import { useAppState } from "../state/useAppState";

const ANALYSIS_XP = 12;

function englishLabel(item: LanguageItem) {
  return item.translation.replace(/^(the|a|an)\s+/i, "").split("/")[0].trim();
}

export function PracticeAnalysis() {
  const navigate = useNavigate();
  const { sceneId } = useParams();
  const scene = getScene(sceneId);
  const { ensureSession, awardAnalysis } = useAppState();
  const [done, setDone] = useState(false);
  const suggestedItems = useMemo(
    () => scene.items.filter((item) => item.wordClass === "noun").slice(0, 2),
    [scene.items],
  );
  const [keptItemIds, setKeptItemIds] = useState<string[]>(() =>
    suggestedItems.map((item) => item.id),
  );
  const [customItems, setCustomItems] = useState<LanguageItem[]>([]);
  const [newWord, setNewWord] = useState("");
  const [pendingWord, setPendingWord] = useState("");
  const [addError, setAddError] = useState("");
  const photoStageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    ensureSession(scene.id);
  }, [scene.id, ensureSession]);

  useEffect(() => {
    setDone(false);
    setKeptItemIds(suggestedItems.map((item) => item.id));
    setCustomItems([]);
    setNewWord("");
    setPendingWord("");
    setAddError("");

    const timer = window.setTimeout(() => setDone(true), 1300);
    return () => window.clearTimeout(timer);
  }, [sceneId, suggestedItems]);

  useEffect(() => {
    if (done) awardAnalysis(ANALYSIS_XP);
  }, [done, awardAnalysis]);

  useEffect(() => {
    if (!pendingWord) return;
    photoStageRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [pendingWord]);

  const keptItems = suggestedItems.filter((item) => keptItemIds.includes(item.id));
  const annotatedItems = [...keptItems, ...customItems];
  const totalWords = annotatedItems.length;

  const startAddingWord = () => {
    const value = newWord.trim();
    if (!value) return;

    const listedWords = [...keptItems.map(englishLabel), ...customItems.map((item) => item.word)];
    if (listedWords.some((word) => word.toLocaleLowerCase() === value.toLocaleLowerCase())) {
      setAddError("That word is already in your list.");
      return;
    }

    setPendingWord(value);
    setNewWord("");
    setAddError("");
  };

  const addWordAtLocation = ({ x, y }: { x: number; y: number }) => {
    if (!pendingWord) return;

    const highestMarker = Math.max(
      0,
      ...suggestedItems.map((item) => item.marker),
      ...customItems.map((item) => item.marker),
    );

    setCustomItems((current) => [
      ...current,
      {
        id: `custom-${Date.now()}`,
        word: pendingWord,
        translation: pendingWord,
        wordClass: "noun",
        gender: null,
        marker: highestMarker + 1,
        x,
        y,
        example: "",
        exampleTranslation: "",
      },
    ]);
    setPendingWord("");
  };

  const cancelPlacement = () => {
    setNewWord(pendingWord);
    setPendingWord("");
  };

  return (
    <div className="stack analysis-page">
      <h1>Scene Analysis</h1>

      {!done ? (
        <section className="analysis-loading" aria-live="polite" aria-busy="true">
          <div className="analysis-scan" aria-hidden="true">
            <ScenePhoto scene={scene} items={[]} />
            <span className="analysis-scan__line" />
          </div>
          <div className="analysis-loading__copy">
            <h2>Finding objects in your image…</h2>
            <p className="muted">This will only take a moment.</p>
          </div>
        </section>
      ) : (
        <>
          <div
            ref={photoStageRef}
            className={`analysis-photo-stage${pendingWord ? " analysis-photo-stage--placing" : ""}`}
          >
            {pendingWord ? (
              <div className="analysis-placement-prompt" aria-live="polite">
                <span>
                  Tap where you see <strong>“{pendingWord}”</strong>
                </span>
                <button type="button" onClick={cancelPlacement}>
                  Cancel
                </button>
              </div>
            ) : null}
            <ScenePhoto
              scene={scene}
              items={annotatedItems}
              onLocationSelect={pendingWord ? addWordAtLocation : undefined}
              locationLabel={pendingWord ? `Choose the location of ${pendingWord}` : undefined}
            />
          </div>

          <section className="analysis-results" aria-labelledby="analysis-found-title">
            <div>
              <h2 id="analysis-found-title">
                {totalWords} {totalWords === 1 ? "word" : "words"} found
              </h2>
              <p className="muted">Keep what matches your photo. Remove or add anything you need.</p>
            </div>

            <Card plain className="analysis-word-card">
              <div className="analysis-word-list" aria-label="Words in this scene">
                {keptItems.map((item) => (
                  <div className="analysis-word-row" key={item.id}>
                    <span className="analysis-word-row__marker">{item.marker}</span>
                    <strong>{englishLabel(item)}</strong>
                    <button
                      className="analysis-word-row__remove"
                      type="button"
                      aria-label={`Remove ${englishLabel(item)}`}
                      onClick={() =>
                        setKeptItemIds((current) => current.filter((id) => id !== item.id))
                      }
                    >
                      <CloseIcon size={18} />
                    </button>
                  </div>
                ))}

                {customItems.map((item) => (
                  <div className="analysis-word-row" key={item.id}>
                    <span className="analysis-word-row__marker analysis-word-row__marker--custom">
                      {item.marker}
                    </span>
                    <strong>{item.word}</strong>
                    <button
                      className="analysis-word-row__remove"
                      type="button"
                      aria-label={`Remove ${item.word}`}
                      onClick={() =>
                        setCustomItems((current) =>
                          current.filter((entry) => entry.id !== item.id),
                        )
                      }
                    >
                      <CloseIcon size={18} />
                    </button>
                  </div>
                ))}

                {totalWords === 0 ? (
                  <p className="small muted">No words selected yet. Add one you can see below.</p>
                ) : null}
              </div>

              <form
                className="analysis-add-word"
                onSubmit={(event) => {
                  event.preventDefault();
                  startAddingWord();
                }}
              >
                <label className="field__label" htmlFor="analysis-new-word">
                  Add another word you see
                </label>
                <div className="analysis-add-word__controls">
                  <input
                    id="analysis-new-word"
                    className="input"
                    value={newWord}
                    placeholder="e.g. window"
                    aria-describedby={addError ? "analysis-add-error" : undefined}
                    onChange={(event) => {
                      setNewWord(event.target.value);
                      if (addError) setAddError("");
                    }}
                  />
                  <Button
                    variant="secondary"
                    type="submit"
                    disabled={!newWord.trim() || Boolean(pendingWord)}
                  >
                    Choose location
                  </Button>
                </div>
                {addError ? (
                  <span id="analysis-add-error" className="small analysis-add-word__error">
                    {addError}
                  </span>
                ) : null}
              </form>
            </Card>
          </section>

          <Button
            block
            disabled={totalWords === 0 || Boolean(pendingWord)}
            onClick={() => navigate(`/practice/${scene.id}/mic-test`)}
          >
            Continue <ArrowRightIcon />
          </Button>
        </>
      )}
    </div>
  );
}
