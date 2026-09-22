import { useNavigate } from "react-router-dom";
import { Button, Card } from "../components/ui";
import { useAppState } from "../state/useAppState";
import { useJournalsQuery, useVocabularyQuery } from "../state/queries";

export function Profile() {
  const navigate = useNavigate();
  const { learner, user, activeProfile, progress, progressLoading, progressError, profileError } = useAppState();
  const { vocabulary, vocabularyLoading, vocabularyError } = useVocabularyQuery();
  const { journal, journalLoading, journalError } = useJournalsQuery();
  const metrics = [
    { value: vocabularyLoading || vocabularyError ? "--" : vocabulary.length, label: "Words" },
    { value: vocabularyLoading || vocabularyError ? "--" : vocabulary.filter(word => word.status === "mastered").length, label: "Mastered" },
    { value: progressLoading || progressError ? "--" : progress?.scenarios.reduce((sum, scene) => sum + scene.completedTaskCount, 0) ?? 0, label: "Tasks" },
    { value: journalLoading || journalError ? "--" : journal.length, label: "Journals" },
  ];
  const preference = activeProfile ? { speech: "Speaking", text: "Typing", both: "Both" }[activeProfile.preferredInputMode] : "Not set";

  return (
    <div className="stack profile-page">
      <div className="profile-page__heading">
        <h2>Profile</h2>
      </div>

      <button
        type="button"
        className="profile-identity-card"
        aria-label="Edit profile"
        onClick={() => navigate("/profile/edit")}
      >
        <span className="profile-avatar">
          <img src="/pasta-assets/farfalle.png" alt="Farfalle pasta" />
        </span>
        <span className="profile-identity__details">
          <h3>{learner.name}</h3>
          <span>{user ? `Joined ${new Date(user.createdAt).toLocaleDateString("en-GB", { month: "long", year: "numeric" })}` : ""}</span>
          <small>Edit profile</small>
        </span>

      </button>

      <div className="profile-streak-card">
        <span>Learning XP</span>
        <strong>{progressLoading || progressError ? "--" : progress?.xp ?? 0} XP</strong>
      </div>

      {progressLoading || vocabularyLoading || journalLoading ? <p role="status">Loading your progress...</p> : null}
      {[progressError, vocabularyError, journalError].filter(Boolean).map((error, index) => <p key={index} role="alert">{error} Reload to retry.</p>)}
      {profileError ? <p role="alert">{profileError}</p> : null}
      <section className="profile-section">
        <div className="profile-section__heading">
          <h2>Your progress</h2>

        </div>
        <div className="profile-progress-grid">
          {metrics.map((metric) => (
            <div key={metric.label} className="profile-progress-stat">
              <strong>{metric.value}</strong>
              <span>{metric.label}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="profile-section">
        <h2>Learning setup</h2>
        <Card plain className="profile-settings-card">
          <div className="profile-setting">
            <span>
              <strong>Target language</strong>
              <small>The language you are learning</small>
            </span>
            <b>{learner.languageFlag} {learner.language}</b>
          </div>

          <div className="profile-setting">
            <span>
              <strong>Daily goal</strong>
              <small>Time set aside each day</small>
            </span>
            <b>{learner.dailyMinutes ? `${learner.dailyMinutes} min` : "Not set"}</b>
          </div>

          <div className="profile-setting">
            <span>
              <strong>Practice preference</strong>
              <small>How you prefer to respond</small>
            </span>
            <b>{preference}</b>
          </div>
        </Card>
      </section>

      <section className="profile-section">
        <h2>Permissions</h2>
        <Card plain className="profile-settings-card">
          <div className="profile-setting">
            <span>
              <strong>Microphone</strong>
              <small>Used for pronunciation practice</small>
            </span>
            <b>{learner.micOn ? "On" : "Off"}</b>
          </div>
          <div className="profile-setting" >
            <span>
              <strong>Camera</strong>
              <small>Used to capture scenes for learning</small>
            </span>
            <b>{learner.cameraOn ? "On" : "Off"}</b>
          </div>
        </Card>
      </section>

      <aside className="profile-ai-note">
        <strong>How AI helps</strong>
        <p>
          Linguini suggests objects, vocabulary, and practice prompts from your scenes. You
          always review the suggestions and decide what to keep, change, or remove.
        </p>
      </aside>

      <Button block className="profile-logout" onClick={() => navigate("/")}>
        Back to welcome
      </Button>
    </div>
  );
}
