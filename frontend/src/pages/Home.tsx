import { useState } from "react";
import type { CSSProperties } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Card } from "../components/ui";
import { BookIcon, ChevronRightIcon, PlusIcon } from "../components/icons";
import { MediaImage } from "../components/MediaImage";
import { getActivePractice } from "../lib/api";
import { sessionDestination } from "../lib/sessionRoute";
import { friendlyError, queryError, queryKeys } from "../lib/queryKeys";
import { useAppState } from "../state/useAppState";
import { useVocabularyQuery } from "../state/queries";

function dayLabel(date: string) {
  return new Intl.DateTimeFormat(undefined, { weekday: "narrow" }).format(new Date(`${date}T12:00:00`));
}

function TaskProgressBadge({ completed, total }: { completed: number; total: number }) {
  const percentage = total === 0 ? 0 : Math.min(100, Math.round((completed / total) * 100));
  return (
    <div className="home-task-progress" style={{ "--home-progress": `${percentage * 3.6}deg` } as CSSProperties} aria-label={`${completed} of ${total} tasks complete`}>
      <strong>{completed}/{total}</strong>
      <span>tasks</span>
    </div>
  );
}

export function Home() {
  const navigate = useNavigate();
  const { learner, activeProfile, progress, progressLoading, progressError } = useAppState();
  const { vocabulary, vocabularyLoading, vocabularyError } = useVocabularyQuery();
  const collected = vocabularyLoading || vocabularyError ? null : vocabulary.length;
  const mastered = vocabularyLoading || vocabularyError ? null : vocabulary.filter(word => word.status === "mastered").length;
  const scenes = progressLoading || progressError ? null : progress?.scenarios.length ?? 0;
  const marks = (count: number | null, symbol: string) => Array.from(
    { length: 5 },
    (_, index) => <span key={index} className={count !== null && index < Math.min(5, Math.ceil(count / 5)) ? "is-filled" : ""}>{symbol}</span>,
  );
  const queryClient = useQueryClient();
  const profileId = activeProfile?.id ?? "";
  const { data: resume, error: resumeQueryError, isPending: resumeLoading } = useQuery({
    queryKey: queryKeys.activeSession(profileId),
    queryFn: () => getActivePractice(),
  });
  const resumeError = queryError(resumeQueryError);
  const [continueError, setContinueError] = useState<string | null>(null);
  const streak = progress?.streak;

  const continuePractice = async () => {
    setContinueError(null);
    try {
      const fresh = await queryClient.fetchQuery({
        queryKey: queryKeys.activeSession(profileId),
        queryFn: () => getActivePractice(),
        staleTime: 0,
      });
      if (!fresh) {
        queryClient.setQueryData(queryKeys.activeSession(profileId), null);
        return;
      }
      navigate(sessionDestination(fresh).path);
    } catch (reason) {
      setContinueError(friendlyError(reason));
    }
  };

  return (
    <div className="home stack">
      <section className="home-welcome-card" aria-labelledby="home-welcome-title">
        <div className="home-welcome">
          <img className="mascot" src="/linguini-logo.png" width={120} height={120} alt="Linguini mascot" />
          <div>
            <h1 id="home-welcome-title">Welcome back, {learner.name}</h1>
            <p>Every place has a few new words waiting for you.</p>
          </div>
        </div>
        <div className="home-streak" aria-label="Your seven day learning streak">
          <div className="home-streak__heading">
            <strong>Current streak</strong>
            <span>{streak?.current ?? 0} {streak?.current === 1 ? "day" : "days"}</span>
          </div>
          {progressLoading ? <p role="status">Loading your streak…</p> : progressError ? null : (
            <ol className="home-streak__week">
              {streak?.days.map((day, index) => (
                <li key={day.date} className={`home-streak__day${day.active ? " home-streak__day--checked" : ""}${index === streak.days.length - 1 ? " home-streak__day--today" : ""}`}>
                  <img className="home-streak__farfalle" src="/pasta-assets/farfalle.png" alt="" />
                  <span>{dayLabel(day.date)}</span>
                </li>
              ))}
            </ol>
          )}
        </div>
      </section>

      <section className="home-plan" aria-labelledby="home-plan-title">
        <h2 id="home-plan-title">Today&apos;s plan</h2>
        {progressLoading || resumeLoading ? <p role="status">Loading your practice...</p> : progressError || resumeError ? (
          <p role="alert">{progressError ?? resumeError} Reload to retry.</p>
        ) : resume ? (
          <Card className="home-featured">
            <div className="home-featured__image">
              <MediaImage assetId={resume.session.sceneMediaAssetId} title={resume.title} />
              {resume.progress.totalTaskCount > 0 ? <TaskProgressBadge completed={resume.progress.completedTaskCount} total={resume.progress.totalTaskCount} /> : null}
            </div>
            <div className="home-featured__body">
              <div className="stack-2">
                <h3>Continue learning</h3>
                <p>{resume.title}</p>
              </div>
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

      <section className="home-quick-actions" aria-label="Quick actions">
        <Button variant="quiet" className="home-action-row home-action-row--new-practice" onClick={() => navigate("/practice")}>
          <span className="home-action-row__icon home-action-row__icon--pasta"><PlusIcon size={20} /></span>
          <span className="home-action-row__copy"><strong>Find more words</strong><small>Use a new photo or ready scene</small></span>
          <ChevronRightIcon />
        </Button>
        <Button variant="quiet" className="home-action-row home-action-row--journal" onClick={() => navigate("/journal/new")}>
          <span className="home-action-row__icon home-action-row__icon--teal"><BookIcon size={20} /></span>
          <span className="home-action-row__copy"><strong>Write a journal entry</strong><small>Use your recent words in a reflection</small></span>
          <ChevronRightIcon />
        </Button>
      </section>

      <section className="home-journey" aria-label="Your learning journey">
        <div className="home-journey__heading"><div><h2>Your learning journey</h2><p>Every small step adds up.</p></div><strong>{progressLoading || progressError ? "--" : progress?.xp ?? 0} XP</strong></div>
        <div className="home-journey__milestones">
          <div><span className="home-journey__marks" aria-hidden="true">{marks(collected, "●")}</span><strong>{collected ?? "--"} words collected</strong></div>
          <div><span className="home-journey__marks" aria-hidden="true">{marks(mastered, "★")}</span><strong>{mastered ?? "--"} words mastered</strong></div>
          <div><span className="home-journey__marks" aria-hidden="true">{marks(scenes, "▣")}</span><strong>{scenes ?? "--"} scenes explored</strong></div>
        </div>
      </section>

      <section className="home-word-bank" aria-label="Vocabulary">
        <Button variant="secondary" onClick={() => navigate("/vocabulary")}>
          <BookIcon size={20} /> Explore your words
        </Button>
      </section>
    </div>
  );
}
