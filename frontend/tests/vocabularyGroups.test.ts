import assert from "node:assert/strict";
import test from "node:test";
import { groupVocabularyByPhoto } from "../src/lib/vocabularyGroups.ts";
import type { VocabRecord } from "../src/data/types.ts";

const photo = (id: string) => ({ mediaAssetId: id, title: "Your photo", sceneId: null });
const word = (id: string, photos: string[]): VocabRecord => ({
  id, word: id, translation: id, wordClass: "noun", gender: null,
  status: "learning", topic: "Uncategorised", sceneId: "", example: "",
  scenes: photos.map(photo),
});

test("uploaded photos retain their own words and shared words appear under each image", () => {
  const { sceneGroups, ungrouped } = groupVocabularyByPhoto([
    word("table", ["kitchen", "office", "office"]), word("cup", ["kitchen"]),
    word("pen", ["office"]), word("hello", []),
  ], [], id => `/images/${id}`);
  assert.deepEqual(sceneGroups.map(group => [group.scene.imageUrl, group.words.map(w => w.id)]), [
    ["/images/kitchen", ["table", "cup"]], ["/images/office", ["table", "pen"]],
  ]);
  assert.deepEqual(ungrouped.map(w => w.id), ["hello"]);
});

test("older ready-scene records keep the catalog image", () => {
  const { sceneGroups, ungrouped } = groupVocabularyByPhoto([
    { ...word("tree", []), sceneId: "street" },
  ], [{ id: "street", mediaAssetId: "street-image", title: "Street", imageUrl: "/street.jpg",
    blurb: "", language: "Spanish", languageCode: "es" }], id => `/images/${id}`);
  assert.equal(sceneGroups[0].scene.imageUrl, "/street.jpg");
  assert.equal(ungrouped.length, 0);
});
