import { useRef, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Button, Card, Feedback, ProgressTrail, TopBar } from "../components/ui";
import { ArrowRightIcon } from "../components/icons";
import { ScenePhoto } from "../components/ScenePhoto";
import { useScene } from "../state/useScene";
import { useAppState } from "../state/useAppState";
import { practiceStages, taskDone } from "../lib/practiceTasks";
import type { SessionTask } from "../lib/api";

export function ISpyPhase2() {
  const scene = useScene();
  const navigate = useNavigate();
  const { session, completeSession, completionPending, completionError, practiceError } = useAppState();
  const [index, setIndex] = useState(() => {
    const tasks = practiceStages(session?.tasks ?? []).reflection;
    const next = tasks.findIndex(task => !taskDone(task));
    return next < 0 ? Math.max(0, tasks.length - 1) : next;
  });
  if (!session) return null;
  const { learning, clues, reflection } = practiceStages(session.tasks);
  const base = `/practice/sessions/${scene.sessionId}`;
  if (session.session.status === "completed") return <Navigate to={`${base}/summary`} replace />;
  if (!learning.every(taskDone) || ["abandoned", "failed"].includes(session.session.status)) return <Navigate to={`${base}/learn`} replace />;
  if (!clues.every(taskDone)) return <Navigate to={`${base}/ispy-1`} replace />;
  const task = reflection[index];
  const finish = () => { if (completeSession()) navigate(`${base}/summary`); };
  const alerts = [practiceError, completionError].filter(Boolean);
  if (!task) return <div className="stack"><TopBar title="Practice complete" />{alerts.map((message, alertIndex) => <p key={alertIndex} role="alert">{message}</p>)}<Button disabled={completionPending} onClick={finish}>Finish session</Button></div>;
  return <Reflection key={task.id} task={task} index={index} total={reflection.length} onNext={() => index === reflection.length - 1 ? finish() : setIndex(value => value + 1)} />;
}

function Reflection({ task, index, total, onNext }: { task: SessionTask; index: number; total: number; onNext: () => void }) {
  const scene = useScene();
  const { actOnTask, practiceSaving, practiceError } = useAppState();
  const [text, setText] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const request = useRef<{ answer: string; key: string } | null>(null);
  const submitting = useRef(false);
  const target = scene.items.find(item => item.id === task.sceneObjectId);
  const content = task.publicContent;
  if (content.kind !== "reflection") return null;
  const answered = taskDone(task);
  const submit = async () => {
    const answer = text.trim();
    if (!answer || answered || practiceSaving || submitting.current) return;
    submitting.current = true;
    if (request.current?.answer !== answer) request.current = { answer, key: crypto.randomUUID() };
    try {
      const result = await actOnTask(task.id, "attempts", { inputMode: "text", text: answer }, request.current.key);
      if (result) {
        setFeedback(result.attempt?.feedback?.message ?? "Reflection saved.");
        request.current = null;
      }
    } finally { submitting.current = false; }
  };
  return <div className="stack">
    <TopBar title="I-Spy · Your turn" help="Write a short reflection about the words you practised." />
    <ProgressTrail value={index + (answered ? 1 : 0)} total={total} label={`${index + 1} / ${total}`} />
    <ScenePhoto scene={scene} items={target ? [target] : []} activeItemId={target?.id ?? null} />
    <Card><div className="stack-2"><span className="label muted">Your reflection</span><h2>{target?.word}</h2><span className="small muted">{target?.translation}</span><p>{content.prompt}</p></div></Card>
    <div className="stack-2"><span className="label muted">Word suggestions</span><div className="chip-row">{scene.items.map(item => <button key={item.id} type="button" className="chip" disabled={answered || practiceSaving} onClick={() => setText(value => `${value} ${item.word}`.trim())}>{item.word}</button>)}</div></div>
    <div className="field"><label className="field__label" htmlFor="reflection">Your words</label><input id="reflection" className="input" value={text} maxLength={2000} disabled={answered || practiceSaving} onChange={event => setText(event.target.value)} /></div>
    {answered || feedback ? <Feedback><div className="stack-2" role="status"><strong>{task.status === "skipped" ? "Skipped — no XP earned." : feedback ?? "Reflection saved."}</strong></div></Feedback> : null}
    {practiceError ? <p role="alert">{practiceError}</p> : null}
    {answered ? <Button block disabled={practiceSaving} onClick={onNext}>{index === total - 1 ? "Finish session" : "Next item"} <ArrowRightIcon /></Button> : <>
      <Button block disabled={!text.trim() || practiceSaving} onClick={() => void submit()}>Send my response</Button>
      <Button variant="quiet" block disabled={practiceSaving} onClick={() => void actOnTask(task.id, "skip")}>Skip task</Button>
    </>}
  </div>;
}
