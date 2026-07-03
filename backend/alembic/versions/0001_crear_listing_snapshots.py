"""crear tabla listing_snapshots

Revision ID: 0001
Revises:
Create Date: 2026-07-03

"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "listing_snapshots",
        sa.Column("url_hash", sa.String(64), primary_key=True),
        sa.Column("url_normalizada", sa.String(2048), nullable=False),
        sa.Column("plataforma", sa.String(32), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=True),
        sa.Column("nivel_resolucion", sa.SmallInteger(), nullable=True),
        sa.Column("score_ml", sa.Float(), nullable=True),
        sa.Column("score_llm", sa.Float(), nullable=True),
        sa.Column("score_final", sa.Float(), nullable=True),
        sa.Column("indicadores", sa.JSON(), nullable=True),
        sa.Column("veredicto", sa.Text(), nullable=True),
        sa.Column("tokens_gastados", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "creado_en",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_listing_snapshots_creado_en", "listing_snapshots", ["creado_en"])


def downgrade() -> None:
    op.drop_index("ix_listing_snapshots_creado_en", table_name="listing_snapshots")
    op.drop_table("listing_snapshots")
