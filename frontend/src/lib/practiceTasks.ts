import type { SessionTask } from "./api";

export const taskDone = (task: SessionTask) => task.status === "completed" || task.status === "skipped";

export function practiceStages(tasks: SessionTask[]) {
  const ordered = [...tasks].sort((a, b) => a.orderIndex - b.orderIndex);
  return {
    learning: ordered.filter(task => task.kind !== "ispyRound" && task.kind !== "reflection"),
    clues: ordered.filter(task => task.kind === "ispyRound"),
    reflection: ordered.filter(task => task.kind === "reflection"),
  };
}

export function taskTitle(task: SessionTask) {
  const content = task.publicContent;
  if ("title" in content) return content.title;
  const labels: Partial<Record<SessionTask["kind"], string>> = {
    pronunciationPractice: "Practise pronunciation", grammarPractice: "Practise grammar",
    sentenceBuilding: "Build a sentence", ispyRound: "Linguini clues", reflection: "Your reflection",
  };
  return labels[task.kind] ?? "Practise";
}

export function taskDescription(task: SessionTask) {
  const content = task.publicContent;
  if ("prompt" in content) return content.prompt;
  if ("explanation" in content) return content.explanation;
  if (content.kind === "vocabularyIntroduction") {
    if (content.words?.length) return `${content.words.length} words from your scene`;
    return `${content.targetText ?? "Vocabulary"} · ${content.translation ?? "Review"}`;
  }
  return content.clue;
}
