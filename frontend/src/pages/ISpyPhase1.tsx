import { useRef, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Button, Feedback, IconButton, ProgressTrail, TopBar } from "../components/ui";
import { ArrowRightIcon, CheckIcon, SpeakerIcon } from "../components/icons";
import { ScenePhoto } from "../components/ScenePhoto";
import { useScene } from "../state/useScene";
import { useAppState } from "../state/useAppState";
import { practiceStages, taskDone } from "../lib/practiceTasks";
import { speak } from "../lib/speech";
import type { SessionTask, TaskActionResult } from "../lib/api";

export function ISpyPhase1() {
  const scene = useScene();
  const { session } = useAppState();
  const [index, setIndex] = useState(() => {
    const clues = practiceStages(session?.tasks ?? []).clues;
    const next = clues.findIndex(task => !taskDone(task));
    return next < 0 ? Math.max(0, clues.length - 1) : next;
  });
  if (!session) return null;
  const { learning, clues } = practiceStages(session.tasks);
  const base = `/practice/sessions/${scene.sessionId}`;
  if (!learning.every(taskDone) || ["abandoned", "failed"].includes(session.session.status)) return <Navigate to={`${base}/learn`} replace />;
  const task = clues[index];
  if (!task) return <Navigate to={`${base}/ispy-2`} replace />;
  return <ClueRound key={task.id} task={task} index={index} total={clues.length} onNext={() => setIndex(value => value + 1)} />;
}

function ClueRound({ task, index, total, onNext }: { task: SessionTask; index: number; total: number; onNext: () => void }) {
  const navigate = useNavigate();
  const scene = useScene();
  const { actOnTask, practiceSaving, practiceError } = useAppState();
  const [picked, setPicked] = useState<string | null>(null);
  const [result, setResult] = useState<TaskActionResult | null>(null);
  const [showTranslation, setShowTranslation] = useState(false);
  const key = useRef(crypto.randomUUID());
  const content = task.publicContent;
  if (content.kind !== "ispyRound") return null;
  const answered = taskDone(task);
  const choose = async (optionId: string) => {
    if (answered || practiceSaving) return;
    setPicked(optionId);
    setResult(await actOnTask(task.id, "attempts", { inputMode: "multipleChoice", optionId }, key.current));
  };
  const selected = content.options.find(option => option.optionId === picked);
  return <div className="stack">
    <TopBar title="I-Spy · Linguini clues" help="Listen or read the clue, then choose what you spy." />
    <ProgressTrail value={index + (answered ? 1 : 0)} total={total} label={`${index + 1} / ${total}`} />
    <ScenePhoto scene={scene} activeItemId={result?.attempt?.isCorrect ? selected?.sceneObjectId : null} />
    <div className="card card--lifted stack-2">
      <div className="spread"><span className="label muted">Linguini says</span><IconButton label="Hear the clue" onClick={() => speak(content.clue, scene.languageCode)}><SpeakerIcon /></IconButton></div>
      <h3>{content.clue}</h3>
      {content.clueTranslation ? showTranslation ? <p className="small muted">{content.clueTranslation}</p> : <Button variant="quiet" onClick={() => setShowTranslation(true)}>Show translation</Button> : null}
    </div>
    <div className="choice-grid">{content.options.map(option => {
      const state = result?.attempt && picked === option.optionId ? (result.attempt.isCorrect ? " choice--correct" : " choice--incorrect") : "";
      return <button key={option.optionId} type="button" className={`choice${state}`} disabled={answered || practiceSaving} onClick={() => void choose(option.optionId)}>
        {result?.attempt?.isCorrect && picked === option.optionId ? <CheckIcon size={16} /> : null}{option.label}
      </button>;
    })}</div>
    {answered ? <Feedback tone={result?.attempt?.isCorrect === false ? "warn" : "good"}><div className="stack-2"><strong>{task.status === "skipped" ? "Skipped — no XP earned." : result?.attempt?.feedback?.message ?? "Answer saved."}</strong>{content.encouragement ? <span className="small muted">{content.encouragement}</span> : null}</div></Feedback> : null}
    {practiceError ? <p role="alert">{practiceError}</p> : null}
    <Button block disabled={!answered || practiceSaving} onClick={() => index === total - 1 ? navigate(`/practice/sessions/${scene.sessionId}/ispy-2`) : onNext()}>{index === total - 1 ? "Your turn" : "Next clue"} <ArrowRightIcon /></Button>
    {!answered ? <Button variant="quiet" block disabled={practiceSaving} onClick={() => void actOnTask(task.id, "skip")}>Skip task</Button> : null}
  </div>;
}
