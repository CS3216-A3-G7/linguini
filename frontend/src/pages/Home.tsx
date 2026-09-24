import { useState } from "react";
import type { CSSProperties } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Card } from "../components/ui";
import { BookIcon, CameraIcon, ChevronRightIcon, JournalIcon } from "../components/icons";
import { MediaImage } from "../components/MediaImage";
import { getActivePractice } from "../lib/api";
import { sessionDestination } from "../lib/sessionRoute";
import { friendlyError, queryError, queryKeys } from "../lib/queryKeys";
import { useAppState } from "../state/useAppState";
import { useVocabularyQuery } from "../state/queries";

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function dayLabel(date: string) {
  return new Intl.DateTimeFormat(undefined, { weekday: "short" }).format(new Date(`${date}T12:00:00`));
}

function TaskProgressRing({ completed, total }: { completed: number; total: number }) {
  const percentage = total === 0 ? 0 : Math.min(100, Math.round((completed / total) * 100));
  return (
    <div className="home-task-progress">
      <div
        className="home-task-progress__ring"
        style={{ "--home-progress": `${percentage * 3.6}deg` } as CSSProperties}
        role="img"
        aria-label={`${completed} of ${total} tasks complete`}
      >
        <strong aria-hidden="true">{percentage}%</strong>
      </div>
      <span className="home-task-progress__caption">{completed} of {total} tasks</span>
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
  const activeDays = streak?.days.filter(day => day.active).length ?? 0;
  const streakCaption = streak
    ? activeDays === streak.days.length
      ? "Perfect week!"
      : streak.days[streak.days.length - 1]?.active
        ? "Keep it going!"
        : "Check in today"
    : "";

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
      <header className="home-greeting">
        <img src="/linguini-logo.png" width={64} height={64} alt="" />
        <div>
          <h1>{greeting()}, {learner.name || "friend"}!</h1>
          <p>Small moments lead to big conversations.</p>
        </div>
      </header>

      <section className="home-streak" aria-label="Your seven day learning streak">
        <h2>Your {streak?.days.length ?? 7}-day streak</h2>
        {progressLoading ? <p role="status">Loading your streak…</p> : progressError ? null : (
          <div className="home-streak__body">
            <ol className="home-streak__week">
              {streak?.days.map((day, index) => (
                <li key={day.date} className={`home-streak__day${day.active ? " home-streak__day--checked" : ""}${index === streak.days.length - 1 ? " home-streak__day--today" : ""}`}>
                  <img className="home-streak__farfalle" src="/pasta-assets/farfalle.png" alt="" />
                  <span>{dayLabel(day.date)}</span>
                </li>
              ))}
            </ol>
            <div className="home-streak__count">
              <strong>{activeDays}<span> / {streak?.days.length ?? 7}</span></strong>
              <span className="home-streak__caption">{streakCaption}</span>
            </div>
          </div>
        )}
      </section>

      <section className="home-plan" aria-label="Today's plan">
        {progressLoading || resumeLoading ? <p role="status">Loading your practice...</p> : progressError || resumeError ? (
          <p role="alert">{progressError ?? resumeError} Reload to retry.</p>
        ) : resume ? (
          <Card className="home-featured home-featured--resume">
            <div className="home-featured__image">
              <MediaImage assetId={resume.session.sceneMediaAssetId} title={resume.title} />
              <span className="home-featured__pill">Featured plan</span>
            </div>
            <div className="home-featured__body">
              {learner.language ? <p className="home-featured__eyebrow">{learner.language}</p> : null}
              <h3>{resume.title}</h3>
              <p className="home-featured__description">{resume.session.sessionSummary ?? "Pick up where you left off."}</p>
              {resume.progress.totalTaskCount > 0 ? <TaskProgressRing completed={resume.progress.completedTaskCount} total={resume.progress.totalTaskCount} /> : null}
              {continueError ? <p role="alert">{continueError}</p> : null}
              <Button block onClick={() => void continuePractice()}>
                Continue learning <ChevronRightIcon size={20} />
              </Button>
            </div>
          </Card>
        ) : (
          <Card className="home-featured home-featured--new">
            <div className="home-featured__body">
              <h3>Turn a place into a lesson</h3>
              <p className="home-featured__description">Choose a photo or one of our ready-made scenes.</p>
              <Button block onClick={() => navigate("/practice")}>
                Begin a new practice <ChevronRightIcon size={20} />
              </Button>
            </div>
          </Card>
        )}
      </section>

      <section className="home-tiles" aria-labelledby="home-tiles-title">
        <h2 id="home-tiles-title">More ways to learn</h2>
        <div className="home-tiles__grid">
          <Button variant="quiet" className="home-tile" onClick={() => navigate("/practice")}>
            <CameraIcon size={28} />
            <span>Capture a scene</span>
          </Button>
          <Button variant="quiet" className="home-tile" onClick={() => navigate("/journal")}>
            <JournalIcon size={28} />
            <span>My journal</span>
          </Button>
          <Button variant="quiet" className="home-tile" onClick={() => navigate("/vocabulary")}>
            <BookIcon size={28} />
            <span>Review words</span>
          </Button>
        </div>
      </section>

      <section className="home-journey" aria-label="Your learning journey">
        <div className="home-journey__heading"><div><h2>Your learning journey</h2><p>Every small step adds up.</p></div><strong>{progressLoading || progressError ? "--" : progress?.xp ?? 0} XP</strong></div>
        <div className="home-journey__milestones">
          <div><span className="home-journey__marks" aria-hidden="true">{marks(collected, "●")}</span><strong>{collected ?? "--"} words collected</strong></div>
          <div><span className="home-journey__marks" aria-hidden="true">{marks(mastered, "★")}</span><strong>{mastered ?? "--"} words mastered</strong></div>
          <div><span className="home-journey__marks" aria-hidden="true">{marks(scenes, "▣")}</span><strong>{scenes ?? "--"} scenes explored</strong></div>
        </div>
      </section>
    </div>
  );
}
