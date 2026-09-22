import { LoadingScreen } from "../components/LoadingScreen";
import { useCallback, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import type { JournalEntry, VocabRecord, VocabStatus } from "../data/types";
import { AppStateContext } from "./context";
import { useAccount } from "./useAccount";
import { usePractice } from "./usePractice";
import { getProgress, saveJournal } from "../lib/api";
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
  // Scenes, vocabulary, and journals are fetched per page via state/queries.ts;
  // only the shared progress record stays global.
  const progress = useQuery({ queryKey: queryKeys.progress(profileId), queryFn: ({ signal }) => getProgress(signal) });

  const onLearningChanged = useCallback((scope: "task" | "session") => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.progress(profileId) });
    if (scope === "session") {
      void queryClient.invalidateQueries({ queryKey: queryKeys.vocabulary(profileId) });
    }
    void queryClient.invalidateQueries({ queryKey: queryKeys.activeSession(profileId) });
  }, [queryClient, profileId]);

  const practice = usePractice(account.user?.id ?? "", profileId, onLearningChanged);
  const [journalSaving, setJournalSaving] = useState(false);
  const [journalSaveError, setJournalSaveError] = useState<string | null>(null);
  const saving = useRef(false);

  const setVocabStatus = useCallback((id: string, status: VocabStatus) => {
    queryClient.setQueryData(queryKeys.vocabulary(profileId),
      (rows: VocabRecord[] | undefined) => rows?.map((row) => row.id === id ? { ...row, status } : row));
  }, [queryClient, profileId]);

  const saveJournalEntry = useCallback(async (draft: JournalDraft, id?: string, date?: string) => {
    if (saving.current) return null;
    saving.current = true;
    setJournalSaving(true);
    setJournalSaveError(null);
    try {
      if (!account.activeProfile && !id) throw new Error("Choose a language first.");
      const entry = await saveJournal(draft, account.activeProfile?.id ?? "", id, date);
      queryClient.setQueryData(queryKeys.journals(profileId),
        (rows: JournalEntry[] | undefined) => rows ? [entry, ...rows.filter(row => row.id !== entry.id)].sort((a, b) => b.date.localeCompare(a.date)) : undefined);
      await queryClient.invalidateQueries({ queryKey: queryKeys.journals(profileId) });
      return entry;
    } catch (error) {
      setJournalSaveError(`${error instanceof Error ? error.message : "Unable to save journal."} Your text is still here; retry saving.`);
      return null;
    } finally { saving.current = false; setJournalSaving(false); }
  }, [account.activeProfile, profileId, queryClient]);

  return <AppStateContext.Provider value={{
    ...account, ...practice,
    setVocabStatus,
    progress: progress.data ?? null, progressLoading: progress.isPending, progressError: queryError(progress.error),
    xp: progress.data?.xp ?? 0,
    journalSaving, journalSaveError, saveJournalEntry,
  }}>{children}</AppStateContext.Provider>;
}
