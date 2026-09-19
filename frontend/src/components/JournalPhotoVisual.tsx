import type { JournalPhoto } from "../data/types";
import { SceneArt } from "./SceneArt";

type Props = {
  photo: JournalPhoto;
  className?: string;
};

export function JournalPhotoVisual({ photo, className }: Props) {
  if (photo.kind === "upload") {
    return <img className={className} src={photo.url} alt={photo.alt} />;
  }

  return <SceneArt scene={photo.art} className={className} />;
}
