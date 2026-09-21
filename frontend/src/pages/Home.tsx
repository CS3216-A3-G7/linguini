import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Card, ProgressTrail } from "../components/ui";
import { BookIcon, ChevronRightIcon, PlusIcon } from "../components/icons";
import { SceneImage } from "../components/SceneImage";
import { getActivePractice, getHomeSummary } from "../lib/api";
import { sessionDestination } from "../lib/sessionRoute";
import { queryError, queryKeys } from "../lib/queryKeys";
import { useAppState } from "../state/useAppState";

export function Home() {
  const navigate = useNavigate();
  const { learner, activeProfile } = useAppState();
  const queryClient = useQueryClient();
  const profileId = activeProfile?.id ?? "";
  const { data: home, error: homeQueryError, isPending: homeLoading } = useQuery({
    queryKey: queryKeys.home(profileId),
    queryFn: ({ signal }) => getHomeSummary(signal),
    staleTime: 60_000,
  });
  const homeError = queryError(homeQueryError);
  const [continueError, setContinueError] = useState<string | null>(null);
  const resume = home?.activeSession ?? null;
  const hasSessionToContinue = Boolean(resume);
  const continuePractice = async () => {
    setContinueError(null);
    try {
      const fresh = await queryClient.fetchQuery({
        queryKey: queryKeys.activeSession(profileId),
        queryFn: () => getActivePractice(),
        staleTime: 0,
      });
      if (!fresh) { queryClient.setQueryData(queryKeys.activeSession(profileId), null); return; }
      navigate(sessionDestination(fresh).path);
    } catch (reason) { setContinueError(reason instanceof Error ? reason.message : "Unable to load your practice."); }
  };

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
        {home ? <p>{home.xp} XP earned</p> : null}
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

      {(home?.vocabularyCount ?? 0) > 0 ? <Button variant="quiet" className="home-action-row home-action-row--journal" onClick={() => navigate("/journal/new")}>
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
        {homeLoading ? <p role="status">Loading your practice...</p> : homeError ? (
          <p role="alert">{homeError} Reload to retry.</p>
        ) : resume ? (
          <Card className="home-featured">
            <div className="home-featured__image"><SceneImage scene={{ imageUrl: resume.imageUrl, title: resume.title }} /></div>
            <div className="home-featured__body">
              <div className="stack-2">
                <h3>Continue learning</h3>
                <p>{resume.title}</p>
              </div>
              {resume.totalTaskCount > 0 ? <ProgressTrail
                value={resume.completedTaskCount}
                total={resume.totalTaskCount}
                label={`${resume.completedTaskCount} of ${resume.totalTaskCount} tasks complete`}
              /> : null}
              {continueError ? <p role="alert">{continueError}</p> : null}
              <Button block onClick={() => void continuePractice()}>
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
        {homeLoading ? <p role="status">Loading your words...</p> : homeError ? (
          <p role="alert">{homeError} Reload to retry.</p>
        ) : <p>{home?.vocabularyCount ? `${home.vocabularyCount} words collected` : "Your words will appear here as you practise."}</p>}
        <Button variant="secondary" onClick={() => navigate("/vocabulary")}>
          <BookIcon size={20} /> Explore your words
        </Button>
      </section>

    </div>
  );
}
