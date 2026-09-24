# Product Hunt submission: Linguini

Everything to paste into the Product Hunt launch form, in form order. Limits were checked against Product Hunt's own pages on 24 September 2026 (sources are listed in `launch-plan.md`, section "What we verified"). Where Product Hunt's pages disagree with each other, this kit follows the stricter limit.

| Field | Limit (verified) | Status |
|---|---|---|
| Name | Name only, "no description or emojis". No character limit published | Ready |
| Tagline | 60 characters max | 5 options below |
| Description | 260 characters in the Help Center; the Launch Guide says 500. We stay under 260 | Ready, plus 2 alternates |
| Launch tags (formerly "Topics") | "Up to 3" | 3 picked, 1 spare |
| Pricing | Free / Paid / Paid (with a free trial or plan) | **Free** |
| Thumbnail | Square, 240×240 recommended, under 3 MB, GIF allowed | Brief below |
| Gallery | At least 2 images, 1270×760 recommended | 6 captions below |
| Video | YouTube only, full URL (short links won't load) | `<YouTube link>` |
| Maker's first comment | No published limit | Ready (241 words) |

---

## Name

```
Linguini
```

## Tagline: pick one (60 characters max)

Counts include spaces and punctuation.

| # | Tagline | Chars |
|---|---|---|
| 1 | **Turn a photo of your day into a 5-minute language lesson** (recommended) | 56 |
| 2 | Learn Spanish and French from the photos you take | 49 |
| 3 | Your camera roll is the textbook: learn Spanish or French | 57 |
| 4 | Learn the language of your day, one photo at a time | 51 |
| 5 | Snap your day, learn the words for it in Spanish or French | 58 |

Why #1: it says what the product does, how long it takes and where the lesson comes from, and it stays under the limit with room to spare. The description then names the two languages. Choose #2 instead if you'd rather put the languages in the headline.

## Description (260 characters max)

**Recommended (250 characters; 251 if the form counts bytes, because of the é):**

```
Snap a café, a street, a sunset. Linguini finds the words in your photo, you pick which to keep, then play a 5-minute Spanish or French session: word cards with audio, I-Spy and fill-in-the-blank. Your day is saved to a journal. Free, in the browser.
```

**Alternate A (221 characters), leads with the problem:**

```
Word lists don't know where you live. Linguini does: photograph a moment from your day and it becomes a 5-minute Spanish or French session, with word cards, I-Spy and sentences, saved to a photo journal. Free, no install.
```

**Alternate B (250 characters), leads with control:**

```
Your camera roll is the textbook. Linguini spots the objects in your photo; you tick the words you want, then learn them through word cards with audio, I-Spy both ways and build-a-sentence. Spanish and French for beginners. Free, runs in the browser.
```

## Launch tags (up to 3)

Product Hunt renamed "Topics" to "Launch Tags" in October 2025, and a launch can have up to 3. We checked that each of these exists on producthunt.com on 24 September 2026:

1. **Education** (`/topics/education`)
2. **Languages** (`/topics/languages`). Duolingo is listed here, so this is where language-learning launches are browsed.
3. **Artificial Intelligence** (`/topics/artificial-intelligence`)

Spare: **Photography** (`/topics/photography`). Use it in place of Artificial Intelligence if we want to stand apart from the many AI launches on the same day.

"Language Learning" is a Product *Category* (`/categories/language-learning`, under Platforms), not a launch tag. Choose it if the form asks for a category. Check the tag picker in the form, because the list can change.

## Pricing

```
Free
```

Do **not** choose "Paid (with a free trial or plan)" until billing works and a person can actually buy Plus. If the form has a status or notes field, write "Free. Paid plans coming later." The first comment says the same thing. See `readiness.md`, blocker 1.

## Links

| Field | Value |
|---|---|
| Website (primary) | `https://linguini-landing.vercel.app/?utm_source=producthunt&utm_medium=launch` |
| Additional link: the app | `https://linguini-navy.vercel.app` |

The primary link goes to the landing page because its no-signup demo on real photos is the quickest way for a Product Hunt visitor to try the idea. The app needs an email and password first. Product Hunt may add its own `ref` parameter to outbound links, so check in the preview that the combined URL still works.

## Thumbnail

- 240×240, square, under 3 MB.
- Artwork: the Linguini mascot, a smiling pasta-strand speech bubble, on the brand background. No text, because it becomes unreadable at list size.
- An animated GIF is allowed. If we make one, keep it gentle: for example, the bubble blinks once or three word markers pop onto a tiny photo. Product Hunt warns against thumbnails that are "overly animated". A still PNG is fine.

## Video

```
<YouTube link>
```

This must be a full `https://www.youtube.com/watch?v=…` URL, because Product Hunt says shortened links won't load. Product Hunt reports that about 53% of Product of the Day winners since 2021 had a video. Use the promo cut from `marketing/promo-video/` once it is uploaded.

## Gallery captions (6 images, 1270×760)

Upload them in this order. Each caption is one line.

1. **Hero:** Learn the language of your day. Your photos are the lesson.
2. **Photo to words:** Linguini finds the objects. You keep, untick or add words.
3. **Word card:** Article, gender, meaning, IPA and audio on every word.
4. **I-Spy:** Linguini gives you a clue in Spanish or French. Can you spot it?
5. **Journal:** Every session becomes a journal page, with your words highlighted.
6. **Streak and avatars:** Keep your farfalle streak going, and pick your pasta.

---

## Maker's first comment

Post this within the first minute of the launch. It has 241 words and no request for upvotes.

> Hi Product Hunt! We're the team behind Linguini, a group of students at NUS in Singapore.
>
> **Why we built it.** Word lists don't know where you live. We kept memorising "the library" and "the train station" while our real days were a kopi at the hawker centre, a rainy bus stop, a friend's bookshelf. So we flipped it round: your camera roll is the textbook.
>
> **How it works:**
> 1. Photograph a moment from your day, or pick a ready-made scene.
> 2. Linguini finds the objects in it. You untick what's wrong and add what it missed. The AI suggests, and you decide.
> 3. A 5-minute session follows: word cards with article, gender, IPA and audio; I-Spy both ways (Linguini gives you a clue, then you describe something back); describe the scene; build a sentence.
> 4. Your day is saved as a journal entry, with the photos and the words you used highlighted.
>
> **Live today:** Spanish and French from English, for beginners (about A1–A2). It runs in the browser on phone, tablet or laptop, and it's free. You can try the demo on the landing page without signing up.
>
> **Next:** pronunciation feedback and more languages. Paid plans come later; for now, everything is free.
>
> We're a student team, so expect rough edges, and please point them out. One question for you: **which moment from your day would you want to learn the words for first, and did Linguini find the right ones?**
