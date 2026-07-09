"""Persistencia de ListingSnapshot: upsert cacheado por hash de URL normalizada."""

import hashlib

from sqlalchemy.orm import Session

from app.models.listing_snapshot import ListingSnapshot
from app.schemas.listing import ListingSnapshotCreate, ListingSnapshotRead


def hash_url(normalized_url: str) -> str:
    return hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()


def upsert_listing_snapshot(db: Session, data: ListingSnapshotCreate) -> ListingSnapshot:
    url_hash = hash_url(data.normalized_url)
    row = db.get(ListingSnapshot, url_hash)
    if row is None:
        row = ListingSnapshot(url_hash=url_hash)
        db.add(row)

    row.url_normalizada = data.normalized_url
    row.original_url = data.original_url
    row.plataforma = data.platform
    row.title = data.title
    row.description = data.description
    row.price = data.price
    row.currency = data.currency
    row.seller_name = data.seller_name
    row.seller_reputation = data.seller_reputation
    row.seller_rating = data.seller_rating
    row.seller_reviews_count = data.seller_reviews_count
    row.image_url = data.image_url
    row.scraped_at = data.scraped_at
    row.snapshot = data.model_dump(mode="json")

    db.commit()
    db.refresh(row)
    return row


def to_read_schema(row: ListingSnapshot) -> ListingSnapshotRead:
    return ListingSnapshotRead(
        id=row.url_hash,
        platform=row.plataforma,
        original_url=row.original_url or row.url_normalizada,
        normalized_url=row.url_normalizada,
        title=row.title,
        description=row.description,
        price=row.price,
        currency=row.currency,
        seller_name=row.seller_name,
        seller_reputation=row.seller_reputation,
        seller_rating=row.seller_rating,
        seller_reviews_count=row.seller_reviews_count,
        image_url=row.image_url,
        scraped_at=row.scraped_at,
    )
