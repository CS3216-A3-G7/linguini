import { SceneImage } from "./SceneImage";

type Props = {
  title: string;
  imageUrl: string | null;
  className?: string;
  width?: number | null;
  height?: number | null;
  loading?: "lazy" | "eager";
  aspectRatio?: string;
  onError?: () => void;
};

export function JournalImage({ title, className, imageUrl, width, height, loading, aspectRatio, onError }: Props) {
  return <SceneImage scene={{ imageUrl, title }} className={className} width={width} height={height} loading={loading} aspectRatio={aspectRatio} onError={onError} />;
}
