BEGIN;
ALTER TABLE public.xp_events DROP CONSTRAINT xp_events_event_type_check;
ALTER TABLE public.xp_events ADD CONSTRAINT xp_events_event_type_check
    CHECK (event_type IN
        ('taskCompleted','ispyCorrect','sessionCompleted','perfectSession','journalEntry','vocabularyMastered','legacyBackfill'));
COMMIT;
