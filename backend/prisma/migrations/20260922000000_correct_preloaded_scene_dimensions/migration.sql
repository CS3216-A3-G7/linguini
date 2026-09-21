-- Correct the placeholder 320x200/svg metadata seeded for the preloaded scene
-- photos; the real objects in the media-assets bucket are JPEG/WebP images.
-- Metadata-only, idempotent: each UPDATE is guarded on the stale placeholder.
BEGIN;

UPDATE public.media_assets
SET mime_type = 'image/jpeg', width = 5456, height = 3064
WHERE id = 'f9507eb2-776b-4a4f-a6a7-a7c622ff3a16' AND width = 320 AND height = 200;

UPDATE public.media_assets
SET mime_type = 'image/webp', width = 1200, height = 673
WHERE id = '40e54611-22fb-4a38-977c-f0786df70866' AND width = 320 AND height = 200;

UPDATE public.media_assets
SET mime_type = 'image/jpeg', width = 1095, height = 700
WHERE id = '79059369-eaa4-4805-a11e-a91bd6eff467' AND width = 320 AND height = 200;

UPDATE public.media_assets
SET mime_type = 'image/jpeg', width = 1280, height = 853
WHERE id = '036a3de3-3ee0-4e75-8226-8204430d096c' AND width = 320 AND height = 200;

UPDATE public.media_assets
SET mime_type = 'image/jpeg', width = 5000, height = 3333
WHERE id = 'aed4f104-241a-42f2-8e3a-d3408787179c' AND width = 320 AND height = 200;

UPDATE public.media_assets
SET mime_type = 'image/webp', width = 474, height = 316
WHERE id = '835e99a0-7a37-4a98-86ff-08185ebb2c63' AND width = 320 AND height = 200;

COMMIT;
