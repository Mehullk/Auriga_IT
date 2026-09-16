# AV Room Rental Management System

A web-based equipment rental management system for managing a college AV room. The system tracks equipment, borrowers, rentals, availability, returns, deposits, late fees, and active loan transfers.

## Problem

The college AV room lends equipment such as DSLR cameras, projectors, microphones, and tripods. The previous paper-based process made it difficult to know:

- Which equipment is available
- How many units are currently booked
- Who currently has an item
- When equipment is due back
- Which rentals are overdue
- How much deposit should be refunded
- Whether equipment can be booked without causing conflicts
- How to transfer an active loan to another borrower

This application provides a centralized system for handling these operations.

---

## Features

### Equipment Management

- Add AV equipment
- Store equipment category
- Track total quantity
- Configure daily rental fee
- Configure refundable deposit per unit
- Configure late fee per day
- Support multiple units of the same equipment

### Borrower Management

- Register borrowers
- Store borrower name
- Store email
- Store phone number

### Availability

- Check equipment availability for a specific date
- Display total quantity
- Display booked quantity
- Display available quantity
- Prevent rentals from exceeding available stock

### Rental Management

- Create equipment rentals
- Select borrower
- Select equipment
- Specify quantity
- Specify start date
- Specify due date
- Calculate rental charges
- Calculate refundable deposit

### Returns

- Record equipment returns
- Calculate late days
- Calculate applicable late fees
- Calculate refundable deposit after deductions

The refund calculation is:

```text
Refundable Amount = Deposit - Late Fee
Loan Transfer

An active rental can be transferred from one borrower to another.

When a transfer occurs:

The borrower changes
The original rental remains active
The original due date remains unchanged
The equipment and quantity remain unchanged
Equipment availability does not change
The transfer is recorded separately

This satisfies the core twist of the problem statement.

Technology Stack
Backend
Python
FastAPI
SQLite
Uvicorn
Pydantic
Frontend
React
Vite
JavaScript
CSS
Project Structure
AV_Room_Rental/
│
├── Backend/
│   ├── App/
│   │   ├── models/
│   │   │   ├── borrower.py
│   │   │   ├── equipment.py
│   │   │   ├── loan_transfer.py
│   │   │   ├── rental.py
│   │   │   └── rental_item.py
│   │   │
│   │   ├── routers/
│   │   │   └── api.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── borrower.py
│   │   │   ├── equipment.py
│   │   │   └── rental.py
│   │   │
│   │   ├── services/
│   │   │   └── rental_service.py
│   │   │
│   │   ├── database.py
│   │   └── main.py
│   │
│   ├── requirements.txt
│   └── av_room.db
│
├── Frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── vite.config.js
│
├── README.md
├── REASONING.md
└── AI_LOGS.md
Backend Setup

Navigate to the backend:

cd Backend

Create a virtual environment:

python -m venv venv

Activate it on Linux/macOS:

source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Start the backend:

uvicorn App.main:app --reload

The backend will normally be available at:

http://localhost:8000
API Documentation

FastAPI automatically provides Swagger documentation.

Open:

http://localhost:8000/docs

This can be used to inspect and test the API endpoints.

Frontend Setup

Open a second terminal.

Navigate to the frontend:

cd Frontend

Install dependencies:

npm install

Start the development server:

npm run dev -- --host 0.0.0.0

The frontend will normally run on:

http://localhost:5173

When using GitHub Codespaces, open the forwarded Vite port from the Ports panel.

API Endpoints
Health
GET /
GET /health
Equipment
GET /api/equipment
POST /api/equipment
Borrowers
GET /api/borrowers
POST /api/borrowers
Availability
GET /api/availability

Example:

/api/availability?date=2026-09-16
Rentals
POST /api/rentals
POST /api/rentals/{rental_id}/issue
POST /api/rentals/{rental_id}/return
POST /api/rentals/{rental_id}/transfer
Rental Workflow

The normal rental lifecycle is:

Available Equipment
        ↓
    Book Rental
        ↓
    Issue Rental
        ↓
   Active Rental
        ↓
   Return Rental
        ↓
 Equipment Available

An active rental can also follow this path:

Active Rental
      ↓
Transfer Borrower
      ↓
Active Rental

The transfer does not create an additional equipment booking.

Rental Fee Calculation

Rental duration is calculated from the start date and due date.

For example:

Start Date = 2026-09-16
Due Date   = 2026-09-20

The rental duration is:

5 days

For equipment with a daily fee of ₹500:

Rental Fee = 5 × ₹500
           = ₹2500
Deposit Calculation

The refundable deposit depends on the equipment deposit per unit and quantity rented.

For example:

Deposit per unit = ₹5000
Quantity         = 1

Therefore:

Deposit = ₹5000

The deposit is returned after the equipment is returned, subject to applicable late-fee deductions.

Late Fee Calculation

If equipment is returned after its due date, late fees are calculated using the equipment's configured late fee per day.

For example:

Late fee per day = ₹200
Late days        = 3

Then:

Late Fee = 3 × ₹200
         = ₹600

The refundable amount becomes:

Refundable Amount = Deposit - Late Fee
Availability Rules

The system tracks multiple units of the same equipment.

For example:

DSLR Camera
Total Quantity = 3
Booked Quantity = 1
Available Quantity = 2

A rental request cannot exceed the available quantity.

This prevents two borrowers from booking the same physical units simultaneously.

Loan Transfer Rules

The transfer feature was designed around the special requirement in the problem statement.

For an active rental:

Original Borrower
       ↓
     Transfer
       ↓
New Borrower

The following values remain unchanged:

Equipment
Quantity
Start Date
Due Date
Rental
Availability

Only the borrower associated with the active loan changes.

A transfer record is maintained so that the transfer can be tracked.

Example Transfer

Suppose:

Borrower: Student A
Equipment: DSLR Camera
Quantity: 1
Start Date: 2026-09-16
Due Date: 2026-09-20

The loan is transferred to Student B.

After transfer:

Borrower: Student B
Equipment: DSLR Camera
Quantity: 1
Start Date: 2026-09-16
Due Date: 2026-09-20

The DSLR remains unavailable for the same rental quantity because the equipment was never returned.

Therefore, the transfer does not affect inventory availability.

Error Handling

The API validates important rental conditions such as:

Borrower existence
Equipment existence
Positive rental quantity
Available equipment quantity
Valid rental dates
Active rental status
Valid borrower during transfer

Invalid operations return an appropriate API error instead of silently creating inconsistent rental data.

Running the Complete Application

Start the backend first:

cd Backend
source venv/bin/activate
uvicorn App.main:app --reload

Then start the frontend in another terminal:

cd Frontend
npm run dev -- --host 0.0.0.0

Open the frontend through the forwarded Vite port.

The backend API can be inspected through:

http://localhost:8000/docs
Debugging
Backend does not start

Verify that the virtual environment is active:

source venv/bin/activate

Then:

uvicorn App.main:app --reload

Check:

http://localhost:8000/health
Frontend does not start

Run:

npm install

Then:

npm run dev -- --host 0.0.0.0
Frontend cannot connect to backend

Make sure the backend is running on:

http://localhost:8000

Also ensure that the backend CORS configuration permits the frontend development server.

API debugging

Open:

http://localhost:8000/docs

FastAPI Swagger UI can be used to inspect request schemas and responses.

Design Decisions

The application prioritizes the core requirements of the problem:

Borrowing
Availability
Returns
Deposits
Late fees
Borrower limits
Active loan transfers

The system keeps the equipment availability tied to active rentals rather than borrowers. This makes transferring a loan a change of responsibility rather than a new equipment booking.

This prevents the transfer operation from incorrectly increasing or decreasing available inventory.

Future Improvements

Possible future extensions include:

Automated return reminders
Email notifications
Authentication and role-based access
Detailed audit history
Advanced reporting
Calendar-based availability
Reservation cancellation
Equipment maintenance tracking
Dashboard analytics
Automated overdue notifications
License

This project was created as part of the Auriga IT Round-II Builder Assessment.


