# Linguini — Design System

> **A curious language-learning companion, served in small real-world moments.**

## Product character

Linguini helps learners notice language in the world around them: capture a scene, choose what matters, play a quick visual game, and collect discoveries in a personal word journal. The experience should feel sunny, tactile, and reassuring—like a small illustrated field notebook with a mischievous noodle guide.

The visual system takes its cue from the provided product screens and mascot: cream paper, tomato-orange action moments, a deep herb-teal anchor, and soft pasta-yellow rewards. It is playful without being childish and warm without becoming rustic.

### Brand distinction

Keep the learning product legible and game-like, but avoid copying any competitor’s recognizable treatments. Linguini is defined by:

- **Noodle motion, not feathers:** a single looping strand can lead the eye, celebrate a correct answer, divide sections, or curl around an illustration.
- **Marker-and-menu outlines:** dark-teal hand-drawn-style contours with subtly imperfect geometry; never thick black cartoon outlines.
- **Food-memory warmth:** buttery surfaces, tomato CTAs, herb-teal confirmation, and pasta-yellow moments of discovery.
- **Real-world learning:** photographic scenes paired with illustrated overlays, vocabulary chips, and a journal-like record—not a fantasy-character world.

## Design principles

1. **Make the next learning action obvious.** One screen should have one dominant action.
2. **Treat progress as a friendly trail.** Show where a learner is, what they found, and what comes next.
3. **Use play as punctuation.** Noodles, spark marks, and the mascot add delight at transitions, success, and empty states—not behind every piece of information.
4. **Keep the scene credible.** Photos are real and useful; decorative illustration frames the interaction rather than obscuring it.
5. **Use tactile depth sparingly.** Actions should feel pressable; information panels should feel like soft paper layers.

## Color

The supplied palette is the starting point. These refinements preserve its intent while improving harmony and contrast.

| Token | Value | Use |
|---|---:|---|
| `--tomato` | `#E85D32` | Primary actions, active navigation, wordmark accents |
| `--tomato-pressed` | `#C94E2C` | Pressed/active primary action depth, destructive emphasis |
| `--pasta` | `#F9B233` | Rewards, discovery highlights, noodle details, progress fill |
| `--butter` | `#FFF9ED` | App canvas / main background |
| `--cream` | `#FFF1D2` | Cards, panels, soft notices |
| `--sage` | `#DCEBDD` | Learned-state fills and calm supporting surfaces |
| `--teal` | `#2E9C99` | Correct states, secondary actions, progress confirmation |
| `--teal-dark` | `#21716F` | Primary text on light surfaces, accessible teal labels |
| `--ink` | `#263238` | High-contrast text, icons, photo markers |
| `--ink-muted` | `#667579` | Supporting copy, inactive icons |
| `--line` | `#D9D2C3` | Quiet boundaries, dashed capture areas, dividers |
| `--danger` | `#C94E2C` | Errors only; pair with a written explanation |
| `--focus` | `#166C84` | Keyboard focus ring; do not rely only on color |

### Color rules

- Butter is the default page background; cream is the default elevated surface.
- Tomato is reserved for the most important action on a screen. Do not use it as general decoration.
- Teal means confidence, confirmation, or an alternate positive route; it should not compete with tomato in the same action group.
- Pasta yellow is a highlight, not a body-text color. Use dark teal or ink for text on yellow.
- Use the full-color wordmark on butter/cream. Use a one-color tomato or cream version only where contrast requires it.

## Typography

Choose licensed fonts with rounded, human shapes rather than a branded competitor typeface.

| Role | Recommended family | Weight | Desktop / mobile | Notes |
|---|---|---:|---:|---|
| Display | **Fredoka** | 600–700 | 52–64 / 32–40 | Friendly, compact headings with a soft bounce |
| UI & body | **Nunito Sans** | 400–800 | 16 / 16 | Clear at small sizes; use 700–800 for controls |
| Numbers / metadata | **Nunito Sans** | 700–800 | 12–16 / 12–16 | Use tabular numerals where progress is compared |

Use sentence case throughout. Headings can be expressive, but keep body text calm and conversational. Avoid all-caps except tiny status labels if needed.

### Type scale

| Token | Size / line-height | Typical use |
|---|---|---|
| `--text-display` | `clamp(32px, 5vw, 64px) / 1.02` | Marketing or major moments |
| `--text-h1` | `32px / 1.12` | Page titles |
| `--text-h2` | `24px / 1.18` | Screen sections |
| `--text-h3` | `20px / 1.25` | Cards and prompts |
| `--text-body` | `16px / 1.45` | Default reading text |
| `--text-small` | `14px / 1.4` | Supporting descriptions |
| `--text-label` | `12px / 1.2` | Tabs, status, compact metadata |

## Spacing, shape, and depth

**Base unit:** 4px. Use a comfortable, mobile-first rhythm.

| Token | Value |
|---|---:|
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 12px |
| `--space-4` | 16px |
| `--space-5` | 20px |
| `--space-6` | 24px |
| `--space-8` | 32px |
| `--space-10` | 40px |
| `--space-12` | 48px |

| Token | Value | Use |
|---|---:|---|
| `--radius-sm` | 12px | Chips, fields, compact controls |
| `--radius-md` | 18px | Buttons, cards, image frames |
| `--radius-lg` | 28px | Major panels, sheets |
| `--radius-pill` | 999px | Tabs and status pills only |
| `--stroke` | 2px | Standard dark-teal outline |
| `--shadow-card` | `0 6px 14px rgba(38, 50, 56, .10)` | Soft paper lift |
| `--shadow-action` | `0 4px 0 #C94E2C` | Primary button press depth |

Use rounded rectangles with a little personality: illustrations and large panels may have asymmetrical or hand-sketched edges, but form controls must retain stable geometry for usability. Do not use glass effects, neon glows, or large blurred shadows.

## Iconography and the noodle system

Icons use a 2px rounded stroke, generally in `--teal-dark` or `--ink-muted`. Pair an unfamiliar icon with a text label. Keep icon containers soft and simple.

The Linguini noodle is a branded path, not a generic squiggle. Its rules:

- Draw it as a warm pasta-yellow tube with tomato-orange outer contour and a small cream inner highlight when it is large enough.
- Keep a consistent stroke rhythm; wide turns and loops should feel elastic, never tangled.
- Use one noodle gesture per composition: a loop around a reward, a divider under a message, or a trail leading to the main action.
- Do not let it cross body copy, controls, faces, or essential photo details.
- Animate only on purposeful moments: a 180–300ms curl on completion, a gentle 1.5–2s idle sway for the mascot, and reduced-motion alternatives with no path movement.

### Mascot

The Linguini mascot is a smiling pasta strand on a plate. It should appear as a supportive guide, not as a constant narrator:

- **Welcome / onboarding:** full mascot, warm and inviting.
- **Success:** small celebratory curl or confetti-like sauce dots.
- **Empty journal:** mascot looking through a tiny frame or holding a word card.
- **Errors:** never use a sad or shaming expression; give a neutral, helpful prompt instead.

## Core components

### Primary button

Tomato fill with cream or white label, 18px radius, 48px minimum height, and a 4px darker tomato bottom edge. Use a 700–800 UI label at 16px. On press, translate `2px` down and reduce the bottom edge to `2px`. Include an icon only when it clarifies the action (camera, play, arrow).

### Secondary button

Cream or transparent fill, 2px teal outline, teal-dark label, 48px minimum height. Use when an action is meaningful but not the screen’s main route. Avoid placing more than one secondary button beside a primary action on small screens.

### Quiet button / icon button

No filled container by default; use teal-dark text or icon with a minimum 44 × 44px hit area. Add a cream hover/pressed surface, not a new border.

### Vocabulary chip

Rounded, tactile selection pill with an illustrated number marker or object icon. Default: cream fill, 1px line border, ink text. Selected: pasta-tint fill with tomato or teal number disc. Chips wrap cleanly; never truncate the word itself.

### Photo scene card

18px rounded photo, 2px teal-dark contour, clipped image, and numbered markers that remain legible over the image. Keep marker labels outside the photo where possible. Provide descriptive alt text and a non-photo route for users who prefer to enter a word manually.

### Progress trail

Use a cream track with a pasta-yellow fill, paired with textual progress such as “1 of 3.” A tiny noodle curl may cap the fill on celebratory screens, but must not replace the numeric status.

### Answer choice

Large 48px-minimum selectable tile on cream. Default state uses a quiet line border; selected state uses teal border plus a pale teal surface; correct uses teal with a check icon; incorrect uses tomato with explanatory text. Never reveal correctness by color alone.

### Journal row

An illustrated thumbnail, a strong target-language word, a smaller translation, and a progress state badge. Use a calm 8–12px vertical gap between rows and clear divider lines rather than a grid of detached cards.

### Toast and feedback panel

Use a cream panel with a color-coded left detail and a concise human message: “Nice catch—*árbol* means tree.” Include a next action only if it moves the learner forward.

## Key screens

### Capture a scene

The home screen invites the learner to begin with their surroundings. Lead with a clear title and a short, practical explanation. The empty photo area is a soft illustrated landscape with a dashed contour and a large camera symbol. The tomato “Open camera” button sits directly beneath it. A small noodle curl and two short spark marks frame the moment; do not surround the entire screen with decoration.

### Choose vocabulary

Place the captured photo at the center of the screen. Numbered markers map directly to selectable vocabulary chips underneath. Use tomato for the current selection and pasta / teal for supporting markers, maintaining high-contrast text. The primary action reads “Start I Spy” and remains fixed above the bottom navigation when the chip list scrolls.

### Play I Spy

Make the challenge feel focused: progress at top, scene photo next, a compact hint card, then 2 × 2 large answer choices. The correct-feedback state should turn the action teal and animate a brief noodle curl around the selected answer. Maintain generous white space around tap targets.

### Word journal

Treat the journal as proof of progress, not a dense database. Put a soft pasta-yellow encouragement panel above or below the list. Segment Review, Learned, and Mastered with text-first tabs. The active tab uses tomato fill; inactive tabs live on a pale cream rail. Each row should feel easy to revisit in under a second.

## Navigation and layout

### Mobile

- Design for 360px wide screens first; allow content padding of 16px, expanding to 20–24px on larger phones.
- Use a persistent four-item bottom bar: Home, Explore, Journal, Profile. Each item has an icon and label; active state is tomato.
- Keep bottom navigation on a cream surface with a top divider and safe-area padding.
- Primary actions belong above the navigation and must not be hidden behind it.
- Use full-width action buttons, except compact paired controls that still preserve 44px hit targets.

### Tablet and web

- Keep content in a centered column of 680–760px for learning flows; use 1120px maximum for marketing or photo-plus-detail layouts.
- At 768px and above, switch the bottom navigation to a left rail or simple top navigation only if the learning flow benefits from more vertical room.
- Retain the large touch targets and visual hierarchy from mobile; do not turn the journal into a cramped desktop table.

## States and accessibility

- Body text must meet WCAG AA contrast; do not use pasta yellow or muted ink for primary body copy.
- Every control has visible focus: a 3px `--focus` outline with a 3px cream offset.
- Respect `prefers-reduced-motion`; replace noodle movement with a static final state.
- Never make a photo the only source of meaning. Provide labels for scene markers and an alternative vocabulary input path.
- Include text and icons for correct, incorrect, learned, and mastered states.
- Use 44 × 44px minimum touch targets and 48px minimum height for primary, secondary, and answer controls.
- Write feedback as encouragement and instruction: “Almost—look for the bus near the curb,” never “Wrong.”

## Motion

| Moment | Motion | Duration |
|---|---|---:|
| Button press | Down 2px; action edge compresses | 100ms |
| Selection | Border/fill settle with a small scale to 1.01 | 160ms |
| Correct answer | Noodle curl + check appears | 240ms |
| Panel entry | Fade and rise 8px | 180ms |
| Mascot idle | Very subtle 2–3px sway | 1800ms loop |

Use ease-out motion. Avoid bouncing entire layouts, looping attention-grabbers, or animation that delays the next answer.

## Copy voice

Warm, direct, and observant. Use short sentences, active verbs, and concrete cues from the learner’s world.

- Good: “What do you spot on this street?”
- Good: “Save *autobús* to your journal.”
- Good: “A few minutes of review goes a long way.”
- Avoid: “You have failed this exercise.”
- Avoid: “Complete module 1 to unlock linguistic mastery.”

## Implementation starter tokens

```css
:root {
  --tomato: #E85D32;
  --tomato-pressed: #C94E2C;
  --pasta: #F9B233;
  --butter: #FFF9ED;
  --cream: #FFF1D2;
  --sage: #DCEBDD;
  --teal: #2E9C99;
  --teal-dark: #21716F;
  --ink: #263238;
  --ink-muted: #667579;
  --line: #D9D2C3;
  --focus: #166C84;

  --font-display: "Fredoka", "Arial Rounded MT Bold", ui-rounded, sans-serif;
  --font-ui: "Nunito Sans", ui-sans-serif, system-ui, sans-serif;

  --radius-sm: 12px;
  --radius-md: 18px;
  --radius-lg: 28px;
  --shadow-card: 0 6px 14px rgba(38, 50, 56, 0.10);
  --shadow-action: 0 4px 0 var(--tomato-pressed);
}
```

## Guardrails

- Do not use a green-led palette, owl imagery, feather motifs, or a copied game layout from another language-learning product.
- Do not make every card float; reserve lifted panels for capture, feedback, and key journal moments.
- Do not use the mascot as a replacement for clear instructions.
- Do not overuse the noodle. It is a signature flourish, not a pattern fill.
- Do not use more than one saturated action color as “primary” on the same screen.
- Do not sacrifice readability for hand-drawn styling: text, touch areas, focus states, and photo markers remain crisp and predictable.
