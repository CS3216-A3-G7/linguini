import { createContext } from "react";
import type { useAccount } from "./useAccount";
import type { usePractice } from "./usePractice";
import type { JournalDraft } from "../lib/api";
import type { JournalEntry, JournalSummary, VocabRecord, VocabStatus } from "../data/types";
import type { ProgressResponse } from "../lib/api";
import type { SceneSummary } from "../data/types";

export type Learner = ReturnType<typeof useAccount>["learner"];

export type AppState = ReturnType<typeof usePractice> & Pick<ReturnType<typeof useAccount>, "user" | "activeProfile" | "languageProfiles" | "activateLanguageProfile" | "profileSaving" | "profileError" | "setLanguage" | "saveUser" | "saveProfileSettings" | "saveLanguageProfile" | "completeOnboarding"> & {
  scenes: SceneSummary[];
  scenesLoading: boolean;
  scenesError: string | null;
  progress: ProgressResponse | null;
  progressError: string | null;
  progressLoading: boolean;
  vocabularyError: string | null;
  vocabularyLoading: boolean;
  learner: Learner;
  xp: number;
  vocabulary: VocabRecord[];
  setVocabStatus: (id: string, status: VocabStatus) => void;
  journal: JournalSummary[];
  journalLoading: boolean;
  journalError: string | null;
  journalSaving: boolean;
  journalSaveError: string | null;
  saveJournalEntry: (draft: JournalDraft, id?: string, date?: string) => Promise<JournalEntry | null>;
};

export const AppStateContext = createContext<AppState | null>(null);
