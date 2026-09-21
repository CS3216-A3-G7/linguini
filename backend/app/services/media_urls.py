"""Resolve public media object URLs from a shared Storage bucket."""

from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, urlsplit

import httpx

SIGN_EXPIRES_IN = 3600


class MediaUrlError(Exception):
    pass


class PrivateMediaUrls:
    """Sign only object keys already authorized by the calling service."""

    def __init__(self, project_url: str, bucket: str, service_key: str) -> None:
        self.project_url = project_url
        self.storage_url = project_url.rstrip("/") + "/storage/v1"
        self.bucket = bucket
        self.service_key = service_key

    def resolve(
        self, keys: list[str], *, width: int | None = None, quality: int = 70
    ) -> dict[str, str | None]:
        result = {key: public_media_url(key, None) for key in keys}
        paths = list(
            dict.fromkeys(
                key for key in keys if not key.startswith("demo-art/") and result[key] is None
            )
        )
        if not paths:
            return result
        parsed = urlsplit(self.project_url)
        if not self.service_key or not self.bucket or parsed.scheme != "https" or not parsed.netloc:
            raise MediaUrlError("Private media signing is not configured.")
        if width is not None:
            return self._resolve_transformed(result, paths, width, quality)
        try:
            response = httpx.post(
                f"{self.storage_url}/object/sign/{quote(self.bucket, safe='')}",
                headers={"apikey": self.service_key, "Authorization": f"Bearer {self.service_key}"},
                json={"paths": paths, "expiresIn": SIGN_EXPIRES_IN},
                timeout=15,
            )
            response.raise_for_status()
            rows = response.json()
            if not isinstance(rows, list):
                raise ValueError("Invalid signing response")
            for row in rows:
                path = row["path"]
                signed = row.get("signedURL")
                if path not in paths or row.get("error") or not isinstance(signed, str):
                    raise ValueError("Unable to sign an object")
                if not signed.startswith("/object/sign/"):
                    raise ValueError("Invalid signed URL")
                result[path] = self.storage_url + quote(signed, safe="/%?=&")
            if any(result[path] is None for path in paths):
                raise ValueError("Missing signed URL")
            return result
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            # Never expose Storage responses, credentials, or signed tokens to API errors.
            raise MediaUrlError("Unable to sign media URLs.") from exc

    def _resolve_transformed(
        self, result: dict[str, str | None], paths: list[str], width: int, quality: int
    ) -> dict[str, str | None]:
        # The batch endpoint ignores transform options, so resized variants are
        # signed per path; the calls run concurrently to avoid N serial waits.
        try:
            with httpx.Client(
                timeout=15,
                headers={
                    "apikey": self.service_key,
                    "Authorization": f"Bearer {self.service_key}",
                },
            ) as client:

                def sign(path: str) -> str:
                    response = client.post(
                        f"{self.storage_url}/object/sign/{quote(self.bucket, safe='')}"
                        f"/{quote(path, safe='/')}",
                        json={
                            "expiresIn": SIGN_EXPIRES_IN,
                            "transform": {"width": width, "quality": quality},
                        },
                    )
                    response.raise_for_status()
                    signed = response.json()["signedURL"]
                    if not isinstance(signed, str) or not signed.startswith(
                        "/render/image/sign/"
                    ):
                        raise ValueError("Invalid signed URL")
                    return self.storage_url + quote(signed, safe="/%?=&")

                with ThreadPoolExecutor(max_workers=min(8, len(paths))) as pool:
                    for path, url in zip(paths, pool.map(sign, paths), strict=True):
                        result[path] = url
            return result
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            # Never expose Storage responses, credentials, or signed tokens to API errors.
            raise MediaUrlError("Unable to sign media URLs.") from exc


def public_media_url(storage_key: str, public_base_url: str | None) -> str | None:
    # Seeded demo illustrations are rendered locally, not stored in Supabase.
    if storage_key.startswith("demo-art/"):
        return None
    parsed = urlsplit(storage_key)
    if parsed.scheme in ("https", "http") and parsed.netloc:
        return storage_key
    if parsed.scheme or storage_key.startswith("//") or not public_base_url:
        return None
    # Keys are raw, bucket-relative object paths. Encode spaces, #, ?, and Unicode.
    return f"{public_base_url.rstrip('/')}/{quote(storage_key.lstrip('/'), safe='/')}"
