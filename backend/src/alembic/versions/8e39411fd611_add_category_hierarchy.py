"""add category hierarchy

Revision ID: 8e39411fd611
Revises: ce787ea24e1d
Create Date: 2026-08-14 16:22:49.117660
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8e39411fd611"
down_revision: Union[str, Sequence[str], None] = "ce787ea24e1d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "categories",
        sa.Column(
            "parent_id",
            sa.UUID(),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_categories_parent_id"),
        "categories",
        ["parent_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_categories_parent_id",
        "categories",
        "categories",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_categories_parent_id",
        "categories",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_categories_parent_id"),
        table_name="categories",
    )

    op.drop_column(
        "categories",
        "parent_id",
    )