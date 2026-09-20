import { LoadingScreen } from "../components/LoadingScreen";
import { useCallback, useRef, useState } from "react";
import type { ReactNode } from "react";
import type { VocabStatus } from "../data/types";
import { AppStateContext } from "./context";
import { useAccount } from "./useAccount";
import { usePractice } from "./usePractice";
import { getProgress, getVocabulary, getScenes, getJournals, saveJournal } from "../lib/api";
import type { JournalDraft } from "../lib/api";
import { useApiData } from "../lib/useApiData";

export function AppStateProvider({ children }: { children: ReactNode }) {
  const account = useAccount();
  if (account.loading) return <LoadingScreen label="Loading your profile…" />;
  if (account.error) return <p role="alert">{account.error} Reload to retry.</p>;
  // Clear profile-scoped caches and practice state when the active account/language changes.
  return <LoadedAppState key={`${account.user?.id ?? "no-user"}:${account.activeProfile?.id ?? "no-language"}`} account={account}>{children}</LoadedAppState>;
}

function LoadedAppState({ account, children }: { account: ReturnType<typeof useAccount>; children: ReactNode }) {
  const scenes = useApiData(getScenes);
  const vocabulary = useApiData(getVocabulary);
  const progress = useApiData(getProgress);
  const journal = useApiData(getJournals);
  const setVocabulary = vocabulary.setData;
  const setJournal = journal.setData;
  const setProgress = progress.setData;

  const updateLearning = useCallback((data: Parameters<typeof setProgress>[0]) => {
    setProgress(data);
    void getVocabulary().then(setVocabulary).catch(() => { /* Reload can retry vocabulary. */ });
  }, [setProgress, setVocabulary]);

  const practice = usePractice(account.user?.id ?? "", account.activeProfile?.id ?? "", updateLearning);
  const [journalSaving, setJournalSaving] = useState(false);
  const [journalSaveError, setJournalSaveError] = useState<string | null>(null);
  const saving = useRef(false);

  const setVocabStatus = useCallback((id: string, status: VocabStatus) => {
    setVocabulary((rows) => rows?.map((row) => row.id === id ? { ...row, status } : row) ?? null);
  }, [setVocabulary]);

  const saveJournalEntry = useCallback(async (draft: JournalDraft, id?: string) => {
    if (saving.current) return null;
    saving.current = true;
    setJournalSaving(true);
    setJournalSaveError(null);
    try {
      if (!account.activeProfile && !id) throw new Error("Choose a language first.");
      const entry = await saveJournal(draft, account.activeProfile?.id ?? "", id);
      setJournal((rows) => [entry, ...(rows ?? []).filter((row) => row.id !== entry.id)].sort((a, b) => b.date.localeCompare(a.date)));
      return entry;
    } catch (error) {
      setJournalSaveError(`${error instanceof Error ? error.message : "Unable to save journal."} Your text is still here; retry saving.`);
      return null;
    } finally { saving.current = false; setJournalSaving(false); }
  }, [account.activeProfile, setJournal]);

  return <AppStateContext.Provider value={{
    ...account, ...practice,
    scenes: scenes.data ?? [], scenesLoading: scenes.loading, scenesError: scenes.error,
    vocabulary: vocabulary.data ?? [], vocabularyLoading: vocabulary.loading, vocabularyError: vocabulary.error, setVocabStatus,
    progress: progress.data, progressLoading: progress.loading, progressError: progress.error,
    xp: progress.data?.xp ?? 0,
    journal: journal.data ?? [], journalLoading: journal.loading, journalError: journal.error,
    journalSaving, journalSaveError, saveJournalEntry,
  }}>{children}</AppStateContext.Provider>;
}
