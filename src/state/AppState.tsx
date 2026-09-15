import { useCallback, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  journalEntries as seedJournal,
  learner as seedLearner,
  vocabulary as seedVocab,
} from "../data/mock";
import type { JournalEntry, VocabStatus } from "../data/types";
import { AppStateContext } from "./context";
import type { AppState, Session } from "./context";

const emptySession: Session = {
  sceneId: "calle-mayor",
  completedTaskIds: [],
  roundsPlayed: 0,
  correctRounds: 0,
  sessionXp: 0,
  micReady: false,
};

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [learner, setLearner] = useState(seedLearner);
  const [xp, setXp] = useState(seedLearner.xp);
  const [vocabulary, setVocabulary] = useState(seedVocab);
  const [journal, setJournal] = useState(seedJournal);
  const [session, setSession] = useState(emptySession);

  const addXp = useCallback((amount: number) => setXp((current) => current + amount), []);

  const setLanguage = useCallback((language: string, languageFlag: string) => {
    setLearner((current) => ({ ...current, language, languageFlag }));
  }, []);

  const setVocabStatus = useCallback((id: string, status: VocabStatus) => {
    setVocabulary((current) =>
      current.map((record) => (record.id === id ? { ...record, status } : record)),
    );
  }, []);

  const addJournalEntry = useCallback((entry: JournalEntry) => {
    setJournal((current) => [entry, ...current]);
  }, []);

  const startSession = useCallback((sceneId: string) => {
    setSession({ ...emptySession, sceneId });
  }, []);

  const completeTask = useCallback(
    (taskId: string, taskXp: number) => {
      setSession((current) => {
        if (current.completedTaskIds.includes(taskId)) return current;
        return {
          ...current,
          completedTaskIds: [...current.completedTaskIds, taskId],
          sessionXp: current.sessionXp + taskXp,
        };
      });
      addXp(taskXp);
    },
    [addXp],
  );

  const setMicReady = useCallback((micReady: boolean) => {
    setSession((current) => ({ ...current, micReady }));
  }, []);

  const recordRound = useCallback(
    (correct: boolean) => {
      const gained = correct ? 5 : 2;
      setSession((current) => ({
        ...current,
        roundsPlayed: current.roundsPlayed + 1,
        correctRounds: current.correctRounds + (correct ? 1 : 0),
        sessionXp: current.sessionXp + gained,
      }));
      addXp(gained);
    },
    [addXp],
  );

  const resetSessionGame = useCallback(() => {
    setSession((current) => ({ ...current, roundsPlayed: 0, correctRounds: 0 }));
  }, []);

  const value = useMemo<AppState>(
    () => ({
      learner,
      setLanguage,
      xp,
      addXp,
      vocabulary,
      setVocabStatus,
      journal,
      addJournalEntry,
      session,
      startSession,
      completeTask,
      setMicReady,
      recordRound,
      resetSessionGame,
    }),
    [
      learner,
      setLanguage,
      xp,
      addXp,
      vocabulary,
      setVocabStatus,
      journal,
      addJournalEntry,
      session,
      startSession,
      completeTask,
      setMicReady,
      recordRound,
      resetSessionGame,
    ],
  );

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>;
}
