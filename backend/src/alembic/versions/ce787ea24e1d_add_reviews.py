"""add reviews

Revision ID: ce787ea24e1d
Revises: 6beafdcb6f15
Create Date: 2026-08-13 13:37:36.676339
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "ce787ea24e1d"
down_revision: Union[str, Sequence[str], None] = "6beafdcb6f15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "booking_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "master_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "client_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "rating",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "comment",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_reviews_rating_range",
        ),
        sa.ForeignKeyConstraint(
            ["booking_id"],
            ["bookings.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["master_id"],
            ["masters.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "booking_id",
            name="uq_reviews_booking_id",
        ),
    )

    op.create_index(
        op.f("ix_reviews_client_id"),
        "reviews",
        ["client_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_reviews_master_id"),
        "reviews",
        ["master_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_reviews_master_id"),
        table_name="reviews",
    )

    op.drop_index(
        op.f("ix_reviews_client_id"),
        table_name="reviews",
    )

    op.drop_table("reviews")
