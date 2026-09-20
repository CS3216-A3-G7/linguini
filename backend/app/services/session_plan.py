"""Deterministic placeholder plans. No image recognition or AI generation."""

from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.repositories.postgres.vocabulary import vocabulary_items, vocabulary_translations
from app.repositories.practice import PracticeConflictError
from app.schemas.media import SceneObject
from app.schemas.tasks import SessionTask
from app.schemas.vocabulary import VocabularyItem, VocabularyTranslation
from app.services.image_analysis import PlaceholderImageExtractor

# Fixed, deliberately small upload vocabulary. Unknown languages fail explicitly.
UPLOAD_WORDS = {
    "es": [("silla", "chair"), ("mesa", "table"), ("planta", "plant")],
    "fr": [("chaise", "chair"), ("table", "table"), ("plante", "plant")],
    "it": [("sedia", "chair"), ("tavolo", "table"), ("pianta", "plant")],
    "de": [("Stuhl", "chair"), ("Tisch", "table"), ("Pflanze", "plant")],
    "ko": [("\uc758\uc790", "chair"), ("\ud14c\uc774\ube14", "table"), ("\uc2dd\ubb3c", "plant")],
    "ja": [
        ("\u6905\u5b50", "chair"),
        ("\u30c6\u30fc\u30d6\u30eb", "table"),
        ("\u690d\u7269", "plant"),
    ],
    "en": [("chair", "chair"), ("table", "table"), ("plant", "plant")],
}


def bootstrap_word(
    connection, language, source_language, word, translation, part="noun", gender=None, example=None
):
    """Reuse catalog records; deterministic IDs make concurrent bootstrap safe."""
    row = (
        connection.execute(
            select(vocabulary_items)
            .where(
                func.lower(vocabulary_items.c.language_code) == language.lower(),
                func.lower(vocabulary_items.c.lemma) == word.lower(),
                vocabulary_items.c.part_of_speech == part,
            )
            .order_by(vocabulary_items.c.created_at, vocabulary_items.c.id)
            .limit(1)
        )
        .mappings()
        .first()
    )
    if row:
        item = VocabularyItem.model_validate(dict(row))
    else:
        item = VocabularyItem(
            id=uuid5(
                NAMESPACE_URL, f"linguini:vocabulary:{language.lower()}:{part}:{word.lower()}"
            ),
            language_code=language,
            lemma=word,
            display_text=word,
            part_of_speech=part,
            gender=gender,
            example_sentence=example,
        )
        connection.execute(
            insert(vocabulary_items)
            .values(**item.model_dump(by_alias=False))
            .on_conflict_do_nothing(index_elements=["id"])
        )
        item = VocabularyItem.model_validate(
            dict(
                connection.execute(select(vocabulary_items).where(vocabulary_items.c.id == item.id))
                .mappings()
                .one()
            )
        )
    translated = VocabularyTranslation(
        id=uuid5(item.id, source_language.lower()),
        vocabulary_item_id=item.id,
        source_language_code=source_language,
        translated_text=translation,
    )
    connection.execute(
        insert(vocabulary_translations)
        .values(**translated.model_dump(by_alias=False))
        .on_conflict_do_nothing()
    )
    translated = VocabularyTranslation.model_validate(
        dict(
            connection.execute(
                select(vocabulary_translations).where(
                    vocabulary_translations.c.vocabulary_item_id == item.id,
                    func.lower(vocabulary_translations.c.source_language_code)
                    == source_language.lower(),
                )
            )
            .mappings()
            .one()
        )
    )
    return item, translated


def build_objects(connection, session, asset, profile, scene):
    objects, words, translations = [], [], []
    if profile["source_language_code"].lower() != "en":
        raise PracticeConflictError(
            "Placeholder plans currently support English as the source language."
        )
    if scene:
        entries = scene["content"]["items"]
        for entry in entries:
            word, translated = bootstrap_word(
                connection,
                profile["target_language_code"],
                profile["source_language_code"],
                entry["word"],
                entry["translation"],
                entry.get("wordClass", entry.get("word_class", "noun")),
                entry.get("gender"),
                entry.get("example"),
            )
            obj = SceneObject(
                id=uuid5(session.id, "curated:" + entry["id"]),
                session_id=session.id,
                media_asset_id=asset.id,
                detected_label=entry["translation"],
                confirmed_label=entry["word"],
                selection_status="accepted",
                vocabulary_item_id=word.id,
                bounding_box={
                    "x": min(float(entry["x"]) / 100, 0.95),
                    "y": min(float(entry["y"]) / 100, 0.95),
                    "width": 0.05,
                    "height": 0.05,
                },
            )
            objects.append(obj)
            words.append(word)
            translations.append(translated)
    else:
        language = profile["target_language_code"].lower()
        if language not in UPLOAD_WORDS:
            raise PracticeConflictError("Placeholder uploads are not configured for this language.")
        for obj, (text, translation) in zip(
            PlaceholderImageExtractor().extract(asset, session.id),
            UPLOAD_WORDS[language],
            strict=True,
        ):
            word, translated = bootstrap_word(
                connection,
                language,
                profile["source_language_code"],
                text,
                translation,
                example=text,
            )
            obj.selection_status = "accepted"
            obj.confirmed_label = text
            obj.vocabulary_item_id = word.id
            objects.append(obj)
            words.append(word)
            translations.append(translated)
    return objects, words, translations


def build_tasks(session_id, objects, words, translations, uploaded):
    # Two sets choose different focus objects and context, with the same public contract.
    index = min(1, len(words) - 1) if uploaded else 0
    word, translation, obj = words[index], translations[index], objects[index]
    focus = word.display_text
    context = "photo sample" if uploaded else "ready scene"
    example = word.example_sentence or focus
    related = [word.id]
    contents = [
        dict(
            kind="vocabularyIntroduction",
            title=f"A word from your {context}",
            vocabulary_item_id=word.id,
            target_text=focus,
            translation=translation.translated_text,
            part_of_speech=word.part_of_speech,
            gender=word.gender,
            example_sentence=example,
        ),
        dict(
            kind="pronunciationPractice",
            vocabulary_item_id=word.id,
            prompt="Practise this word by typing it. Speech evaluation is not available yet.",
            target_text=focus,
        ),
        dict(
            kind="grammarExplanation",
            title="Words in context",
            explanation=f"This word is a {word.part_of_speech.value}. Read the sample below.",
            examples=[example],
            related_vocabulary_ids=related,
        ),
        dict(
            kind="grammarPractice",
            prompt=f'Which word means "{translation.translated_text}"?',
            options=list(dict.fromkeys([words[(index + 1) % len(words)].display_text, focus])),
            related_vocabulary_ids=related,
        ),
        dict(
            kind="syntaxExplanation",
            title="A sample expression",
            sentence_pattern=example,
            explanation="Read the expression, then practise putting its tokens in order.",
            examples=[example],
            related_vocabulary_ids=related,
        ),
        dict(
            kind="sentenceBuilding",
            prompt="Rebuild the sample expression.",
            source_text=example,
            token_bank=list(reversed(example.split())),
            related_vocabulary_ids=related,
            allow_speech=False,
        ),
        dict(
            kind="ispyRound",
            clue=f"Find: {translation.translated_text}",
            interaction_mode="selectObject",
            options=[
                dict(option_id=str(o.id), label=w.display_text, scene_object_id=o.id)
                for o, w in zip(objects, words, strict=True)
            ],
            encouragement="Keep practising!",
            hint_available=False,
        ),
        dict(
            kind="reflection",
            prompt=(
                f"Write a short reflection about your {context}. "
                "This sample task records participation."
            ),
            suggested_vocabulary_ids=related,
            allow_speech=False,
        ),
    ]
    keys = [
        None,
        dict(accepted_text_answers=[focus]),
        None,
        dict(accepted_text_answers=[focus], correct_option_id=focus),
        None,
        dict(accepted_text_answers=[example], expected_token_order=example.split()),
        dict(
            correct_scene_object_id=obj.id,
            correct_option_id=str(obj.id),
            accepted_text_answers=[focus],
        ),
        None,
    ]
    return [
        SessionTask(
            id=uuid5(session_id, "placeholder-v1:" + content["kind"]),
            session_id=session_id,
            phase="ispy" if content["kind"] == "ispyRound" else "learning",
            kind=content["kind"],
            order_index=i,
            public_content=content,
            answer_key=key,
            vocabulary_item_id=word.id,
            scene_object_id=obj.id,
        )
        for i, (content, key) in enumerate(zip(contents, keys, strict=True))
    ]
