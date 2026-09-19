import type { Scene } from "../data/types";
import type { PracticeDetail, UploadedImage } from "./api";

/** Join accepted objects to catalog vocabulary by ID; labels are only a fallback. */
export function practiceScene(detail: PracticeDetail, media: UploadedImage, language: string): Scene {
  return {
      sessionId: detail.session.id, isUploaded: detail.mediaAsset.source !== "preloaded", id: detail.sceneId ?? detail.session.id,
      mediaAssetId: media.id, imageUrl: media.signedUrl, title: detail.title,
      languageCode: detail.vocabulary[0]?.languageCode ?? "", language,
      blurb: "",
      items: detail.sceneObjects.map((object, i) => {
        const word = detail.vocabulary.find(w => w.id === object.vocabularyItemId);
        const translation = detail.translations.find(t => t.vocabularyItemId === object.vocabularyItemId);
        return { id: object.id, word: word?.displayText ?? object.confirmedLabel ?? object.detectedLabel,
          translation: translation?.translatedText ?? object.detectedLabel, wordClass: word?.partOfSpeech ?? "noun",
          gender: word?.gender === "la" || word?.gender === "el" ? word.gender : null,
          marker: i + 1, x: Number(object.boundingBox.x) * 100, y: Number(object.boundingBox.y) * 100,
          example: word?.exampleSentence ?? word?.displayText ?? "", exampleTranslation: "" };
      }),
    };
}
