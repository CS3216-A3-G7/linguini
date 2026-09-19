import { useEffect, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { Button, IconButton, ProgressTrail } from "../components/ui";
import { ArrowRightIcon, CloseIcon, SpeakerIcon } from "../components/icons";
import { getScene } from "../data/mock";
import { speak } from "../lib/speech";
import { useAppState } from "../state/useAppState";

type CardPosition = {
  taskId: string;
  index: number;
};

export function LearningTaskPage() {
  const navigate = useNavigate();
  const { sceneId, taskId } = useParams();
  const scene = getScene(sceneId);
  const { session, ensureSession, completeTask } = useAppState();
  const taskIndex = scene.tasks.findIndex((task) => task.id === taskId);
  const task = scene.tasks[taskIndex];
  const [position, setPosition] = useState<CardPosition>({ taskId: taskId ?? "", index: 0 });

  useEffect(() => {
    ensureSession(scene.id);
  }, [scene.id, ensureSession]);

  if (!task) return <Navigate to={`/practice/${scene.id}/learn`} replace />;

  const items = scene.items.filter((item) => task.itemIds.includes(item.id));
  const cardIndex = position.taskId === task.id ? position.index : 0;
  const card = items[cardIndex];
  const nextTask = scene.tasks[taskIndex + 1];
  const isComplete = session.completedTaskIds.includes(task.id);
  const isLastCard = cardIndex >= items.length - 1;

  const nextCard = () => {
    setPosition({ taskId: task.id, index: cardIndex + 1 });
  };

  const finishTask = () => {
    completeTask(task.id, task.xp);
    if (nextTask) {
      navigate(`/practice/${scene.id}/learn/${nextTask.id}`);
      return;
    }
    navigate(`/practice/${scene.id}/learn`);
  };

  const finishLabel = nextTask
    ? isComplete
      ? "Next task"
      : `Complete task`
    : isComplete
      ? "Back to tasks"
      : `Finish tasks`;

  return (
    <div className="stack learning-task-page">
      <ProgressTrail
        value={taskIndex + 1}
        total={scene.tasks.length}
        label={`Task ${taskIndex + 1} of ${scene.tasks.length}`}
      />

      <div className="stack-2">
        <div className="learning-title-row">
          <h1>{task.title}</h1>
          <Button variant="quiet" className="learning-exit" onClick={() => navigate("/home")}> 
            <CloseIcon size={18} /> Exit
          </Button>
        </div>
        <p className="muted">{task.summary}</p>
      </div>

      {task.note ? <div className="panel-note">{task.note}</div> : null}

      {card ? (
        <article className="flashcard learning-card">
          <div className="spread">
            <span className="label muted learning-card__meta">
              {card.wordClass}
              {card.gender ? ` · ${card.gender}` : ""}
            </span>
            <IconButton
              className="learning-card__audio"
              label={`Hear ${card.word}`}
              onClick={() => speak(card.word)}
            >
              <SpeakerIcon size={26} />
            </IconButton>
          </div>

          <div className="learning-card__word">
            <h2>{card.word}</h2>
            <p className="muted">{card.translation}</p>
          </div>

          <div className="learning-example">
            <strong>{card.example}</strong>
            <span className="small muted">{card.exampleTranslation}</span>
          </div>

          <span className="learning-card__position">
            Word {cardIndex + 1} of {items.length}
          </span>
        </article>
      ) : (
        <div className="panel-note">This task does not have any words yet.</div>
      )}

      {!isLastCard && card ? (
        <Button block onClick={nextCard}>
          Next word <ArrowRightIcon />
        </Button>
      ) : (
        <Button block onClick={finishTask}>
          {finishLabel} <ArrowRightIcon />
        </Button>
      )}

      <Button
        variant="quiet"
        className="learning-task-page__all-tasks"
        onClick={() => navigate(`/practice/${scene.id}/learn`)}
      >
        Back to tasks
      </Button>
    </div>
  );
}
