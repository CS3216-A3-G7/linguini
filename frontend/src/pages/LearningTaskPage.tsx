import { useRef, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { Button, Card, Feedback, IconButton, ProgressTrail } from "../components/ui";
import { CheckIcon, SpeakerIcon } from "../components/icons";
import { useScene } from "../state/useScene";
import { useAppState } from "../state/useAppState";
import { practiceStages, taskDone, taskTitle } from "../lib/practiceTasks";
import { speak } from "../lib/speech";
import type { SessionTask, TaskAnswer, VocabularyLearningWord } from "../lib/api";

export function LearningTaskPage() {
  const { taskId } = useParams();
  const { session } = useAppState();
  const navigate = useNavigate();
  const scene = useScene();
  const base = `/practice/sessions/${scene.sessionId}`;
  if (!session) return null;
  if (session.session.status === "completed") return <Navigate to={`${base}/summary`} replace />;
  const tasks = practiceStages(session.tasks).learning;
  const index = tasks.findIndex(item => item.id === taskId);
  const task = tasks[index];
  if (!task || ["abandoned", "failed"].includes(session.session.status)) return <Navigate to={`${base}/learn`} replace />;
  const next = tasks[index + 1];
  return <div className="stack learning-task-page"><LearningTaskContent key={task.id} task={task} index={index} total={tasks.length}
    onNext={() => navigate(next ? `${base}/learn/${next.id}` : `${base}/learn`)} onClose={() => navigate(`${base}/learn`)} /></div>;
}

function LearningTaskContent({ task, index, total, onNext, onClose }: { task: SessionTask; index: number; total: number; onNext: () => void; onClose: () => void }) {
  const scene = useScene();
  const { actOnTask, practiceSaving, practiceError } = useAppState();
  const [text, setText] = useState("");
  const [choice, setChoice] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const request = useRef<{ answer: string; key: string } | null>(null);
  const busy = useRef(false);
  const content = task.publicContent;
  if (content.kind === "vocabularyIntroduction" && content.words.length) {
    return <VocabularyLearningFlow task={task} index={index} total={total} onNext={onNext} onClose={onClose} />;
  }
  if (content.kind === "grammarLesson") {
    return <GrammarLessonFlow task={task} index={index} total={total} onNext={onNext} onClose={onClose} />;
  }
  const card = scene.items.find(item => item.id === task.sceneObjectId);
  const terminal = taskDone(task);
  const reading = ["vocabularyIntroduction", "grammarExplanation", "syntaxExplanation"].includes(task.kind);
  const submit = async () => {
    const answer: TaskAnswer | undefined = reading ? undefined : content.kind === "grammarPractice"
      ? { inputMode: "multipleChoice", optionId: choice } : { inputMode: "text", text };
    if (terminal || practiceSaving || busy.current || (!reading && !(content.kind === "grammarPractice" ? choice : text.trim()))) return;
    busy.current = true;
    const identity = JSON.stringify(answer ?? {});
    if (request.current?.answer !== identity) request.current = { answer: identity, key: crypto.randomUUID() };
    try {
      const result = await actOnTask(task.id, reading ? "complete" : "attempts", answer, request.current.key);
      if (result) {
        request.current = null;
        if (reading) onNext();
        else setFeedback(result.attempt?.feedback?.message ?? "Saved.");
      }
    } finally { busy.current = false; }
  };
  return <div className="stack">
    <ProgressTrail value={index + 1} total={total} label={`Task ${index + 1} of ${total}`} />
    <div className="learning-title-row"><h1>{taskTitle(task)}</h1><Button variant="quiet" className="learning-exit" onClick={onClose}>Back to tasks</Button></div>
    {card && ["vocabularyIntroduction", "pronunciationPractice"].includes(content.kind) ? <div className="flashcard learning-card">
      <div className="spread"><span className="label muted">{card.wordClass}{card.gender ? " · " + card.gender : ""}</span>
        <IconButton label={"Hear " + card.word} onClick={() => speak(card.word, scene.languageCode)}><SpeakerIcon /></IconButton></div>
      <div className="learning-card__word"><h2>{card.word}</h2><p className="muted">{card.translation}</p></div>
      {card.example ? <Card plain><div className="stack-2"><strong className="small">{card.example}</strong><span className="small muted">{card.exampleTranslation}</span></div></Card> : null}
    </div> : null}
    {!card && content.kind === "vocabularyIntroduction" ? <article className="flashcard learning-card">
      <div className="learning-card__word"><h2>{content.targetText}</h2><p>{content.translation}</p></div>
      <p>{content.exampleSentence}</p>
      <IconButton label={`Hear ${content.targetText ?? "word"}`} onClick={() => speak(content.targetText ?? "", scene.languageCode)}><SpeakerIcon /></IconButton>
    </article> : null}
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
    {terminal ? <Button block disabled={practiceSaving} onClick={onNext}>{index < total - 1 ? "Next task" : "Back to tasks"}</Button> : <>
      <Button block disabled={practiceSaving || (!reading && !(content.kind === "grammarPractice" ? choice : text.trim()))} onClick={() => void submit()}>{reading ? "Mark complete" : "Submit answer"}</Button>
      <Button variant="quiet" block disabled={practiceSaving} onClick={async () => { if (await actOnTask(task.id, "skip")) onNext(); }}>Skip task</Button>
    </>}
  </div>;
}

function VocabularyLearningFlow({ task, index, total, onNext, onClose }: { task: SessionTask; index: number; total: number; onNext: () => void; onClose: () => void }) {
  const scene = useScene();
  const { actOnTask, practiceSaving, practiceError } = useAppState();
  const [stage, setStage] = useState<"review" | "quiz" | "typing">("review");
  const [page, setPage] = useState(0);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [typingIndex, setTypingIndex] = useState(0);
  const [typedAnswers, setTypedAnswers] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<string | null>(null);
  const requestKey = useRef(crypto.randomUUID());
  const content = task.publicContent;
  if (content.kind !== "vocabularyIntroduction") return null;
  const terminal = taskDone(task);
  const pageCount = Math.ceil(content.words.length / 3);
  const visibleWords = content.words.slice(page * 3, page * 3 + 3);
  const question = content.questions[questionIndex];
  const typingWord = content.words[typingIndex];
  const typingKey = typingWord ? typingWord.learningKey ?? typingWord.vocabularyItemId ?? typingWord.targetText : "";
  const submit = async () => {
    const result = await actOnTask(task.id, "attempts", { inputMode: "vocabularyReview", answers, typedAnswers }, requestKey.current);
    if (result) setFeedback(result.attempt?.feedback?.message ?? "Vocabulary practice saved.");
  };
  const finishReview = () => page < pageCount - 1 ? setPage(value => value + 1) : setStage("quiz");
  const finishQuestion = () => questionIndex < content.questions.length - 1 ? setQuestionIndex(value => value + 1) : setStage("typing");
  return <div className="stack vocabulary-flow">
    <ProgressTrail value={index + 1} total={total} label={`Task ${index + 1} of ${total}`} />
    <div className="learning-title-row"><h1>{content.title}</h1><Button variant="quiet" className="learning-exit" onClick={onClose}>Back to tasks</Button></div>
    {!terminal && stage === "review" ? <>
      <div className="spread"><p className="muted">Take a moment to learn each word.</p><span className="label muted">{page + 1} / {pageCount}</span></div>
      <div className="vocabulary-learning-grid">{visibleWords.map(word => <VocabularyLearningCard key={word.learningKey ?? word.vocabularyItemId ?? word.targetText} word={word} languageCode={scene.languageCode} />)}</div>
      <div className="vocabulary-flow__actions">{page > 0 ? <Button variant="quiet" onClick={() => setPage(value => value - 1)}>Previous words</Button> : <span />}
        <Button onClick={finishReview}>{page < pageCount - 1 ? "Next words" : "Start quick quiz"}</Button></div>
    </> : null}
    {!terminal && stage === "quiz" && question ? <Card plain><div className="stack">
      <span className="label muted">Question {questionIndex + 1} of {content.questions.length}</span><h2>{question.prompt}</h2>
      <div className="choice-grid">{question.options.map(option => <button key={option.optionId} className="choice" aria-pressed={answers[question.questionId] === option.optionId} onClick={() => setAnswers(value => ({ ...value, [question.questionId]: option.optionId }))}>{answers[question.questionId] === option.optionId ? <CheckIcon size={16} /> : null}{option.label}</button>)}</div>
      <Button block disabled={!answers[question.questionId]} onClick={finishQuestion}>{questionIndex < content.questions.length - 1 ? "Next question" : "Continue"}</Button>
    </div></Card> : null}
    {!terminal && stage === "typing" && typingWord ? <Card plain><div className="stack">
      <div><span className="label muted">Optional typing practice</span><h2>Type “{typingWord.translation}”</h2><p className="muted">Word {typingIndex + 1} of {content.words.length}</p></div>
      <input className="input" aria-label={`Type ${typingWord.translation}`} value={typedAnswers[typingKey] ?? ""} onChange={event => setTypedAnswers(value => ({ ...value, [typingKey]: event.target.value }))} />
      <Button block disabled={!typedAnswers[typingKey]?.trim() || practiceSaving} onClick={() => typingIndex < content.words.length - 1 ? setTypingIndex(value => value + 1) : void submit()}>{typingIndex < content.words.length - 1 ? "Next word" : "Finish task"}</Button>
      <Button variant="quiet" block disabled={practiceSaving} onClick={() => void submit()}>Skip typing practice</Button>
    </div></Card> : null}
    {feedback ? <Feedback><p role="status">{feedback}</p></Feedback> : null}
    {practiceError ? <p role="alert">{practiceError}</p> : null}
    {terminal ? <Button block onClick={onNext}>{index < total - 1 ? "Next task" : "Back to tasks"}</Button> : null}
  </div>;
}

function GrammarLessonFlow({ task, index, total, onNext, onClose }: { task: SessionTask; index: number; total: number; onNext: () => void; onClose: () => void }) {
  const { actOnTask, practiceSaving, practiceError } = useAppState();
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<string | null>(null);
  const requestKey = useRef(crypto.randomUUID());
  const content = task.publicContent;
  if (content.kind !== "grammarLesson") return null;
  const terminal = taskDone(task);
  const answered = content.questions.every(question => answers[question.questionId]);
  const submit = async () => {
    const result = await actOnTask(task.id, "attempts", { inputMode: "vocabularyReview", answers, typedAnswers: {} }, requestKey.current);
    if (result) setFeedback(result.attempt?.feedback?.message ?? "Grammar practice saved.");
  };
  return <div className="stack vocabulary-flow">
    <ProgressTrail value={index + 1} total={total} label={`Task ${index + 1} of ${total}`} />
    <div className="learning-title-row"><h1>{content.title}</h1><Button variant="quiet" className="learning-exit" onClick={onClose}>Back to tasks</Button></div>
    <div className="panel-note">{content.explanation}</div>
    {content.questions.map((question, position) => <Card key={question.questionId} plain><div className="stack">
      <span className="label muted">Question {position + 1} of {content.questions.length}</span>
      <h2>{question.prompt}</h2>
      {question.translation ? <p className="muted">{question.translation}</p> : null}
      <div className="choice-grid">{question.options.map(option => <button key={option.optionId} className="choice" aria-pressed={answers[question.questionId] === option.optionId} disabled={terminal || practiceSaving}
        onClick={() => setAnswers(value => ({ ...value, [question.questionId]: option.optionId }))}>{answers[question.questionId] === option.optionId ? <CheckIcon size={16} /> : null}{option.label}</button>)}</div>
    </div></Card>)}
    {feedback ? <Feedback><p role="status">{feedback}</p></Feedback> : null}
    {practiceError ? <p role="alert">{practiceError}</p> : null}
    {terminal ? <Button block onClick={onNext}>{index < total - 1 ? "Next task" : "Back to tasks"}</Button> : <>
      <Button block disabled={!answered || practiceSaving} onClick={() => void submit()}>Submit answers</Button>
      <Button variant="quiet" block disabled={practiceSaving} onClick={async () => { if (await actOnTask(task.id, "skip")) onNext(); }}>Skip task</Button>
    </>}
  </div>;
}

function VocabularyLearningCard({ word, languageCode }: { word: VocabularyLearningWord; languageCode: string }) {
  return <article className="flashcard learning-card vocabulary-learning-card">
    <div className="spread"><span className="label muted learning-card__meta">{word.termType === "relationship" ? "relationship" : word.partOfSpeech}{word.gender ? ` · ${word.gender}` : ""}</span>
      <IconButton className="learning-card__audio" label={`Hear ${word.targetText}`} onClick={() => speak(word.targetText, languageCode)}><SpeakerIcon /></IconButton></div>
    <div className="learning-card__word"><h2>{word.targetText}</h2><p className="muted">{word.translation}</p></div>
    {word.pluralForm ? <p className="small"><strong>Plural:</strong> {word.pluralForm}</p> : null}
    {word.exampleSentence ? <div className="learning-example"><strong className="small">{word.exampleSentence}</strong></div> : null}
  </article>;
}
