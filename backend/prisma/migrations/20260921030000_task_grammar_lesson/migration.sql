BEGIN;
-- Generated grammar lessons join the plan; pronunciation practice is dropped for now.
ALTER TABLE public.session_tasks DROP CONSTRAINT session_tasks_kind_check;
ALTER TABLE public.session_tasks ADD CONSTRAINT session_tasks_kind_check
    CHECK (kind IN ('vocabularyIntroduction','grammarLesson','grammarExplanation',
        'grammarPractice','syntaxExplanation','sentenceBuilding','ispyRound','reflection'));
-- Grouped vocabulary and grammar lessons submit one attempt in `vocabularyReview` mode.
ALTER TABLE public.task_attempts ALTER COLUMN input_mode TYPE VARCHAR(16);
ALTER TABLE public.task_attempts DROP CONSTRAINT task_attempts_input_mode_check;
ALTER TABLE public.task_attempts ADD CONSTRAINT task_attempts_input_mode_check
    CHECK (input_mode IN ('speech','text','objectSelection','multipleChoice','vocabularyReview'));
COMMIT;
