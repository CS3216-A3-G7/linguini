import type { PracticeDetail } from "../lib/api";
import { Card } from "./ui";

export function TranslationPreview({ preview }: { preview: NonNullable<PracticeDetail["translationPreview"]> }) {
  return <Card plain className="translation-preview">
    <h2>Your translations</h2>
    {([
      ["Objects", preview.objects],
      ["Attributes", preview.attributes],
      ["Relationships", preview.relationships],
    ] as const).map(([label, terms]) => terms.length ? <section key={label} className="translation-preview__group">
      <h3>{label}</h3>
      <div className="translation-preview__terms">{terms.map(term => <span className="translation-preview__term" key={term.key}>
        <span>{term.source}</span><strong>{term.translation}</strong>
      </span>)}</div>
    </section> : null)}
  </Card>;
}
