import { useCallback } from "react";
import { Link, Outlet, useParams } from "react-router-dom";
import { analyzePractice, getMedia, getPractice } from "../lib/api";
import { useApiData } from "../lib/useApiData";
import { useAppState } from "../state/useAppState";
import type { Scene } from "../data/types";
import { LoadingScreen } from "./LoadingScreen";

export function UploadedSceneRoute() {
  const { sessionId = "" } = useParams();
  return <UploadedSceneLoader key={sessionId} sessionId={sessionId} />;
}

function UploadedSceneLoader({ sessionId }: { sessionId: string }) {
  const { learner, activeProfile } = useAppState();
  const load = useCallback(async () => {
    const session = await getPractice(sessionId);
    if (session.analysisMode !== "placeholder") throw new Error("This is not an uploaded image session.");
    const media = await getMedia(session.session.sceneMediaAssetId);
    const result = session.sceneObjects.length ? session : await analyzePractice(sessionId);
    return { media, result };
  }, [sessionId]);
  const { data, error, loading } = useApiData(load);
  if (loading) return <LoadingScreen label="Analysing your image…" />;
  if (error || !data) return <div className="stack"><p role="alert">{error ?? "Unable to analyse image."}</p><button className="btn" onClick={() => window.location.reload()}>Retry</button><Link to="/practice">Choose another image</Link></div>;
  const scene: Scene = {
    id: data.result.demoState.sceneId, uploadedSessionId: sessionId,
    mediaAssetId: data.media.id, imageUrl: data.media.signedUrl,
    title: "Your uploaded image", blurb: "", language: learner.language,
    languageCode: activeProfile?.targetLanguageCode ?? "", tasks: [], rounds: [], prompts: [],
    items: data.result.sceneObjects.filter((o) => o.selectionStatus !== "rejected").map((o, i) => ({
      id: o.id, word: o.confirmedLabel ?? o.detectedLabel, translation: "Sample object",
      wordClass: "noun", gender: null, marker: i + 1,
      x: (Number(o.boundingBox.x) + Number(o.boundingBox.width) / 2) * 100,
      y: (Number(o.boundingBox.y) + Number(o.boundingBox.height) / 2) * 100,
      example: "Testing my microphone.", exampleTranslation: "",
    })),
  };
  return <Outlet context={scene} />;
}
