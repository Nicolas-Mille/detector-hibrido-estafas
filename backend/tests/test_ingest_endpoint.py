from datetime import UTC, datetime

from app.schemas.listing import ListingSnapshotCreate
from app.services.ingestion import registry
from app.services.ingestion.adapters.base import AdapterResult


class _StubMercadoLibreAdapter:
    def fetch_listing(self, detection):
        data = ListingSnapshotCreate(
            platform="mercadolibre",
            original_url=detection.original_url,
            normalized_url=detection.normalized_url,
            title="iPhone 15 128GB",
            price=850000,
            currency="ARS",
            scraped_at=datetime.now(UTC),
        )
        return AdapterResult(
            data=data, source="live_scrape", warnings=["seller_name no disponible"]
        )


def test_ingest_mercadolibre_ok(client, monkeypatch):
    monkeypatch.setitem(registry.ADAPTER_REGISTRY, "mercadolibre", _StubMercadoLibreAdapter())

    response = client.post(
        "/api/ingest", json={"url": "https://articulo.mercadolibre.com.ar/MLA-123-iphone"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["platform"] == "mercadolibre"
    assert body["source"] == "live_scrape"
    assert body["snapshot"]["title"] == "iPhone 15 128GB"
    assert body["snapshot"]["price"] == 850000
    assert "seller_name no disponible" in body["warnings"]


def test_ingest_facebook_fixture_ok(client):
    response = client.post(
        "/api/ingest",
        json={"url": "https://www.facebook.com/marketplace/item/iphone-13-pro"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["platform"] == "facebook_marketplace"
    assert body["source"] == "fixture"
    assert body["snapshot"]["title"]


def test_ingest_url_no_soportada_devuelve_error_controlado(client):
    response = client.post("/api/ingest", json={"url": "https://example.com/foo"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["platform"] == "unsupported"
    assert body["snapshot"] is None
