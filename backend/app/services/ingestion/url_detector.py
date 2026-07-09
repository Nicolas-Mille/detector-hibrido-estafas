"""Detección de plataforma y normalización de URLs de publicaciones P2P."""

from dataclasses import dataclass
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

Platform = Literal["mercadolibre", "facebook_marketplace", "unsupported"]

_MERCADOLIBRE_HOST_FRAGMENTS = ("mercadolibre.com", "mercadolivre.com", "meli.la")
_FACEBOOK_HOSTS = {"facebook.com", "www.facebook.com", "m.facebook.com", "web.facebook.com"}
_TRACKING_PARAM_PREFIXES = ("utm_", "matt_", "ref", "forceInApp", "click_id", "position")


@dataclass(frozen=True)
class PlatformDetection:
    platform: Platform
    original_url: str
    normalized_url: str


def detect_platform(raw_url: str) -> PlatformDetection:
    """Identifica la plataforma de una URL y devuelve su forma normalizada.

    Nunca lanza excepciones: URLs vacías, malformadas o de dominios
    desconocidos resuelven a platform="unsupported".
    """
    original = (raw_url or "").strip()
    if not original:
        return PlatformDetection(
            platform="unsupported", original_url=original, normalized_url=original
        )

    parseable = original if "://" in original else f"https://{original}"
    try:
        parts = urlsplit(parseable)
    except ValueError:
        return PlatformDetection(
            platform="unsupported", original_url=original, normalized_url=original
        )

    host = parts.netloc.lower().split(":")[0]
    if host.startswith("www."):
        host = host[4:]

    platform = _resolve_platform(host, parts.path)
    normalized = _normalize(parts) if platform != "unsupported" else original
    return PlatformDetection(platform=platform, original_url=original, normalized_url=normalized)


def _resolve_platform(host: str, path: str) -> Platform:
    if not host:
        return "unsupported"
    if any(fragment in host for fragment in _MERCADOLIBRE_HOST_FRAGMENTS):
        return "mercadolibre"
    if host in _FACEBOOK_HOSTS and path.startswith("/marketplace"):
        return "facebook_marketplace"
    return "unsupported"


def _normalize(parts) -> str:
    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=False)
        if not key.startswith(_TRACKING_PARAM_PREFIXES)
    ]
    scheme = parts.scheme or "https"
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((scheme, netloc, path, urlencode(query_pairs), ""))
