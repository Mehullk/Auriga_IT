# Reasoning and Design Decisions

## 1. Understanding the Problem

The problem was interpreted as an equipment rental management system for an organization that owns audiovisual equipment such as cameras, projectors, microphones, and tripods.

The system needed to support the complete rental lifecycle rather than only storing equipment records.

The main workflow identified was:

1. Maintain equipment inventory.
2. Maintain borrower information.
3. Check equipment availability.
4. Create a rental booking.
5. Issue equipment to the borrower.
6. Return equipment.
7. Calculate applicable rental, deposit, and late fees.
8. Transfer an active rental to another borrower when required.
9. Provide a simple dashboard for operational visibility.

The solution was therefore designed around the rental lifecycle and the business rules associated with it.

---

## 2. Technology Selection

A lightweight full-stack architecture was selected so that the application could be developed quickly and remain easy to run in GitHub Codespaces.

### Backend

- Python
- FastAPI
- SQLite
- Pydantic

FastAPI was selected because it provides simple REST API development and automatic API documentation.

SQLite was selected because the application is intended as a compact demonstration project and does not require a separate database server.

### Frontend

- React
- Vite
- JavaScript
- CSS

React was selected to provide a responsive single-page interface, while Vite provides a fast development environment.

---

## 3. Data Model

The application uses separate entities for the main business objects.

### Equipment

Equipment stores:

- Name
- Category
- Total quantity
- Daily rental fee
- Deposit per unit
- Late fee per day

Keeping pricing information with equipment makes fee calculation consistent and avoids hardcoding prices into the rental workflow.

### Borrower

Borrower information contains:

- Name
- Email
- Phone

A separate borrower entity allows multiple rentals to be associated with the same person.

### Rental

A rental represents the overall booking and contains information such as:

- Borrower
- Start date
- Due date
- Booking date
- Rental status
- Rental fee
- Deposit

### Rental Items

Rental items connect a rental with specific equipment and quantities.

This separation allows a rental to contain equipment quantities independently of the equipment master record.

---

## 4. Availability Logic

Equipment availability is calculated from the total inventory and currently booked quantities.

The basic calculation is:

Available Quantity = Total Quantity - Booked Quantity

The system checks the rental date range when determining whether equipment can be booked.

A booking is rejected when the requested quantity exceeds the available quantity.

This prevents the same physical inventory from being allocated to multiple rentals beyond the available stock.

---

## 5. Rental Fee Calculation

The rental duration is calculated from the start date and due date.

For the selected inclusive rental period:

Days = Due Date - Start Date + 1

The rental fee is then calculated as:

Rental Fee = Daily Fee × Quantity × Number of Days

For example, if equipment costs ₹500 per day, one unit is rented for five days:

₹500 × 1 × 5 = ₹2,500

The deposit is calculated separately:

Deposit = Deposit Per Unit × Quantity

Keeping the rental fee and deposit separate makes the financial information easier to understand.

---

## 6. Return and Late Fee Logic

The return workflow records when equipment is returned.

If the actual return date exceeds the due date, a late fee is calculated.

The basic calculation is:

Late Days = Actual Return Date - Due Date

Late Fee = Late Days × Late Fee Per Day × Quantity

If the equipment is returned on or before the due date, the late fee is zero.

This keeps normal returns and overdue returns separate.

---

## 7. Equipment Issue Workflow

A booking and an equipment issue are treated as different stages.

### Booking

A borrower reserves equipment for a specified period.

### Issue

The equipment is physically handed over to the borrower.

This separation reflects a real rental process where an item may be booked in advance but has not yet been physically issued.

The rental status therefore provides visibility into the current stage of the rental.

---

## 8. Rental Transfer

A rental may need to be transferred from one borrower to another.

Instead of creating an entirely new rental, the transfer operation changes the borrower associated with the existing rental.

This preserves:

- Rental ID
- Original booking information
- Rental dates
- Equipment allocation
- Existing financial information

The transfer operation therefore maintains historical continuity while changing the responsible borrower.

---

## 9. API Design

The backend exposes REST endpoints for the main operations.

The important endpoints include:

- `GET /health`
- `GET /api/equipment`
- `POST /api/equipment`
- `GET /api/borrowers`
- `POST /api/borrowers`
- `GET /api/availability`
- `POST /api/rentals`
- `POST /api/rentals/{rental_id}/issue`
- `POST /api/rentals/{rental_id}/return`
- `POST /api/rentals/{rental_id}/transfer`

The API-first approach keeps the frontend independent of the database implementation.

It also makes the backend directly testable through FastAPI's Swagger documentation.

---

## 10. Frontend Design

The frontend is organized around the main operations an equipment manager would perform.

The interface provides sections for:

- Dashboard
- Equipment
- Borrowers
- Availability
- Rentals

The dashboard provides a quick operational summary, while the other sections expose the detailed management workflows.

The interface was intentionally kept simple so that the important business operations can be demonstrated quickly without unnecessary complexity.

---

## 11. Error Handling

The backend validates input before performing operations.

Examples include:

- Invalid borrower IDs
- Invalid equipment IDs
- Invalid rental dates
- Requests exceeding available quantity
- Invalid rental state transitions
- Missing required fields

FastAPI/Pydantic validation is used for request validation, while application-level checks handle business rules.

Errors are returned through HTTP responses so that the frontend can display meaningful feedback.

---

## 12. Architectural Approach

The project follows a simple layered structure:

```text
Frontend
   ↓
REST API
   ↓
Application / Service Logic
   ↓
SQLite Database