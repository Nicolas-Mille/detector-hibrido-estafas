"""Adaptador de MercadoLibre: metadata pública > JSON-LD > OpenGraph > HTML básico.

No usa Playwright. Los selectores de HTML de MercadoLibre cambian con
frecuencia, por lo que cada extracción está aislada y es tolerante a
fallos: si un campo no se puede obtener queda en None y se agrega un
warning, en vez de romper la respuesta completa.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.schemas.listing import ListingSnapshotCreate
from app.services.ingestion.adapters.base import AdapterFetchError, AdapterResult
from app.services.ingestion.url_detector import PlatformDetection

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 DetectorHibridoBot/0.1"
    ),
    "Accept-Language": "es-AR,es;q=0.9",
}


def _default_http_get(url: str) -> httpx.Response:
    with httpx.Client(timeout=10, follow_redirects=True, headers=_DEFAULT_HEADERS) as client:
        return client.get(url)


class MercadoLibreAdapter:
    def __init__(self, http_get: Callable[[str], httpx.Response] | None = None) -> None:
        self._http_get = http_get or _default_http_get

    def fetch_listing(self, detection: PlatformDetection) -> AdapterResult:
        try:
            response = self._http_get(detection.normalized_url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AdapterFetchError(
                f"No se pudo obtener la publicación de MercadoLibre: {exc}"
            ) from exc

        soup = BeautifulSoup(response.text, "html.parser")
        warnings: list[str] = []

        json_ld = self._extract_json_ld(soup)
        if json_ld is None:
            warnings.append("No se encontró JSON-LD en la página; se usó fallback de metadata/HTML")
        og = self._extract_open_graph(soup)
        html_fallback = self._extract_html_fallback(soup)
        seller = self._extract_seller(soup)

        json_ld_title = json_ld.get("title") if json_ld else None
        json_ld_description = json_ld.get("description") if json_ld else None
        json_ld_price = json_ld.get("price") if json_ld else None
        json_ld_currency = json_ld.get("currency") if json_ld else None
        json_ld_image = json_ld.get("image") if json_ld else None

        title = _first_non_empty(json_ld_title, og.get("title"), html_fallback.get("title"))
        description = _first_non_empty(
            json_ld_description, og.get("description"), html_fallback.get("description")
        )
        price = _first_non_empty(json_ld_price, og.get("price"))
        currency = _first_non_empty(json_ld_currency, og.get("currency"))
        image_url = _first_non_empty(json_ld_image, og.get("image"))

        for field_name, value in (
            ("title", title),
            ("price", price),
            ("image_url", image_url),
        ):
            if value is None:
                warnings.append(f"No se pudo extraer '{field_name}'")

        if seller.get("seller_name") is None:
            warnings.append("No se pudo extraer datos del vendedor (seller_name/rating/reputation)")

        data = ListingSnapshotCreate(
            platform="mercadolibre",
            original_url=detection.original_url,
            normalized_url=detection.normalized_url,
            title=title,
            description=description,
            price=price,
            currency=currency,
            image_url=image_url,
            scraped_at=datetime.now(UTC),
            **seller,
        )
        return AdapterResult(data=data, source="live_scrape", warnings=warnings)

    @staticmethod
    def _extract_json_ld(soup: BeautifulSoup) -> dict[str, Any] | None:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                payload = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue
            candidates = payload if isinstance(payload, list) else [payload]
            for candidate in candidates:
                if isinstance(candidate, dict) and candidate.get("@type") == "Product":
                    offers = candidate.get("offers") or {}
                    if isinstance(offers, list):
                        offers = offers[0] if offers else {}
                    price = _to_float(offers.get("price"))
                    image = candidate.get("image")
                    if isinstance(image, list):
                        image = image[0] if image else None
                    return {
                        "title": candidate.get("name"),
                        "description": candidate.get("description"),
                        "price": price,
                        "currency": offers.get("priceCurrency"),
                        "image": image,
                    }
        return None

    @staticmethod
    def _extract_open_graph(soup: BeautifulSoup) -> dict[str, Any]:
        def meta(prop: str) -> str | None:
            tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            return tag.get("content") if tag and tag.get("content") else None

        return {
            "title": meta("og:title"),
            "description": meta("og:description"),
            "image": meta("og:image"),
            "price": _to_float(meta("product:price:amount") or meta("og:price:amount")),
            "currency": meta("product:price:currency") or meta("og:price:currency"),
        }

    @staticmethod
    def _extract_html_fallback(soup: BeautifulSoup) -> dict[str, Any]:
        title_tag = soup.find("h1")
        description_tag = soup.find("meta", attrs={"name": "description"})
        return {
            "title": title_tag.get_text(strip=True) if title_tag else None,
            "description": description_tag.get("content") if description_tag else None,
        }

    @staticmethod
    def _extract_seller(soup: BeautifulSoup) -> dict[str, Any]:
        seller_tag = soup.find(attrs={"itemprop": "seller"})
        seller_name = None
        if seller_tag is not None:
            name_tag = seller_tag.find(attrs={"itemprop": "name"})
            if name_tag is not None:
                seller_name = name_tag.get_text(strip=True)
            else:
                seller_name = seller_tag.get_text(strip=True) or None

        rating_tag = soup.find(attrs={"itemprop": "ratingValue"})
        reviews_tag = soup.find(attrs={"itemprop": "reviewCount"})
        return {
            "seller_name": seller_name or None,
            "seller_reputation": None,
            "seller_rating": _to_float(rating_tag.get("content") if rating_tag else None),
            "seller_reviews_count": _to_int(reviews_tag.get("content") if reviews_tag else None),
        }


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def _to_int(value: Any) -> int | None:
    parsed = _to_float(value)
    return int(parsed) if parsed is not None else None
