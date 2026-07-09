"""Adaptador de Facebook Marketplace basado en fixtures locales.

Facebook Marketplace real queda fuera de la Fase 1 por restricciones
técnicas (login, fragilidad del scraping, términos de uso). Este
adaptador resuelve URLs demo/reconocidas contra fixtures JSON
controlados, para validar la arquitectura de adaptadores sin scraping
real. Ver README para más contexto.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.listing import ListingSnapshotCreate
from app.services.ingestion.adapters.base import AdapterResult
from app.services.ingestion.url_detector import PlatformDetection

_FIXTURES_DIR = Path(__file__).resolve().parents[3] / "fixtures" / "facebook"

_KEYWORD_FIXTURES = {
    "iphone": "facebook_marketplace_iphone_suspicious.json",
    "auto": "facebook_marketplace_car_normal.json",
    "car": "facebook_marketplace_car_normal.json",
    "gol": "facebook_marketplace_car_normal.json",
}
_DEFAULT_FIXTURE = "facebook_marketplace_car_normal.json"


class FacebookFixtureAdapter:
    def fetch_listing(self, detection: PlatformDetection) -> AdapterResult:
        warnings: list[str] = []
        lowered = detection.normalized_url.lower()

        fixture_name = next(
            (name for keyword, name in _KEYWORD_FIXTURES.items() if keyword in lowered),
            None,
        )
        if fixture_name is None:
            fixture_name = _DEFAULT_FIXTURE
            warnings.append(f"URL demo no reconocida; se usó fixture por defecto ({fixture_name})")

        payload = json.loads((_FIXTURES_DIR / fixture_name).read_text(encoding="utf-8"))

        data = ListingSnapshotCreate(
            platform="facebook_marketplace",
            original_url=detection.original_url,
            normalized_url=detection.normalized_url,
            scraped_at=datetime.now(UTC),
            **payload,
        )
        return AdapterResult(data=data, source="fixture", warnings=warnings)
