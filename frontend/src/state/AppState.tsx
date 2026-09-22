import { LoadingScreen } from "../components/LoadingScreen";
import { useCallback, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { JournalEntry, VocabRecord, VocabStatus } from "../data/types";
import { AppStateContext } from "./context";
import { useAccount } from "./useAccount";
import { usePractice } from "./usePractice";
import { getJournals, getProgress, getScenes, getVocabulary, saveJournal } from "../lib/api";
import type { JournalDraft } from "../lib/api";
import { queryError, queryKeys } from "../lib/queryKeys";

export function AppStateProvider({ children }: { children: ReactNode }) {
  const account = useAccount();
  if (account.loading) return <LoadingScreen label="Loading your profile…" />;
  if (account.error) return <p role="alert">{account.error} Reload to retry.</p>;
  // Clear profile-scoped caches and practice state when the active account/language changes.
  return <LoadedAppState key={`${account.user?.id ?? "no-user"}:${account.activeProfile?.id ?? "no-language"}`} account={account}>{children}</LoadedAppState>;
}

function LoadedAppState({ account, children }: { account: ReturnType<typeof useAccount>; children: ReactNode }) {
  const queryClient = useQueryClient();
  const profileId = account.activeProfile?.id ?? "";
  const scenes = useQuery({ queryKey: queryKeys.scenes, queryFn: ({ signal }) => getScenes(signal) });
  const vocabulary = useQuery({ queryKey: queryKeys.vocabulary(profileId), queryFn: ({ signal }) => getVocabulary(signal) });
  const progress = useQuery({ queryKey: queryKeys.progress(profileId), queryFn: ({ signal }) => getProgress(signal) });
  const journal = useQuery({ queryKey: queryKeys.journals(profileId), queryFn: ({ signal }) => getJournals(signal) });

  const onLearningChanged = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.progress(profileId) });
    void queryClient.invalidateQueries({ queryKey: queryKeys.vocabulary(profileId) });
    void queryClient.invalidateQueries({ queryKey: queryKeys.activeSession(profileId) });
  }, [queryClient, profileId]);

  const practice = usePractice(account.user?.id ?? "", profileId, onLearningChanged);
  const journalSave = useMutation({
    mutationFn: ({ draft, id, date }: { draft: JournalDraft; id?: string; date?: string }) => {
      if (!account.activeProfile && !id) throw new Error("Choose a language first.");
      return saveJournal(draft, account.activeProfile?.id ?? "", id, date);
    },
    onSuccess: (entry) => {
      queryClient.setQueryData(queryKeys.journals(profileId),
        (rows: JournalEntry[] | undefined) => [entry, ...(rows ?? []).filter((row) => row.id !== entry.id)].sort((a, b) => b.date.localeCompare(a.date)));
    },
    onError: (error) => setJournalSaveError(`${error instanceof Error ? error.message : "Unable to save journal."} Your text is still here; retry saving.`),
    onSettled: () => { journalSavingRef.current = false; },
  });
  const journalSavingRef = useRef(false);
  const [journalSaveError, setJournalSaveError] = useState<string | null>(null);

  const setVocabStatus = useCallback((id: string, status: VocabStatus) => {
    queryClient.setQueryData(queryKeys.vocabulary(profileId),
      (rows: VocabRecord[] | undefined) => rows?.map((row) => row.id === id ? { ...row, status } : row));
  }, [queryClient, profileId]);

  const saveJournalEntry = useCallback(async (draft: JournalDraft, id?: string, date?: string) => {
    if (journalSavingRef.current) return null;
    journalSavingRef.current = true;
    setJournalSaveError(null);
    try { return await journalSave.mutateAsync({ draft, id, date }); }
    catch { journalSavingRef.current = false; return null; }
  }, [journalSave.mutateAsync]);

  return <AppStateContext.Provider value={{
    ...account, ...practice,
    scenes: scenes.data ?? [], scenesLoading: scenes.isPending, scenesError: queryError(scenes.error),
    vocabulary: vocabulary.data ?? [], vocabularyLoading: vocabulary.isPending, vocabularyError: queryError(vocabulary.error), setVocabStatus,
    progress: progress.data ?? null, progressLoading: progress.isPending, progressError: queryError(progress.error),
    xp: progress.data?.xp ?? 0,
    journal: journal.data ?? [], journalLoading: journal.isPending, journalError: queryError(journal.error),
    journalSaving: journalSave.isPending, journalSaveError, saveJournalEntry,
  }}>{children}</AppStateContext.Provider>;
}
