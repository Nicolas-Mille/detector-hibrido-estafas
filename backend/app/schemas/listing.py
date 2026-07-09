"""Schemas de ingesta: request/response del endpoint POST /api/ingest."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Platform = Literal["mercadolibre", "facebook_marketplace", "unsupported"]
IngestionSource = Literal["live_scrape", "fixture", "unsupported"]


class ListingSnapshotCreate(BaseModel):
    platform: Platform
    original_url: str
    normalized_url: str
    title: str | None = None
    description: str | None = None
    price: float | None = None
    currency: str | None = None
    seller_name: str | None = None
    seller_reputation: str | None = None
    seller_rating: float | None = None
    seller_reviews_count: int | None = None
    image_url: str | None = None
    scraped_at: datetime


class ListingSnapshotRead(ListingSnapshotCreate):
    id: str


class IngestionRequest(BaseModel):
    url: str = Field(min_length=1)


class IngestionResponse(BaseModel):
    status: Literal["success", "error"]
    platform: str
    source: IngestionSource | None = None
    snapshot: ListingSnapshotRead | None = None
    warnings: list[str] = Field(default_factory=list)
    message: str | None = None
