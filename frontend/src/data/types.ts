export type WordClass = "noun" | "verb" | "adjective" | "adverb" | "pronoun" | "preposition" | "conjunction" | "interjection" | "determiner" | "phrase" | "other";
export type VocabStatus = "new" | "learning" | "familiar" | "mastered";
export type Gender = "la" | "el" | null;

export type LanguageItem = {
  id: string;
  word: string;
  translation: string;
  wordClass: WordClass;
  gender: Gender;
  marker: number;
  /** marker position on the scene, in percent of width/height */
  x: number;
  y: number;
  example: string;
  exampleTranslation: string;
};

export type LearningTaskKind = "word" | "gender" | "syntax" | "phrase";

export type LearningTask = {
  id: string;
  kind: LearningTaskKind;
  title: string;
  summary: string;
  xp: number;
  /** language items this task teaches */
  itemIds: string[];
  note?: string | null;
};

export type ISpyChoice = {
  id: string;
  label: string;
};

export type ISpyRound = {
  id: string;
  clue: string;
  clueTranslation: string;
  answerId: string;
  choices: ISpyChoice[];
  encouragement: string;
};

export type Phase2Prompt = {
  id: string;
  itemId: string;
  suggestions: string[];
  llmGuess: string;
  feedback: string;
};

export type Scene = {
  imageUrl: string | null;
  mediaAssetId: string;
  languageCode: string;
  id: string;
  title: string;
  blurb: string;
  language: string;
  items: LanguageItem[];
  tasks: LearningTask[];
  rounds: ISpyRound[];
  prompts: Phase2Prompt[];
};

export type SceneSummary = Pick<Scene, "id" | "mediaAssetId" | "imageUrl" | "title" | "blurb" | "language" | "languageCode">;

export type ScenarioProgress = {
  sceneId: string;
  status: "in-progress" | "completed" | "mastered";
  spokenItems: number;
  totalItems: number;
  level: string;
};

export type VocabRecord = {
  id: string;
  word: string;
  translation: string;
  wordClass: WordClass;
  gender: Gender;
  status: VocabStatus;
  topic: string;
  sceneId: string;
  example: string;
};

export type JournalEntry = {
  imageUrl: string | null;
  languageProfileId: string;
  id: string;
  date: string;
  title: string;
  mediaAssetId: string | null;
  body: string;
  wordsUsed: string[];
};

export type LeaderboardRow = {
  rank: number;
  name: string;
  xp: number;
  isYou?: boolean;
};
