import { useNavigate } from "react-router-dom";
import { OnboardingSteps } from "../components/OnboardingSteps";
import { clearOnboardingDraft, readOnboardingDraft, saveOnboardingDraft, type OnboardingDraft } from "../lib/onboardingDraft";
import { languages } from "../config/languages";
import { useAppState } from "../state/useAppState";

const defaultDraft: OnboardingDraft = {
  name: "", languageCode: languages[0].code, goal: "Chat with neighbours", minutes: 10,
  microphoneEnabled: false, cameraEnabled: false,
};

/** Collect preferences before an account exists, then continue to account creation. */
export function PreAccountOnboarding() {
  const navigate = useNavigate();
  return <OnboardingSteps initial={readOnboardingDraft() ?? defaultDraft} onComplete={draft => {
    saveOnboardingDraft(draft);
    navigate("/login?mode=signup");
  }} />;
}

/** Apply the saved pre-account choices after Supabase has created the user. */
export function Onboarding() {
  const navigate = useNavigate();
  const { learner, completeOnboarding, profileSaving, profileError } = useAppState();
  const draft = readOnboardingDraft();
  const initial: OnboardingDraft = draft ?? {
    name: learner.name,
    languageCode: learner.languageCode || languages[0].code,
    goal: learner.goal || defaultDraft.goal,
    minutes: learner.dailyMinutes ?? 10,
    microphoneEnabled: learner.micOn,
    cameraEnabled: learner.cameraOn,
  };
  return <OnboardingSteps initial={initial} saving={profileSaving} error={profileError} onComplete={async values => {
    const saved = await completeOnboarding(values.languageCode, values.minutes, {
      displayName: values.name || learner.name,
      learningGoal: values.goal,
      microphoneEnabled: values.microphoneEnabled,
      cameraEnabled: values.cameraEnabled,
      onboardingCompleted: true,
    });
    if (saved) {
      clearOnboardingDraft();
      navigate("/home");
    }
  }} />;
}
