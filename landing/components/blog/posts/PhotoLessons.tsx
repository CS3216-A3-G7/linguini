import { LessonFlow } from "../interactive/LessonFlow";
import s from "../article.module.css";

export function PhotoLessons() {
  return (
    <div className={s.body}>
      <p>
        Most language apps teach the same words to everyone, in the same order. <em>La manzana</em> comes early whether or
        not you have ever photographed an apple. We wanted the opposite. We wanted to start from the café table, the
        street on the way to class, the view from a walk. Those are the things you would actually want to talk about.
      </p>

      <h2 id="loop">One small loop</h2>
      <p>
        A Linguini lesson is short on purpose. It is meant to fit into a day, not take it over.
      </p>
      <LessonFlow sceneId="golden-gate-bridge" stages={["snap", "find", "ispy", "journal"]} />

      <h2 id="why-photos">Why a photo helps</h2>
      <ul>
        <li><strong>The words are relevant.</strong> They name things that are really in front of you, so you will use them.</li>
        <li><strong>The words have a place.</strong> <em>El puente</em> is the bridge in your photo from the bay, not a line on a list.</li>
        <li><strong>The journal gives a reason to return.</strong> Tomorrow’s lesson starts from yesterday’s page.</li>
      </ul>

      <h2 id="today">What you can try today</h2>
      <p>
        The interactive demo on our home page takes you through a whole lesson in Spanish or French. It uses curated real
        photos: explore the words, play I-Spy and a sentence game, then see the day saved as a journal page. The learner
        app, where your own photos become lessons, is being refined with a small group of testers.
      </p>
      <p>
        Tell us which part helped a word stick. That feedback decides what we build next.
      </p>
    </div>
  );
}
