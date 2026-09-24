# Linguini launch media

This directory contains four ordered Product Hunt gallery images, a social square, an icon derived from the repo's existing logo, and an 18-second silent teaser. The teaser is **illustrative artwork, not a captured product walkthrough**. It is visibly labeled as such on every frame. The graphics use the landing site's existing brand assets, sample photographs, and Spanish lesson/journal content; the layouts are marketing mockups rather than screenshots of the app.

| Asset | Purpose | Size |
| --- | --- | --- |
| `export/01-your-world.png` through `04-keep-the-day.png` | Ordered Product Hunt gallery | 1270 × 760 px each |
| `export/product-hunt-icon-240.png` | Product Hunt thumbnail | 240 × 240 px |
| `export/product-hunt-icon-512.png` | Larger icon source | 512 × 512 px |
| `export/social-square.png` | Instagram, Facebook, and LinkedIn square post | 1080 × 1080 px |
| `export/teaser-illustrated.mp4` | Silent illustrated teaser with captions | 1280 × 720 px, 24 fps, 18 s |
| `export/teaser-preview.png` | Poster frame from the teaser | 1280 × 720 px |

Regenerate with `bash launch/media/build_video.sh` (requires Pillow and ffmpeg). Edit copy, colors, or composition in `render.py`. The gallery sequence is: promise → photo vocabulary → practice → journal and return habit.

The two photographs in the exports are attributed to **Viktor Hanáček / picjumbo** in [`landing/public/photos/credits.json`](../../landing/public/photos/credits.json). [Picjumbo's official FAQ](https://picjumbo.com/faq-and-terms/) says free photos may be used commercially (credit appreciated), and its [Golden Gate photo page](https://picjumbo.com/golden-gate-bridge-2/) names Hanáček. Before public upload, verify that the repository files match those source images and review any depicted property or brand rights. Replace a photograph with a team-owned image if rights cannot be confirmed. Confirm the live demo and URL still match the artwork and final video frame.
