from sqlalchemy import create_engine, insert, select

from app.db.base import Base
from app.models import ListingSnapshot


def test_tabla_listing_snapshots_se_crea_y_acepta_filas():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with engine.begin() as conn:
        conn.execute(
            insert(ListingSnapshot).values(
                url_hash="a" * 64,
                url_normalizada="https://articulo.mercadolibre.com.ar/MLA-123",
                plataforma="mercadolibre",
                snapshot={"titulo": "iPhone 15"},
                indicadores=["precio_extremo"],
            )
        )
        fila = conn.execute(select(ListingSnapshot)).one()

    assert fila.url_hash == "a" * 64
    assert fila.plataforma == "mercadolibre"
    assert fila.tokens_gastados == 0
    assert fila.creado_en is not None
