import { createContext } from "react";
import type { learner as seedLearner } from "../data/mock";
import type { JournalEntry, VocabRecord, VocabStatus } from "../data/types";

export type Session = {
  sceneId: string;
  completedTaskIds: string[];
  roundsPlayed: number;
  correctRounds: number;
  sessionXp: number;
  micReady: boolean;
};

export type AppState = {
  learner: typeof seedLearner;
  setLanguage: (language: string, flag: string) => void;
  xp: number;
  addXp: (amount: number) => void;
  vocabulary: VocabRecord[];
  setVocabStatus: (id: string, status: VocabStatus) => void;
  journal: JournalEntry[];
  addJournalEntry: (entry: JournalEntry) => void;
  session: Session;
  startSession: (sceneId: string) => void;
  completeTask: (taskId: string, xp: number) => void;
  setMicReady: (ready: boolean) => void;
  recordRound: (correct: boolean) => void;
  resetSessionGame: () => void;
};

export const AppStateContext = createContext<AppState | null>(null);
