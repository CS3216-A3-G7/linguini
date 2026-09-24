export type OnboardingDraft = {
  name: string;
  languageCode: string;
  goal: string;
  minutes: number;
  microphoneEnabled: boolean;
  cameraEnabled: boolean;
};

const storageKey = "linguini-onboarding-draft";

export function readOnboardingDraft(): OnboardingDraft | null {
  try {
    const value = sessionStorage.getItem(storageKey);
    if (!value) return null;
    const parsed = JSON.parse(value) as Partial<OnboardingDraft>;
    if (typeof parsed.name !== "string" || typeof parsed.languageCode !== "string" || typeof parsed.goal !== "string" || typeof parsed.minutes !== "number") return null;
    return { name: parsed.name, languageCode: parsed.languageCode, goal: parsed.goal, minutes: parsed.minutes, microphoneEnabled: Boolean(parsed.microphoneEnabled), cameraEnabled: Boolean(parsed.cameraEnabled) };
  } catch { return null; }
}

export function saveOnboardingDraft(draft: OnboardingDraft): void { sessionStorage.setItem(storageKey, JSON.stringify(draft)); }
export function clearOnboardingDraft(): void { sessionStorage.removeItem(storageKey); }
