"""Detección de plataforma y normalización de URLs de publicaciones P2P."""

from dataclasses import dataclass
from typing import Literal
from urllib.parse import SplitResult, parse_qsl, urlencode, urlsplit, urlunsplit

Platform = Literal["mercadolibre", "facebook_marketplace", "unsupported"]

# Allow-list de dominios reales, comparados por igualdad o por sufijo de
# subdominio (nunca por substring crudo). Un substring check dejaría pasar
# hosts como "mercadolibre.com.atacante.io" como si fueran MercadoLibre
# legítimo, habilitando SSRF: el backend haría requests salientes a
# cualquier host que un atacante nombre parecido.
_MERCADOLIBRE_ALLOWED_DOMAINS = (
    "mercadolibre.com",
    "mercadolibre.com.ar",
    "mercadolibre.com.mx",
    "mercadolibre.com.co",
    "mercadolibre.com.uy",
    "mercadolibre.com.pe",
    "mercadolibre.cl",
    "mercadolivre.com.br",
    "meli.la",
)
_FACEBOOK_ALLOWED_DOMAINS = ("facebook.com",)
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
        # `.hostname` descarta userinfo ("user:pass@") y puerto; nunca hay
        # que confiar en `netloc` crudo para decidir el host real.
        host = (parts.hostname or "").lower()
        port = parts.port
    except ValueError:
        return PlatformDetection(
            platform="unsupported", original_url=original, normalized_url=original
        )

    platform = _resolve_platform(host, parts.path)
    normalized = _normalize(parts, host, port) if platform != "unsupported" else original
    return PlatformDetection(platform=platform, original_url=original, normalized_url=normalized)


def _is_domain_or_subdomain(host: str, allowed_domain: str) -> bool:
    """True si host es exactamente allowed_domain o un subdominio real suyo."""
    return host == allowed_domain or host.endswith(f".{allowed_domain}")


def _resolve_platform(host: str, path: str) -> Platform:
    if not host:
        return "unsupported"
    if any(_is_domain_or_subdomain(host, domain) for domain in _MERCADOLIBRE_ALLOWED_DOMAINS):
        return "mercadolibre"
    if any(
        _is_domain_or_subdomain(host, domain) for domain in _FACEBOOK_ALLOWED_DOMAINS
    ) and path.startswith("/marketplace"):
        return "facebook_marketplace"
    return "unsupported"


def _normalize(parts: SplitResult, host: str, port: int | None) -> str:
    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=False)
        if not key.startswith(_TRACKING_PARAM_PREFIXES)
    ]
    scheme = parts.scheme or "https"
    # Se reconstruye el netloc desde host+port (nunca desde parts.netloc
    # crudo) para no arrastrar credenciales tipo "user:pass@" al guardar
    # o reutilizar la URL normalizada.
    netloc = f"{host}:{port}" if port else host
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((scheme, netloc, path, urlencode(query_pairs), ""))
