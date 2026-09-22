import { Navigate, useNavigate } from "react-router-dom";
import { Button, Card } from "../components/ui";
import { ArrowRightIcon, CheckIcon, CloseIcon } from "../components/icons";
import { ScenePhoto } from "../components/ScenePhoto";
import { useScene } from "../state/useScene";
import { practiceStages, taskDone, taskTitle, taskDescription } from "../lib/practiceTasks";
import { useAppState } from "../state/useAppState";

export function Learn() {
  const navigate = useNavigate();
  const scene = useScene();
  const { session, practiceSaving, practiceError } = useAppState();
  if (!session) return null;
  const base = `/practice/sessions/${scene.sessionId}`;
  if (session.session.status === "completed") return <Navigate to={`${base}/summary`} replace />;
  if (["abandoned", "failed"].includes(session.session.status)) return <div className="stack"><h1>Session closed</h1><Button onClick={() => navigate("/practice")}>Choose an image</Button></div>;
  const tasks = practiceStages(session.tasks).learning;
  const completed = tasks.filter(taskDone);
  const allDone = tasks.every(taskDone);
  const nextTask = tasks.find(task => !taskDone(task));

  const openTask = (taskId: string) => {
    navigate(`${base}/learn/${taskId}`);
  };

  return (
    <div className="stack learn-page">
      <div className="stack-2">
        <div className="learning-title-row">
          <h1>Learning tasks</h1>
          <Button variant="quiet" className="learning-exit" onClick={() => navigate("/home")}>
            <CloseIcon size={18} /> Exit
          </Button>
        </div>
        <p className="muted">Build confidence with each short activity.</p>
      </div>

      <ScenePhoto scene={scene} />
      {practiceError ? <p role="alert">{practiceError}</p> : null}

      {session.translationPreview ? (
        <Card plain className="translation-preview">
          <div>
            <h2>Translation preview</h2>
            <p className="small muted">Temporary testing view</p>
          </div>
          {([
            ["Objects", session.translationPreview.objects],
            ["Attributes", session.translationPreview.attributes],
            ["Relationships", session.translationPreview.relationships],
          ] as const).map(([label, terms]) => terms.length ? (
            <section key={label} className="translation-preview__group">
              <h3>{label}</h3>
              <div className="translation-preview__terms">
                {terms.map(term => (
                  <span className="translation-preview__term" key={term.key}>
                    <span>{term.source}</span><strong>{term.translation}</strong>
                  </span>
                ))}
              </div>
            </section>
          ) : null)}
        </Card>
      ) : null}

      <div className="task-list" aria-label="Learning tasks">
        {tasks.map((task, index) => {
          const isDone = taskDone(task);
          return (
            <button
              key={task.id}
              type="button"
              className={`task-row${isDone ? " task-row--done" : ""}`}
              onClick={() => openTask(task.id)}
            >
              <span className="task-row__index">
                {isDone ? <CheckIcon size={16} /> : index + 1}
              </span>
              <span className="grow stack-2">
                <strong>{taskTitle(task)}</strong>
                <span className="small muted">{taskDescription(task)}</span>
              </span>
              {isDone ? <span className="pill pill--mastered">{task.status === "skipped" ? "Skipped" : "Done"}</span> : <ArrowRightIcon />}
            </button>
          );
        })}
      </div>

      {allDone ? (
        <Button block disabled={practiceSaving} onClick={() => navigate(`${base}/ispy-1`)}>
          Play I-Spy <ArrowRightIcon />
        </Button>
      ) : (
        <Button block disabled={practiceSaving} onClick={() => nextTask && openTask(nextTask.id)}>
          {completed.length === 0 ? "Begin tasks" : "Continue tasks"} <ArrowRightIcon />
        </Button>
      )}

    </div>
  );
}
