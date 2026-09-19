import type { KeyboardEvent, MouseEvent } from "react";
import { SceneVisual } from "./SceneVisual";
import type { LanguageItem, Scene } from "../data/types";

type Props = {
  scene: Scene;
  items?: LanguageItem[];
  activeItemId?: string | null;
  onMarkerClick?: (item: LanguageItem) => void;
  onLocationSelect?: (position: { x: number; y: number }) => void;
  locationLabel?: string;
};

export function ScenePhoto({
  scene,
  items,
  activeItemId,
  onMarkerClick,
  onLocationSelect,
  locationLabel,
}: Props) {
  const markers = items ?? scene.items;

  const selectLocation = (event: MouseEvent<HTMLDivElement>) => {
    if (!onLocationSelect) return;

    const bounds = event.currentTarget.getBoundingClientRect();
    onLocationSelect({
      x: ((event.clientX - bounds.left) / bounds.width) * 100,
      y: ((event.clientY - bounds.top) / bounds.height) * 100,
    });
  };

  const selectCenterWithKeyboard = (event: KeyboardEvent<HTMLDivElement>) => {
    if (!onLocationSelect || (event.key !== "Enter" && event.key !== " ")) return;
    event.preventDefault();
    onLocationSelect({ x: 50, y: 50 });
  };

  return (
    <div
      className={`scene${onLocationSelect ? " scene--location-selectable" : ""}`}
      onClick={selectLocation}
      onKeyDown={selectCenterWithKeyboard}
      role={onLocationSelect ? "button" : undefined}
      tabIndex={onLocationSelect ? 0 : undefined}
      aria-label={onLocationSelect ? locationLabel : undefined}
    >
      <SceneVisual scene={scene} className="scene__art" />
      {markers.map((item) => {
        const active = item.id === activeItemId;
        const custom = item.id.startsWith("custom-");
        const className = [
          "scene__marker",
          custom ? "scene__marker--custom" : "",
          active ? "scene__marker--active" : "",
        ]
          .filter(Boolean)
          .join(" ");
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
