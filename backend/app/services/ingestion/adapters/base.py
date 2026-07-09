"""Abstracción común para adaptadores de ingesta de publicaciones."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from app.schemas.listing import ListingSnapshotCreate
    from app.services.ingestion.url_detector import PlatformDetection

IngestionSource = Literal["live_scrape", "fixture"]


class AdapterFetchError(Exception):
    """Se lanza cuando un adaptador no logra obtener los datos de la publicación."""


@dataclass
class AdapterResult:
    data: ListingSnapshotCreate
    source: IngestionSource
    warnings: list[str] = field(default_factory=list)


class ListingAdapter(Protocol):
    def fetch_listing(self, detection: PlatformDetection) -> AdapterResult: ...
