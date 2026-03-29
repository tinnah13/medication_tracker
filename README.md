# Medication Adherence Tracker (MAT) 

Upgraded version with **MySQL database**, **doctor login system**, and **JSON backup**.

---

## Requirements

- Python 3.10+
- MySQL Server running locally
- mysql-connector-python

Install the connector:
```bash
pip install mysql-connector-python
```

---

## MySQL Setup (do this once)

1. Open MySQL and create the database:
```sql
CREATE DATABASE mat_db;
```

2. Open `mat.py` and update the DB_CONFIG section at the top:
```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",        # your MySQL username
    "password": "yourpassword", # your MySQL password
    "database": "mat_db",
}
```

3. The tables are created **automatically** when you run the app.

---

## How to Run

```bash
python mat.py
```

---

## Database Tables

| Table | Stores |
|---|---|
| `doctors` | doctor_id, name, title, hospital, phone, country |
| `patients` | patient_id, doctor_id, name, age, sex, village, phone, country |
| `medications` | med_id, patient_id, doctor_id, name, dosage, frequency, times, dates |
| `adherence` | intake logs — when taken, scheduled time, confirmed time |
| `messages` | patient inbox messages — subject, body, read status |

---

## How It Works

### Doctor Flow
1. **Main Menu → [2] Register as a new Doctor** — fill in your details, get a Doctor ID
2. **Main Menu → [1] Doctor Login** — enter your Doctor ID
3. Inside the portal:
   - Register patients (each patient belongs to you only)
   - Set medication schedules
   - View your patients and their prescriptions
   - View adherence reports with visual bar
   - Check due reminders

### Patient Flow
1. **Main Menu → [3] Patient Portal**
2. Enter your Patient ID (given by your doctor)
3. Options:
   - **My Inbox** — read welcome message and prescription notifications
   - **Confirm medication intake** — log whether you took your dose
   - **Check my reminders** — see medications due within 15 minutes

### Admin Flow
1. **Main Menu → [4] Admin Panel**
2. Enter Admin ID: `ADMIN001`
3. View all registered doctors across all hospitals

---

## JSON Backup

Every write to the database is also saved to the `backup/` folder:
```
backup/
├── doctors.json
├── patients.json
├── medications.json
├── adherence.json
└── messages.json
```

---

## Reminder Logic

Reminders appear when you select **Check my reminders** and a scheduled medication time is within **±15 minutes** of the current clock time.

Example: medication scheduled at `14:00`
- Reminder appears: **13:45 → 14:15**

---

## Admin ID
Default admin ID: `ADMIN001`  
You can change this in `mat.py` at the top: `ADMIN_ID = "ADMIN001"`
