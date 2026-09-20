import { SceneImage } from "./SceneImage";

type Props = {
  title: string;
  imageUrl: string | null;
  className?: string;
};

export function JournalImage({ title, className, imageUrl }: Props) {
  return <SceneImage scene={{ imageUrl, title }} className={className} />;
}
