import { useNavigate } from "react-router-dom";
import { Button, Card, Mascot, Noodle } from "../components/ui";
import { languages } from "../data/mock";
import { useAppState } from "../state/useAppState";

export function Profile() {
  const navigate = useNavigate();
  const { learner, setLanguage, updateLearner, xp, vocabulary, journal } = useAppState();

  return (
    <div className="stack">
      <h1>Profile</h1>

      <Card lifted>
        <div className="row">
           <img
              className="mascot"
              src="pasta-assets/farfalle.png"
              width={90}
              height={90}
              alt="Linguini mascot"
            />
            <div className="grow stack-2">
              <h2>{learner.name}</h2>
              <span className="small muted">
                {learner.languageFlag} {learner.language} · 
              </span>
              <div className="row">
                <span className="pill pill--xp">{xp} XP</span>
              </div>
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
          <div className="stat__value">{learner.dailyMinutes}</div>
          <span className="small muted">Min / day</span>
        </div>
      </div>
       <Noodle />
      <div className="stack-2">
        <h2>Target language</h2>
        <div className="chip-row">
          {languages.map((option) => (
            <button
              key={option.code}
              type="button"
              className={`chip${option.name === learner.language ? " chip--selected" : ""}`}
              aria-pressed={option.name === learner.language}
              onClick={() => setLanguage(option.name, option.flag)}
            >
              {option.flag} {option.name}
            </button>
          ))}
        </div>
      </div>

      <div className="stack-2">
        <h2>Preferences</h2>
        <Card plain>
          <div className="stack-2">
            <label className="spread">
              <span>Microphone for speaking practice</span>
              <input
                type="checkbox"
                aria-label="Microphone permission"
                checked={learner.micOn}
                onChange={(event) => updateLearner({ micOn: event.target.checked })}
              />
            </label>
            <label className="spread">
              <span>Camera for scene capture</span>
              <input
                type="checkbox"
                aria-label="Camera permission"
                checked={learner.cameraOn}
                onChange={(event) => updateLearner({ cameraOn: event.target.checked })}
              />
            </label>
            <label className="spread">
              <span>Daily practice reminder</span>
              <input type="checkbox" defaultChecked aria-label="Daily reminder" />
            </label>
            <label className="spread">
              <span>Show English translations first</span>
              <input type="checkbox" aria-label="Translations first" />
            </label>
          </div>
        </Card>
      </div>
      <Button variant="secondary" block onClick={() => navigate("/")}>
        Log out
      </Button>
    </div>
  );
}
