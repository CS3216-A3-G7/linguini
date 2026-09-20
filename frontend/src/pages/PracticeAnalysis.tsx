import { useRef, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Button, Card } from "../components/ui";
import { ArrowRightIcon, CloseIcon } from "../components/icons";
import { ScenePhoto } from "../components/ScenePhoto";
import { LeaveSession } from "../components/LeaveSession";
import { useScene } from "../state/useScene";
import { useAppState } from "../state/useAppState";
import { checkPracticeWord } from "../lib/api";
import type { PracticeReview } from "../lib/api";
import type { LanguageItem } from "../data/types";

export function PracticeAnalysis() {
  const navigate = useNavigate();
  const scene = useScene();
  const { session, saveReview, practiceSaving, practiceError } = useAppState();
  const [removed, setRemoved] = useState<string[]>([]);
  const [added, setAdded] = useState<PracticeReview["addedObjects"]>([]);
  const [label, setLabel] = useState("");
  const [checking, setChecking] = useState(false);
  const [pending, setPending] = useState<{ label: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const photoRef = useRef<HTMLDivElement>(null);
  const base = `/practice/sessions/${scene.sessionId}`;
  if (!session) return null;
  if (session.session.status === "completed") return <Navigate to={`${base}/summary`} replace />;
  if (["abandoned", "failed"].includes(session.session.status)) return <Navigate to={`${base}/learn`} replace />;
  const locked = session.tasks.some(task => task.status !== "pending");
  const kept = scene.items.filter(item => !removed.includes(item.id));
  const custom: LanguageItem[] = added.map((item, index) => ({ id: `custom-${item.id}`, word: item.label,
    translation: item.label, wordClass: "noun", gender: null, marker: scene.items.length + index + 1,
    x: item.x * 100, y: item.y * 100, example: "", exampleTranslation: "" }));
  const startAdding = async () => {
    const word = label.trim();
    if (!word || pending || practiceSaving || checking) return;
    if ([...kept.map(item => item.translation), ...added.map(item => item.label)].some(item => item.toLowerCase() === word.toLowerCase())) {
      setError("That word is already in your list."); return;
    }
    setChecking(true);
    try { await checkPracticeWord(session.session.id, word); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to check this word. Please retry."); return; }
    finally { setChecking(false); }
    setPending({ label: word });
    setError(null);
    photoRef.current?.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" });
  };
  const place = ({ x, y }: { x: number; y: number }) => {
    if (!pending || practiceSaving) return;
    setAdded(current => [...current, { id: crypto.randomUUID(), ...pending, x: Math.min(x / 100, 0.99), y: Math.min(y / 100, 0.99) }]);
    setPending(null); setLabel("");
  };
  const proceed = async () => {
    if (pending || practiceSaving || (!kept.length && !added.length)) return;
    if (locked || await saveReview({ acceptedObjectIds: kept.map(item => item.id), addedObjects: added })) navigate(`${base}/mic-test`);
  };
  return <div className="stack analysis-page">
    <div className="analysis-titlebar">
      <h1>Scene analysis</h1>
      <LeaveSession sessionId={session.session.id} warning={locked ? "Words you have already practised stay in your word bank, but this scene's remaining tasks are dropped." : "The words you picked for this scene will not be saved."} />
    </div>
    <div className="analysis-layout">
    <div className="analysis-stage-column">
    {session.analysisMode === "placeholder" ? <p className="small muted">These are sample suggestions. Keep what matches your photo and add anything missing.</p> : null}
    <div ref={photoRef} className={`analysis-photo-stage${pending ? " analysis-photo-stage--placing" : ""}`}>
      {pending ? <div className="analysis-placement-prompt" role="status">
        <span>Tap where you see <strong>{pending.label}</strong></span>
        <button type="button" onClick={() => setPending(null)}>Cancel</button>
      </div> : null}
      <ScenePhoto scene={scene} items={[...kept, ...custom]} onLocationSelect={pending ? place : undefined}
        locationLabel={pending ? `Choose the location of ${pending.label}` : undefined} />
    </div>
    </div>
    <div className="analysis-review-column">
    <section className="analysis-results" aria-labelledby="analysis-found-title">
      <div><h2 id="analysis-found-title">{kept.length + added.length} words selected</h2>
        <p className="muted">{locked ? "Your lesson has started. Start a new practice to change its words." : "Keep what matches your photo. Remove or add anything you need."}</p>
      </div>
      <Card plain className="analysis-word-card">
        <div className="analysis-word-list" aria-label="Words in this scene">
          {kept.map(item => <div className="analysis-word-row" key={item.id}>
            <span className="analysis-word-row__marker">{item.marker}</span>
            <div className="grow"><strong>{item.translation}</strong></div>
            {!locked ? <button className="analysis-word-row__remove" type="button" disabled={checking || practiceSaving} aria-label={`Remove ${item.translation}`}
              onClick={() => setRemoved(current => [...current, item.id])}><CloseIcon size={18} /></button> : null}
          </div>)}
          {added.map((item, index) => <div className="analysis-word-row" key={item.id}>
            <span className="analysis-word-row__marker analysis-word-row__marker--custom">{scene.items.length + index + 1}</span>
            <div className="grow"><strong>{item.label}</strong>
            </div>
            <button className="analysis-word-row__remove" type="button" disabled={checking || practiceSaving} aria-label={`Remove ${item.label}`}
              onClick={() => setAdded(current => current.filter(row => row.id !== item.id))}><CloseIcon size={18} /></button>
          </div>)}
          {!kept.length && !added.length ? <p className="small muted">Add a word you can see below.</p> : null}
        </div>
        {removed.length ? (
          <div className="analysis-restore">
            <Button variant="quiet" disabled={checking || practiceSaving} onClick={() => setRemoved([])}>
              Restore removed words
            </Button>
          </div>
        ) : null}
        {!locked ? <form className="analysis-add-word" onSubmit={event => { event.preventDefault(); void startAdding(); }}>
          <label className="field__label" htmlFor="analysis-new-word">Add another object you see</label>
          <div className="analysis-add-word__controls">
            <input id="analysis-new-word" className="input" maxLength={200} value={label} placeholder="e.g. window" disabled={checking || practiceSaving || !!pending} onChange={event => setLabel(event.target.value)} />
            <Button variant="secondary" type="submit" disabled={checking || !label.trim() || !!pending || practiceSaving || added.length >= 20}>{checking ? "Checking word..." : "Choose location"}</Button>
          </div>
        </form> : null}
      </Card>
    </section>
    {error || practiceError ? <p role="alert">{error ?? practiceError}</p> : null}
    <Button block disabled={checking || practiceSaving || !!pending || (!kept.length && !added.length)} onClick={() => void proceed()}>
      {practiceSaving ? "Saving your words..." : "Continue"} <ArrowRightIcon />
    </Button>
    </div>
    </div>
  </div>;
}
