"""Empty migration retained to preserve migration history.

Revision ID: 3efc6eb3d0e0
Revises: 67b68e589493
Create Date: 2026-08-07 18:15:22.514800
"""

from collections.abc import Sequence

revision: str = "3efc6eb3d0e0"
down_revision: str | Sequence[str] | None = "67b68e589493"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass