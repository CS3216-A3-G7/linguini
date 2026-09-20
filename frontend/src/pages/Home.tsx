import { useNavigate } from "react-router-dom";
import { Button, Card, ProgressTrail } from "../components/ui";
import { BookIcon, ChevronRightIcon, PlusIcon } from "../components/icons";
import { MediaImage } from "../components/MediaImage";
import { useAppState } from "../state/useAppState";

export function Home() {
  const navigate = useNavigate();
  const { learner, progress, progressLoading, progressError, scenes,
    vocabulary, vocabularyLoading, vocabularyError } = useAppState();
  const resume = progress?.scenarios.find((item) => item.status === "in-progress");
  const resumeScene = scenes.find((scene) => scene.id === resume?.sceneId);
  const hasSessionToContinue = Boolean(resume);

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
      <section className="home-streak" aria-label="Your learning goal">
        <div className="home-streak__heading">
          <strong>Your daily goal</strong>
          <span>{learner.dailyMinutes ? `${learner.dailyMinutes} minutes` : "Not set"}</span>
        </div>
        <p>Learning {learner.language}</p>
        {progress ? <p>{progress.xp} XP earned</p> : null}
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

      {vocabulary.length > 0 ? <Button variant="quiet" className="home-action-row home-action-row--journal" onClick={() => navigate("/journal/new")}>
        <span className="home-action-row__icon home-action-row__icon--teal">
          <BookIcon size={20} />
        </span>
        <span className="home-action-row__copy">
          <strong>Write a journal entry</strong>
          <small>Use your recent words in a short reflection</small>
        </span>
        <ChevronRightIcon />
      </Button> : null}
        </div>

      <section className="home-plan" aria-labelledby="home-plan-title">
        <h2 id="home-plan-title">Today&apos;s plan</h2>
        {progressLoading ? <p role="status">Loading your practice...</p> : progressError ? (
          <p role="alert">{progressError} Reload to retry.</p>
        ) : resume ? (
          <Card className="home-featured">
            <div className="home-featured__image"><MediaImage assetId={resume.mediaAssetId} title={resume.title} imageUrl={resumeScene?.imageUrl} /></div>
            <div className="home-featured__body">
              <div className="stack-2">
                <h3>Continue learning</h3>
                <p>{resume.title}</p>
              </div>
              <ProgressTrail
                value={resume.completedTaskCount}
                total={resume.totalTaskCount}
                label={`${resume.completedTaskCount} of ${resume.totalTaskCount} tasks complete`}
              />
              <Button block onClick={() => navigate(`/practice/sessions/${resume.sessionId}/learn`)}>
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
      <section className="stack-2" aria-labelledby="home-word-bank">
        <h2 id="home-word-bank">Your word bank</h2>
        {vocabularyLoading ? <p role="status">Loading your words...</p> : vocabularyError ? (
          <p role="alert">{vocabularyError} Reload to retry.</p>
        ) : <p>{vocabulary.length ? `${vocabulary.length} words collected` : "Your words will appear here as you practise."}</p>}
        <Button variant="secondary" onClick={() => navigate("/vocabulary")}>
          <BookIcon size={20} /> Explore your words
        </Button>
      </section>

    </div>
  );
}
