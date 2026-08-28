"""add user avatar

Revision ID: 6beafdcb6f15
Revises: d73b45caf5d2
Create Date: 2026-08-13 01:33:18.887891
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.

revision: str = "6beafdcb6f15"
down_revision: Union[str, Sequence[str], None] = "d73b45caf5d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "avatar_storage_key",
            sa.String(length=255),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "users",
        "avatar_storage_key",
    )
