import { SceneImage } from "./SceneImage";

type Props = {
  scene: { title: string; imageUrl?: string | null; width?: number | null; height?: number | null };
  className?: string;
  loading?: "lazy" | "eager";
};

/** Backend photos retain their full dimensions so object markers stay aligned. */
export function SceneVisual({ scene, className, loading }: Props) {
  // Missing and failed photos share SceneImage's accessible placeholder.
  return <SceneImage scene={{ title: scene.title, imageUrl: scene.imageUrl ?? null }} className={className} width={scene.width} height={scene.height} loading={loading} />;
}
