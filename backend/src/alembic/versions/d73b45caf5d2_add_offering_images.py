"""add offering images

Revision ID: d73b45caf5d2
Revises: 3efc6eb3d0e0
Create Date: 2026-08-12 21:20:19.406978

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.

revision: str = "d73b45caf5d2"
down_revision: Union[str, Sequence[str], None] = "3efc6eb3d0e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "offering_images",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "offering_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "storage_key",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "is_primary",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["offering_id"],
            ["master_services.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )

    op.create_index(
        op.f("ix_offering_images_offering_id"),
        "offering_images",
        ["offering_id"],
        unique=False,
    )

    op.create_index(
        "uq_offering_images_one_primary",
        "offering_images",
        ["offering_id"],
        unique=True,
        postgresql_where=sa.text("is_primary = true"),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "uq_offering_images_one_primary",
        table_name="offering_images",
    )

    op.drop_index(
        op.f("ix_offering_images_offering_id"),
        table_name="offering_images",
    )

    op.drop_table("offering_images")
