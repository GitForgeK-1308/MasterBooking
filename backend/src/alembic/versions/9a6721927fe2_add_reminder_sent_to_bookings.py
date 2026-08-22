"""add reminder_sent to bookings

Revision ID: 9a6721927fe2
Revises: 9ff73e7a05ef
Create Date: 2026-08-23 00:38:55.857291

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9a6721927fe2'
down_revision: Union[str, Sequence[str], None] = '9ff73e7a05ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "bookings",
        sa.Column(
            "reminder_sent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.alter_column(
        "bookings",
        "reminder_sent",
        server_default=None,
    )
