import type { PracticeDetail, TaskActionResult } from "./api";

// A saved action may arrive after the user has opened another session.
export function applyTaskResult(current: PracticeDetail | null, sessionId: string, result: TaskActionResult): PracticeDetail | null {
  if (!current || current.session.id !== sessionId) return current;
  return {
    ...current,
    tasks: current.tasks.map(task => task.id === result.task.id ? result.task : task),
    nextTaskId: result.nextTaskId,
    progress: result.sessionProgress,
  };
}
