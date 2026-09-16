from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, timedelta
import sqlite3
import os

DB = "av_room.db"

app = FastAPI(title="AV Room Equipment Rental API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            total_quantity INTEGER NOT NULL,
            daily_fee REAL NOT NULL,
            deposit_per_unit REAL NOT NULL,
            late_fee_per_day REAL NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS borrowers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            borrower_id INTEGER NOT NULL,
            booking_date TEXT NOT NULL,
            start_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            returned_date TEXT,
            status TEXT NOT NULL,
            deposit REAL NOT NULL,
            late_fee REAL DEFAULT 0,
            total_fee REAL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rental_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rental_id INTEGER NOT NULL,
            equipment_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS loan_transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rental_id INTEGER NOT NULL,
            from_borrower_id INTEGER NOT NULL,
            to_borrower_id INTEGER NOT NULL,
            transferred_at TEXT NOT NULL
        )
    """)

    conn.commit()

    # Seed equipment
    count = cur.execute(
        "SELECT COUNT(*) FROM equipment"
    ).fetchone()[0]

    if count == 0:
        equipment = [
            ("DSLR Camera", "Camera", 3, 500, 5000, 200),
            ("Projector", "Projector", 2, 400, 4000, 150),
            ("Microphone", "Audio", 6, 150, 1500, 75),
            ("Tripod", "Accessories", 5, 100, 1000, 50),
        ]

        cur.executemany("""
            INSERT INTO equipment
            (name, category, total_quantity, daily_fee,
             deposit_per_unit, late_fee_per_day)
            VALUES (?, ?, ?, ?, ?, ?)
        """, equipment)

        conn.commit()

    conn.close()


init_db()


# ---------------- SCHEMAS ----------------

class BorrowerCreate(BaseModel):
    name: str
    email: str = ""
    phone: str = ""


class RentalCreate(BaseModel):
    borrower_id: int
    equipment_id: int
    quantity: int
    start_date: date
    due_date: date


class TransferCreate(BaseModel):
    new_borrower_id: int


# ---------------- BASIC ----------------

@app.get("/")
def root():
    return {
        "message": "AV Room Equipment Rental API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# ---------------- EQUIPMENT ----------------

@app.get("/api/equipment")
def get_equipment():
    conn = get_db()

    rows = conn.execute(
        "SELECT * FROM equipment ORDER BY name"
    ).fetchall()

    result = []

    for row in rows:
        result.append(dict(row))

    conn.close()

    return result


@app.post("/api/equipment")
def create_equipment(data: dict):
    conn = get_db()

    cur = conn.execute("""
        INSERT INTO equipment
        (name, category, total_quantity, daily_fee,
         deposit_per_unit, late_fee_per_day)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["category"],
        data["total_quantity"],
        data["daily_fee"],
        data["deposit_per_unit"],
        data["late_fee_per_day"]
    ))

    conn.commit()

    row = conn.execute(
        "SELECT * FROM equipment WHERE id=?",
        (cur.lastrowid,)
    ).fetchone()

    conn.close()

    return dict(row)


# ---------------- BORROWERS ----------------

@app.get("/api/borrowers")
def get_borrowers():
    conn = get_db()

    rows = conn.execute(
        "SELECT * FROM borrowers ORDER BY name"
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


@app.post("/api/borrowers")
def create_borrower(data: BorrowerCreate):
    conn = get_db()

    cur = conn.execute("""
        INSERT INTO borrowers(name, email, phone)
        VALUES (?, ?, ?)
    """, (data.name, data.email, data.phone))

    conn.commit()

    row = conn.execute(
        "SELECT * FROM borrowers WHERE id=?",
        (cur.lastrowid,)
    ).fetchone()

    conn.close()

    return dict(row)


# ---------------- AVAILABILITY ----------------

@app.get("/api/availability")
def availability(check_date: date = None):

    if check_date is None:
        check_date = date.today()

    conn = get_db()

    equipment = conn.execute(
        "SELECT * FROM equipment ORDER BY name"
    ).fetchall()

    result = []

    for item in equipment:

        booked = conn.execute("""
            SELECT COALESCE(SUM(ri.quantity), 0)
            FROM rental_items ri
            JOIN rentals r ON r.id = ri.rental_id
            WHERE ri.equipment_id = ?
            AND r.status IN ('BOOKED', 'ISSUED')
            AND date(r.start_date) <= date(?)
            AND date(r.due_date) >= date(?)
        """, (
            item["id"],
            check_date.isoformat(),
            check_date.isoformat()
        )).fetchone()[0]

        result.append({
            "equipment_id": item["id"],
            "name": item["name"],
            "category": item["category"],
            "total_quantity": item["total_quantity"],
            "booked_quantity": booked,
            "available_quantity": max(
                0,
                item["total_quantity"] - booked
            ),
            "daily_fee": item["daily_fee"]
        })

    conn.close()

    return {
        "date": check_date.isoformat(),
        "equipment": result
    }


# ---------------- RENTALS ----------------

@app.get("/api/rentals")
def get_rentals():
    conn = get_db()

    rows = conn.execute("""
        SELECT
            r.id,
            r.booking_date,
            r.start_date,
            r.due_date,
            r.returned_date,
            r.status,
            r.deposit,
            r.late_fee,
            r.total_fee,
            b.name AS borrower_name,
            b.email AS borrower_email,
            b.phone AS borrower_phone,
            e.name AS equipment_name,
            e.category,
            ri.quantity
        FROM rentals r
        JOIN borrowers b ON b.id = r.borrower_id
        JOIN rental_items ri ON ri.rental_id = r.id
        JOIN equipment e ON e.id = ri.equipment_id
        ORDER BY r.id DESC
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]


@app.post("/api/rentals")
def create_rental(data: RentalCreate):

    if data.quantity <= 0:
        raise HTTPException(
            400,
            "Quantity must be greater than zero"
        )

    if data.due_date < data.start_date:
        raise HTTPException(
            400,
            "Due date cannot be before start date"
        )

    conn = get_db()

    equipment = conn.execute(
        "SELECT * FROM equipment WHERE id=?",
        (data.equipment_id,)
    ).fetchone()

    if not equipment:
        conn.close()
        raise HTTPException(404, "Equipment not found")

    borrower = conn.execute(
        "SELECT * FROM borrowers WHERE id=?",
        (data.borrower_id,)
    ).fetchone()

    if not borrower:
        conn.close()
        raise HTTPException(404, "Borrower not found")

    # Per-person, per-equipment limit:
    # one person cannot book more than half
    # of equipment quantity when inventory > 3.
    if equipment["total_quantity"] > 3:
        limit = equipment["total_quantity"] // 2

        if data.quantity > limit:
            conn.close()
            raise HTTPException(
                400,
                f"Maximum allowed quantity is {limit} for this equipment"
            )

    # Check overlapping bookings
    booked = conn.execute("""
        SELECT COALESCE(SUM(ri.quantity), 0)
        FROM rental_items ri
        JOIN rentals r ON r.id = ri.rental_id
        WHERE ri.equipment_id = ?
        AND r.status IN ('BOOKED', 'ISSUED')
        AND date(r.start_date) <= date(?)
        AND date(r.due_date) >= date(?)
    """, (
        data.equipment_id,
        data.due_date.isoformat(),
        data.start_date.isoformat()
    )).fetchone()[0]

    if booked + data.quantity > equipment["total_quantity"]:
        conn.close()
        raise HTTPException(
            400,
            "Equipment is not available for the selected dates"
        )

    days = (data.due_date - data.start_date).days + 1

    daily_cost = equipment["daily_fee"] * data.quantity
    total_fee = daily_cost * days

    deposit = equipment["deposit_per_unit"] * data.quantity

    cur = conn.execute("""
        INSERT INTO rentals
        (borrower_id, booking_date, start_date, due_date,
         status, deposit, total_fee)
        VALUES (?, ?, ?, ?, 'BOOKED', ?, ?)
    """, (
        data.borrower_id,
        date.today().isoformat(),
        data.start_date.isoformat(),
        data.due_date.isoformat(),
        deposit,
        total_fee
    ))

    rental_id = cur.lastrowid

    conn.execute("""
        INSERT INTO rental_items
        (rental_id, equipment_id, quantity)
        VALUES (?, ?, ?)
    """, (
        rental_id,
        data.equipment_id,
        data.quantity
    ))

    conn.commit()

    conn.close()

    return {
        "message": "Rental booked successfully",
        "rental_id": rental_id,
        "days": days,
        "rental_fee": total_fee,
        "deposit": deposit
    }


# ---------------- ISSUE ----------------

@app.post("/api/rentals/{rental_id}/issue")
def issue_rental(rental_id: int):

    conn = get_db()

    rental = conn.execute(
        "SELECT * FROM rentals WHERE id=?",
        (rental_id,)
    ).fetchone()

    if not rental:
        conn.close()
        raise HTTPException(404, "Rental not found")

    if rental["status"] != "BOOKED":
        conn.close()
        raise HTTPException(
            400,
            "Only booked rentals can be issued"
        )

    conn.execute("""
        UPDATE rentals
        SET status='ISSUED'
        WHERE id=?
    """, (rental_id,))

    conn.commit()
    conn.close()

    return {
        "message": "Equipment issued",
        "rental_id": rental_id
    }


# ---------------- RETURN ----------------

@app.post("/api/rentals/{rental_id}/return")
def return_rental(rental_id: int):

    conn = get_db()

    rental = conn.execute("""
        SELECT r.*, ri.quantity, e.late_fee_per_day
        FROM rentals r
        JOIN rental_items ri ON ri.rental_id = r.id
        JOIN equipment e ON e.id = ri.equipment_id
        WHERE r.id=?
    """, (rental_id,)).fetchone()

    if not rental:
        conn.close()
        raise HTTPException(404, "Rental not found")

    if rental["status"] not in ("BOOKED", "ISSUED"):
        conn.close()
        raise HTTPException(
            400,
            "Rental has already been returned"
        )

    today = date.today()
    due = date.fromisoformat(rental["due_date"])

    late_days = max(0, (today - due).days)

    late_fee = (
        late_days *
        rental["late_fee_per_day"] *
        rental["quantity"]
    )

    refundable_deposit = max(
        0,
        rental["deposit"] - late_fee
    )

    conn.execute("""
        UPDATE rentals
        SET
            status='RETURNED',
            returned_date=?,
            late_fee=?
        WHERE id=?
    """, (
        today.isoformat(),
        late_fee,
        rental_id
    ))

    conn.commit()
    conn.close()

    return {
        "message": "Equipment returned",
        "rental_id": rental_id,
        "late_days": late_days,
        "late_fee": late_fee,
        "original_deposit": rental["deposit"],
        "refunded_deposit": refundable_deposit
    }


# ---------------- TRANSFER ----------------

@app.post("/api/rentals/{rental_id}/transfer")
def transfer_rental(
    rental_id: int,
    data: TransferCreate
):

    conn = get_db()

    rental = conn.execute(
        "SELECT * FROM rentals WHERE id=?",
        (rental_id,)
    ).fetchone()

    if not rental:
        conn.close()
        raise HTTPException(404, "Rental not found")

    if rental["status"] != "ISSUED":
        conn.close()
        raise HTTPException(
            400,
            "Only active issued loans can be transferred"
        )

    new_borrower = conn.execute(
        "SELECT * FROM borrowers WHERE id=?",
        (data.new_borrower_id,)
    ).fetchone()

    if not new_borrower:
        conn.close()
        raise HTTPException(404, "New borrower not found")

    if rental["borrower_id"] == data.new_borrower_id:
        conn.close()
        raise HTTPException(
            400,
            "New borrower must be different"
        )

    old_borrower_id = rental["borrower_id"]

    # IMPORTANT:
    # due date is NOT changed.
    # rental itself remains the same.
    conn.execute("""
        UPDATE rentals
        SET borrower_id=?
        WHERE id=?
    """, (
        data.new_borrower_id,
        rental_id
    ))

    conn.execute("""
        INSERT INTO loan_transfers
        (rental_id, from_borrower_id,
         to_borrower_id, transferred_at)
        VALUES (?, ?, ?, ?)
    """, (
        rental_id,
        old_borrower_id,
        data.new_borrower_id,
        date.today().isoformat()
    ))

    conn.commit()
    conn.close()

    return {
        "message": "Loan transferred successfully",
        "rental_id": rental_id,
        "new_borrower_id": data.new_borrower_id,
        "due_date_preserved": True
    }