"""Resized WebP renditions cached in Storage and in process."""

import threading
from collections import OrderedDict
from io import BytesIO

from PIL import Image

from app.services.image_storage import ImageStorage, UploadObjectMissing

ALLOWED_WIDTHS = (320, 640, 1280)


class ImageDerivatives:
    """Serves cached WebP renditions so clients never download full-resolution originals."""

    def __init__(self, storage: ImageStorage, max_entries: int = 64) -> None:
        self.storage = storage
        self.max_entries = max_entries
        self._cache: OrderedDict[tuple[str, int], bytes] = OrderedDict()
        self._lock = threading.Lock()

    def derived_key(self, storage_key: str, width: int) -> str:
        return f"derived/w{width}/{storage_key}.webp"

    def get(self, storage_key: str, width: int) -> bytes:
        if storage_key.startswith("demo-art/"):
            # Seeded scenes have no Storage object behind their key.
            raise UploadObjectMissing()
        cache_key = (storage_key, width)
        with self._lock:
            if cache_key in self._cache:
                self._cache.move_to_end(cache_key)
                return self._cache[cache_key]
        try:
            data = self.storage.download(self.derived_key(storage_key, width))
            self._remember(cache_key, data)
            return data
        except UploadObjectMissing:
            pass
        data = self._resize(self.storage.download(storage_key), width)
        self._remember(cache_key, data)
        try:
            self.storage.put(self.derived_key(storage_key, width), data, "image/webp")
        except Exception:
            # The durable write-back is best effort; the request must still succeed.
            pass
        return data

    def _remember(self, cache_key: tuple[str, int], data: bytes) -> None:
        with self._lock:
            self._cache[cache_key] = data
            self._cache.move_to_end(cache_key)
            while len(self._cache) > self.max_entries:
                self._cache.popitem(last=False)

    @staticmethod
    def _resize(data: bytes, width: int) -> bytes:
        with Image.open(BytesIO(data)) as image:
            if image.mode not in ("RGB", "L"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode in ("RGBA", "LA") or (
                    image.mode == "P" and "transparency" in image.info
                ):
                    background.paste(image.convert("RGBA"), mask=image.convert("RGBA").split()[-1])
                else:
                    background.paste(image.convert("RGB"))
                image = background
            else:
                image = image.copy()
            if image.width > width:
                image.thumbnail((width, width * 10), Image.LANCZOS)
            buffer = BytesIO()
            image.save(buffer, format="WEBP", quality=72, method=4)
            return buffer.getvalue()
