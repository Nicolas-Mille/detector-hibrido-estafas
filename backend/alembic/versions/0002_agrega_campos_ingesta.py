"""agrega campos normalizados de ingesta a listing_snapshots

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-08

"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("listing_snapshots", sa.Column("original_url", sa.String(2048), nullable=True))
    op.add_column("listing_snapshots", sa.Column("title", sa.String(512), nullable=True))
    op.add_column("listing_snapshots", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("listing_snapshots", sa.Column("price", sa.Float(), nullable=True))
    op.add_column("listing_snapshots", sa.Column("currency", sa.String(8), nullable=True))
    op.add_column("listing_snapshots", sa.Column("seller_name", sa.String(255), nullable=True))
    op.add_column("listing_snapshots", sa.Column("seller_reputation", sa.String(64), nullable=True))
    op.add_column("listing_snapshots", sa.Column("seller_rating", sa.Float(), nullable=True))
    op.add_column("listing_snapshots", sa.Column("seller_reviews_count", sa.Integer(), nullable=True))
    op.add_column("listing_snapshots", sa.Column("image_url", sa.String(2048), nullable=True))
    op.add_column("listing_snapshots", sa.Column("scraped_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("listing_snapshots", "scraped_at")
    op.drop_column("listing_snapshots", "image_url")
    op.drop_column("listing_snapshots", "seller_reviews_count")
    op.drop_column("listing_snapshots", "seller_rating")
    op.drop_column("listing_snapshots", "seller_reputation")
    op.drop_column("listing_snapshots", "seller_name")
    op.drop_column("listing_snapshots", "currency")
    op.drop_column("listing_snapshots", "price")
    op.drop_column("listing_snapshots", "description")
    op.drop_column("listing_snapshots", "title")
    op.drop_column("listing_snapshots", "original_url")
