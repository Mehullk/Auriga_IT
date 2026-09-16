import { useEffect, useState } from "react";
import "./App.css";

const API = "https://organic-space-halibut-9vp67qrxx9529gg-8000.app.github.dev";

function App() {
  const [tab, setTab] = useState("dashboard");

  const [equipment, setEquipment] = useState([]);
  const [borrowers, setBorrowers] = useState([]);
  const [rentals, setRentals] = useState([]);
  const [availability, setAvailability] = useState([]);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [equipmentForm, setEquipmentForm] = useState({
    name: "",
    category: "",
    total_quantity: 1,
    daily_fee: 0,
    deposit_per_unit: 0,
    late_fee_per_day: 0,
  });

  const [borrowerForm, setBorrowerForm] = useState({
    name: "",
    email: "",
    phone: "",
  });

  const [rentalForm, setRentalForm] = useState({
    borrower_id: "",
    equipment_id: "",
    quantity: 1,
    start_date: "",
    due_date: "",
  });

  const [transferForm, setTransferForm] = useState({
    rental_id: "",
    new_borrower_id: "",
  });

  const showMessage = (msg) => {
    setMessage(msg);
    setError("");
    setTimeout(() => setMessage(""), 3500);
  };

  const showError = (msg) => {
    setError(msg);
    setMessage("");
    setTimeout(() => setError(""), 5000);
  };

  const loadData = async () => {
    try {
      const [equipmentRes, borrowersRes, rentalsRes, availabilityRes] =
        await Promise.all([
          fetch(`${API}/api/equipment`),
          fetch(`${API}/api/borrowers`),
          fetch(`${API}/api/rentals`),
          fetch(`${API}/api/availability`),
        ]);

      if (!equipmentRes.ok || !borrowersRes.ok || !rentalsRes.ok) {
        throw new Error("Unable to load backend data");
      }

      const equipmentData = await equipmentRes.json();
      const borrowersData = await borrowersRes.json();
      const rentalsData = await rentalsRes.json();
      const availabilityData = await availabilityRes.json();

      setEquipment(equipmentData);
      setBorrowers(borrowersData);
      setRentals(rentalsData);
      setAvailability(availabilityData.equipment || []);
    } catch (err) {
      console.error(err);
      showError("Backend connection failed. Make sure FastAPI is running.");
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // ---------------- EQUIPMENT ----------------

  const addEquipment = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch(`${API}/api/equipment`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...equipmentForm,
          total_quantity: Number(equipmentForm.total_quantity),
          daily_fee: Number(equipmentForm.daily_fee),
          deposit_per_unit: Number(equipmentForm.deposit_per_unit),
          late_fee_per_day: Number(equipmentForm.late_fee_per_day),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to add equipment");
      }

      setEquipmentForm({
        name: "",
        category: "",
        total_quantity: 1,
        daily_fee: 0,
        deposit_per_unit: 0,
        late_fee_per_day: 0,
      });

      showMessage("Equipment added successfully.");
      loadData();
    } catch (err) {
      showError(err.message);
    }
  };

  // ---------------- BORROWERS ----------------

  const addBorrower = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch(`${API}/api/borrowers`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(borrowerForm),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to add borrower");
      }

      setBorrowerForm({
        name: "",
        email: "",
        phone: "",
      });

      showMessage("Borrower registered successfully.");
      loadData();
    } catch (err) {
      showError(err.message);
    }
  };

  // ---------------- RENTAL ----------------

  const createRental = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch(`${API}/api/rentals`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          borrower_id: Number(rentalForm.borrower_id),
          equipment_id: Number(rentalForm.equipment_id),
          quantity: Number(rentalForm.quantity),
          start_date: rentalForm.start_date,
          due_date: rentalForm.due_date,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to create rental");
      }

      setRentalForm({
        borrower_id: "",
        equipment_id: "",
        quantity: 1,
        start_date: "",
        due_date: "",
      });

      showMessage(
        `Rental #${data.rental_id} booked. Fee ₹${data.rental_fee} | Deposit ₹${data.deposit}`
      );

      loadData();
    } catch (err) {
      showError(err.message);
    }
  };

  // ---------------- ISSUE ----------------

  const issueRental = async (id) => {
    try {
      const response = await fetch(`${API}/api/rentals/${id}/issue`, {
        method: "POST",
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to issue rental");
      }

      showMessage(`Rental #${id} issued successfully.`);
      loadData();
    } catch (err) {
      showError(err.message);
    }
  };

  // ---------------- RETURN ----------------

  const returnRental = async (id) => {
    try {
      const response = await fetch(`${API}/api/rentals/${id}/return`, {
        method: "POST",
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to return rental");
      }

      showMessage(
        `Returned. Late fee: ₹${data.late_fee} | Deposit refunded: ₹${data.refunded_deposit}`
      );

      loadData();
    } catch (err) {
      showError(err.message);
    }
  };

  // ---------------- TRANSFER ----------------

  const transferRental = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch(
        `${API}/api/rentals/${transferForm.rental_id}/transfer`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            new_borrower_id: Number(transferForm.new_borrower_id),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to transfer loan");
      }

      setTransferForm({
        rental_id: "",
        new_borrower_id: "",
      });

      showMessage(
        `Loan #${data.rental_id} transferred successfully. Due date preserved.`
      );

      loadData();
    } catch (err) {
      showError(err.message);
    }
  };

  // ---------------- HELPERS ----------------

  const getBorrowerName = (id) => {
    const borrower = borrowers.find((b) => b.id === id);
    return borrower ? borrower.name : `Borrower #${id}`;
  };

  const getEquipmentName = (id) => {
    const item = equipment.find((e) => e.id === id);
    return item ? item.name : `Equipment #${id}`;
  };

  const activeRentals = rentals.filter(
    (r) => r.status === "ISSUED" || r.status === "BOOKED"
  );

  const issuedRentals = rentals.filter((r) => r.status === "ISSUED");

  const bookedRentals = rentals.filter((r) => r.status === "BOOKED");

  const returnedRentals = rentals.filter((r) => r.status === "RETURNED");

  const totalUnits = equipment.reduce(
    (sum, item) => sum + item.total_quantity,
    0
  );

  const availableUnits = availability.reduce(
    (sum, item) => sum + item.available_quantity,
    0
  );

  // ---------------- UI ----------------

  return (
    <div className="app">
      <header className="navbar">
        <div className="brand">
          <div className="brand-icon">AV</div>

          <div>
            <h1>AV Room Manager</h1>
            <span>Equipment Rental System</span>
          </div>
        </div>

        <div className="nav-actions">
          <button
            className="btn btn-secondary"
            onClick={() => {
              loadData();
              showMessage("Data refreshed.");
            }}
          >
            ↻ Refresh
          </button>
        </div>
      </header>

      <main className="container">
        <div className="page-header">
          <div>
            <h2>
              {tab === "dashboard" && "Dashboard"}
              {tab === "equipment" && "Equipment Inventory"}
              {tab === "borrowers" && "Borrowers"}
              {tab === "rentals" && "Rental Management"}
              {tab === "availability" && "Live Availability"}
              {tab === "transfer" && "Transfer Loan"}
            </h2>

            <p>
              Manage equipment borrowing, availability, returns and transfers.
            </p>
          </div>

          <div className="toolbar">
            {[
              ["dashboard", "Dashboard"],
              ["equipment", "Equipment"],
              ["borrowers", "Borrowers"],
              ["rentals", "Rentals"],
              ["availability", "Availability"],
              ["transfer", "Transfer"],
            ].map(([key, label]) => (
              <button
                key={key}
                className={`btn ${
                  tab === key ? "btn-primary" : "btn-secondary"
                }`}
                onClick={() => setTab(key)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {message && <div className="alert alert-success">{message}</div>}

        {error && <div className="alert alert-error">{error}</div>}

        {/* ================= DASHBOARD ================= */}

        {tab === "dashboard" && (
          <>
            <section className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Equipment Types</div>
                <div className="stat-value">{equipment.length}</div>
                <div className="stat-sub">{totalUnits} total units</div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Available Today</div>
                <div className="stat-value">{availableUnits}</div>
                <div className="stat-sub">Ready to be booked</div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Active Rentals</div>
                <div className="stat-value">{activeRentals.length}</div>
                <div className="stat-sub">
                  {issuedRentals.length} currently issued
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Returned</div>
                <div className="stat-value">{returnedRentals.length}</div>
                <div className="stat-sub">Completed rentals</div>
              </div>
            </section>

            <section className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Live Equipment Availability</h3>
                  <p className="card-subtitle">
                    Current availability based on active bookings.
                  </p>
                </div>

                <button
                  className="btn btn-secondary btn-small"
                  onClick={() => setTab("availability")}
                >
                  View Details
                </button>
              </div>

              <div className="equipment-grid">
                {availability.map((item) => {
                  const percentage =
                    item.total_quantity > 0
                      ? (item.available_quantity / item.total_quantity) * 100
                      : 0;

                  return (
                    <div className="equipment-card" key={item.equipment_id}>
                      <h3>{item.name}</h3>

                      <div className="equipment-category">
                        {item.category}
                      </div>

                      <div className="equipment-count">
                        <strong>{item.available_quantity}</strong>

                        <span>
                          / {item.total_quantity} available
                        </span>
                      </div>

                      <div className="availability-bar">
                        <div
                          className="availability-fill"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>

            <section className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Recent Rentals</h3>
                  <p className="card-subtitle">
                    Latest equipment activity.
                  </p>
                </div>
              </div>

              <RentalTable
                rentals={rentals.slice(0, 8)}
                getBorrowerName={getBorrowerName}
                getEquipmentName={getEquipmentName}
                issueRental={issueRental}
                returnRental={returnRental}
              />
            </section>
          </>
        )}

        {/* ================= EQUIPMENT ================= */}

        {tab === "equipment" && (
          <>
            <section className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Add Equipment</h3>
                  <p className="card-subtitle">
                    Add a new equipment type to the inventory.
                  </p>
                </div>
              </div>

              <form onSubmit={addEquipment}>
                <div className="form-grid">
                  <div className="form-group">
                    <label>Equipment Name</label>
                    <input
                      value={equipmentForm.name}
                      onChange={(e) =>
                        setEquipmentForm({
                          ...equipmentForm,
                          name: e.target.value,
                        })
                      }
                      placeholder="e.g. DSLR Camera"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Category</label>
                    <input
                      value={equipmentForm.category}
                      onChange={(e) =>
                        setEquipmentForm({
                          ...equipmentForm,
                          category: e.target.value,
                        })
                      }
                      placeholder="e.g. Camera"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Total Quantity</label>
                    <input
                      type="number"
                      min="1"
                      value={equipmentForm.total_quantity}
                      onChange={(e) =>
                        setEquipmentForm({
                          ...equipmentForm,
                          total_quantity: e.target.value,
                        })
                      }
                    />
                  </div>

                  <div className="form-group">
                    <label>Daily Rental Fee (₹)</label>
                    <input
                      type="number"
                      min="0"
                      value={equipmentForm.daily_fee}
                      onChange={(e) =>
                        setEquipmentForm({
                          ...equipmentForm,
                          daily_fee: e.target.value,
                        })
                      }
                    />
                  </div>

                  <div className="form-group">
                    <label>Deposit Per Unit (₹)</label>
                    <input
                      type="number"
                      min="0"
                      value={equipmentForm.deposit_per_unit}
                      onChange={(e) =>
                        setEquipmentForm({
                          ...equipmentForm,
                          deposit_per_unit: e.target.value,
                        })
                      }
                    />
                  </div>

                  <div className="form-group">
                    <label>Late Fee Per Day (₹)</label>
                    <input
                      type="number"
                      min="0"
                      value={equipmentForm.late_fee_per_day}
                      onChange={(e) =>
                        setEquipmentForm({
                          ...equipmentForm,
                          late_fee_per_day: e.target.value,
                        })
                      }
                    />
                  </div>
                </div>

                <div className="form-actions">
                  <button className="btn btn-primary">
                    Add Equipment
                  </button>
                </div>
              </form>
            </section>

            <section className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Inventory</h3>
                  <p className="card-subtitle">
                    All equipment currently registered.
                  </p>
                </div>
              </div>

              <div className="equipment-grid">
                {equipment.map((item) => (
                  <div className="equipment-card" key={item.id}>
                    <h3>{item.name}</h3>

                    <div className="equipment-category">
                      {item.category}
                    </div>

                    <div className="equipment-count">
                      <strong>{item.total_quantity}</strong>
                      <span>units</span>
                    </div>

                    <div className="loan-meta">
                      ₹{item.daily_fee}/day
                      <br />
                      Deposit: ₹{item.deposit_per_unit}
                      <br />
                      Late fee: ₹{item.late_fee_per_day}/day
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}

        {/* ================= BORROWERS ================= */}

        {tab === "borrowers" && (
          <>
            <section className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Register Borrower</h3>
                  <p className="card-subtitle">
                    Students, clubs or staff borrowing equipment.
                  </p>
                </div>
              </div>

              <form onSubmit={addBorrower}>
                <div className="form-grid">
                  <div className="form-group">
                    <label>Name</label>
                    <input
                      value={borrowerForm.name}
                      onChange={(e) =>
                        setBorrowerForm({
                          ...borrowerForm,
                          name: e.target.value,
                        })
                      }
                      placeholder="Student / Club name"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Email</label>
                    <input
                      type="email"
                      value={borrowerForm.email}
                      onChange={(e) =>
                        setBorrowerForm({
                          ...borrowerForm,
                          email: e.target.value,
                        })
                      }
                      placeholder="email@example.com"
                    />
                  </div>

                  <div className="form-group">
                    <label>Phone</label>
                    <input
                      value={borrowerForm.phone}
                      onChange={(e) =>
                        setBorrowerForm({
                          ...borrowerForm,
                          phone: e.target.value,
                        })
                      }
                      placeholder="Phone number"
                    />
                  </div>
                </div>

                <div className="form-actions">
                  <button className="btn btn-primary">
                    Register Borrower
                  </button>
                </div>
              </form>
            </section>

            <section className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">
                    Registered Borrowers
                  </h3>
                </div>
              </div>

              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Phone</th>
                    </tr>
                  </thead>

                  <tbody>
                    {borrowers.map((b) => (
                      <tr key={b.id}>
                        <td>#{b.id}</td>
                        <td>{b.name}</td>
                        <td>{b.email || "—"}</td>
                        <td>{b.phone || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}

        {/* ================= RENTALS ================= */}

        {tab === "rentals" && (
          <>
            <section className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Create Rental</h3>
                  <p className="card-subtitle">
                    Book equipment for a future or current date.
                  </p>
                </div>
              </div>

              <form onSubmit={createRental}>
                <div className="form-grid">
                  <div className="form-group">
                    <label>Borrower</label>

                    <select
                      value={rentalForm.borrower_id}
                      onChange={(e) =>
                        setRentalForm({
                          ...rentalForm,
                          borrower_id: e.target.value,
                        })
                      }
                      required
                    >
                      <option value="">Select borrower</option>

                      {borrowers.map((b) => (
                        <option key={b.id} value={b.id}>
                          {b.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Equipment</label>

                    <select
                      value={rentalForm.equipment_id}
                      onChange={(e) =>
                        setRentalForm({
                          ...rentalForm,
                          equipment_id: e.target.value,
                        })
                      }
                      required
                    >
                      <option value="">Select equipment</option>

                      {equipment.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Quantity</label>

                    <input
                      type="number"
                      min="1"
                      value={rentalForm.quantity}
                      onChange={(e) =>
                        setRentalForm({
                          ...rentalForm,
                          quantity: e.target.value,
                        })
                      }
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Start Date</label>

                    <input
                      type="date"
                      value={rentalForm.start_date}
                      onChange={(e) =>
                        setRentalForm({
                          ...rentalForm,
                          start_date: e.target.value,
                        })
                      }
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Due Date</label>

                    <input
                      type="date"
                      value={rentalForm.due_date}
                      onChange={(e) =>
                        setRentalForm({
                          ...rentalForm,
                          due_date: e.target.value,
                        })
                      }
                      required
                    />
                  </div>
                </div>

                <div className="form-actions">
                  <button className="btn btn-primary">
                    Book Equipment
                  </button>
                </div>
              </form>
            </section>

            <section className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Rental Records</h3>
                  <p className="card-subtitle">
                    Booked, issued and returned equipment.
                  </p>
                </div>
              </div>

              <RentalTable
                rentals={rentals}
                getBorrowerName={getBorrowerName}
                getEquipmentName={getEquipmentName}
                issueRental={issueRental}
                returnRental={returnRental}
              />
            </section>
          </>
        )}

        {/* ================= AVAILABILITY ================= */}

        {tab === "availability" && (
          <section className="card">
            <div className="card-header">
              <div>
                <h3 className="card-title">
                  Today's Live Availability
                </h3>

                <p className="card-subtitle">
                  Equipment currently available for booking.
                </p>
              </div>
            </div>

            <div className="equipment-grid">
              {availability.map((item) => {
                const percentage =
                  item.total_quantity > 0
                    ? (item.available_quantity / item.total_quantity) * 100
                    : 0;

                return (
                  <div className="equipment-card" key={item.equipment_id}>
                    <h3>{item.name}</h3>

                    <div className="equipment-category">
                      {item.category}
                    </div>

                    <div className="equipment-count">
                      <strong>{item.available_quantity}</strong>

                      <span>
                        / {item.total_quantity} available
                      </span>
                    </div>

                    <div className="availability-bar">
                      <div
                        className="availability-fill"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>

                    <div className="loan-meta">
                      {item.booked_quantity} currently booked
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* ================= TRANSFER ================= */}

        {tab === "transfer" && (
          <>
            <section className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">
                    Transfer Active Loan
                  </h3>

                  <p className="card-subtitle">
                    Transfer an issued item to another borrower without
                    changing its due date or availability.
                  </p>
                </div>
              </div>

              <form onSubmit={transferRental}>
                <div className="form-grid">
                  <div className="form-group">
                    <label>Active Loan</label>

                    <select
                      value={transferForm.rental_id}
                      onChange={(e) =>
                        setTransferForm({
                          ...transferForm,
                          rental_id: e.target.value,
                        })
                      }
                      required
                    >
                      <option value="">
                        Select active loan
                      </option>

                      {issuedRentals.map((r) => (
                        <option key={r.id} value={r.id}>
                          #{r.id} — {r.equipment_name} —{" "}
                          {r.borrower_name} — Due {r.due_date}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Transfer To</label>

                    <select
                      value={transferForm.new_borrower_id}
                      onChange={(e) =>
                        setTransferForm({
                          ...transferForm,
                          new_borrower_id: e.target.value,
                        })
                      }
                      required
                    >
                      <option value="">
                        Select new borrower
                      </option>

                      {borrowers.map((b) => (
                        <option key={b.id} value={b.id}>
                          {b.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="form-actions">
                  <button className="btn btn-primary">
                    Transfer Loan
                  </button>
                </div>
              </form>
            </section>

            <section className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">
                    Active Issued Loans
                  </h3>
                </div>
              </div>

              <RentalTable
                rentals={issuedRentals}
                getBorrowerName={getBorrowerName}
                getEquipmentName={getEquipmentName}
                issueRental={issueRental}
                returnRental={returnRental}
              />
            </section>
          </>
        )}
      </main>
    </div>
  );
}

function RentalTable({
  rentals,
  getBorrowerName,
  getEquipmentName,
  issueRental,
  returnRental,
}) {
  if (!rentals.length) {
    return <div className="empty">No rental records found.</div>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Borrower</th>
            <th>Equipment</th>
            <th>Qty</th>
            <th>Start</th>
            <th>Due</th>
            <th>Status</th>
            <th>Fee</th>
            <th>Actions</th>
          </tr>
        </thead>

        <tbody>
          {rentals.map((r) => (
            <tr key={r.id}>
              <td>#{r.id}</td>

              <td>
                {r.borrower_name ||
                  getBorrowerName(r.borrower_id)}
              </td>

              <td>
                {r.equipment_name ||
                  getEquipmentName(r.equipment_id)}
              </td>

              <td>{r.quantity}</td>

              <td>{r.start_date}</td>

              <td>{r.due_date}</td>

              <td>
                <span
                  className={`badge ${
                    r.status === "RETURNED"
                      ? "badge-green"
                      : r.status === "ISSUED"
                      ? "badge-blue"
                      : r.status === "BOOKED"
                      ? "badge-yellow"
                      : "badge-gray"
                  }`}
                >
                  {r.status}
                </span>
              </td>

              <td>₹{r.total_fee || 0}</td>

              <td>
                <div className="actions">
                  {r.status === "BOOKED" && (
                    <button
                      className="btn btn-primary btn-small"
                      onClick={() => issueRental(r.id)}
                    >
                      Issue
                    </button>
                  )}

                  {(r.status === "BOOKED" ||
                    r.status === "ISSUED") && (
                    <button
                      className="btn btn-success btn-small"
                      onClick={() => returnRental(r.id)}
                    >
                      Return
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;