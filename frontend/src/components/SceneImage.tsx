import { useState } from "react";
import type { SceneSummary } from "../data/types";

type Props = {
  scene: Pick<SceneSummary, "imageUrl" | "title">;
  className?: string;
  width?: number | null;
  height?: number | null;
  loading?: "lazy" | "eager";
  onError?: () => void;
};

export function SceneImage({ scene, className, width, height, loading, onError }: Props) {
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  if (!scene.imageUrl || failedUrl === scene.imageUrl) {
    return (
      <span
        className={`scene-image scene-image--error${className ? ` ${className}` : ""}`}
        role="img"
        aria-label={`Image unavailable: ${scene.title}`}
      >
        Image unavailable
      </span>
    );
  }
  const hasDimensions = typeof width === "number" && typeof height === "number";
  return (
    <img
      src={scene.imageUrl}
      alt={scene.title}
      className={`scene-image${className ? ` ${className}` : ""}`}
      loading={loading ?? "lazy"}
      decoding="async"
      width={hasDimensions ? width : undefined}
      height={hasDimensions ? height : undefined}
      onError={() => {
        setFailedUrl(scene.imageUrl);
        onError?.();
      }}
    />
  );
}
