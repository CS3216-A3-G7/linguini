import type { PracticeDetail } from "./api";
import { practiceStages, taskDone } from "./practiceTasks.ts";

export interface SessionDestination {
  /** Canonical path for this session's current state. */
  path: string;
  /** Learner-facing notice to surface at the destination, or null. */
  notice: string | null;
}

const failureNotices: Record<string, string> = {
  imageUploadFailed: "We couldn't save your photo. Start a new practice when you are ready.",
  sceneAnalysisFailed: "We couldn't read that photo. Try a new practice with a clearer view.",
  noValidObjects: "We couldn't find anything to learn in that photo. Try a busier scene.",
  vocabularyMappingFailed: "We couldn't turn that scene into words. Start a new practice when you are ready.",
  taskGenerationFailed: "We couldn't build your lesson. Start a new practice when you are ready.",
};

const fallbackNotice = "That practice couldn't continue. Start a new one when you are ready.";

export function sessionDestination(detail: PracticeDetail): SessionDestination {
  const base = `/practice/sessions/${detail.session.id}`;
  switch (detail.session.status) {
    case "created":
    case "analyzingScene":
    case "awaitingObjectReview":
    case "generatingTasks":
      return { path: `${base}/analysis`, notice: null };
    case "ready":
      return { path: `${base}/mic-test`, notice: null };
    case "inProgress": {
      const stages = practiceStages(detail.tasks);
      if (!detail.tasks.length || stages.learning.some(task => !taskDone(task))) return { path: `${base}/learn`, notice: null };
      if (stages.clues.some(task => !taskDone(task))) return { path: `${base}/ispy-1`, notice: null };
      return { path: `${base}/ispy-2`, notice: null };
    }
    case "completed":
      return { path: `${base}/summary`, notice: null };
    case "abandoned":
      return { path: "/practice", notice: "That practice was discarded. Start a new one when you are ready." };
    case "failed":
      return { path: "/practice", notice: (detail.session.failureCode && failureNotices[detail.session.failureCode]) || fallbackNotice };
    default:
      return { path: "/practice", notice: fallbackNotice };
  }
}

const allowedSubPaths: Record<string, string[]> = {
  created: ["analysis"],
  analyzingScene: ["analysis"],
  awaitingObjectReview: ["analysis"],
  generatingTasks: ["analysis"],
  ready: ["mic-test", "learn"],
  inProgress: ["learn", "ispy-1", "ispy-2", "summary", "mic-test"],
  completed: ["summary"],
  abandoned: [],
  failed: [],
};

export function isSessionRouteAllowed(detail: PracticeDetail, pathname: string): boolean {
  const base = `/practice/sessions/${detail.session.id}/`;
  if (!pathname.startsWith(base)) return false;
  const step = pathname.slice(base.length).split("/")[0];
  return allowedSubPaths[detail.session.status]?.includes(step) ?? false;
}
