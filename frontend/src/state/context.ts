import { createContext } from "react";
import type { learner as seedLearner } from "../data/mock";
import type { JournalEntry, VocabRecord, VocabStatus } from "../data/types";

export type Learner = typeof seedLearner;

export type Session = {
  sceneId: string;
  completedTaskIds: string[];
  scoredRoundIds: string[];
  analysisScored: boolean;
  roundsPlayed: number;
  correctRounds: number;
  sessionXp: number;
  micReady: boolean;
};

export type AppState = {
  learner: Learner;
  updateLearner: (patch: Partial<Learner>) => void;
  setLanguage: (language: string, flag: string) => void;
  xp: number;
  vocabulary: VocabRecord[];
  setVocabStatus: (id: string, status: VocabStatus) => void;
  journal: JournalEntry[];
  addJournalEntry: (entry: JournalEntry) => void;
  session: Session;
  /** Starts a session for the scene, keeping progress when it is already the active scene. */
  ensureSession: (sceneId: string) => void;
  startSession: (sceneId: string) => void;
  awardAnalysis: (xp: number) => void;
  completeTask: (taskId: string, xp: number) => void;
  setMicReady: (ready: boolean) => void;
  recordRound: (roundId: string, correct: boolean) => void;
  replayGame: () => void;
};

export const AppStateContext = createContext<AppState | null>(null);
