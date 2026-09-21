from uuid import uuid4

from app.schemas.learning_tasks import LearningTaskResult
from app.schemas.tasks import SessionTaskPublic
from app.services.session_plan import build_grammar_lessons
from tests.test_openai_learning_tasks import tasks


def test_generated_lessons_become_private_grammar_lesson_tasks():
    session_id = uuid4()
    result = LearningTaskResult.model_validate(tasks())

    lessons = build_grammar_lessons(session_id, result)

    assert [task.kind for task in lessons] == ["grammarLesson"] * 3
    assert [task.public_content.focus for task in lessons] == [
        "genderAgreement",
        "singularPlural",
        "sceneDescription",
    ]
    assert all(task.phase == "learning" for task in lessons)
    assert [task.id for task in build_grammar_lessons(session_id, result)] == [
        task.id for task in lessons
    ]
    scene = lessons[-1]
    assert scene.public_content.questions[0].translation == "The cup is red."
    assert scene.answer_key.correct_option_ids == {"scene-1": "scene-1-a", "scene-2": "scene-2-a"}
    public = SessionTaskPublic.from_internal(scene).model_dump(mode="json")
    assert "answerKey" not in public and "correctOptionIds" not in str(public)
