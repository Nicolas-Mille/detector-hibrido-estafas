"""Registro de adaptadores de ingesta por plataforma."""

from app.services.ingestion.adapters.base import ListingAdapter
from app.services.ingestion.adapters.facebook_fixture import FacebookFixtureAdapter
from app.services.ingestion.adapters.mercadolibre import MercadoLibreAdapter

ADAPTER_REGISTRY: dict[str, ListingAdapter] = {
    "mercadolibre": MercadoLibreAdapter(),
    "facebook_marketplace": FacebookFixtureAdapter(),
}


def get_adapter(platform: str) -> ListingAdapter:
    try:
        return ADAPTER_REGISTRY[platform]
    except KeyError as exc:
        raise ValueError(f"No hay adaptador registrado para la plataforma '{platform}'") from exc
