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


def test_detecta_mercadolibre_meli_la():
    result = detect_platform("https://meli.la/1234567")
    assert result.platform == "mercadolibre"


# --- Regresión SSRF: dominios "parecidos" no deben clasificarse como mercadolibre ---


def test_rechaza_dominio_disfrazado_como_subdominio_de_atacante():
    result = detect_platform("https://mercadolibre.com.atacante.io/x")
    assert result.platform == "unsupported"


def test_rechaza_dominio_falso_con_userinfo_estilo_email():
    result = detect_platform("https://mercadolibre.com@atacante.io/x")
    assert result.platform == "unsupported"


def test_rechaza_host_que_contiene_meli_la_como_substring():
    result = detect_platform("https://somemeli.latency.io/x")
    assert result.platform == "unsupported"


def test_no_arrastra_credenciales_a_la_url_normalizada():
    result = detect_platform("https://user:pass@articulo.mercadolibre.com.ar/MLA-1")
    assert result.platform == "mercadolibre"
    assert "user" not in result.normalized_url
    assert "pass" not in result.normalized_url
    assert "@" not in result.normalized_url


def test_facebook_sigue_funcionando_con_subdominios_reales():
    result = detect_platform("https://m.facebook.com/marketplace/item/555")
    assert result.platform == "facebook_marketplace"


def test_rechaza_dominio_facebook_disfrazado():
    result = detect_platform("https://facebook.com.atacante.io/marketplace/item/1")
    assert result.platform == "unsupported"
