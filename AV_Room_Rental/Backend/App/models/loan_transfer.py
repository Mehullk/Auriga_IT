from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from App.database import Base


class LoanTransfer(Base):
    __tablename__ = "loan_transfers"

    id = Column(Integer, primary_key=True, index=True)

    rental_id = Column(
        Integer,
        ForeignKey("rentals.id"),
        nullable=False
    )

    from_borrower_id = Column(
        Integer,
        ForeignKey("borrowers.id"),
        nullable=False
    )

    to_borrower_id = Column(
        Integer,
        ForeignKey("borrowers.id"),
        nullable=False
    )

    transferred_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    reason = Column(String(255), nullable=True)

    rental = relationship("Rental", back_populates="transfers")

    from_borrower = relationship(
        "Borrower",
        foreign_keys=[from_borrower_id]
    )

    to_borrower = relationship(
        "Borrower",
        foreign_keys=[to_borrower_id]
    )