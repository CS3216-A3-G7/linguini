import { useNavigate } from "react-router-dom";
import { Button, Card, Mascot, Noodle } from "../components/ui";
import { languages, learner as seedLearner } from "../data/mock";
import { useAppState } from "../state/useAppState";

export function Profile() {
  const navigate = useNavigate();
  const { learner, setLanguage, xp, vocabulary, journal } = useAppState();

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
            <div className="row">
              <span className="pill pill--xp">{xp} XP</span>
              <span className="pill pill--learning">🔥 {learner.streak} day streak</span>
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
          <div className="stat__value">{seedLearner.dailyMinutes}</div>
          <span className="small muted">Min / day</span>
        </div>
      </div>

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
              <input type="checkbox" defaultChecked aria-label="Microphone permission" />
            </label>
            <label className="spread">
              <span>Camera for scene capture</span>
              <input type="checkbox" defaultChecked aria-label="Camera permission" />
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

      <div className="stack-2">
        <h2>Your goal</h2>
        <Card>
          <p className="small">{learner.goal}</p>
        </Card>
      </div>

      <Noodle />

      <Button variant="secondary" block onClick={() => navigate("/")}>
        Log out
      </Button>
    </div>
  );
}
