from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from App.database import Base


class Rental(Base):
    __tablename__ = "rentals"

    id = Column(Integer, primary_key=True, index=True)

    borrower_id = Column(
        Integer,
        ForeignKey("borrowers.id"),
        nullable=False,
    )

    start_date = Column(Date, nullable=False)
    expected_return_date = Column(Date, nullable=False)
    actual_return_date = Column(Date, nullable=True)

    deposit_amount = Column(Float, default=0)
    rental_charge = Column(Float, default=0)
    late_fee = Column(Float, default=0)

    status = Column(
        String(20),
        nullable=False,
        default="RESERVED",
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    borrower = relationship(
        "Borrower",
        back_populates="rentals",
    )

    items = relationship(
        "RentalItem",
        back_populates="rental",
        cascade="all, delete-orphan",
    )

    transfers = relationship(
        "LoanTransfer",
        back_populates="rental",
        cascade="all, delete-orphan",
    )