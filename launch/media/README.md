# Linguini launch media

This directory contains four ordered Product Hunt gallery images, a social square, an icon derived from the repo's existing logo, and the original 18-second silent teaser. The **primary video for review and a future Product Hunt submission** is now the [30-second narrated launch film](../video/review.html); its source and export instructions are in the [video guide](../video/README.md). The silent teaser remains available as an older alternate asset. Both videos are illustrative marketing pieces about the curated landing demo, rather than captured walkthroughs of personal-photo analysis. The graphics use the landing site's brand assets, sample photographs, and Spanish lesson/journal content.

| Asset | Purpose | Size |
| --- | --- | --- |
| `export/01-your-world.png` through `04-keep-the-day.png` | Ordered Product Hunt gallery | 1270 × 760 px each |
| `export/product-hunt-icon-240.png` | Product Hunt thumbnail | 240 × 240 px |
| `export/product-hunt-icon-512.png` | Larger icon source | 512 × 512 px |
| `export/social-square.png` | Instagram, Facebook, and LinkedIn square post | 1080 × 1080 px |
| [`../video/renders/linguini-launch-v2.mp4`](../video/renders/linguini-launch-v2.mp4) | **Primary narrated film** for team review and, after approval, Product Hunt video upload via YouTube | 1920 × 1080 px, 30 fps, 30 s |
| [`../video/voice/narration.srt`](../video/voice/narration.srt) | Timed narration captions for the primary film | SRT |
| `export/teaser-illustrated.mp4` | Older silent illustrated teaser, retained as an alternate | 1280 × 720 px, 24 fps, 18 s |
| `export/teaser-preview.png` | Poster frame from the older teaser | 1280 × 720 px |

To review the primary film, serve the worktree root with `python3 -m http.server 8018 --bind 127.0.0.1` and open `http://localhost:8018/launch/video/review.html`. The page links to the MP4, poster, captions and gallery. The production render must exist at `launch/video/renders/linguini-launch-v2.mp4`; follow the [video build instructions](../video/README.md) if it has not been rendered yet. Product Hunt accepts a **YouTube URL** for video, so upload the approved MP4 there before adding it to a submission.

Regenerate the gallery and older silent teaser with `bash launch/media/build_video.sh` (requires Pillow and ffmpeg). Edit copy, colors, or composition in `render.py`. The gallery sequence is: promise → photo vocabulary → practice → journal and return habit.

The two photographs in the exports are attributed to **Viktor Hanáček / picjumbo** in [`landing/public/photos/credits.json`](../../landing/public/photos/credits.json). [Picjumbo's official FAQ](https://picjumbo.com/faq-and-terms/) says free photos may be used commercially (credit appreciated), and its [Golden Gate photo page](https://picjumbo.com/golden-gate-bridge-2/) names Hanáček. Before public upload, verify that the repository files match those source images and review any depicted property or brand rights. Replace a photograph with a team-owned image if rights cannot be confirmed. Confirm the live demo and URL still match the artwork and final video frame.
