import { useCallback, useRef, useState } from "react";
import { languages } from "../config/languages";
import { createLanguageProfile, getCurrentUser, getLanguageProfiles, updateLanguageProfile, updateUser } from "../lib/api";
import type { LanguageProfilePatch, UserPatch } from "../lib/api";
import { useApiData } from "../lib/useApiData";

async function loadAccount(signal?: AbortSignal) {
  const [user, profiles] = await Promise.all([getCurrentUser(signal), getLanguageProfiles(signal)]);
  return { user, profiles };
}

export function useAccount() {
  const { data, setData, loading, error } = useApiData(loadAccount);
  const [profileSaving, setSaving] = useState(false);
  const [profileError, setError] = useState<string | null>(null);
  const busy = useRef(false);
  const activeProfile = data?.profiles.find((profile) => profile.isActive) ?? null;
  const option = languages.find((language) => language.code === activeProfile?.targetLanguageCode);

  const run = useCallback(async (action: () => Promise<unknown>): Promise<boolean> => {
    if (busy.current) return false;
    busy.current = true;
    setSaving(true);
    setError(null);
    try {
      await action();
      setData(await loadAccount());
      return true;
    } catch (reason) {
      setError(`${reason instanceof Error ? reason.message : "Unable to save profile."} Please retry or reload.`);
      return false;
    } finally {
      busy.current = false;
      setSaving(false);
    }
  }, [setData]);

  const setLanguage = useCallback((code: string, minutes?: number) => run(async () => {
    const profile = data?.profiles.find((row) => row.targetLanguageCode.toLowerCase() === code && row.sourceLanguageCode === "en");
    if (profile) return updateLanguageProfile(profile.id, { isActive: true, ...(minutes === undefined ? {} : { dailyGoalMinutes: minutes }) });
    return createLanguageProfile(code, minutes);
  }), [data, run]);
  const saveUser = useCallback((patch: UserPatch) => run(() => updateUser(patch)), [run]);
  const completeOnboarding = useCallback((code: string, minutes: number, patch: UserPatch) => run(async () => {
    await updateUser(patch);
    const profile = data?.profiles.find((row) => row.targetLanguageCode === code && row.sourceLanguageCode === "en");
    if (profile) await updateLanguageProfile(profile.id, { isActive: true, dailyGoalMinutes: minutes });
    else await createLanguageProfile(code, minutes);
  }), [data, run]);
  const saveLanguageProfile = useCallback((patch: LanguageProfilePatch) => run(() => {
    if (!activeProfile) throw new Error("Choose a language first.");
    return updateLanguageProfile(activeProfile.id, patch);
  }), [activeProfile, run]);

  return {
    data, loading, error,
    user: data?.user ?? null,
    activeProfile,
    profileSaving, profileError, setLanguage, saveUser, saveLanguageProfile, completeOnboarding,
    learner: {
      name: data?.user.displayName ?? "",
      languageCode: activeProfile?.targetLanguageCode ?? "",
      language: option?.name ?? activeProfile?.targetLanguageCode ?? "Choose a language",
      languageFlag: option?.flag ?? "",
      level: activeProfile?.proficiencyLevel ?? "A1",
      dailyMinutes: activeProfile?.dailyGoalMinutes ?? null,
      goal: data?.user.learningGoal ?? "",
      micOn: data?.user.microphoneEnabled ?? false,
      cameraOn: data?.user.cameraEnabled ?? false,
    },
  };
}
