import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card } from "../components/ui";
import { languages } from "../config/languages";
import { useAppState } from "../state/useAppState";

export function ProfileEdit() {
  const navigate = useNavigate();
  const { learner, activeProfile, saveProfileSettings, profileSaving, profileError } = useAppState();
  const [name, setName] = useState(learner.name);
  const [language, setLanguageDraft] = useState(learner.languageCode || "es");
  const [dailyMinutes, setDailyMinutes] = useState(learner.dailyMinutes ?? 10);
  const [practicePreference, setPracticePreference] = useState(activeProfile?.preferredInputMode ?? "both");
  const [micOn, setMicOn] = useState(learner.micOn);
  const [cameraOn, setCameraOn] = useState(learner.cameraOn);

  const saveProfile = async () => {
    if (profileSaving || !name.trim()) return;
    const saved = await saveProfileSettings(language, {
      displayName: name.trim(), microphoneEnabled: micOn, cameraEnabled: cameraOn,
    }, { dailyGoalMinutes: dailyMinutes, preferredInputMode: practicePreference });
    if (saved) navigate("/profile");
  };

  return (
    <div className="stack profile-page profile-edit-page">
      <div>
        <h1>Edit profile</h1>
        <p className="small muted">Make Linguini feel like your learning space.</p>
      </div>

      <section className="profile-section">
        <h2>About you</h2>
        <Card plain className="profile-edit-card">
          <label className="profile-edit-field">
            <span>Name</span>
            <input maxLength={100} disabled={profileSaving} value={name} onChange={(event) => setName(event.target.value)} />
          </label>
        </Card>
      </section>

      <section className="profile-section">
        <h2>Learning setup</h2>
        <Card plain className="profile-settings-card">
          <label className="profile-setting">
            <span><strong>Target language</strong><small>The language you are learning</small></span>
            <select disabled={profileSaving} value={language} onChange={(event) => setLanguageDraft(event.target.value)}>
              {languages.map((option) => (
                <option key={option.code} value={option.code}>{option.flag} {option.name}</option>
              ))}
            </select>
          </label>
          <label className="profile-setting">
            <span><strong>Daily goal</strong><small>Time set aside each day</small></span>
            <select
              disabled={profileSaving}
              value={dailyMinutes}
              onChange={(event) => setDailyMinutes(Number(event.target.value))}
            >
              {[...new Set([5, 10, 15, 20, dailyMinutes])].sort((a, b) => a - b).map((minutes) => (
                <option key={minutes} value={minutes}>{minutes} min</option>
              ))}
            </select>
          </label>
          <label className="profile-setting">
            <span><strong>Practice preference</strong><small>How you prefer to respond</small></span>
            <select
              disabled={profileSaving}
              value={practicePreference}
              onChange={(event) => setPracticePreference(event.target.value as "speech" | "text" | "both")}
            >
              <option value="both">Both</option>
              <option value="speech">Speaking</option>
              <option value="text">Typing</option>
            </select>
          </label>
        </Card>
      </section>

      <section className="profile-section">
        <h2>Permissions</h2>
        <Card plain className="profile-settings-card">
          <label className="profile-setting">
            <span><strong>Microphone</strong><small>Used for pronunciation practice</small></span>
            <input type="checkbox" disabled={profileSaving} checked={micOn} onChange={(event) => setMicOn(event.target.checked)} />
          </label>
          <label className="profile-setting">
            <span><strong>Camera</strong><small>Used to capture scenes for learning</small></span>
            <input type="checkbox" disabled={profileSaving} checked={cameraOn} onChange={(event) => setCameraOn(event.target.checked)} />
          </label>
        </Card>
      </section>

      {profileError ? <p role="alert">{profileError} Your changes are still here.</p> : null}
      {profileSaving ? <p role="status">Saving profile...</p> : null}
      <Button block disabled={profileSaving || !name.trim()} onClick={() => void saveProfile()}>Save changes</Button>
    </div>
  );
}
