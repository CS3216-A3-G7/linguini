import { useNavigate } from "react-router-dom";
import { Button, Card, ProgressTrail } from "../components/ui";
import { BookIcon, ChevronRightIcon, PlusIcon } from "../components/icons";
import { SceneVisual } from "../components/SceneVisual";
import { getScene } from "../data/mock";
import { useAppState } from "../state/useAppState";

const WEEK_DAYS = ["M", "T", "W", "T", "F", "S", "S"];

export function Home() {
  const navigate = useNavigate();
  const { learner, session } = useAppState();
  const sessionScene = getScene(session.sceneId);
  const hasPracticeActivity =
    session.analysisScored || session.completedTaskIds.length > 0 || session.roundsPlayed > 0;
  const sessionIsComplete =
    session.completedTaskIds.length === sessionScene.tasks.length &&
    session.roundsPlayed >= sessionScene.rounds.length + sessionScene.prompts.length;
  const hasSessionToContinue = hasPracticeActivity && !sessionIsComplete;
  const completedDays = Math.min(learner.streak, WEEK_DAYS.length);

  return (
    <div className="home stack">
      <section className="home-welcome">
        <img
          className="mascot"
          src="/linguini-logo.png"
          width={120}
          height={120}
          alt="Linguini mascot"
        />
        <div>
          <h1>Welcome back, {learner.name}</h1>
          <p>Every place has a few new words waiting for you.</p>
        </div>
      </section>

      <div className="home-dashboard">
        <div className="home-dashboard__left">
      <section className="home-streak" aria-label={`${learner.streak}-day learning streak`}>
        <div className="home-streak__heading">
          <strong>This week</strong>
          <span>{completedDays} days active</span>
        </div>
        <ol className="home-streak__week" aria-label={`${learner.streak}-day learning streak this week`}>
          {WEEK_DAYS.map((day, index) => {
            const checkedIn = index < completedDays;
            const isToday = index === completedDays - 1;
            return (
              <li
                className={`home-streak__day${checkedIn ? " home-streak__day--checked" : ""}${isToday ? " home-streak__day--today" : ""}`}
                key={`${day}-${index}`}
              >
                <img
                  className="home-streak__farfalle"
                  src="/pasta-assets/farfalle.png"
                  alt=""
                />
                <span>{day}</span>
              </li>
            );
          })}
        </ol>
      </section>

      {hasSessionToContinue ? (
        <Button
          variant="quiet"
          className="home-action-row home-action-row--new-practice"
          onClick={() => navigate("/practice")}
        >
          <span className="home-action-row__icon home-action-row__icon--pasta">
            <PlusIcon size={20} />
          </span>
          <span className="home-action-row__copy">
            <strong>Find more words</strong>
            <small>Use a new photo or ready scene</small>
          </span>
          <ChevronRightIcon />
        </Button>
      ) : null}

      <Button variant="quiet" className="home-action-row home-action-row--journal" onClick={() => navigate("/journal/new")}>
        <span className="home-action-row__icon home-action-row__icon--teal">
          <BookIcon size={20} />
        </span>
        <span className="home-action-row__copy">
          <strong>Write a journal entry</strong>
          <small>Use your recent words in a short reflection</small>
        </span>
        <ChevronRightIcon />
      </Button>
        </div>

      <section className="home-plan" aria-labelledby="home-plan-title">
        <h2 id="home-plan-title">Today&apos;s plan</h2>
        {hasSessionToContinue ? (
          <Card className="home-featured">
            <SceneVisual scene={sessionScene} className="home-featured__image" />
            <div className="home-featured__body">
              <div className="stack-2">
                <h3>Continue learning</h3>
                <p>{sessionScene.title}</p>
              </div>
              <ProgressTrail
                value={session.completedTaskIds.length}
                total={sessionScene.tasks.length}
                label={`${session.completedTaskIds.length} of ${sessionScene.tasks.length} learning tasks complete`}
              />
              <Button block onClick={() => navigate(`/practice/${sessionScene.id}/learn`)}>
                Continue learning <ChevronRightIcon size={20} />
              </Button>
            </div>
          </Card>
        ) : (
          <Card className="home-featured home-featured--new">
            <div className="home-featured__body">
              <div className="stack-2">
                <h3>Turn a place into a lesson</h3>
                <p>Choose a photo or one of our ready-made scenes.</p>
              </div>
              <Button block onClick={() => navigate("/practice")}>
                Begin a new practice <ChevronRightIcon size={20} />
              </Button>
            </div>
          </Card>
        )}

      </section>
      </div>

    </div>
  );
}
