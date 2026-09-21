import { useCallback, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { languages } from "../config/languages";
import { createLanguageProfile, getAccount, getLanguageProfiles, updateLanguageProfile, updateUser } from "../lib/api";
import type { LanguageProfilePatch, UserPatch } from "../lib/api";
import { queryError, queryKeys } from "../lib/queryKeys";

async function loadAccount(signal?: AbortSignal) {
  const account = await getAccount(signal);
  return { user: account.user, profiles: account.languageProfiles };
}

export function useAccount() {
  const queryClient = useQueryClient();
  const { data, isPending: loading, error: queryErrorValue } = useQuery({ queryKey: queryKeys.account, queryFn: ({ signal }) => loadAccount(signal) });
  const error = queryError(queryErrorValue);
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
      await queryClient.invalidateQueries({ queryKey: queryKeys.account });
      return true;
    } catch (reason) {
      setError(`${reason instanceof Error ? reason.message : "Unable to save profile."} Please retry or reload.`);
      return false;
    } finally {
      busy.current = false;
      setSaving(false);
    }
  }, [queryClient]);

  const setLanguage = useCallback((code: string, minutes?: number) => run(async () => {
    const profile = data?.profiles.find((row) => row.targetLanguageCode.toLowerCase() === code && row.sourceLanguageCode === "en");
    if (profile) return updateLanguageProfile(profile.id, { isActive: true, ...(minutes === undefined ? {} : { dailyGoalMinutes: minutes }) });
    return createLanguageProfile(code, minutes);
  }), [data, run]);
  const saveUser = useCallback((patch: UserPatch) => run(() => updateUser(patch)), [run]);
  const saveProfileSettings = useCallback((code: string, patch: UserPatch, preferences: LanguageProfilePatch) => run(async () => {
    if (!languages.some(language => language.code === code)) throw new Error("Choose a supported language.");
    await updateUser(patch);
    // A previous save may have created the profile before a later request failed.
    const profiles = await getLanguageProfiles();
    const existing = profiles.find(profile => profile.targetLanguageCode === code && profile.sourceLanguageCode === "en");
    const profile = existing ?? await createLanguageProfile(code, preferences.dailyGoalMinutes ?? 10);
    await updateLanguageProfile(profile.id, { ...preferences, isActive: true });
  }), [run]);
  const activateLanguageProfile = useCallback((id: string) => run(async () => {
    if (!data?.profiles.some((profile) => profile.id === id)) throw new Error("Language profile not found.");
    return updateLanguageProfile(id, { isActive: true });
  }), [data, run]);
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
    languageProfiles: data?.profiles ?? [],
    activateLanguageProfile,
    profileSaving, profileError, setLanguage, saveUser, saveProfileSettings, saveLanguageProfile, completeOnboarding,
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
