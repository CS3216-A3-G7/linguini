import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, Noodle, ProgressTrail, TopBar } from "../components/ui";
import { CameraIcon, CheckIcon, MicIcon } from "../components/icons";
import { languages } from "../data/mock";
import { useAppState } from "../state/useAppState";

const goals = [
  "Chat with neighbours",
  "Travel confidently",
  "Order food and drinks",
  "Understand my family",
];

const minutesOptions = [5, 10, 20];

export function Onboarding() {
  const navigate = useNavigate();
  const { setLanguage } = useAppState();
  const [step, setStep] = useState(0);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [language, setLocalLanguage] = useState(languages[0]);
  const [goal, setGoal] = useState(goals[0]);
  const [minutes, setMinutes] = useState(10);
  const [mic, setMic] = useState(true);
  const [camera, setCamera] = useState(true);

  const steps = ["Create account", "Choose a language", "Set your goal", "Permissions"];

  const next = () => {
    if (step === steps.length - 1) {
      setLanguage(language.name, language.flag);
      navigate("/home");
      return;
    }
    setStep((current) => current + 1);
  };

  const back = () => (step === 0 ? navigate("/") : setStep((current) => current - 1));

  return (
    <div className="stack">
      <TopBar title={steps[step]} onBack={back} help="Four short steps and you are ready to practise." />
      <ProgressTrail value={step + 1} total={steps.length} label={`Step ${step + 1} of ${steps.length}`} />

      {step === 0 && (
        <div className="stack">
          <h1>Nice to meet you</h1>
          <p className="muted">We only need a name to cheer you on.</p>
          <div className="field">
            <label className="field__label" htmlFor="ob-name">
              Your name
            </label>
            <input
              id="ob-name"
              className="input"
              value={name}
              placeholder="Roshni"
              onChange={(event) => setName(event.target.value)}
            />
          </div>
          <div className="field">
            <label className="field__label" htmlFor="ob-email">
              Email
            </label>
            <input
              id="ob-email"
              className="input"
              type="email"
              value={email}
              placeholder="you@example.com"
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="stack">
          <h1>Which language today?</h1>
          <p className="muted">You can change this later in your profile.</p>
          <div className="grid-2">
            {languages.map((option) => (
              <button
                key={option.code}
                type="button"
                className={`scene-pick${option.code === language.code ? " scene-pick--selected" : ""}`}
                onClick={() => setLocalLanguage(option)}
                style={{ alignItems: "center", padding: "var(--space-4)" }}
              >
                <span style={{ fontSize: 28 }}>{option.flag}</span>
                <strong>{option.name}</strong>
              </button>
            ))}
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="stack">
          <h1>What are you practising for?</h1>
          <div className="stack-2">
            {goals.map((option) => (
              <button
                key={option}
                type="button"
                className={`task-row${option === goal ? " task-row--done" : ""}`}
                onClick={() => setGoal(option)}
              >
                <span className="task-row__index">{option === goal ? <CheckIcon size={16} /> : ""}</span>
                <span className="grow">{option}</span>
              </button>
            ))}
          </div>
          <h3>Minutes a day</h3>
          <div className="row">
            {minutesOptions.map((option) => (
              <button
                key={option}
                type="button"
                className={`chip${option === minutes ? " chip--selected" : ""}`}
                onClick={() => setMinutes(option)}
              >
                {option} min
              </button>
            ))}
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="stack">
          <h1>Two quick permissions</h1>
          <p className="muted">
            Linguini uses your camera for scenes and your microphone for speaking practice. You can
            always type instead.
          </p>
          <Card>
            <div className="spread">
              <div className="row">
                <CameraIcon />
                <div>
                  <strong>Camera</strong>
                  <p className="small muted">Capture the scene you want to learn from.</p>
                </div>
              </div>
              <input
                type="checkbox"
                aria-label="Allow camera"
                checked={camera}
                onChange={(event) => setCamera(event.target.checked)}
              />
            </div>
          </Card>
          <Card>
            <div className="spread">
              <div className="row">
                <MicIcon />
                <div>
                  <strong>Microphone</strong>
                  <p className="small muted">Speak your clues out loud during I-Spy.</p>
                </div>
              </div>
              <input
                type="checkbox"
                aria-label="Allow microphone"
                checked={mic}
                onChange={(event) => setMic(event.target.checked)}
              />
            </div>
          </Card>
          <Noodle />
          <p className="small muted center-text">
            {name ? `${name}, ` : ""}you are learning {language.name} · {goal} · {minutes} min a day
          </p>
        </div>
      )}

      <Button block onClick={next}>
        {step === steps.length - 1 ? "Start learning" : "Continue"}
      </Button>
    </div>
  );
}
