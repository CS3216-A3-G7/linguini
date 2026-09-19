import { useNavigate } from "react-router-dom";
import { Button, Card, ProgressTrail } from "../components/ui";
import { BookIcon, ChevronRightIcon, FarfalleIcon, PlusIcon } from "../components/icons";
import { SceneVisual } from "../components/SceneVisual";
import { getScene } from "../data/mock";
import { useAppState } from "../state/useAppState";

const WEEK_DAYS = ["M", "T", "W", "T", "F", "S", "S"];

export function Home() {
  const navigate = useNavigate();
  const { learner, session, vocabulary } = useAppState();
  const sessionScene = getScene(session.sceneId);
  const hasPracticeActivity =
    session.analysisScored || session.completedTaskIds.length > 0 || session.roundsPlayed > 0;
  const sessionIsComplete =
    session.completedTaskIds.length === sessionScene.tasks.length &&
    session.roundsPlayed >= sessionScene.rounds.length + sessionScene.prompts.length;
  const hasSessionToContinue = hasPracticeActivity && !sessionIsComplete;
  const hasWordsToUse = session.completedTaskIds.length > 0;
  const wordsToReview = vocabulary.filter((word) => word.status !== "mastered").slice(0, 3);
  const wordCount = vocabulary.filter((word) => word.status !== "mastered").length;
  const completedDays = Math.min(learner.streak, WEEK_DAYS.length);

  return (
    <div className="home stack" style={{ gap: "var(--space-6)" }}>
      <section className="home-streak" aria-label={`${learner.streak}-day learning streak`}>
        
        <ol className="home-streak__week" aria-label={`${learner.streak}-day learning streak this week`}>
          {WEEK_DAYS.map((day, index) => {
            const checkedIn = index < completedDays;
            const isToday = index === completedDays - 1;
            return (
              <li
                className={`home-streak__day${checkedIn ? " home-streak__day--checked" : ""}${isToday ? " home-streak__day--today" : ""}`}
                key={`${day}-${index}`}
              >
                <FarfalleIcon size={28} />
                <span>{day}</span>
              </li>
            );
          })}
        </ol>
      </section>

      <section className="home-plan" aria-labelledby="home-plan-title">
        <h2 id="home-plan-title">Today&apos;s learning</h2>
        {hasSessionToContinue ? (
          <Card lifted className="home-featured">
            <div className="stack">
              <div className="stack-2">
                <h3>Continue learning</h3>
                <p>Return to your {sessionScene.title.toLowerCase()} scene.</p>
              </div>
              <div className="row home-session-preview">
                <span className="thumb thumb--lg">
                  <SceneVisual scene={sessionScene} />
                </span>
                <div className="grow stack-2">
                  <strong>{sessionScene.title}</strong>
                  <ProgressTrail
                    value={session.completedTaskIds.length}
                    total={sessionScene.tasks.length}
                    label={`${session.completedTaskIds.length} of ${sessionScene.tasks.length} learning tasks complete`}
                  />
                </div>
              </div>
              <Button block onClick={() => navigate(`/practice/${sessionScene.id}/learn`)}>
                Continue learning <ChevronRightIcon size={20} />
              </Button>
            </div>
          </Card>
        ) : (
          <Card lifted className="home-featured">
            <div className="stack">
              <div className="stack-2">
                <h3>Start a new scene</h3>
                <p>Choose a photo or ready scene. We&apos;ll suggest useful words—you choose what to learn.</p>
              </div>
              <Button block onClick={() => navigate("/practice")}>
                Begin a new practice <ChevronRightIcon size={20} />
              </Button>
            </div>
          </Card>
        )}

        {hasSessionToContinue ? (
          <Button variant="quiet" className="home-action-row" onClick={() => navigate("/practice")}>
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
      </section>

      <section className="home-word-bank" aria-labelledby="home-word-bank-title">
        <div className="spread home-word-bank__heading">
          <div className="stack-2">
            <h2 id="home-word-bank-title">Your words</h2>
            <p className="small muted">
              {wordCount > 0 ? `${wordCount} words ready to revisit.` : "Your next scene will add words here."}
            </p>
          </div>
          <Button variant="quiet" className="home-word-bank__link" onClick={() => navigate("/vocabulary")}>
            View all <ChevronRightIcon size={18} />
          </Button>
        </div>
        {wordsToReview.length > 0 ? (
          <div className="home-word-bank__words" aria-label="Words ready to revisit">
            {wordsToReview.map((word) => (
              <span className="home-word" key={word.id}>
                <strong>{word.word}</strong>
                <span>{word.translation}</span>
              </span>
            ))}
          </div>
        ) : null}
      </section>

      {hasWordsToUse ? (
        <Button variant="quiet" className="home-action-row home-action-row--journal" onClick={() => navigate("/journal/new")}>
          <span className="home-action-row__icon home-action-row__icon--teal">
            <BookIcon size={20} />
          </span>
          <span className="home-action-row__copy">
            <strong>Write a journal</strong>
            <small>Use today&apos;s words in your own story</small>
          </span>
          <ChevronRightIcon />
        </Button>
      ) : null}

    </div>
  );
}
