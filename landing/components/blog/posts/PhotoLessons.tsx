import Image from "next/image";
import Link from "next/link";
import { SoundVideo } from "@/components/SoundVideo";
import { CostVideo } from "../story/CostVideo";
import { LessonFlow } from "../interactive/LessonFlow";
import s from "../article.module.css";

const FILM = "/blog/photos";

export function PhotoLessons() {
  return (
    <div className={s.body}>
      <p>
        Most language apps teach the same words to everyone, in the same order. <em>La manzana</em> comes early whether or
        not you have ever photographed an apple. That’s convenient for the app. It isn’t how people remember words.
      </p>
      <p>
        We wanted to start from the other end, from your day: the café table, the street on the way to class, the view
        from a walk. Those are the things you would actually want to talk about, so those are the things a lesson should
        be made of. Here’s the idea in 30 seconds.
      </p>

      <figure className={s.fig}>
        <div className="no-print">
          <SoundVideo
            sources={[
              { src: `${FILM}/narrated-film-1080p.mp4`, media: "(min-width: 900px)" },
              { src: `${FILM}/narrated-film-720p.mp4` },
            ]}
            poster={`${FILM}/narrated-film-poster.jpg`}
            label="Linguini launch film: one street photo becomes Spanish and French words, an I-Spy game, a sentence and a journal page"
          />
        </div>
        <Image
          src={`${FILM}/narrated-film-poster.jpg`}
          alt="A frame from the film: a hillside street photo labelled la casa, el árbol, el coche, la flor and la calle"
          width={1280}
          height={720}
          className="print-only"
          style={{ width: "100%", height: "auto" }}
        />
        <figcaption>
          One street from our demo, narrated. Tap <strong>Sound on</strong> to hear it. Everything in the film comes from
          the curated demo, not from a personal photo.
        </figcaption>
      </figure>

      <h2 id="why-photos">Why a photo helps</h2>
      <p>A photo does three things a word list can’t.</p>
      <ul>
        <li><strong>The words are relevant.</strong> They name things that are really in front of you, so you will use them.</li>
        <li><strong>The words have a place.</strong> <em>El puente</em> is the bridge in your photo from the bay, not a line on a list.</li>
        <li><strong>The journal gives a reason to return.</strong> Tomorrow’s lesson starts from yesterday’s page.</li>
      </ul>

      <h2 id="loop">One small loop</h2>
      <p>
        Put those together and you get a short loop. You snap a photo, find the words in it, play I-Spy, and keep the day
        as a journal page. It’s short on purpose. A lesson should fit into a day, not take it over.
      </p>
      <LessonFlow sceneId="golden-gate-bridge" stages={["snap", "find", "ispy", "journal"]} />
      <p>That’s what you see. Here’s what happens underneath.</p>

      <h2 id="underneath">What happens underneath</h2>
      <p>
        When you start a lesson from your own photo, the learner app runs a short chain of AI steps. Each step has one
        job. Each returns structured data, and the app checks that data before you see it. Here is one lesson played out
        on a real scene from our demo, a hillside street, with what each step costs us.
      </p>
      <LessonFlow
        sceneId="hillside-street"
        stages={["snap", "check", "find", "choose", "build", "ispy", "journal"]}
        costs={{ check: "Free", find: "$0.0139 · vision", build: "$0.0035 · translation + tasks", ispy: "$0.0015" }}
      />
      <p>
        Each of those is a fraction of a cent. But they are paid on every lesson, for every learner, every day. So we
        watch them closely.
      </p>

      <h2 id="cost">What each step costs</h2>
      <p>
        The chart below shows where the cost goes today, what it looks like from 2027, and what it looks like with the
        cheaper pipeline we are testing.
      </p>
      <CostVideo />
      <p>
        The biggest share is the first real step: looking at the photo and finding the words in it. That’s the $0.0139
        vision call. The steps after it are smaller: $0.0035 to translate the words and build the tasks, and $0.0015 for
        I-Spy. So if we want lessons to stay cheap, the photo is where to look.
      </p>

      <h2 id="cheap">Keeping it light</h2>
      <p>We keep the bill small in three plain ways.</p>
      <ul>
        <li><strong>Curated scenes are analysed once.</strong> Their words are computed in advance, so replaying one only costs the I-Spy feedback.</li>
        <li><strong>Words are reused.</strong> A translation stored in our vocabulary table doesn’t need to be generated again.</li>
        <li><strong>Every output has a limit.</strong> Each step has a cap on how much the model can write.</li>
      </ul>
      <p>
        Scene analysis is still most of the cost. That’s where we are testing cheaper models first. We test them against a
        labelled set of photos, so that quality doesn’t slip when the price does. The numbers behind all this are in{" "}
        <Link href="/blog/linguini-business-model">our business model</Link>.
      </p>
      <p>Cost matters. But a photo of your day is personal, and that matters more.</p>

      <h2 id="privacy">Your photos</h2>
      <p>
        A lesson built from your street means we handle a picture of your street. So uploaded photos are kept in private
        storage and shown only through short-lived signed links. AI tracing is off by default. When it is on, it records
        timings and outcomes, not your photos or your text.
      </p>
      <p>All of that describes the learner app. Here’s what you can use right now.</p>

      <h2 id="today">What you can try today</h2>
      <p>
        The <Link href="/">interactive demo on our home page</Link> takes you through a whole lesson in Spanish or French.
        It uses curated real photos, like the street in the film. You explore the words, play I-Spy and a sentence game,
        then see the day saved as a journal page.
      </p>
      <p className={s.note}>
        <strong>Status:</strong> the demo on our home page uses curated scenes. The own-photo chain described above runs
        in the learner app and is being verified in production with a small group of testers before a wider launch.
      </p>
      <p>
        We don’t know yet which part of the loop does the most work. It might be seeing a word on your own photo. It might
        be I-Spy, or the journal page the next morning. Tell us which part helped a word stick. That feedback decides what
        we build next.
      </p>
    </div>
  );
}
