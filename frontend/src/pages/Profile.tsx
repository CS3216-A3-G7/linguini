import { useNavigate } from "react-router-dom";
import { Button, Card } from "../components/ui";
import { useAppState } from "../state/useAppState";

const avatars = [
  { id: "farfalle", label: "Farfalle", src: "/pasta-assets/farfalle.png" },
  { id: "penne", label: "Penne", src: "/pasta-assets/penne.png" },
  { id: "fusilli", label: "Fusilli", src: "/pasta-assets/fusilli.png" },
  { id: "macaroni", label: "Macaroni", src: "/pasta-assets/macaroni.png" },
];

export function Profile() {
  const navigate = useNavigate();
  const { learner, vocabulary, journal, session } = useAppState();
  const selectedAvatar = avatars.find((option) => option.id === learner.avatar) ?? avatars[0];

  const weeklyProgress = [
    { value: Math.min(vocabulary.length, 4), label: "Words" },
    {
      value: Math.min(vocabulary.filter((word) => word.status === "mastered").length, 1),
      label: "Mastered",
    },
    { value: session.completedTaskIds.length, label: "Tasks" },
    { value: Math.min(journal.length, 1), label: "Journals" },
  ];

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
          <img src={selectedAvatar.src} alt={`${selectedAvatar.label} pasta avatar`} />
        </span>
        <span className="profile-identity__details">
          <h3>{learner.name}</h3>
          <span>Joined September 2026</span>
          <small>Edit profile</small>
        </span>
       
      </button>

      <div className="profile-streak-card">
        <span>Max streak</span>
        <strong>{learner.streak} days</strong>
      </div>

      <section className="profile-section">
        <div className="profile-section__heading">
          <h2>This week</h2>
         
        </div>
        <div className="profile-progress-grid">
          {weeklyProgress.map((metric) => (
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
            <b>{learner.dailyMinutes} min</b>
          </div>

          <div className="profile-setting">
            <span>
              <strong>Practice preference</strong>
              <small>How you prefer to respond</small>
            </span>
            <b>{learner.practicePreference}</b>
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
        Log out
      </Button>
    </div>
  );
}
