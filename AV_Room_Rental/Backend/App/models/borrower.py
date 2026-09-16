from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from App.database import Base


class Borrower(Base):
    __tablename__ = "borrowers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    student_id = Column(String(50), nullable=False, unique=True, index=True)
    phone_number = Column(String(20), nullable=False)
    club = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    rentals = relationship(
        "Rental",
        back_populates="borrower"
    )