import { SceneImage } from "./SceneImage";
import type { LanguageItem, Scene } from "../data/types";

type Props = {
  scene: Scene;
  items?: LanguageItem[];
  activeItemId?: string | null;
  onMarkerClick?: (item: LanguageItem) => void;
};

export function ScenePhoto({ scene, items, activeItemId, onMarkerClick }: Props) {
  const markers = items ?? scene.items;
  return (
    <div className="scene">
      <SceneImage scene={scene} className="scene__art" />
      {markers.map((item) => {
        const active = item.id === activeItemId;
        const className = `scene__marker${active ? " scene__marker--active" : ""}`;
        const style = { left: `${item.x}%`, top: `${item.y}%` };
        return onMarkerClick ? (
          <button
            key={item.id}
            type="button"
            className={className}
            style={style}
            onClick={() => onMarkerClick(item)}
            aria-label={`Marker ${item.marker}: ${item.word}`}
          >
            {item.marker}
          </button>
        ) : (
          <span key={item.id} className={className} style={style} aria-hidden="true">
            {item.marker}
          </span>
        );
      })}
    </div>
  );
}
