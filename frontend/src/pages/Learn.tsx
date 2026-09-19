import { useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, Feedback, IconButton, ProgressTrail, Sheet, TopBar, XpPill } from "../components/ui";
import { ArrowRightIcon, CheckIcon, SpeakerIcon } from "../components/icons";
import { ScenePhoto } from "../components/ScenePhoto";
import { useScene } from "../state/useScene";
import { useAppState } from "../state/useAppState";
import { getPracticeSummary } from "../lib/api";
import type { SessionTask, TaskAnswer } from "../lib/api";
import { practiceStages, taskDescription, taskDone, taskTitle } from "../lib/practiceTasks";
import { useApiData } from "../lib/useApiData";
import { speak } from "../lib/speech";

export function Learn() {
  const scene = useScene();
  const navigate = useNavigate();
  const { session, practiceSaving, practiceError } = useAppState();
  const [openId, setOpenId] = useState<string | null>(null);
  const loadSummary = useCallback(() => getPracticeSummary(session?.session.id ?? scene.sessionId!), [scene.sessionId, session]);
  const summary = useApiData(loadSummary);
  if (!session) return null;
  if (["abandoned", "failed"].includes(session.session.status)) return <div className="stack"><TopBar title="Session closed" /><p>This session is no longer active.</p><Button onClick={() => navigate("/practice")}>Choose an image</Button></div>;
  const learning = practiceStages(session.tasks).learning;
  const completed = learning.filter(task => task.status === "completed").length;
  const skipped = learning.filter(task => task.status === "skipped").length;
  const allDone = learning.every(taskDone);
  const openTask = learning.find(task => task.id === openId);
  return <div className="stack">
    <TopBar title="Phase 1: Learn words" help="Complete or skip these short tasks to unlock I-Spy."
      right={summary.data ? <XpPill xp={summary.data.xpEarned} /> : undefined} />
    <ProgressTrail value={completed + skipped} total={learning.length}
      label={completed + " of " + learning.length + " tasks completed" + (skipped ? " · " + skipped + " skipped" : "")} />
    <ScenePhoto scene={scene} />
    <div className="stack-2"><h1>Learn words and phrases</h1><p className="muted">Work down the list. Complete or skip each task to unlock the game.</p></div>
    {practiceError ? <p role="alert">{practiceError}</p> : null}
    <div className="stack-2">
      {learning.map((task, index) => <button key={task.id} type="button"
        className={"task-row" + (task.status === "completed" ? " task-row--done" : "")} onClick={() => setOpenId(task.id)}>
        <span className="task-row__index">{task.status === "completed" ? <CheckIcon size={16} /> : index + 1}</span>
        <span className="grow stack-2"><strong>{taskTitle(task)}</strong><span className="small muted">{taskDescription(task)}</span></span>
        {taskDone(task) ? <span className={"pill pill--" + (task.status === "skipped" ? "new" : "mastered")}>{task.status === "skipped" ? "Skipped" : "Done"}</span> : <ArrowRightIcon />}
      </button>)}
    </div>
    <Button block disabled={!allDone || practiceSaving} onClick={() => navigate("/practice/sessions/" + scene.sessionId + "/ispy-1")}>Play I-Spy <ArrowRightIcon /></Button>
    {!allDone ? <p className="small muted center-text">Clickable after completing or skipping all tasks.</p> : null}
    {openTask ? <Sheet title={taskTitle(openTask)} onClose={() => setOpenId(null)}>
      <LearningTaskSheet key={openTask.id} task={openTask} onClose={() => setOpenId(null)} />
    </Sheet> : null}
  </div>;
}

function LearningTaskSheet({ task, onClose }: { task: SessionTask; onClose: () => void }) {
  const scene = useScene();
  const { actOnTask, practiceSaving, practiceError } = useAppState();
  const [text, setText] = useState("");
  const [choice, setChoice] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const requestKey = useRef(crypto.randomUUID());
  const content = task.publicContent;
  const card = scene.items.find(item => item.id === task.sceneObjectId);
  const terminal = taskDone(task);
  const reading = ["vocabularyIntroduction", "grammarExplanation", "syntaxExplanation"].includes(task.kind);
  const submit = async () => {
    const answer: TaskAnswer | undefined = reading ? undefined : content.kind === "grammarPractice"
      ? { inputMode: "multipleChoice", optionId: choice } : { inputMode: "text", text };
    const result = await actOnTask(task.id, reading ? "complete" : "attempts", answer, requestKey.current);
    if (result) { if (reading) onClose(); else setFeedback(result.attempt?.feedback?.message ?? "Saved."); }
  };
  return <div className="stack">
    {card && ["vocabularyIntroduction", "pronunciationPractice"].includes(content.kind) ? <div className="flashcard">
      <div className="spread"><span className="label muted">{card.wordClass}{card.gender ? " · " + card.gender : ""}</span>
        <IconButton label={"Hear " + card.word} onClick={() => speak(card.word, scene.languageCode)}><SpeakerIcon /></IconButton></div>
      <h2>{card.word}</h2><p className="muted">{card.translation}</p>
      {card.example ? <Card plain><div className="stack-2"><strong className="small">{card.example}</strong><span className="small muted">{card.exampleTranslation}</span></div></Card> : null}
      <ProgressTrail value={1} total={1} label="1 of 1" />
    </div> : null}
    {content.kind === "grammarExplanation" || content.kind === "syntaxExplanation" ? <>
      <div className="panel-note">{content.explanation}</div>
      <Card plain><div className="stack-2">{content.kind === "syntaxExplanation" ? <strong>{content.sentencePattern}</strong> : null}{content.examples.map((example, i) => <p key={i}>{example}</p>)}</div></Card>
    </> : null}
    {"prompt" in content ? <p className="muted">{content.prompt}</p> : null}
    {content.kind === "grammarPractice" ? <div className="choice-grid">{content.options.map(option => <button key={option} className="choice" aria-pressed={choice === option} disabled={terminal || practiceSaving} onClick={() => setChoice(option)}>{choice === option ? <CheckIcon size={16} /> : null}{option}</button>)}</div> : null}
    {content.kind === "sentenceBuilding" ? <><p>{content.sourceText}</p><div className="chip-row">{content.tokenBank.map((token, i) => <button key={i} className="chip" disabled={terminal || practiceSaving} onClick={() => setText(value => (value + " " + token).trim())}>{token}</button>)}</div></> : null}
    {!reading && content.kind !== "grammarPractice" ? <div className="field"><label className="field__label" htmlFor="task-answer">Your answer</label><input id="task-answer" className="input" value={text} maxLength={2000} disabled={terminal || practiceSaving} onChange={event => setText(event.target.value)} /></div> : null}
    {feedback ? <Feedback><p role="status">{feedback}</p></Feedback> : null}
    {practiceError ? <p role="alert">{practiceError}</p> : null}
    {terminal ? <Button block onClick={onClose}>{task.status === "skipped" ? "Skipped — close" : "Done — close"}</Button> : <>
      <Button block disabled={practiceSaving || (!reading && !(content.kind === "grammarPractice" ? choice : text.trim()))} onClick={() => void submit()}>{reading ? "Mark complete" : "Submit answer"}</Button>
      <Button variant="quiet" block disabled={practiceSaving} onClick={async () => { if (await actOnTask(task.id, "skip")) onClose(); }}>Skip task</Button>
    </>}
  </div>;
}
