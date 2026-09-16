import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Button,
  Card,
  IconButton,
  ProgressTrail,
  Sheet,
  TopBar,
  XpPill,
} from "../components/ui";
import { ArrowRightIcon, CheckIcon, SpeakerIcon } from "../components/icons";
import { ScenePhoto } from "../components/ScenePhoto";
import { getScene } from "../data/mock";
import type { LearningTask } from "../data/types";
import { speak } from "../lib/speech";
import { useAppState } from "../state/useAppState";

export function Learn() {
  const navigate = useNavigate();
  const { sceneId } = useParams();
  const scene = getScene(sceneId);
  const { session, ensureSession, completeTask } = useAppState();
  const [openTask, setOpenTask] = useState<LearningTask | null>(null);
  const [cardIndex, setCardIndex] = useState(0);

  useEffect(() => {
    ensureSession(scene.id);
  }, [scene.id, ensureSession]);

  const completed = session.completedTaskIds;
  const allDone = scene.tasks.every((task) => completed.includes(task.id));

  const open = (task: LearningTask) => {
    setOpenTask(task);
    setCardIndex(0);
  };

  const finishTask = () => {
    if (!openTask) return;
    completeTask(openTask.id, openTask.xp);
    setOpenTask(null);
  };

  const items = openTask ? scene.items.filter((item) => openTask.itemIds.includes(item.id)) : [];
  const card = items[cardIndex];

  return (
    <div className="stack">
      <TopBar
        title="Phase 1: Learn words"
        help="Finish these short tasks to unlock I-Spy."
        right={<XpPill xp={session.sessionXp} />}
      />
      <ProgressTrail
        value={completed.length}
        total={scene.tasks.length}
        label={`${completed.length} of ${scene.tasks.length} tasks done`}
      />

      <ScenePhoto scene={scene} />

      <div className="stack-2">
        <h1>Learn words and phrases</h1>
        <p className="muted">Work down the list. Each task adds XP and unlocks the game.</p>
      </div>

      <div className="stack-2">
        {scene.tasks.map((task, index) => {
          const isDone = completed.includes(task.id);
          return (
            <button
              key={task.id}
              type="button"
              className={`task-row${isDone ? " task-row--done" : ""}`}
              onClick={() => open(task)}
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

      <Button block disabled={!allDone} onClick={() => navigate(`/practice/${scene.id}/ispy-1`)}>
        Play I-Spy <ArrowRightIcon />
      </Button>
      {!allDone ? (
        <p className="small muted center-text">Clickable after completing all tasks.</p>
      ) : null}

      {openTask ? (
        <Sheet title={openTask.title} onClose={() => setOpenTask(null)}>
          <div className="stack">
            {openTask.note ? <div className="panel-note">{openTask.note}</div> : null}

            {card ? (
              <div className="flashcard">
                <div className="spread">
                  <span className="label muted">
                    {card.wordClass}
                    {card.gender ? ` · ${card.gender}` : ""}
                  </span>
                  <IconButton label={`Hear ${card.word}`} onClick={() => speak(card.word)}>
                    <SpeakerIcon />
                  </IconButton>
                </div>
                <h2>{card.word}</h2>
                <p className="muted">{card.translation}</p>
                <Card plain>
                  <div className="stack-2">
                    <strong className="small">{card.example}</strong>
                    <span className="small muted">{card.exampleTranslation}</span>
                  </div>
                </Card>
                <ProgressTrail
                  value={cardIndex + 1}
                  total={items.length}
                  label={`${cardIndex + 1} of ${items.length}`}
                />
              </div>
            ) : null}

            {cardIndex < items.length - 1 ? (
              <Button block onClick={() => setCardIndex((current) => current + 1)}>
                Next card
              </Button>
            ) : (
              <Button block onClick={finishTask}>
                {completed.includes(openTask.id) ? (
                  "Done — close"
                ) : (
                  <>
                    Mark complete <XpPill xp={openTask.xp} />
                  </>
                )}
              </Button>
            )}
          </div>
        </Sheet>
      ) : null}
    </div>
  );
}
