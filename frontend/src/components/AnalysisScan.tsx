import type { Scene } from "../data/types";
import { ScenePhoto } from "./ScenePhoto";

/** A playful, non-interactive treatment while a scene is being prepared. */
export function AnalysisScan({ scene }: { scene: Scene }) {
  return (
    <div className="analysis-scan" aria-hidden="true">
      <ScenePhoto scene={scene} items={[]} />
      <span className="analysis-scan__wash" />
      <span className="analysis-scan__line" />
      <img className="analysis-scan__pasta analysis-scan__pasta--one" src="/pasta-assets/farfalle.png" alt="" />
      <img className="analysis-scan__pasta analysis-scan__pasta--two" src="/pasta-assets/fusilli.png" alt="" />
      <span className="analysis-scan__tag">Spotting new words</span>
    </div>
  );
}
