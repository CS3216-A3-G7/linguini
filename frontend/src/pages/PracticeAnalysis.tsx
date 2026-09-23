import { useRef, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Button, Card, ComboBox } from "../components/ui";
import { ArrowRightIcon, CloseIcon } from "../components/icons";
import { ScenePhoto } from "../components/ScenePhoto";
import { TranslationPreview } from "../components/TranslationPreview";
import { LeaveSession } from "../components/LeaveSession";
import { useScene } from "../state/useScene";
import { useAppState } from "../state/useAppState";
import { sessionDestination } from "../lib/sessionRoute";
import type { PracticeReview } from "../lib/api";
import type { LanguageItem } from "../data/types";

const ATTRIBUTE_TYPES = ["color", "size", "shape", "material", "pattern", "state", "quantity"] as const;
const RELATION_OPTIONS = [
  ["leftOf", "Left of"], ["rightOf", "Right of"], ["above", "Above"], ["below", "Below"],
  ["on", "On"], ["under", "Under"], ["in", "Inside"], ["inFrontOf", "In front of"],
  ["behind", "Behind"], ["nextTo", "Next to"], ["near", "Near"],
] as const;
const RELATION_CHOICES = RELATION_OPTIONS.map(([value, label]) => ({ value, label }));
type AnalysisPanel = "objects" | "attributes" | "relations";

export function PracticeAnalysis() {
  const navigate = useNavigate();
  const scene = useScene();
  const { session, saveReview, practiceSaving, practiceError, practiceStalled, retryProcessing } = useAppState();
  const [removed, setRemoved] = useState<string[]>([]);
  const [added, setAdded] = useState<PracticeReview["addedObjects"]>([]);
  const [relations, setRelations] = useState<PracticeReview["relations"]>(() => session?.sceneObjectRelations ?? []);
  const [panel, setPanel] = useState<AnalysisPanel>("objects");
  const [attributes, setAttributes] = useState<Record<string, Record<string, string>>>(() =>
    Object.fromEntries((session?.sceneObjects ?? []).map(item => [item.id,
      Object.fromEntries(Object.entries(item.attributes ?? {}).filter((entry): entry is [string, string] => typeof entry[1] === "string"))])));
  const [attributeObjectId, setAttributeObjectId] = useState(session?.sceneObjects[0]?.id ?? "");
  const [subject, setSubject] = useState("");
  const [relationText, setRelationText] = useState("");
  const [reference, setReference] = useState("");
  const [label, setLabel] = useState("");
  const [pending, setPending] = useState<{ label: string; id?: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const photoRef = useRef<HTMLDivElement>(null);
  const base = `/practice/sessions/${scene.sessionId}`;
  if (!session) return null;
  if (["completed", "failed", "abandoned"].includes(session.session.status)) {
    const dest = sessionDestination(session);
    return <Navigate to={dest.path} replace state={dest.notice ? { practiceNotice: dest.notice } : undefined} />;
  }
  if (["created", "analyzingScene", "generatingTasks"].includes(session.session.status)) return <div className="stack analysis-page">
    <h1>Scene analysis</h1>
    {session.session.status === "generatingTasks" && session.translationPreview ? <>
      <TranslationPreview preview={session.translationPreview} scene={scene} />
      <section role="status" className="panel-note">
        {session.tasks.some(task => task.kind === "vocabularyIntroduction") ? <>
          <h2>Your first task is ready</h2>
          <p className="muted">Start learning your words now. The remaining tasks will finish in the background.</p>
          <Button block onClick={() => navigate(`${base}/learn/${session.tasks.find(task => task.kind === "vocabularyIntroduction")!.id}`)}>
            Begin tasks <ArrowRightIcon />
          </Button>
        </> : <>
          <h2>Preparing your first task...</h2>
          <p className="muted">Your translations are ready. Your first task will appear here shortly.</p>
        </>}
        {practiceStalled ? <Button onClick={() => retryProcessing(session.session.id)}>Check again</Button> : null}
        {practiceError ? <p role="alert">{practiceError}</p> : null}
      </section>
    </> : <>
    {practiceStalled ? <section className="analysis-loading" aria-live="polite">
      <div className="analysis-loading__copy"><h2>Still working on your scene...</h2><p className="muted">This is taking longer than usual. You can check again.</p>{practiceError ? <p role="alert">{practiceError}</p> : null}<Button onClick={() => retryProcessing(session.session.id)}>Retry</Button></div>
    </section> : <section className="analysis-loading" aria-live="polite" aria-busy="true">
      <div className="analysis-scan" aria-hidden="true"><ScenePhoto scene={scene} items={[]} /><span className="analysis-scan__line" /></div>
      <div className="analysis-loading__copy"><h2>{session.session.status === "generatingTasks" ? "Translating your scene..." : "Finding objects in your image..."}</h2><p className="muted">{session.session.status === "generatingTasks" ? "Turning your confirmed words into your learning language." : "This will only take a moment."}</p></div>
    </section>}
    </>}
  </div>;
  const locked = session.tasks.some(task => task.status !== "pending");
  const kept = scene.items.filter(item => !removed.includes(item.id));
  const custom: LanguageItem[] = added.map((item, index) => ({ id: `custom-${item.id}`, word: item.label,
    translation: item.label, wordClass: "noun", gender: null, marker: scene.items.length + index + 1,
    x: item.x * 100, y: item.y * 100, attributes: attributes[item.id] ?? {}, example: "", exampleTranslation: "" }));
  const relationObjects = [...kept.map(item => ({ id: item.id, label: item.translation })), ...added];
  const selectedIds = new Set(relationObjects.map(item => item.id));
  const activeAttributeObjectId = selectedIds.has(attributeObjectId) ? attributeObjectId : relationObjects[0]?.id ?? "";
  const visibleRelations = relations.filter(row => selectedIds.has(row.subjectSceneObjectId) && selectedIds.has(row.referenceSceneObjectId));
  const addRelation = () => {
    const text = relationText;
    if (!text || subject === reference || !selectedIds.has(subject) || !selectedIds.has(reference)) return;
    if (visibleRelations.some(row => row.subjectSceneObjectId === subject && row.referenceSceneObjectId === reference && row.relation.toLowerCase() === text.toLowerCase())) {
      setError("That relation is already in your list."); return;
    }
    setRelations(current => [...current, { id: crypto.randomUUID(), subjectSceneObjectId: subject, relation: text, referenceSceneObjectId: reference, sourceRelationKey: null }]);
    setRelationText(""); setError(null);
  };
  const startAdding = () => {
    const word = label.trim();
    if (!word || pending || practiceSaving) return;
    if ([...kept.map(item => item.translation), ...added.map(item => item.label)].some(item => item.toLowerCase() === word.toLowerCase())) {
      setError("That word is already in your list."); return;
    }
    setPending({ label: word });
    setError(null);
    photoRef.current?.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" });
  };
  const place = ({ x, y }: { x: number; y: number }) => {
    if (!pending || practiceSaving) return;
    const location = { x: Math.min(x / 100, 0.99), y: Math.min(y / 100, 0.99) };
    setAdded(current => pending.id
      ? current.map(item => item.id === pending.id ? { ...item, ...location } : item)
      : [...current, { id: crypto.randomUUID(), label: pending.label, ...location }]);
    setPending(null); setLabel("");
  };
  const replaceLocation = (item: PracticeReview["addedObjects"][number]) => {
    setPending({ id: item.id, label: item.label });
    setError(null);
    photoRef.current?.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" });
  };
  const proceed = async () => {
    if (pending || practiceSaving || (!kept.length && !added.length)) return;
    const selectedAttributes = Object.fromEntries([...kept.map(item => item.id), ...added.map(item => item.id)]
      .map(id => [id, attributes[id] ?? {}]));
    if (locked) {
      navigate(`${base}/mic-test`);
      return;
    }
    // Stay on the translating screen while background generation runs.
    // SessionRoute forwards to the mic check when the session becomes ready.
    await saveReview({ acceptedObjectIds: kept.map(item => item.id), addedObjects: added, relations: visibleRelations, objectAttributes: selectedAttributes });
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
        <div className="analysis-panel-tabs" role="tablist" aria-label="Scene analysis details">
          {(["objects", "attributes", "relations"] as const).map(value => <button key={value} type="button" role="tab"
            aria-selected={panel === value} className={panel === value ? "is-active" : ""} onClick={() => setPanel(value)}>
            {value[0].toUpperCase() + value.slice(1)}
            <span>{value === "objects" ? kept.length + added.length : value === "attributes" ? Object.values(attributes).reduce((sum, row) => sum + Object.values(row).filter(Boolean).length, 0) : visibleRelations.length}</span>
          </button>)}
        </div>
      </div>
      <div className="analysis-review-column">
        {panel === "objects" ? <section className="analysis-results" aria-labelledby="analysis-found-title">
          <div><h2 id="analysis-found-title">{kept.length + added.length} words selected</h2>
            <p className="muted">{locked ? "Your lesson has started. Start a new practice to change its words." : "Keep what matches your photo. Remove or add anything you need."}</p>
          </div>
          <Card plain className="analysis-word-card">
            <div className="analysis-word-list" aria-label="Words in this scene">
              {kept.map(item => <div className="analysis-word-row" key={item.id}>
                <span className="analysis-word-row__marker">{item.marker}</span>
                <div className="grow"><strong>{item.translation}</strong></div>
                {!locked ? <button className="analysis-word-row__remove" type="button" disabled={practiceSaving} aria-label={`Remove ${item.translation}`}
                  onClick={() => setRemoved(current => [...current, item.id])}><CloseIcon size={18} /></button> : null}
              </div>)}
              {added.map((item, index) => <div className="analysis-word-row" key={item.id}>
                <span className="analysis-word-row__marker analysis-word-row__marker--custom">{scene.items.length + index + 1}</span>
                <div className="grow"><strong>{item.label}</strong>
                  <button className="analysis-location-action" type="button" disabled={practiceSaving || !!pending}
                    onClick={() => replaceLocation(item)}>Change location</button>
                </div>
                <button className="analysis-word-row__remove" type="button" disabled={practiceSaving} aria-label={`Remove ${item.label}`}
                  onClick={() => setAdded(current => current.filter(row => row.id !== item.id))}><CloseIcon size={18} /></button>
              </div>)}
              {!kept.length && !added.length ? <p className="small muted">Add a word you can see below.</p> : null}
            </div>
            {removed.length ? (
              <div className="analysis-restore">
                <Button variant="quiet" disabled={practiceSaving} onClick={() => setRemoved([])}>
                  Restore removed words
                </Button>
              </div>
            ) : null}
          </Card>
          {!locked ? <form className="analysis-add-word" onSubmit={event => { event.preventDefault(); startAdding(); }}>
            <label className="field__label" htmlFor="analysis-new-word">Add another object you see</label>
            <div className="analysis-add-word__controls">
              <input id="analysis-new-word" className="input" maxLength={200} value={label} placeholder="e.g. window" disabled={practiceSaving || !!pending} onChange={event => setLabel(event.target.value)} />
              <Button variant="secondary" type="submit" disabled={!label.trim() || !!pending || practiceSaving || added.length >= 20}>Select location</Button>
            </div>
          </form> : null}
        </section> : null}
        {panel === "attributes" ? <section className="analysis-results" aria-labelledby="analysis-attributes-title">
          <div><h2 id="analysis-attributes-title">Visible attributes</h2><p className="muted">Correct only what you can clearly see in the photo.</p></div>
          <Card plain className="analysis-word-card analysis-attribute-card">
            <label className="field__label" htmlFor="attribute-object">Object</label>
            <ComboBox id="attribute-object" value={activeAttributeObjectId}
              options={relationObjects.map(item => ({ value: item.id, label: item.label }))}
              onChange={setAttributeObjectId} />
            <div className="analysis-attribute-fields">
              {ATTRIBUTE_TYPES.map(type => { const value = attributes[activeAttributeObjectId]?.[type] ?? ""; return <label key={type}><span>{type}</span><input className={`input${value.trim() ? " is-filled" : ""}`} value={value}
                placeholder={`No ${type}`} disabled={locked || practiceSaving} onChange={event => setAttributes(current => ({ ...current,
                  [activeAttributeObjectId]: { ...(current[activeAttributeObjectId] ?? {}), [type]: event.target.value } }))} /></label>; })}
            </div>
          </Card>
        </section> : null}
        {panel === "relations" ? <section className="analysis-results" aria-labelledby="analysis-relations-title">
          <h2 id="analysis-relations-title">How objects relate</h2>
          <p className="muted">Keep or add connections you can see, such as a cup on a table. Removing a word also removes its connections.</p>
          <Card plain className="analysis-word-card">
            <div className="analysis-word-list">
              {visibleRelations.map((row, index) => <div className="analysis-relation-row" key={row.id}>
                <span className="analysis-word-row__marker analysis-relation-row__marker">{index + 1}</span>
                <div className="analysis-relation-row__flow">
                  <strong>{relationObjects.find(item => item.id === row.subjectSceneObjectId)?.label}</strong>
                  {locked ? <span className="analysis-relation-row__relation">{RELATION_OPTIONS.find(option => option[0] === row.relation)?.[1] ?? row.relation}</span> :
                    <ComboBox compact ariaLabel="Connection" value={row.relation}
                      options={!RELATION_OPTIONS.some(option => option[0] === row.relation)
                        ? [{ value: row.relation, label: row.relation }, ...RELATION_CHOICES]
                        : RELATION_CHOICES}
                      onChange={value => setRelations(current => current.map(item => item.id === row.id ? { ...item, relation: value } : item))} />}
                  <strong>{relationObjects.find(item => item.id === row.referenceSceneObjectId)?.label}</strong>
                </div>
                {!locked ? <button type="button" className="analysis-word-row__remove" disabled={practiceSaving} aria-label={`Remove relation ${row.relation}`} onClick={() => setRelations(current => current.filter(item => item.id !== row.id))}><CloseIcon size={18} /></button> : null}
              </div>)}
              {!visibleRelations.length ? <p className="small muted">No connections selected. You can continue without adding any.</p> : null}
            </div>
            {!locked ? <form className="stack" onSubmit={event => { event.preventDefault(); addRelation(); }}>
              <label className="field__label" htmlFor="relation-subject">Object</label>
              <ComboBox id="relation-subject" value={subject} disabled={practiceSaving} placeholder="Choose an object"
                options={relationObjects.map(item => ({ value: item.id, label: item.label }))} onChange={setSubject} />
              <label className="field__label" htmlFor="relation-text">Connection</label>
              <ComboBox id="relation-text" value={relationText} disabled={practiceSaving} placeholder="Choose a connection"
                options={RELATION_CHOICES} onChange={setRelationText} />
              <label className="field__label" htmlFor="relation-reference">Related object</label>
              <ComboBox id="relation-reference" value={reference} disabled={practiceSaving} placeholder="Choose another object"
                options={relationObjects.filter(item => item.id !== subject).map(item => ({ value: item.id, label: item.label }))}
                onChange={setReference} />
              <Button type="submit" variant="secondary" disabled={practiceSaving || !relationText.trim() || subject === reference || !selectedIds.has(subject) || !selectedIds.has(reference) || visibleRelations.length >= 100}>Add connection</Button>
            </form> : null}
          </Card>
        </section> : null}
        {error || practiceError ? <p role="alert">{error ?? practiceError}</p> : null}
        <Button block className="analysis-continue" disabled={practiceSaving || !!pending || (!kept.length && !added.length)} onClick={() => void proceed()}>
          {practiceSaving ? "Saving your words..." : "Continue"} <ArrowRightIcon />
        </Button>
      </div>
    </div>
  </div>;
}
