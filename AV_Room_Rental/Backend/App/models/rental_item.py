from sqlalchemy import Column, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from App.database import Base


class RentalItem(Base):
    __tablename__ = "rental_items"

    id = Column(Integer, primary_key=True, index=True)

    rental_id = Column(
        Integer,
        ForeignKey("rentals.id"),
        nullable=False
    )

    equipment_id = Column(
        Integer,
        ForeignKey("equipment.id"),
        nullable=False
    )

    quantity = Column(Integer, nullable=False)
    daily_fee = Column(Float, nullable=False)

    rental = relationship(
        "Rental",
        back_populates="items"
    )

    equipment = relationship(
        "Equipment",
        back_populates="rental_items"
    )