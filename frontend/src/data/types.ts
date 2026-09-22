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
  attributes?: Record<string, string>;
};

export type Scene = {
  sessionId?: string;
  isUploaded?: boolean;
  imageUrl: string | null;
  mediaAssetId: string;
  languageCode: string;
  id: string;
  title: string;
  blurb: string;
  language: string;
  items: LanguageItem[];
};

export type SceneSummary = Pick<Scene, "id" | "mediaAssetId" | "imageUrl" | "title" | "blurb" | "language" | "languageCode">;

export type ScenarioProgress = {
  sceneId: string;
  sessionId: string;
  mediaAssetId: string;
  title: string;
  status: "in-progress" | "completed" | "mastered";
  completedTaskCount: number;
  totalTaskCount: number;
  level: string;
};

export type VocabularyScene = {
  mediaAssetId: string;
  title: string;
  sceneId: string | null;
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
  scenes?: VocabularyScene[];
};

export type JournalEntry = {
  photos: { mediaAssetId: string; displayOrder: number; imageUrl: string | null }[];
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
