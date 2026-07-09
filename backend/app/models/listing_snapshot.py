from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ListingSnapshot(Base):
    """Resultado de análisis de una publicación, usado también como caché (TTL 7 días).

    nivel_resolucion: 0 = caché, 1 = heurísticas, 2 = ML local, 3 = LLM multimodal.
    """

    __tablename__ = "listing_snapshots"

    url_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    url_normalizada: Mapped[str] = mapped_column(String(2048), nullable=False)
    plataforma: Mapped[str] = mapped_column(String(32), nullable=False)
    original_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    seller_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seller_reputation: Mapped[str | None] = mapped_column(String(64), nullable=True)
    seller_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    seller_reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    scraped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    nivel_resolucion: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    score_ml: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_llm: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_final: Mapped[float | None] = mapped_column(Float, nullable=True)
    indicadores: Mapped[list | None] = mapped_column(JSON, nullable=True)
    veredicto: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_gastados: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )
