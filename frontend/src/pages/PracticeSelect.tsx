import { useCallback, useEffect, useId, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "../components/ui";
import { CameraIcon } from "../components/icons";
import { ImageUpload } from "../components/ImageUpload";
import { createPractice, getActivePractice } from "../lib/api";
import { SceneVisual } from "../components/SceneVisual";
import { SceneCatalogStatus } from "../components/SceneCatalogStatus";
import { sessionDestination } from "../lib/sessionRoute";
import { friendlyError, queryError, queryKeys } from "../lib/queryKeys";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useAppState } from "../state/useAppState";
import { useScenesQuery } from "../state/queries";

export function PracticeSelect() {
  const navigate = useNavigate();
  const notice = (useLocation().state as { practiceNotice?: string } | null)?.practiceNotice;
  const { learner, activeProfile } = useAppState();
  const { scenes } = useScenesQuery();
  const activeProfileId = activeProfile?.id;
  const [uploading, setUploading] = useState(false);
  const [selected, setSelected] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingAsset, setPendingAsset] = useState<string | null>(null);
  const busy = useRef(false);
  const dialogRef = useRef<HTMLElement>(null);
  const dialogTitleId = useId();
  const request = useRef<{ asset: string; key: string } | null>(null);
  const queryClient = useQueryClient();
  // Mount check consumes the shared cache; only the flows below force a fresh fetch.
  const activeCheck = useQuery({
    queryKey: queryKeys.activeSession(activeProfileId ?? ""),
    queryFn: () => getActivePractice(),
    enabled: !!activeProfileId,
  });
  const activeSession = activeProfileId ? activeCheck.data ?? null : null;
  const activeCheckLoading = !!activeProfileId && activeCheck.isPending;
  const activeCheckError = queryError(activeCheck.error);
  const activeFetch = useCallback(() => queryClient.fetchQuery({
    queryKey: queryKeys.activeSession(activeProfileId ?? ""),
    queryFn: () => getActivePractice(),
    staleTime: 0,
  }), [queryClient, activeProfileId]);
  const interactionDisabled = selected || starting || !!activeCheckError || !activeProfile;
  useEffect(() => {
    if (!pendingAsset) return;
    dialogRef.current?.querySelector<HTMLButtonElement>("button")?.focus();
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !starting) setPendingAsset(null);
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [pendingAsset, starting]);
  const start = async (asset: string) => {
    if (busy.current || !activeProfile || activeCheckError) return;
    busy.current = true; setSelected(true); setStarting(true); setError(null);
    if (request.current?.asset !== asset) request.current = { asset, key: crypto.randomUUID() };
    try {
      const detail = await createPractice(activeProfile.id, asset, request.current.key);
      navigate(sessionDestination(detail).path);
    } catch (reason) {
      setError(friendlyError(reason));
    }
    finally { busy.current = false; setStarting(false); }
  };
  const continueActive = async () => {
    try {
      const fresh = await activeFetch();
      if (!fresh) return;
      navigate(sessionDestination(fresh).path);
    } catch (reason) { setError(friendlyError(reason)); }
  };
  const chooseAsset = (asset: string) => {
    if (activeSession) {
      setPendingAsset(asset);
      return;
    }
    void start(asset);
  };
  return <div className="stack practice-select">
    <h1>Capture a scene</h1>
    {notice ? <p role="alert">{notice}</p> : null}
    <p className="muted">Take a photo of the world around you, or start from a ready scene.</p>
    {activeCheckLoading ? <p role="status">Checking your current practice...</p> : null}
    {activeCheckError ? <p role="alert">{activeCheckError} Reload to resume an open practice.</p> : null}
    {activeSession ? <div className="practice-select__active" role="status">
      <div>
        <strong>Continue an open practice</strong>
        <p className="small muted">You can also start another photo below.</p>
      </div>
      <Button variant="secondary" onClick={() => void continueActive()}>
        Continue practice
      </Button>
    </div> : null}
    <div className="dashed-capture">
      <span style={{ color: "var(--teal-dark)" }}><CameraIcon size={44} /></span>
      <ImageUpload compact disabled={interactionDisabled} cameraEnabled={learner.cameraOn}
        onBusyChange={setUploading} onUploaded={image => chooseAsset(image.id)} />
    </div>
    {starting ? <p role="status">Starting analysis...</p> : null}
    {error ? <div className="stack-2"><p role="alert">{error}</p><Button disabled={starting || uploading} onClick={() => request.current && void start(request.current.asset)}>Retry</Button></div> : null}
    {!activeProfile ? <p role="alert">Choose a learning language in Profile to start.</p> : null}
    <h2>Or practise with the below</h2>
    <SceneCatalogStatus />
    <div className="grid-2">
      {scenes.map(scene => <button key={scene.id} type="button" className="scene-pick"
        disabled={interactionDisabled || uploading} aria-label={`Choose ${scene.title}`} onClick={() => chooseAsset(scene.mediaAssetId)}>
        <SceneVisual scene={scene} />
        <span className="small items-center justify-center" style={{ fontWeight: 700 }}>{scene.title}</span>
      </button>)}
    </div>
    {pendingAsset ? <div className="help-modal__backdrop" onMouseDown={() => !starting && setPendingAsset(null)}>
      <section ref={dialogRef} className="help-modal leave-session__dialog" role="dialog" aria-modal="true" aria-labelledby={dialogTitleId} onMouseDown={event => event.stopPropagation()}>
        <h2 id={dialogTitleId}>Keep this practice open?</h2>
        <p>You already have a practice in progress. You can keep it and start this photo too. You can have up to three open practices.</p>
        <div className="leave-session__actions">
          <Button block disabled={starting} onClick={() => { setPendingAsset(null); void continueActive(); }}>Continue practice</Button>
          <Button variant="secondary" block disabled={starting} onClick={() => { const asset = pendingAsset; setPendingAsset(null); if (asset) void start(asset); }}>Start another photo</Button>
        </div>
      </section>
    </div> : null}
  </div>;
}
