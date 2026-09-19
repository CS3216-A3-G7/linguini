import { useRef, useState } from "react";
import { uploadImage } from "../lib/api";
import type { UploadedImage } from "../lib/api";
import { Button } from "./ui";
import { CameraIcon, UploadIcon } from "./icons";

export function ImageUpload({ onUploaded, cameraEnabled = true, disabled = false, onBusyChange }: {
  onUploaded: (image: UploadedImage) => void;
  cameraEnabled?: boolean;
  disabled?: boolean;
  onBusyChange?: (busy: boolean) => void;
}) {
  const fileInput = useRef<HTMLInputElement>(null);
  const cameraInput = useRef<HTMLInputElement>(null);
  const busyRef = useRef(false);
  const [busy, setBusy] = useState(false);
  const [phase, setPhase] = useState("");
  const [error, setError] = useState<string | null>(null);
  const select = async (file: File | undefined, source: "camera" | "userUpload") => {
    if (!file || busyRef.current) return;
    busyRef.current = true;
    setBusy(true);
    onBusyChange?.(true);
    setError(null);
    try { onUploaded(await uploadImage(file, source, setPhase)); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to upload image."); }
    finally { busyRef.current = false; setBusy(false); setPhase(""); onBusyChange?.(false); }
  };
  return <div className="stack-2">
    <input ref={fileInput} type="file" hidden accept="image/jpeg,image/png,image/webp"
      onChange={(e) => { void select(e.target.files?.[0], "userUpload"); e.target.value = ""; }} />
    <input ref={cameraInput} type="file" hidden accept="image/jpeg,image/png,image/webp" capture="environment"
      onChange={(e) => { void select(e.target.files?.[0], "camera"); e.target.value = ""; }} />
    <div className="row">
      <Button disabled={disabled || busy || !cameraEnabled} onClick={() => cameraInput.current?.click()}><CameraIcon size={18} /> Open camera</Button>
      <Button variant="secondary" disabled={disabled || busy} onClick={() => fileInput.current?.click()}><UploadIcon size={18} /> Upload</Button>
    </div>
    <p className="small muted">JPEG, PNG or WebP, up to 10 MB</p>
    {busy ? <p role="status">{phase}</p> : null}
    {error ? <p role="alert">{error}</p> : null}
  </div>;
}
