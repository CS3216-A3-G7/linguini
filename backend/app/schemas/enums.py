"""Shared API and domain enum values."""

from enum import Enum


class ProficiencyLevel(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class PreferredInputMode(str, Enum):
    SPEECH = "speech"
    TEXT = "text"
    BOTH = "both"


class MediaType(str, Enum):
    IMAGE = "image"
    AUDIO = "audio"


class MediaSource(str, Enum):
    USER_UPLOAD = "userUpload"
    CAMERA = "camera"
    PRELOADED = "preloaded"
    GENERATED = "generated"


class SceneObjectSelectionStatus(str, Enum):
    SUGGESTED = "suggested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CORRECTED = "corrected"


class PartOfSpeech(str, Enum):
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PRONOUN = "pronoun"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    INTERJECTION = "interjection"
    DETERMINER = "determiner"
    PHRASE = "phrase"
    OTHER = "other"


class VocabularyLearningStatus(str, Enum):
    NEW = "new"
    LEARNING = "learning"
    FAMILIAR = "familiar"
    MASTERED = "mastered"


class VocabularyEncounterType(str, Enum):
    INTRODUCED = "introduced"
    PRACTISED = "practised"
    RECALLED = "recalled"
    MASTERED = "mastered"


class VocabularyEncounterOutcome(str, Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    COMPLETED = "completed"


class SessionStatus(str, Enum):
    CREATED = "created"
    ANALYZING_SCENE = "analyzingScene"
    AWAITING_OBJECT_REVIEW = "awaitingObjectReview"
    GENERATING_TASKS = "generatingTasks"
    IN_PROGRESS = "inProgress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    FAILED = "failed"


class TaskPhase(str, Enum):
    LEARNING = "learning"
    ISPY = "ispy"


class TaskKind(str, Enum):
    VOCABULARY_INTRODUCTION = "vocabularyIntroduction"
    PRONUNCIATION_PRACTICE = "pronunciationPractice"
    GRAMMAR_EXPLANATION = "grammarExplanation"
    GRAMMAR_PRACTICE = "grammarPractice"
    SYNTAX_EXPLANATION = "syntaxExplanation"
    SENTENCE_BUILDING = "sentenceBuilding"
    ISPY_ROUND = "ispyRound"
    REFLECTION = "reflection"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "inProgress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class AttemptInputMode(str, Enum):
    SPEECH = "speech"
    TEXT = "text"
    OBJECT_SELECTION = "objectSelection"
    MULTIPLE_CHOICE = "multipleChoice"


class ISpyInteractionMode(str, Enum):
    SELECT_OBJECT = "selectObject"
    SPEAK_ANSWER = "speakAnswer"
    TYPE_ANSWER = "typeAnswer"


class JournalStatus(str, Enum):
    DRAFT = "draft"
    COMPLETED = "completed"


class JournalRevisionCreator(str, Enum):
    USER = "user"
    AI = "ai"
    MERGED = "merged"


class JournalSuggestionType(str, Enum):
    GRAMMAR = "grammar"
    SPELLING = "spelling"
    SYNTAX = "syntax"
    VOCABULARY = "vocabulary"
    CLARITY = "clarity"


class JournalSuggestionStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class WordMatchMethod(str, Enum):
    EXACT = "exact"
    INFLECTED = "inflected"
    SEMANTIC = "semantic"
    USER_CONFIRMED = "userConfirmed"


class AiFeature(str, Enum):
    SCENE_ANALYSIS = "sceneAnalysis"
    VOCABULARY_GENERATION = "vocabularyGeneration"
    SESSION_PLAN_GENERATION = "sessionPlanGeneration"
    CLUE_GENERATION = "clueGeneration"
    ATTEMPT_EVALUATION = "attemptEvaluation"
    SPEECH_TRANSCRIPTION = "speechTranscription"
    PRONUNCIATION_EVALUATION = "pronunciationEvaluation"
    JOURNAL_FEEDBACK = "journalFeedback"
    JOURNAL_WORD_MATCHING = "journalWordMatching"


class AiRunStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
