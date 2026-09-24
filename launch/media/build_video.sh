#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
python3 launch/media/render.py

ffmpeg -y -hide_banner -loglevel error \
  -loop 1 -framerate 24 -t 4 -i launch/media/export/teaser-frames/01.png \
  -loop 1 -framerate 24 -t 4 -i launch/media/export/teaser-frames/02.png \
  -loop 1 -framerate 24 -t 4 -i launch/media/export/teaser-frames/03.png \
  -loop 1 -framerate 24 -t 4 -i launch/media/export/teaser-frames/04.png \
  -loop 1 -framerate 24 -t 4 -i launch/media/export/teaser-frames/05.png \
  -filter_complex '[0:v][1:v]xfade=transition=fade:duration=0.5:offset=3.5[v1];[v1][2:v]xfade=transition=fade:duration=0.5:offset=7[v2];[v2][3:v]xfade=transition=fade:duration=0.5:offset=10.5[v3];[v3][4:v]xfade=transition=fade:duration=0.5:offset=14,format=yuv420p[v]' \
  -map '[v]' -c:v libx264 -crf 22 -preset medium -movflags +faststart \
  launch/media/export/teaser-illustrated.mp4

ffmpeg -y -hide_banner -loglevel error -ss 17 \
  -i launch/media/export/teaser-illustrated.mp4 -frames:v 1 \
  launch/media/export/teaser-preview.png
