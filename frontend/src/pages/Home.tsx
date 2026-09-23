import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Card, ProgressTrail } from "../components/ui";
import { BookIcon, ChevronRightIcon, PlusIcon } from "../components/icons";
import { MediaImage } from "../components/MediaImage";
import { getActivePractice } from "../lib/api";
import { sessionDestination } from "../lib/sessionRoute";
import { queryError, queryKeys } from "../lib/queryKeys";
import { useAppState } from "../state/useAppState";
import { useVocabularyQuery } from "../state/queries";

export function Home() {
  const navigate = useNavigate();
  const { learner, activeProfile, progress, progressLoading, progressError } = useAppState();
  const { vocabulary, vocabularyLoading, vocabularyError } = useVocabularyQuery();
  const collected = vocabularyLoading || vocabularyError ? null : vocabulary.length;
  const mastered = vocabularyLoading || vocabularyError ? null : vocabulary.filter(word => word.status === "mastered").length;
  const scenes = progressLoading || progressError ? null : progress?.scenarios.length ?? 0;
  const marks = (count: number | null, symbol: string) => Array.from({ length: 5 }, (_, index) => <span key={index} className={count !== null && index < Math.min(5, Math.ceil(count / 5)) ? "is-filled" : ""}>{symbol}</span>);
  const queryClient = useQueryClient();
  const profileId = activeProfile?.id ?? "";
  const { data: resume, error: resumeQueryError, isPending: resumeLoading } = useQuery({
    queryKey: queryKeys.activeSession(profileId),
    queryFn: () => getActivePractice(),
  });
  const resumeError = queryError(resumeQueryError);
  const [continueError, setContinueError] = useState<string | null>(null);
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

      {(progress?.xp ?? 0) > 0 ? <Button variant="quiet" className="home-action-row home-action-row--journal" onClick={() => navigate("/journal/new")}>
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
        {progressLoading || resumeLoading ? <p role="status">Loading your practice...</p> : progressError || resumeError ? (
          <p role="alert">{progressError ?? resumeError} Reload to retry.</p>
        ) : resume ? (
          <Card className="home-featured">
            <div className="home-featured__image"><MediaImage assetId={resume.session.sceneMediaAssetId} title={resume.title} /></div>
            <div className="home-featured__body">
              <div className="stack-2">
                <h3>Continue learning</h3>
                <p>{resume.title}</p>
              </div>
              {resume.progress.totalTaskCount > 0 ? <ProgressTrail
                value={resume.progress.completedTaskCount}
                total={resume.progress.totalTaskCount}
                label={`${resume.progress.completedTaskCount} of ${resume.progress.totalTaskCount} tasks complete`}
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
      <section className="home-journey" aria-label="Your learning journey">
        <div className="home-journey__heading"><div><h2>Your learning journey</h2><p>Every small step adds up.</p></div><strong>{progressLoading || progressError ? "--" : progress?.xp ?? 0} XP</strong></div>
        <div className="home-journey__milestones">
          <div><span className="home-journey__marks" aria-hidden="true">{marks(collected, "●")}</span><strong>{collected ?? "--"} words collected</strong></div>
          <div><span className="home-journey__marks" aria-hidden="true">{marks(mastered, "★")}</span><strong>{mastered ?? "--"} words mastered</strong></div>
          <div><span className="home-journey__marks" aria-hidden="true">{marks(scenes, "▣")}</span><strong>{scenes ?? "--"} scenes explored</strong></div>
        </div>
      </section>
      <section className="stack-2" aria-labelledby="home-word-bank">
       
        <Button variant="secondary" onClick={() => navigate("/vocabulary")}>
          <BookIcon size={20} /> Explore your words
        </Button>
      </section>

    </div>
  );
}
