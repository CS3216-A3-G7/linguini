import type { Scene } from "../data/types";
import { ScenePhoto } from "./ScenePhoto";

/** A playful, non-interactive treatment while a scene is being prepared. */
export function AnalysisScan({ scene }: { scene: Scene }) {
  return (
    <div className="analysis-scan" aria-hidden="true">
      <ScenePhoto scene={scene} items={[]} />
      <span className="analysis-scan__wash" />
      <span className="analysis-scan__glint" />
      <span className="analysis-scan__magnifier">
        <span className="analysis-scan__glass" />
        <span className="analysis-scan__handle" />
      </span>
      <span className="analysis-scan__tag">
        <span className="analysis-scan__caption analysis-scan__caption--words">Looking for words...</span>
        <span className="analysis-scan__caption analysis-scan__caption--veo">Veo, veo...</span>
      </span>
    </div>
  );
}
