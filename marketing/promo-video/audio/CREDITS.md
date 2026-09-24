# Promo film audio: credits and provenance

Every file in this folder is either **CC BY 4.0** (music, credit required) or **CC0 1.0** (sound effects, no credit required). Nothing here is NonCommercial, NoDerivatives, "personal use only", or AI-generated music. The upstream licence pages were checked on 2026-09-24.

## Required attribution for the video description

Copy this block exactly into the YouTube, Product Hunt and X descriptions (or the end card):

```
"Life of Riley" Kevin MacLeod (incompetech.com)
Licensed under Creative Commons: By Attribution 4.0 License
http://creativecommons.org/licenses/by/4.0/
```

That is the only attribution the licences require. The CC0 sound effects need no credit. If you want a courtesy line anyway, use: `Sound effects: Kenney, OwlishMedia, StarNinjas, HaelDB, rubberduck, unicaegames, Jofae, zazz.sound.design, xkeril, thaighaudio, AtomCut, UI SFX (all CC0)`.

## Music

| File | Title / author | Licence | Source |
|---|---|---|---|
| `music.flac` | "Life of Riley", Kevin MacLeod | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Official page: https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1400054 (original MP3: https://incompetech.com/music/royalty-free/mp3-royaltyfree/Life%20of%20Riley.mp3). Retrieved from the mirror `github.com/theartroutine/GoPlan` @ `1670740269a5`, `backend/memories/assets/music/life-of-riley.mp3`, whose CREDITS.md lists it as CC BY 4.0. ID3 tags: title "Life of Riley", artist "Kevin MacLeod". |

**Edit (a derivative, which CC BY allows; the description credit above covers it):** 55.66 s long, 48 kHz stereo, 16-bit, peak at −1 dBFS. The tempo is 102 BPM in 4/4, so one bar lasts 2.353 s.
- 0.00 to 42.35 s is source bars 38 to 55 (89.45 to 131.80 s of the original). The first 10 bars are the ukulele and glockenspiel breakdown, and the full band comes in on the downbeat at 23.53 s.
- 42.35 s to the end is source bar 92 onward (216.51 s to about 229.5 s): the second half of the chorus phrase, the final chord at 51.76 s, and a fade over the last 2.5 s.
- The two parts are joined on a bar line with a 30 ms equal-power crossfade. The splice was aligned to the sample by cross-correlation. Source bar 92 has the same harmony as bar 56 (chroma similarity 0.999).

## Sound effects (all CC0 1.0: https://creativecommons.org/publicdomain/zero/1.0/)

Processing was the same for every file: converted to 48 kHz stereo 24-bit WAV, leading and trailing silence trimmed (−50 dB gate), short fade-out, peak-normalized to −3 dBFS. Longer sources were cut down as noted.

| File | What it is | Original title / author | Upstream source | Retrieved from (repo @ commit : path) |
|---|---|---|---|---|
| `sfx-curtain.wav` | Cloth swish, 1.4 s (curtain) | "Cloth_02", OwlishMedia, *202 More Sound Effects* | https://opengameart.org/content/202-more-sound-effects | `novincode/atomcut-library` @ `391f87ff50bd` : `packs/opengameart-202-more-sound-effects/audio/cloth-02.m4a` |
| `sfx-curtain2.wav` | Longer cloth rustle, 1.7 s (alternate) | "Cloth_03", OwlishMedia | same | same pack, `cloth-03.m4a` |
| `sfx-shutter.wav` | Real camera shutter click | "Camera_01", OwlishMedia | same | same pack, `camera-01.m4a` |
| `sfx-shutter2.wav` | Alternate shutter | "Camera_02", OwlishMedia | same | same pack, `camera-02.m4a` |
| `sfx-pop.wav` | Soft bubbly pop (word markers) | `drop_002.ogg`, Kenney, *Interface Sounds* | https://kenney.nl/assets/interface-sounds | `ricardo/overlay-motion` @ `a4f42bb19183` : `public/sfx/library/kenney-drop-002.ogg` |
| `sfx-pop2.wav` | Low, round pop (variant) | "pop-in", AtomCut, *Motion Essentials* (DSP-synthesized) | https://github.com/novincode/atomcut-library (`pack.json`: licence CC0-1.0) | `atomcut-library` : `packs/motion-essentials/audio/pop-in.wav` |
| `sfx-pop3.wav` | Water bubble pop (variant) | "bubble 02", rubberduck, *40 CC0 water/splash/slime SFX* | https://opengameart.org/content/40-cc0-water-splash-slime-sfx | `atomcut-library` : `packs/opengameart-40-cc0-water-splash-slime-sfx/audio/bubble-02.m4a` |
| `sfx-flip.wav` | Card flip/draw | "draw", HaelDB, *Card Game sounds* | https://opengameart.org/content/card-game-sounds | `atomcut-library` : `packs/opengameart-card-game-sounds/audio/draw.m4a` |
| `sfx-whoosh.wav` | Short fast whoosh pass | "whoosh-pass-fast", AtomCut (DSP) | atomcut-library, CC0-1.0 | `packs/motion-essentials/audio/whoosh-pass-fast.wav` |
| `sfx-chime.wav` | Bright success chime | "Chime Notification", Jofae (Freesound #380482) | https://freesound.org/people/Jofae/sounds/380482/ | `overlay-motion` : `public/sfx/library/freesound-chime-notification.mp3` |
| `sfx-chime2.wav` | Two-note confirmation (alternate) | `confirmation_002.ogg`, Kenney, *Interface Sounds* | https://kenney.nl/assets/interface-sounds | `overlay-motion` : `public/sfx/library/kenney-confirmation-002.ogg` |
| `sfx-coin.wav` | Coin/XP ding | `sounds/arcade/reward.mp3`, UI SFX (romainsimon/uisfx; deterministic synthesis recipes, audio released as CC0) | https://github.com/romainsimon/uisfx/blob/main/LICENSE-AUDIO | npm `uisfx@0.4.0` tarball : `package/sounds/arcade/reward.mp3` |
| `sfx-xp.wav` | Softer glassy reward shimmer (alternate XP) | `sounds/glass/reward.mp3`, UI SFX | same | npm `uisfx@0.4.0` : `package/sounds/glass/reward.mp3` |
| `sfx-page.wav` | Book page turn | "10 Book Page Flips", StarNinjas | https://opengameart.org/content/10-book-page-flips | `overlay-motion` : `public/sfx/library/oga-book-flip.ogg` |
| `sfx-page2.wav` | Page flip (alternate) | `bookFlip1.ogg`, Kenney, *RPG Audio* | https://kenney.nl/assets/rpg-audio | `atomcut-library` : `packs/kenney-rpg-audio/audio/book-flip1.m4a` |
| `sfx-riser.wav` | 2.4 s riser into the drop (start it about 2.4 s before 23.53 s) | "riser-long", AtomCut, *Impacts & Risers* (DSP) | atomcut-library, CC0-1.0 | `packs/impacts-risers/audio/riser-long.wav` |
| `sfx-riser2.wav` | 3.0 s tension riser (alternate) | "riser-tension", AtomCut (DSP) | same | `packs/motion-essentials/audio/riser-tension.wav` |
| `sfx-impact.wav` | Deep cinematic boom for the logo reveal (first 4.0 s, 1.8 s fade) | "DSGNImpt_Deep Cinematic Impact 5_ZAZZ", zazz.sound.design (Freesound #754424) | https://freesound.org/people/zazz.sound.design/sounds/754424/ | `overlay-motion` : `public/sfx/library/freesound-deep-cinematic-impact.mp3` |
| `sfx-impact-soft.wav` | Short soft low thump (gentler reveal option) | "impact-deep", AtomCut (DSP) | atomcut-library, CC0-1.0 | `packs/impacts-risers/audio/impact-deep.wav` |
| `sfx-whoosh-hit.wav` | Whoosh plus double hit, made for logo animations (optional) | "Transition (hit and whoosh)", xkeril (Freesound #736852) | https://freesound.org/people/xkeril/sounds/736852/ | `overlay-motion` : `public/sfx/library/freesound-transition-hit.mp3` |
| `sfx-typing.wav` | Natural keyboard typing, 5.4 s (optional) | `Human Typing/human_vel-006.wav`, unicaegames, *Keyboard Soundpack #1* | https://opengameart.org/content/keyboard-soundpack-1-typing-and-single-keystrokes | `overlay-motion` : `public/sfx/keyboard-typing-natural.wav` (SOURCE.md there: unmodified CC0 file) |
| `sfx-cheer.wav` | Audience applause/cheer, 7 s (optional; 19 to 26 s of the source, fades in and out) | "Concert audience applause 5", thaighaudio (Freesound #478415) | https://freesound.org/people/thaighaudio/sounds/478415/ | `overlay-motion` : `public/sfx/library/freesound-applause-concert.mp3` |

Kenney assets are CC0 1.0 (https://kenney.nl/support, and `License.txt` in every Kenney pack). Each OpenGameArt and Freesound page above was checked on 2026-09-24 and shows CC0.

## Music timing reference

`beats.json` goes with `music.flac`:
- `bpm` is 102.
- `beats` and `downbeats` are the 102 BPM grid, confirmed against librosa `beat_track` (median offset 4 ms). The unsnapped librosa output is kept in `beats_librosa_raw`.
- `onsets` are the strongest 25% of librosa onsets.
- `sections`: intro 0 to 18.82 s, build 18.82 to 23.53 s, drop 23.53 to 42.35 s, drop 42.35 to 51.76 s, outro 51.76 s to the end.
- `energy` is RMS normalized to 0–1, sampled every 0.25 s.

The untouched original track is not stored in the repo; download it from the official incompetech page above if the edit needs redoing.
