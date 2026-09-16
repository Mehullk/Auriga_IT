from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from App.database import get_db
from App.models import Equipment, Borrower, Rental, RentalItem
from App.models.loan_transfer import LoanTransfer

router = APIRouter(prefix="/api")


# ---------- Schemas ----------

class EquipmentCreate(BaseModel):
    name: str
    category: str
    total_quantity: int
    daily_fee: float
    deposit_per_unit: float
    late_fee_per_day: float


class BorrowerCreate(BaseModel):
    name: str
    student_id: str
    phone_number: str
    club: str | None = None


class RentalItemCreate(BaseModel):
    equipment_id: int
    quantity: int


class RentalCreate(BaseModel):
    borrower_id: int
    start_date: date
    expected_return_date: date
    items: list[RentalItemCreate]


class TransferCreate(BaseModel):
    to_borrower_id: int
    reason: str | None = None


# ---------- Equipment ----------

@router.get("/equipment")
def get_equipment(db: Session = Depends(get_db)):
    equipment = db.query(Equipment).all()

    return [
        {
            "id": e.id,
            "name": e.name,
            "category": e.category,
            "total_quantity": e.total_quantity,
            "daily_fee": e.daily_fee,
            "deposit_per_unit": e.deposit_per_unit,
            "late_fee_per_day": e.late_fee_per_day,
        }
        for e in equipment
    ]


@router.post("/equipment")
def create_equipment(
    data: EquipmentCreate,
    db: Session = Depends(get_db)
):
    equipment = Equipment(**data.model_dump())

    db.add(equipment)
    db.commit()
    db.refresh(equipment)

    return equipment


# ---------- Borrowers ----------

@router.get("/borrowers")
def get_borrowers(db: Session = Depends(get_db)):
    return db.query(Borrower).all()


@router.post("/borrowers")
def create_borrower(
    data: BorrowerCreate,
    db: Session = Depends(get_db)
):
    if db.query(Borrower).filter(
        Borrower.student_id == data.student_id
    ).first():
        raise HTTPException(400, "Student ID already exists")

    borrower = Borrower(**data.model_dump())

    db.add(borrower)
    db.commit()
    db.refresh(borrower)

    return borrower


# ---------- Availability ----------

def booked_quantity(
    db: Session,
    equipment_id: int,
    target_date: date
):
    rentals = db.query(Rental).filter(
        Rental.start_date <= target_date,
        Rental.expected_return_date >= target_date,
        Rental.status.in_(["RESERVED", "ISSUED", "OVERDUE"])
    ).all()

    total = 0

    for rental in rentals:
        for item in rental.items:
            if item.equipment_id == equipment_id:
                total += item.quantity

    return total


@router.get("/availability")
def availability(
    start_date: date | None = None,
    days: int = 15,
    db: Session = Depends(get_db)
):
    start_date = start_date or date.today()
    days = min(max(days, 1), 15)

    result = []

    for equipment in db.query(Equipment).all():
        daily = []

        for i in range(days):
            d = start_date + timedelta(days=i)
            booked = booked_quantity(db, equipment.id, d)

            daily.append({
                "date": d.isoformat(),
                "booked": booked,
                "available": max(
                    0,
                    equipment.total_quantity - booked
                )
            })

        result.append({
            "equipment_id": equipment.id,
            "name": equipment.name,
            "total_quantity": equipment.total_quantity,
            "days": daily
        })

    return result


# ---------- Rentals ----------

@router.post("/rentals")
def create_rental(
    data: RentalCreate,
    db: Session = Depends(get_db)
):
    borrower = db.get(Borrower, data.borrower_id)

    if not borrower:
        raise HTTPException(404, "Borrower not found")

    if data.start_date > data.expected_return_date:
        raise HTTPException(400, "Invalid dates")

    days = (
        data.expected_return_date - data.start_date
    ).days + 1

    rental = Rental(
        borrower_id=borrower.id,
        start_date=data.start_date,
        expected_return_date=data.expected_return_date,
        status="RESERVED"
    )

    db.add(rental)
    db.flush()

    total_charge = 0
    total_deposit = 0

    for requested in data.items:

        equipment = db.get(
            Equipment,
            requested.equipment_id
        )

        if not equipment:
            db.rollback()
            raise HTTPException(
                404,
                "Equipment not found"
            )

        if requested.quantity <= 0:
            db.rollback()
            raise HTTPException(
                400,
                "Quantity must be positive"
            )

        current = data.start_date

        while current <= data.expected_return_date:

            booked = booked_quantity(
                db,
                equipment.id,
                current
            )

            if booked + requested.quantity > equipment.total_quantity:
                db.rollback()
                raise HTTPException(
                    400,
                    f"{equipment.name} unavailable on {current}"
                )

            # Fair-use rule:
            # equipment with >3 units → max half per person
            if equipment.total_quantity > 3:
                limit = equipment.total_quantity // 2

                person_booked = 0

                existing = db.query(Rental).filter(
                    Rental.borrower_id == borrower.id,
                    Rental.start_date <= current,
                    Rental.expected_return_date >= current,
                    Rental.status.in_(
                        ["RESERVED", "ISSUED", "OVERDUE"]
                    )
                ).all()

                for r in existing:
                    for item in r.items:
                        if item.equipment_id == equipment.id:
                            person_booked += item.quantity

                if person_booked + requested.quantity > limit:
                    db.rollback()
                    raise HTTPException(
                        400,
                        f"Fair-use limit exceeded. "
                        f"Maximum {limit} units per day."
                    )

            current += timedelta(days=1)

        db.add(
            RentalItem(
                rental_id=rental.id,
                equipment_id=equipment.id,
                quantity=requested.quantity,
                daily_fee=equipment.daily_fee
            )
        )

        total_charge += (
            equipment.daily_fee *
            requested.quantity *
            days
        )

        total_deposit += (
            equipment.deposit_per_unit *
            requested.quantity
        )

    rental.rental_charge = total_charge
    rental.deposit_amount = total_deposit

    db.commit()
    db.refresh(rental)

    return {
        "id": rental.id,
        "borrower_id": rental.borrower_id,
        "start_date": rental.start_date,
        "expected_return_date": rental.expected_return_date,
        "rental_charge": rental.rental_charge,
        "deposit_amount": rental.deposit_amount,
        "status": rental.status
    }


@router.get("/rentals")
def get_rentals(db: Session = Depends(get_db)):
    rentals = db.query(Rental).order_by(
        Rental.id.desc()
    ).all()

    return [
        {
            "id": r.id,
            "borrower": r.borrower.name,
            "student_id": r.borrower.student_id,
            "start_date": r.start_date,
            "expected_return_date": r.expected_return_date,
            "actual_return_date": r.actual_return_date,
            "status": r.status,
            "rental_charge": r.rental_charge,
            "deposit_amount": r.deposit_amount,
            "late_fee": r.late_fee,
            "items": [
                {
                    "equipment": item.equipment.name,
                    "quantity": item.quantity
                }
                for item in r.items
            ]
        }
        for r in rentals
    ]


# ---------- Issue ----------

@router.post("/rentals/{rental_id}/issue")
def issue_rental(
    rental_id: int,
    db: Session = Depends(get_db)
):
    rental = db.get(Rental, rental_id)

    if not rental:
        raise HTTPException(404, "Rental not found")

    if rental.status != "RESERVED":
        raise HTTPException(400, "Rental is not reserved")

    rental.status = "ISSUED"

    db.commit()

    return {
        "message": "Equipment issued",
        "status": rental.status
    }


# ---------- Return ----------

@router.post("/rentals/{rental_id}/return")
def return_rental(
    rental_id: int,
    db: Session = Depends(get_db)
):
    rental = db.get(Rental, rental_id)

    if not rental:
        raise HTTPException(404, "Rental not found")

    if rental.status not in ["ISSUED", "OVERDUE"]:
        raise HTTPException(
            400,
            "Only active loans can be returned"
        )

    today = date.today()

    late_days = max(
        0,
        (today - rental.expected_return_date).days
    )

    late_fee = sum(
        item.equipment.late_fee_per_day *
        item.quantity *
        late_days
        for item in rental.items
    )

    rental.actual_return_date = today
    rental.late_fee = late_fee
    rental.status = "RETURNED"

    refund = max(
        0,
        rental.deposit_amount - late_fee
    )

    db.commit()

    return {
        "message": "Equipment returned",
        "late_days": late_days,
        "late_fee": late_fee,
        "deposit": rental.deposit_amount,
        "refund": refund
    }


# ---------- Transfer ----------

@router.post("/rentals/{rental_id}/transfer")
def transfer_rental(
    rental_id: int,
    data: TransferCreate,
    db: Session = Depends(get_db)
):
    rental = db.get(Rental, rental_id)

    if not rental:
        raise HTTPException(404, "Rental not found")

    if rental.status not in ["ISSUED", "OVERDUE"]:
        raise HTTPException(
            400,
            "Only active loans can be transferred"
        )

    new_borrower = db.get(
        Borrower,
        data.to_borrower_id
    )

    if not new_borrower:
        raise HTTPException(
            404,
            "Target borrower not found"
        )

    if new_borrower.id == rental.borrower_id:
        raise HTTPException(
            400,
            "Same borrower"
        )

    old_borrower = rental.borrower_id

    db.add(
        LoanTransfer(
            rental_id=rental.id,
            from_borrower_id=old_borrower,
            to_borrower_id=new_borrower.id,
            reason=data.reason
        )
    )

    rental.borrower_id = new_borrower.id

    db.commit()

    return {
        "message": "Loan transferred",
        "previous_borrower_id": old_borrower,
        "new_borrower_id": new_borrower.id,
        "due_date": rental.expected_return_date
    }