import { LoadingScreen } from "../components/LoadingScreen";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, Mascot, Noodle } from "../components/ui";
import { PlusIcon } from "../components/icons";
import { languages } from "../config/languages";
import { useAppState } from "../state/useAppState";
import type { LanguageProfile } from "../lib/api";

export function Profile() {
  const navigate = useNavigate();
  const { learner, languageProfiles, activateLanguageProfile, saveUser, saveLanguageProfile, profileSaving, profileError, xp, vocabulary, journal, activeProfile } = useAppState();
  const [name, setName] = useState(learner.name);
  const [goal, setGoal] = useState(learner.goal);
  const [saved, setSaved] = useState(false);
  const targetProfiles = languageProfiles.filter((profile, index, profiles) =>
    profiles.findIndex((row) => row.targetLanguageCode.toLowerCase() === profile.targetLanguageCode.toLowerCase()) === index
  );
  return (
    <div className="stack">
      <h1>Profile</h1>
      <Card lifted>
        <div className="row">
          <Mascot size={72} />
          <div className="grow stack-2">
            <h2>{learner.name}</h2>
            <span className="small muted">
              {learner.languageFlag} {learner.language} · level {learner.level}
            </span>
            <span className="pill pill--xp">{xp} XP</span>
          </div>
        </div>
      </Card>

      <div className="stat-grid">
        <div className="stat">
          <div className="stat__value">{vocabulary.length}</div>
          <span className="small muted">Words</span>
        </div>
        <div className="stat">
          <div className="stat__value">{journal.length}</div>
          <span className="small muted">Entries</span>
        </div>
        <div className="stat">
          <div className="stat__value">{learner.dailyMinutes ?? "—"}</div>
          <span className="small muted">Min / day</span>
        </div>
      </div>

      {profileSaving ? <LoadingScreen label="Saving profile…" /> : null}
      {profileError ? <p role="alert">{profileError}</p> : null}

      <div className="stack-2">
        <h2>Target language</h2>
        <div className="chip-row">
          {targetProfiles.map((profile) => {
            const code = profile.targetLanguageCode.toLowerCase();
            const option = languages.find((language) => language.code === code);
            const selected = code === learner.languageCode.toLowerCase();
            return <button key={code} type="button" disabled={profileSaving}
              className={`chip${selected ? " chip--selected" : ""}`}
              aria-pressed={selected}
              onClick={() => { if (!selected) { setSaved(false); void activateLanguageProfile(profile.id); } }}>
              {option?.flag} {option?.name ?? profile.targetLanguageCode}
            </button>;
          })}
          <button type="button" className="chip chip--static" disabled aria-label="Add target language" title="Add target language (coming soon)">
            <PlusIcon />
          </button>
        </div>
        <p className="small muted">Your selection is saved. Scenes, vocabulary, and progress follow this language. Demo content is currently available in Spanish only.</p>
      </div>

      <Card>
        <form className="stack" onSubmit={async (event) => {
          event.preventDefault();
          setSaved(await saveUser({ displayName: name.trim(), learningGoal: goal.trim() }));
        }}>
          <label className="field">Your name<input className="input" required maxLength={100} value={name} onChange={(event) => { setName(event.target.value); setSaved(false); }} /></label>
          <label className="field">Your goal<input className="input" maxLength={300} value={goal} onChange={(event) => { setGoal(event.target.value); setSaved(false); }} /></label>
          <Button disabled={profileSaving || !name.trim()} type="submit">Save profile</Button>
          {saved && !profileError ? <p role="status">Profile saved.</p> : null}
        </form>
      </Card>

      <div className="stack-2">
        <h2>Learning preferences</h2>
        <Card>
          <div className="stack">
            <label className="spread">
              Level
              <select disabled={profileSaving || !activeProfile} value={learner.level} onChange={(event) => void saveLanguageProfile({ proficiencyLevel: event.target.value as LanguageProfile["proficiencyLevel"] })}>
                {["A1", "A2", "B1", "B2", "C1", "C2"].map((level) => <option key={level}>{level}</option>)}
              </select>
            </label>
            <label className="spread">
              Daily goal
              <select disabled={profileSaving || !activeProfile} value={learner.dailyMinutes ?? ""} onChange={(event) => void saveLanguageProfile({ dailyGoalMinutes: event.target.value ? Number(event.target.value) : null })}>
                <option value="">Not set</option>
                {[...new Set([5, 10, 20, ...(learner.dailyMinutes ? [learner.dailyMinutes] : [])])].sort((a, b) => a - b).map((minutes) => <option key={minutes} value={minutes}>{minutes} min</option>)}
              </select>
            </label>
            <label className="spread">
              Microphone for speaking practice
              <input type="checkbox" disabled={profileSaving} checked={learner.micOn} onChange={(event) => void saveUser({ microphoneEnabled: event.target.checked })} />
            </label>
            <label className="spread">
              Camera for scene capture
              <input type="checkbox" disabled={profileSaving} checked={learner.cameraOn} onChange={(event) => void saveUser({ cameraEnabled: event.target.checked })} />
            </label>
            <p className="small muted">Device preferences are saved; browser permission is requested separately when needed.</p>
          </div>
        </Card>
      </div>

      <Noodle />

      <Button variant="secondary" block onClick={() => navigate("/")}>
        Log out
      </Button>
    </div>
  );
}
