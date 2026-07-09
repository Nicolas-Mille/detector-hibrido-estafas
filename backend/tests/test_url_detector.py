from app.services.ingestion.url_detector import detect_platform


def test_detecta_mercadolibre_articulo():
    result = detect_platform("https://articulo.mercadolibre.com.ar/MLA-123456-iphone-15-_JM")
    assert result.platform == "mercadolibre"


def test_detecta_mercadolibre_dominio_base():
    result = detect_platform("https://www.mercadolibre.com.ar/iphone-15/p/MLA123")
    assert result.platform == "mercadolibre"


def test_detecta_facebook_marketplace():
    result = detect_platform("https://www.facebook.com/marketplace/item/1234567890")
    assert result.platform == "facebook_marketplace"


def test_facebook_sin_marketplace_es_unsupported():
    result = detect_platform("https://www.facebook.com/algunapagina")
    assert result.platform == "unsupported"


def test_url_de_dominio_no_soportado():
    result = detect_platform("https://example.com/producto/1")
    assert result.platform == "unsupported"


def test_url_vacia_no_rompe():
    result = detect_platform("")
    assert result.platform == "unsupported"
    assert result.normalized_url == ""


def test_normaliza_quitando_query_de_tracking():
    result = detect_platform(
        "https://articulo.mercadolibre.com.ar/MLA-123?utm_source=x&matt_word=y&foo=bar"
    )
    assert "utm_source" not in result.normalized_url
    assert "matt_word" not in result.normalized_url
    assert "foo=bar" in result.normalized_url


def test_normaliza_quitando_barra_final():
    result = detect_platform("https://www.mercadolibre.com.ar/iphone-15/p/MLA123/")
    assert not result.normalized_url.endswith("MLA123/")
