import { SceneImage } from "./SceneImage";

type Props = {
  scene: { title: string; imageUrl?: string | null };
  className?: string;
  eager?: boolean;
};

/** Backend photos retain their full dimensions so object markers stay aligned. */
export function SceneVisual({ scene, className, eager }: Props) {
  // Missing and failed photos share SceneImage's accessible placeholder.
  return <SceneImage scene={{ title: scene.title, imageUrl: scene.imageUrl ?? null }} className={className} eager={eager} />;
}
