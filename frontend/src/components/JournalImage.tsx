import { SceneImage } from "./SceneImage";

type Props = {
  title: string;
  imageUrl: string | null;
  className?: string;
  width?: number | null;
  height?: number | null;
  loading?: "lazy" | "eager";
};

export function JournalImage({ title, className, imageUrl, width, height, loading }: Props) {
  return <SceneImage scene={{ imageUrl, title }} className={className} width={width} height={height} loading={loading} />;
}
