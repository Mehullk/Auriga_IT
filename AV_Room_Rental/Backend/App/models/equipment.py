from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship

from App.database import Base


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    total_quantity = Column(Integer, nullable=False)
    daily_fee = Column(Float, nullable=False)
    deposit_per_unit = Column(Float, nullable=False)
    late_fee_per_day = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    rental_items = relationship(
        "RentalItem",
        back_populates="equipment"
    )