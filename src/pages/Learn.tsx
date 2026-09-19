import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, XpPill } from "../components/ui";
import { ArrowRightIcon, CheckIcon } from "../components/icons";
import { ScenePhoto } from "../components/ScenePhoto";
import { getScene } from "../data/mock";
import { useAppState } from "../state/useAppState";

export function Learn() {
  const navigate = useNavigate();
  const { sceneId } = useParams();
  const scene = getScene(sceneId);
  const { session, ensureSession } = useAppState();

  useEffect(() => {
    ensureSession(scene.id);
  }, [scene.id, ensureSession]);

  const completed = session.completedTaskIds;
  const allDone = scene.tasks.every((task) => completed.includes(task.id));
  const nextTask = scene.tasks.find((task) => !completed.includes(task.id)) ?? scene.tasks[0];

  const openTask = (taskId: string) => {
    navigate(`/practice/${scene.id}/learn/${taskId}`);
  };

  return (
    <div className="stack learn-page">
      <div className="stack-2">
        <h1>Learning tasks</h1>
        <p className="muted">Build confidence with each short activity.</p>
      </div>

      <ScenePhoto scene={scene} />

      <div className="task-list" aria-label="Learning tasks">
        {scene.tasks.map((task, index) => {
          const isDone = completed.includes(task.id);
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
                <strong>{task.title}</strong>
                <span className="small muted">{task.summary}</span>
              </span>
              {isDone ? <span className="pill pill--mastered">Done</span> : <XpPill xp={task.xp} />}
            </button>
          );
        })}
      </div>

      {allDone ? (
        <Button block onClick={() => navigate(`/practice/${scene.id}/ispy-1`)}>
          Play I-Spy <ArrowRightIcon />
        </Button>
      ) : (
        <Button block onClick={() => openTask(nextTask.id)}>
          {completed.length === 0 ? "Begin tasks" : "Continue tasks"} <ArrowRightIcon />
        </Button>
      )}
    </div>
  );
}
