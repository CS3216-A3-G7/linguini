import type { Scene } from "../data/types";
import { SceneArt } from "./SceneArt";

type Props = {
  scene: Scene;
  className?: string;
};

/** Uses a real scene photo when available, with the illustration as a graceful fallback. */
export function SceneVisual({ scene, className }: Props) {
  if (scene.imageUrl) {
    return <img className={className} src={scene.imageUrl} alt={scene.title} />;
  }

  return <SceneArt scene={scene.art} className={className} />;
}
