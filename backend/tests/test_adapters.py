import httpx
import pytest

from app.services.ingestion.adapters.base import AdapterFetchError
from app.services.ingestion.adapters.facebook_fixture import FacebookFixtureAdapter
from app.services.ingestion.adapters.mercadolibre import MercadoLibreAdapter
from app.services.ingestion.url_detector import detect_platform

SAMPLE_HTML_JSON_LD = """
<html><head>
<script type="application/ld+json">
{"@type": "Product", "name": "iPhone 15 128GB Azul", "description": "Nuevo, sellado",
 "image": "https://http2.mlstatic.com/foo.jpg",
 "offers": {"price": "850000", "priceCurrency": "ARS"}}
</script>
</head><body></body></html>
"""


def _fake_response(html: str, status_code: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code=status_code, text=html, request=httpx.Request("GET", "https://x")
    )


def test_mercadolibre_adapter_extrae_json_ld():
    adapter = MercadoLibreAdapter(http_get=lambda url: _fake_response(SAMPLE_HTML_JSON_LD))
    detection = detect_platform("https://articulo.mercadolibre.com.ar/MLA-123-iphone")

    result = adapter.fetch_listing(detection)

    assert result.source == "live_scrape"
    assert result.data.title == "iPhone 15 128GB Azul"
    assert result.data.price == 850000
    assert result.data.currency == "ARS"
    assert result.data.image_url == "https://http2.mlstatic.com/foo.jpg"


def test_mercadolibre_adapter_html_vacio_devuelve_nulos_con_warning():
    adapter = MercadoLibreAdapter(http_get=lambda url: _fake_response("<html></html>"))
    detection = detect_platform("https://articulo.mercadolibre.com.ar/MLA-999")

    result = adapter.fetch_listing(detection)

    assert result.data.title is None
    assert result.data.price is None
    assert len(result.warnings) > 0


def test_mercadolibre_adapter_error_de_red_es_controlado():
    def _raise(url: str) -> httpx.Response:
        raise httpx.ConnectError("boom", request=httpx.Request("GET", url))

    adapter = MercadoLibreAdapter(http_get=_raise)
    detection = detect_platform("https://articulo.mercadolibre.com.ar/MLA-1")

    with pytest.raises(AdapterFetchError):
        adapter.fetch_listing(detection)


def test_facebook_fixture_adapter_reconoce_keyword_iphone():
    adapter = FacebookFixtureAdapter()
    detection = detect_platform(
        "https://www.facebook.com/marketplace/item/iphone-13-pro-suspicious"
    )

    result = adapter.fetch_listing(detection)

    assert result.source == "fixture"
    assert "iPhone" in result.data.title
    assert result.data.platform == "facebook_marketplace"
    assert result.warnings == []


def test_facebook_fixture_adapter_usa_default_si_no_reconoce_keyword():
    adapter = FacebookFixtureAdapter()
    detection = detect_platform("https://www.facebook.com/marketplace/item/999999")

    result = adapter.fetch_listing(detection)

    assert result.source == "fixture"
    assert len(result.warnings) == 1
