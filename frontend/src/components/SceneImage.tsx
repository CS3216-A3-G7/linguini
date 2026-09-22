import { useState } from "react";
import type { SceneSummary } from "../data/types";
import { imageLoadingAttrs } from "../lib/imageLoading";

type Props = {
  scene: Pick<SceneSummary, "imageUrl" | "title">;
  className?: string;
  lazy?: boolean;
};

export function SceneImage({ scene, className, lazy }: Props) {
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
  return (
    <img
      src={scene.imageUrl}
      alt={scene.title}
      className={`scene-image${className ? ` ${className}` : ""}`}
      decoding="async"
      {...imageLoadingAttrs(lazy)}
      onError={() => setFailedUrl(scene.imageUrl)}
    />
  );
}
