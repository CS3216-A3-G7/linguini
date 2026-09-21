import { LoadingScreen } from "../components/LoadingScreen";
import { useCallback, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import type { JournalSummary, VocabRecord, VocabStatus } from "../data/types";
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
  const location = useLocation();
  const pathname = location.pathname.replace(/\/+$/, "") || "/";
  // Keep shared caches, but only fetch data consumed by the current page.
  const needsScenes = pathname === "/practice" || pathname === "/vocabulary";
  const needsProgress = ["/progress", "/profile"].includes(pathname);
  const needsVocabulary = needsProgress || pathname === "/vocabulary"
    || (pathname.startsWith("/journal/") && !pathname.startsWith("/journal/new"))
    || /^\/practice\/sessions\/[^/]+\/summary$/.test(pathname);
  const needsJournal = pathname === "/journal" || pathname === "/profile";
  const scenes = useQuery({ enabled: needsScenes, queryKey: queryKeys.scenes, queryFn: ({ signal }) => getScenes(signal) });
  const vocabulary = useQuery({ enabled: needsVocabulary, queryKey: queryKeys.vocabulary(profileId), queryFn: ({ signal }) => getVocabulary(signal) });
  const progress = useQuery({ enabled: needsProgress, queryKey: queryKeys.progress(profileId), queryFn: ({ signal }) => getProgress(signal) });
  const journal = useQuery({ enabled: needsJournal, queryKey: queryKeys.journals(profileId), queryFn: ({ signal }) => getJournals(signal) });

  const onLearningChanged = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.home(profileId) });
    void queryClient.invalidateQueries({ queryKey: queryKeys.progress(profileId) });
    void queryClient.invalidateQueries({ queryKey: queryKeys.vocabulary(profileId) });
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
      const summary: JournalSummary = {
        id: entry.id, languageProfileId: entry.languageProfileId, date: entry.date,
        title: entry.title, wordCount: entry.body.trim().split(/\s+/).filter(Boolean).length,
        mediaAssetId: entry.mediaAssetId, imageUrl: entry.imageUrl,
      };
      queryClient.setQueryData(queryKeys.journals(profileId),
        (rows: JournalSummary[] | undefined) => rows ? [summary, ...rows.filter(row => row.id !== entry.id)].sort((a, b) => b.date.localeCompare(a.date)) : undefined);
      await queryClient.invalidateQueries({ queryKey: queryKeys.journals(profileId) });
      return entry;
    } catch (error) {
      setJournalSaveError(`${error instanceof Error ? error.message : "Unable to save journal."} Your text is still here; retry saving.`);
      return null;
    } finally { saving.current = false; setJournalSaving(false); }
  }, [account.activeProfile, profileId, queryClient]);

  return <AppStateContext.Provider value={{
    ...account, ...practice,
    scenes: scenes.data ?? [], scenesLoading: scenes.isPending, scenesError: queryError(scenes.error),
    vocabulary: vocabulary.data ?? [], vocabularyLoading: vocabulary.isPending, vocabularyError: queryError(vocabulary.error), setVocabStatus,
    progress: progress.data ?? null, progressLoading: progress.isPending, progressError: queryError(progress.error),
    xp: progress.data?.xp ?? 0,
    journal: journal.data ?? [], journalLoading: journal.isPending, journalError: queryError(journal.error),
    journalSaving, journalSaveError, saveJournalEntry,
  }}>{children}</AppStateContext.Provider>;
}
