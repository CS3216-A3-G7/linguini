import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card } from "../components/ui";
import { languages } from "../data/mock";
import { useAppState } from "../state/useAppState";

const avatars = [
  { id: "farfalle", label: "Farfalle", src: "/pasta-assets/farfalle.png" },
  { id: "penne", label: "Penne", src: "/pasta-assets/penne.png" },
  { id: "fusilli", label: "Fusilli", src: "/pasta-assets/fusilli.png" },
  { id: "macaroni", label: "Macaroni", src: "/pasta-assets/macaroni.png" },
];

export function ProfileEdit() {
  const navigate = useNavigate();
  const { learner, updateLearner, setLanguage } = useAppState();
  const [name, setName] = useState(learner.name);
  const [avatar, setAvatar] = useState(learner.avatar);
  const [language, setLanguageDraft] = useState(learner.language);
  const [dailyMinutes, setDailyMinutes] = useState(learner.dailyMinutes);
  const [practicePreference, setPracticePreference] = useState(learner.practicePreference);
  const [micOn, setMicOn] = useState(learner.micOn);
  const [cameraOn, setCameraOn] = useState(learner.cameraOn);

  const saveProfile = () => {
    const selectedLanguage = languages.find((option) => option.name === language);
    updateLearner({
      name: name.trim() || learner.name,
      avatar,
      dailyMinutes,
      practicePreference,
      micOn,
      cameraOn,
    });
    if (selectedLanguage) setLanguage(selectedLanguage.name, selectedLanguage.flag);
    navigate("/profile");
  };

  return (
    <div className="stack profile-page profile-edit-page">
      <div>
        <h1>Edit profile</h1>
        <p className="small muted">Make Linguini feel like your learning space.</p>
      </div>

      <section className="profile-section">
        <h2>Your pasta</h2>
        <div className="profile-avatar-options">
          {avatars.map((option) => (
            <button
              key={option.id}
              type="button"
              className={option.id === avatar ? "is-selected" : ""}
              aria-pressed={option.id === avatar}
              onClick={() => setAvatar(option.id)}
            >
              <img src={option.src} alt="" />
              <span>{option.label}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="profile-section">
        <h2>About you</h2>
        <Card plain className="profile-edit-card">
          <label className="profile-edit-field">
            <span>Name</span>
            <input value={name} onChange={(event) => setName(event.target.value)} />
          </label>
        </Card>
      </section>

      <section className="profile-section">
        <h2>Learning setup</h2>
        <Card plain className="profile-settings-card">
          <label className="profile-setting">
            <span><strong>Target language</strong><small>The language you are learning</small></span>
            <select value={language} onChange={(event) => setLanguageDraft(event.target.value)}>
              {languages.map((option) => (
                <option key={option.code} value={option.name}>{option.flag} {option.name}</option>
              ))}
            </select>
          </label>
          <label className="profile-setting">
            <span><strong>Daily goal</strong><small>Time set aside each day</small></span>
            <select
              value={dailyMinutes}
              onChange={(event) => setDailyMinutes(Number(event.target.value))}
            >
              {[5, 10, 15, 20].map((minutes) => (
                <option key={minutes} value={minutes}>{minutes} min</option>
              ))}
            </select>
          </label>
          <label className="profile-setting">
            <span><strong>Practice preference</strong><small>How you prefer to respond</small></span>
            <select
              value={practicePreference}
              onChange={(event) => setPracticePreference(event.target.value)}
            >
              <option>Both</option>
              <option>Speaking</option>
              <option>Typing</option>
            </select>
          </label>
        </Card>
      </section>

      <section className="profile-section">
        <h2>Permissions</h2>
        <Card plain className="profile-settings-card">
          <label className="profile-setting">
            <span><strong>Microphone</strong><small>Used for pronunciation practice</small></span>
            <input type="checkbox" checked={micOn} onChange={(event) => setMicOn(event.target.checked)} />
          </label>
          <label className="profile-setting">
            <span><strong>Camera</strong><small>Used to capture scenes for learning</small></span>
            <input type="checkbox" checked={cameraOn} onChange={(event) => setCameraOn(event.target.checked)} />
          </label>
        </Card>
      </section>

      <Button block onClick={saveProfile}>Save changes</Button>
    </div>
  );
}
