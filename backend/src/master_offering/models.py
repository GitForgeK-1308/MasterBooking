import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from src.database.base import Base
from src.tags.models import master_offering_tags

if TYPE_CHECKING:
    from src.bookings.models import Booking
    from src.categories.models import Category
    from src.masters.models import Master
    from src.offering_images.models import OfferingImage
    from src.tags.models import Tag


class MasterOffering(Base):
    __tablename__ = "master_services"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    master_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "masters.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "categories.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    discount_percent: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    duration_minutes: Mapped[int] = mapped_column(
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    master: Mapped["Master"] = relationship(
        back_populates="master_services",
    )

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="offering",
    )

    category: Mapped["Category | None"] = relationship(
        back_populates="offerings",
    )

    images: Mapped[list["OfferingImage"]] = relationship(
        back_populates="offering",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    tags: Mapped[list["Tag"]] = relationship(
        secondary=master_offering_tags,
        back_populates="offerings",
    )

    @property
    def final_price(self) -> Decimal:
        if self.discount_percent <= 0:
            return self.price

        return (
            self.price * Decimal(100 - self.discount_percent) / Decimal(100)
        ).quantize(Decimal("0.01"))
