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
