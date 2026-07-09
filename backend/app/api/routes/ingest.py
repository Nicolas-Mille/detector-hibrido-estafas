from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud.listing_snapshot import to_read_schema, upsert_listing_snapshot
from app.db.session import get_db
from app.schemas.listing import IngestionRequest, IngestionResponse
from app.services.ingestion.adapters.base import AdapterFetchError
from app.services.ingestion.registry import get_adapter
from app.services.ingestion.url_detector import detect_platform

router = APIRouter(prefix="/api", tags=["ingestion"])


@router.post("/ingest", response_model=IngestionResponse)
def ingest_listing(payload: IngestionRequest, db: Session = Depends(get_db)) -> IngestionResponse:
    detection = detect_platform(payload.url)

    if detection.platform == "unsupported":
        return IngestionResponse(
            status="error",
            platform="unsupported",
            source="unsupported",
            message="URL platform is not supported yet",
        )

    adapter = get_adapter(detection.platform)
    try:
        result = adapter.fetch_listing(detection)
    except AdapterFetchError as exc:
        return IngestionResponse(
            status="error",
            platform=detection.platform,
            message=str(exc),
        )

    row = upsert_listing_snapshot(db, result.data)
    return IngestionResponse(
        status="success",
        platform=detection.platform,
        source=result.source,
        snapshot=to_read_schema(row),
        warnings=result.warnings,
    )
