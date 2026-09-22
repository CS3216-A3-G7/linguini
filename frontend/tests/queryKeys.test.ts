import assert from "node:assert/strict";
import test from "node:test";
import { queryError, queryKeys } from "../src/lib/queryKeys.ts";

test("profile-scoped keys carry the profile id and differ across profiles", () => {
  for (const key of [queryKeys.vocabulary, queryKeys.progress, queryKeys.journals, queryKeys.activeSession]) {
    assert.ok(key("profile-a").includes("profile-a"));
    assert.notDeepEqual(key("profile-a"), key("profile-b"));
  }
});

test("keys are stable and serialisable", () => {
  assert.deepEqual(queryKeys.account, ["account"]);
  assert.deepEqual(queryKeys.scenes, ["scenes"]);
  assert.deepEqual(queryKeys.journal("j1"), ["journal", "j1"]);
  assert.deepEqual(queryKeys.journalDayContext("2026-01-02"), ["journal", "day", "2026-01-02"]);
  assert.deepEqual(queryKeys.sessionScene("s1"), ["session", "s1", "scene"]);
  assert.deepEqual(queryKeys.sessionSummary("s1"), ["session", "s1", "summary"]);
  for (const key of [queryKeys.account, queryKeys.vocabulary("p"), queryKeys.activeSession("p"), queryKeys.sessionScene("s")]) {
    assert.deepEqual(JSON.parse(JSON.stringify(key)), [...key]);
  }
});

test("queryError maps errors to display strings", () => {
  assert.equal(queryError(new Error("Request failed.")), "Request failed.");
  assert.equal(queryError("oops"), "Unable to load data.");
  assert.equal(queryError(null), null);
  assert.equal(queryError(undefined), null);
});
