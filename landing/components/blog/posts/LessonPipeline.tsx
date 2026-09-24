import Link from "next/link";
import { CostVideo } from "../story/CostVideo";
import { LessonFlow } from "../interactive/LessonFlow";
import s from "../article.module.css";

export function LessonPipeline() {
  return (
    <div className={s.body}>
      <p>
        When you start a lesson from your own photo, the learner app runs a short chain of AI steps. Each step has one job
        and returns structured data that the app checks before you see it. Watch one lesson play out on a real scene from
        our demo, with what each step costs us.
      </p>

      <LessonFlow
        sceneId="hillside-street"
        stages={["snap", "check", "find", "choose", "build", "ispy", "journal"]}
        costs={{ check: "Free", find: "$0.0139 · vision", build: "$0.0035 · translation + tasks", ispy: "$0.0015" }}
      />

      <h2 id="cost">What each step costs</h2>
      <p>Where the cost goes today, from 2027, and with the cheaper pipeline we are testing.</p>
      <CostVideo />

      <h2 id="cheap">Keeping it light</h2>
      <ul>
        <li><strong>Curated scenes are analysed once.</strong> Their words are computed in advance, so replaying one only costs the I-Spy feedback.</li>
        <li><strong>Words are reused.</strong> A translation stored in our vocabulary table doesn’t need to be generated again.</li>
        <li><strong>Every output has a limit.</strong> Each step has a cap on how much the model can write.</li>
      </ul>
      <p>
        Scene analysis is most of the cost. That is where we are testing cheaper models first, against a labelled set of
        photos, so that quality doesn’t slip. The numbers behind this are in{" "}
        <Link href="/blog/linguini-business-model">our business model</Link>.
      </p>

      <h2 id="privacy">Your photos</h2>
      <p>
        Uploaded photos are kept in private storage and shown through short-lived signed links. AI tracing is off by
        default. When it is on, it records timings and outcomes, not your photos or your text.
      </p>

      <p className={s.note}>
        <strong>Status:</strong> the demo on our home page uses curated scenes. The own-photo chain above runs in the
        learner app and is being verified in production with testers before a wider launch.
      </p>
    </div>
  );
}
