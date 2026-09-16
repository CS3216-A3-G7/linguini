import { useCallback, useMemo, useReducer, useState } from "react";
import type { ReactNode } from "react";
import {
  journalEntries as seedJournal,
  learner as seedLearner,
  vocabulary as seedVocab,
} from "../data/mock";
import type { JournalEntry, VocabStatus } from "../data/types";
import { AppStateContext } from "./context";
import type { AppState, Learner, Session } from "./context";

const CORRECT_XP = 5;
const ATTEMPT_XP = 2;

function newSession(sceneId: string): Session {
  return {
    sceneId,
    completedTaskIds: [],
    scoredRoundIds: [],
    analysisScored: false,
    roundsPlayed: 0,
    correctRounds: 0,
    sessionXp: 0,
    micReady: false,
  };
}

/**
 * XP and session progress live in one reducer so every reward is awarded once:
 * the global total and the session total can never drift apart.
 */
type Core = { xp: number; session: Session };

type Action =
  | { type: "start"; sceneId: string }
  | { type: "ensure"; sceneId: string }
  | { type: "analysis"; xp: number }
  | { type: "task"; taskId: string; xp: number }
  | { type: "round"; roundId: string; correct: boolean }
  | { type: "mic"; ready: boolean }
  | { type: "replay" };

function award(state: Core, session: Session, xp: number): Core {
  return { xp: state.xp + xp, session: { ...session, sessionXp: session.sessionXp + xp } };
}

function reducer(state: Core, action: Action): Core {
  const { session } = state;
  switch (action.type) {
    case "start":
      return { ...state, session: newSession(action.sceneId) };
    case "ensure":
      return session.sceneId === action.sceneId
        ? state
        : { ...state, session: newSession(action.sceneId) };
    case "analysis":
      if (session.analysisScored) return state;
      return award(state, { ...session, analysisScored: true }, action.xp);
    case "task":
      if (session.completedTaskIds.includes(action.taskId)) return state;
      return award(
        state,
        { ...session, completedTaskIds: [...session.completedTaskIds, action.taskId] },
        action.xp,
      );
    case "round": {
      if (session.scoredRoundIds.includes(action.roundId)) return state;
      const gained = action.correct ? CORRECT_XP : ATTEMPT_XP;
      return award(
        state,
        {
          ...session,
          scoredRoundIds: [...session.scoredRoundIds, action.roundId],
          roundsPlayed: session.roundsPlayed + 1,
          correctRounds: session.correctRounds + (action.correct ? 1 : 0),
        },
        gained,
      );
    }
    case "mic":
      return { ...state, session: { ...session, micReady: action.ready } };
    case "replay":
      return {
        ...state,
        session: { ...session, scoredRoundIds: [], roundsPlayed: 0, correctRounds: 0 },
      };
  }
}

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [learner, setLearner] = useState<Learner>(seedLearner);
  const [vocabulary, setVocabulary] = useState(seedVocab);
  const [journal, setJournal] = useState(seedJournal);
  const [core, dispatch] = useReducer(reducer, {
    xp: seedLearner.xp,
    session: newSession("calle-mayor"),
  });

  const updateLearner = useCallback((patch: Partial<Learner>) => {
    setLearner((current) => ({ ...current, ...patch }));
  }, []);

  const setLanguage = useCallback(
    (language: string, languageFlag: string) => updateLearner({ language, languageFlag }),
    [updateLearner],
  );

  const setVocabStatus = useCallback((id: string, status: VocabStatus) => {
    setVocabulary((current) =>
      current.map((record) => (record.id === id ? { ...record, status } : record)),
    );
  }, []);

  const addJournalEntry = useCallback((entry: JournalEntry) => {
    setJournal((current) => [entry, ...current]);
  }, []);

  const startSession = useCallback((sceneId: string) => dispatch({ type: "start", sceneId }), []);
  const ensureSession = useCallback((sceneId: string) => dispatch({ type: "ensure", sceneId }), []);
  const awardAnalysis = useCallback((xp: number) => dispatch({ type: "analysis", xp }), []);
  const completeTask = useCallback(
    (taskId: string, xp: number) => dispatch({ type: "task", taskId, xp }),
    [],
  );
  const setMicReady = useCallback((ready: boolean) => dispatch({ type: "mic", ready }), []);
  const recordRound = useCallback(
    (roundId: string, correct: boolean) => dispatch({ type: "round", roundId, correct }),
    [],
  );
  const replayGame = useCallback(() => dispatch({ type: "replay" }), []);

  const value = useMemo<AppState>(
    () => ({
      learner,
      updateLearner,
      setLanguage,
      xp: core.xp,
      vocabulary,
      setVocabStatus,
      journal,
      addJournalEntry,
      session: core.session,
      ensureSession,
      startSession,
      awardAnalysis,
      completeTask,
      setMicReady,
      recordRound,
      replayGame,
    }),
    [
      learner,
      updateLearner,
      setLanguage,
      core,
      vocabulary,
      setVocabStatus,
      journal,
      addJournalEntry,
      ensureSession,
      startSession,
      awardAnalysis,
      completeTask,
      setMicReady,
      recordRound,
      replayGame,
    ],
  );

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>;
}
