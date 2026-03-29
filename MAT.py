"""
Medication Adherence Tracker (MAT) v2
======================================
Database  : SQLite (built-in, zero setup)
Backup    : JSON files in /backup folder
Features  :
  - Doctor registration & ID-based login
  - Each doctor sees only their own patients
  - Admin panel (ID: ADMIN001)
  - Patient registration, medication scheduling
  - Inbox messaging system
  - Medication reminders (±15 min window)
  - Adherence tracking & reports with visual bar
  - JSON backup on every write

Run:  python mat.py
"""

import sqlite3
import json
import uuid
import os
import sys
from datetime import datetime, date

# ─────────────────────────────────────────────
#  PATHS
# ─────────────────────────────────────────────
BACKUP_DIR       = os.path.join(BASE_DIR, "backup")
DOCTORS_BACKUP   = os.path.join(BACKUP_DIR, "doctors.json")
PATIENTS_BACKUP  = os.path.join(BACKUP_DIR, "patients.json")
MEDS_BACKUP      = os.path.join(BACKUP_DIR, "medications.json")
ADHERENCE_BACKUP = os.path.join(BACKUP_DIR, "adherence.json")
MESSAGES_BACKUP  = os.path.join(BACKUP_DIR, "messages.json")

ADMIN_ID = "ADMIN001"

# ─────────────────────────────────────────────
#  DISPLAY HELPERS
# ─────────────────────────────────────────────
LINE  = "=" * 58
SLINE = "-" * 58

def banner(title):
    print(f"\n{LINE}")
    print(f"  {title}")
    print(LINE)

def info(msg):    print(f"  {msg}")
def success(msg): print(f"\n  ✔  {msg}")
def error(msg):   print(f"\n  ✘  {msg}")
def divider():    print(SLINE)
def prompt(msg):  return input(f"  → {msg}: ").strip()


# ─────────────────────────────────────────────
#  DATABASE — CONNECT & SETUP
# ─────────────────────────────────────────────
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def setup_database():
    conn = get_connection()
    c    = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            doctor_id   TEXT PRIMARY KEY,
            full_name   TEXT NOT NULL,
            title       TEXT,
            hospital    TEXT,
            phone       TEXT,
            country     TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id  TEXT PRIMARY KEY,
            doctor_id   TEXT NOT NULL,
            full_name   TEXT NOT NULL,
            age         TEXT,
            sex         TEXT,
            village     TEXT,
            phone       TEXT,
            country     TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            med_id      TEXT PRIMARY KEY,
            patient_id  TEXT NOT NULL,
            doctor_id   TEXT NOT NULL,
            med_name    TEXT NOT NULL,
            dosage      TEXT,
            frequency   TEXT,
            times       TEXT,
            start_date  TEXT,
            end_date    TEXT,
            notes       TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY (doctor_id)  REFERENCES doctors(doctor_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS adherence (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id      TEXT NOT NULL,
            med_id          TEXT NOT NULL,
            med_name        TEXT,
            dosage          TEXT,
            taken           INTEGER,
            scheduled_time  TEXT,
            confirmed_at    TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            msg_id      TEXT PRIMARY KEY,
            patient_id  TEXT NOT NULL,
            subject     TEXT,
            body        TEXT,
            sent_at     TEXT DEFAULT (datetime('now','localtime')),
            is_read     INTEGER DEFAULT 0,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )
    """)

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
#  JSON BACKUP HELPER
# ─────────────────────────────────────────────
def _backup(filepath, new_data):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    existing = {}
    if os.path.exists(filepath):
        try:
            with open(filepath) as f:
                existing = json.load(f)
        except Exception:
            existing = {}
    if isinstance(existing, dict) and isinstance(new_data, dict):
        existing.update(new_data)
    else:
        existing = new_data
    with open(filepath, "w") as f:
        json.dump(existing, f, indent=2, default=str)


def _row(row):
    return dict(row) if row else None


# ─────────────────────────────────────────────
#  DOCTOR — REGISTER
# ─────────────────────────────────────────────
def register_doctor():
    banner("Register New Doctor Account")
    print()

    full_name = prompt("Full Name")
    if not full_name:
        error("Name cannot be empty.")
        return

    title    = prompt("Title (e.g. Dr., Prof., Nurse)")
    hospital = prompt("Hospital / Clinic Name")
    phone    = prompt("Phone Number")
    country  = prompt("Country")

    doctor_id  = "DR" + str(uuid.uuid4())[:6].upper()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO doctors
            (doctor_id, full_name, title, hospital, phone, country, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (doctor_id, full_name, title, hospital, phone, country, created_at))
        conn.commit()

        _backup(DOCTORS_BACKUP, {
            doctor_id: {
                "doctor_id": doctor_id, "full_name": full_name,
                "title": title,         "hospital": hospital,
                "phone": phone,         "country": country,
                "created_at": created_at,
            }
        })

        success("Doctor registered successfully!")
        print()
        print("  ╔══════════════════════════════════════════════════╗")
        print("  ║           YOUR DOCTOR ACCOUNT DETAILS             ║")
        print("  ╠══════════════════════════════════════════════════╣")
        print(f"  ║  Doctor ID : {doctor_id:<37}║")
        print(f"  ║  Name      : {(title + ' ' + full_name)[:37]:<37}║")
        print(f"  ║  Hospital  : {hospital[:37]:<37}║")
        print(f"  ║  Country   : {country[:37]:<37}║")
        print(f"  ║  Phone     : {phone[:37]:<37}║")
        print("  ╠══════════════════════════════════════════════════╣")
        print("  ║  ⚠  Save your Doctor ID — you need it to login   ║")
        print("  ╚══════════════════════════════════════════════════╝")

    except sqlite3.IntegrityError as e:
        error(f"Registration failed: {e}")
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  DOCTOR — LOGIN
# ─────────────────────────────────────────────
def doctor_login():
    banner("Doctor Login")
    print()
    doctor_id = prompt("Enter your Doctor ID").upper().strip()

    if not doctor_id:
        error("Doctor ID cannot be empty.")
        return None

    conn   = get_connection()
    doctor = _row(conn.execute(
        "SELECT * FROM doctors WHERE doctor_id = ?", (doctor_id,)
    ).fetchone())
    conn.close()

    if not doctor:
        error(f"Doctor ID '{doctor_id}' not found. Please register first.")
        return None

    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║           LOGIN SUCCESSFUL                        ║")
    print("  ╠══════════════════════════════════════════════════╣")
    print(f"  ║  Welcome, {(doctor['title'] + ' ' + doctor['full_name'])[:46]:<46}║")
    print(f"  ║  Hospital : {doctor['hospital'][:46]:<46}║")
    print(f"  ║  Country  : {doctor['country'][:46]:<46}║")
    print("  ╚══════════════════════════════════════════════════╝")
    return doctor


# ─────────────────────────────────────────────
#  ADMIN — VIEW ALL DOCTORS
# ─────────────────────────────────────────────
def admin_panel():
    banner("Admin Panel")
    admin_input = prompt("Enter Admin ID").upper()
    if admin_input != ADMIN_ID:
        error("Invalid Admin ID. Access denied.")
        return

    conn    = get_connection()
    doctors = [_row(r) for r in conn.execute(
        "SELECT * FROM doctors ORDER BY created_at DESC"
    ).fetchall()]
    conn.close()

    banner("All Registered Doctors")
    if not doctors:
        info("No doctors registered yet.")
        return

    print(f"\n  {'Doctor ID':<12} {'Name':<22} {'Title':<10} {'Hospital':<22} {'Country':<14} {'Phone'}")
    print(f"  {'-'*12} {'-'*22} {'-'*10} {'-'*22} {'-'*14} {'-'*14}")
    for d in doctors:
        name = f"{d['title']} {d['full_name']}"
        print(f"  {d['doctor_id']:<12} {name[:22]:<22} {d['title'][:10]:<10} "
              f"{d['hospital'][:22]:<22} {d['country'][:14]:<14} {d['phone']}")
    divider()
    info(f"Total registered doctors: {len(doctors)}")


# ─────────────────────────────────────────────
#  PATIENT — REGISTER
# ─────────────────────────────────────────────
def register_patient(doctor):
    banner("Register New Patient")
    print()

    full_name = prompt("Full Name")
    if not full_name:
        error("Name cannot be empty.")
        return

    age     = prompt("Age")
    sex     = prompt("Sex (Male/Female/Other)")
    village = prompt("Village / Address")
    phone   = prompt("Phone Number")
    country = prompt("Country")

    patient_id = str(uuid.uuid4())[:8].upper()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO patients
            (patient_id, doctor_id, full_name, age, sex, village, phone, country, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (patient_id, doctor["doctor_id"], full_name, age, sex,
              village, phone, country, created_at))

        msg_id = str(uuid.uuid4())[:8].upper()
        body = (
            f"Hello {full_name},\n\n"
            f"You have been registered on the\n"
            f"Medication Adherence Tracker (MAT) system.\n\n"
            f"Your unique Patient ID is:  {patient_id}\n\n"
            f"Keep this ID safe. You need it every time\n"
            f"you log into the Patient Portal to confirm\n"
            f"your medication intake.\n\n"
            f"Registered by: {doctor['title']} {doctor['full_name']}\n"
            f"Hospital: {doctor['hospital']}\n"
            f"Date: {created_at}\n\n"
            f"— Your Healthcare Team"
        )
        conn.execute("""
            INSERT INTO messages (msg_id, patient_id, subject, body, sent_at)
            VALUES (?, ?, ?, ?, ?)
        """, (msg_id, patient_id,
              "Welcome to MAT — Your Patient ID", body, created_at))
        conn.commit()

        _backup(PATIENTS_BACKUP, {
            patient_id: {
                "patient_id": patient_id, "doctor_id": doctor["doctor_id"],
                "full_name": full_name, "age": age, "sex": sex,
                "village": village, "phone": phone, "country": country,
                "created_at": created_at,
            }
        })

        success("Patient registered!")
        print()
        print("  ╔══════════════════════════════════════════════════╗")
        print("  ║           PATIENT REGISTERED                      ║")
        print("  ╠══════════════════════════════════════════════════╣")
        print(f"  ║  Patient ID : {patient_id:<37}║")
        print(f"  ║  Name       : {full_name[:37]:<37}║")
        print(f"  ║  Age / Sex  : {(age + ' / ' + sex)[:37]:<37}║")
        print(f"  ║  Country    : {country[:37]:<37}║")
        print(f"  ║  Phone      : {phone[:37]:<37}║")
        print("  ╠══════════════════════════════════════════════════╣")
        print("  ║  📬 Welcome message sent to patient inbox         ║")
        print("  ╚══════════════════════════════════════════════════╝")

    except sqlite3.Error as e:
        error(f"Database error: {e}")
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  PATIENTS — LIST
# ─────────────────────────────────────────────
def _list_patients_table(patients):
    if not patients:
        info("No patients found.")
        return
    print(f"\n  {'ID':<12} {'Name':<25} {'Age':<5} {'Sex':<8} {'Country':<15} {'Phone'}")
    print(f"  {'-'*12} {'-'*25} {'-'*5} {'-'*8} {'-'*15} {'-'*14}")
    for p in patients:
        print(f"  {p['patient_id']:<12} {p['full_name'][:25]:<25} {p['age']:<5} "
              f"{p['sex']:<8} {p['country'][:15]:<15} {p['phone']}")
    print()


def view_all_patients(doctor):
    banner("My Patients")
    conn     = get_connection()
    patients = [_row(r) for r in conn.execute(
        "SELECT * FROM patients WHERE doctor_id = ? ORDER BY full_name",
        (doctor["doctor_id"],)
    ).fetchall()]
    conn.close()

    if not patients:
        info("You have no registered patients yet.")
        return
    _list_patients_table(patients)
    info(f"Total: {len(patients)} patient(s)")


# ─────────────────────────────────────────────
#  PATIENT DETAILS & PRESCRIPTIONS
# ─────────────────────────────────────────────
def view_patient_details(doctor):
    banner("Patient Details & Prescriptions")
    conn     = get_connection()
    patients = [_row(r) for r in conn.execute(
        "SELECT * FROM patients WHERE doctor_id = ? ORDER BY full_name",
        (doctor["doctor_id"],)
    ).fetchall()]

    if not patients:
        info("No patients found.")
        conn.close(); return

    _list_patients_table(patients)
    patient_id = prompt("Enter Patient ID for full details").upper()
    p = _row(conn.execute(
        "SELECT * FROM patients WHERE patient_id = ? AND doctor_id = ?",
        (patient_id, doctor["doctor_id"])
    ).fetchone())

    if not p:
        error("Patient not found or does not belong to you.")
        conn.close(); return

    banner(f"Record — {p['full_name']}")
    info(f"Patient ID : {p['patient_id']}")
    info(f"Name       : {p['full_name']}")
    info(f"Age        : {p['age']}")
    info(f"Sex        : {p['sex']}")
    info(f"Village    : {p['village']}")
    info(f"Phone      : {p['phone']}")
    info(f"Country    : {p['country']}")
    info(f"Registered : {p['created_at']}")
    divider()

    meds = [_row(r) for r in conn.execute(
        "SELECT * FROM medications WHERE patient_id = ? ORDER BY created_at",
        (patient_id,)
    ).fetchall()]
    conn.close()

    if not meds:
        info("No medications scheduled yet.")
    else:
        info(f"Scheduled Medications ({len(meds)}):")
        for m in meds:
            print()
            info(f"  • {m['med_name']}  [{m['med_id']}]")
            info(f"    Dosage     : {m['dosage']}")
            info(f"    Frequency  : {m['frequency']}")
            info(f"    Times      : {m['times']}")
            info(f"    Start Date : {m['start_date']}")
            info(f"    End Date   : {m['end_date'] or 'Open-ended'}")
            info(f"    Notes      : {m['notes'] or 'None'}")
    print()


# ─────────────────────────────────────────────
#  MEDICATION — SCHEDULE
# ─────────────────────────────────────────────
def set_medication_schedule(doctor):
    banner("Set / Modify Medication Schedule")
    conn     = get_connection()
    patients = [_row(r) for r in conn.execute(
        "SELECT * FROM patients WHERE doctor_id = ? ORDER BY full_name",
        (doctor["doctor_id"],)
    ).fetchall()]

    if not patients:
        error("You have no registered patients yet.")
        conn.close(); return

    _list_patients_table(patients)
    patient_id = prompt("Enter Patient ID").upper()
    patient    = _row(conn.execute(
        "SELECT * FROM patients WHERE patient_id = ? AND doctor_id = ?",
        (patient_id, doctor["doctor_id"])
    ).fetchone())

    if not patient:
        error("Patient not found or does not belong to you.")
        conn.close(); return

    info(f"Patient: {patient['full_name']}  (ID: {patient_id})")
    print()

    med_name  = prompt("Medication Name")
    dosage    = prompt("Dosage (e.g. 400 mg)")
    frequency = prompt("Frequency (e.g. twice daily)")
    times_str = prompt("Scheduled times, comma-separated (e.g. 08:00, 20:00)")
    start     = prompt("Start Date (YYYY-MM-DD)  [Enter = today]") or str(date.today())
    end       = prompt("End Date   (YYYY-MM-DD)  [Enter = blank]") or None
    notes     = prompt("Additional notes         [Enter = none]") or ""

    med_id = str(uuid.uuid4())[:8].upper()
    now    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn.execute("""
            INSERT INTO medications
            (med_id, patient_id, doctor_id, med_name, dosage, frequency,
             times, start_date, end_date, notes, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (med_id, patient_id, doctor["doctor_id"], med_name, dosage,
              frequency, times_str, start, end, notes, now))

        msg_id = str(uuid.uuid4())[:8].upper()
        body   = (
            f"Hello {patient['full_name']},\n\n"
            f"Your doctor has prescribed a new medication.\n\n"
            f"  Medication : {med_name}\n"
            f"  Dosage     : {dosage}\n"
            f"  Frequency  : {frequency}\n"
            f"  Times      : {times_str}\n"
            f"  Start Date : {start}\n"
            f"  End Date   : {end or 'Open-ended'}\n"
            f"  Notes      : {notes or 'None'}\n\n"
            f"Prescribed by: {doctor['title']} {doctor['full_name']}\n"
            f"Hospital: {doctor['hospital']}\n\n"
            f"— Your Healthcare Team"
        )
        conn.execute("""
            INSERT INTO messages (msg_id, patient_id, subject, body, sent_at)
            VALUES (?, ?, ?, ?, ?)
        """, (msg_id, patient_id, f"New Medication: {med_name}", body, now))
        conn.commit()

        _backup(MEDS_BACKUP, {
            med_id: {
                "med_id": med_id, "patient_id": patient_id,
                "doctor_id": doctor["doctor_id"], "med_name": med_name,
                "dosage": dosage, "frequency": frequency,
                "times": times_str, "start_date": start,
                "end_date": str(end) if end else "", "notes": notes,
            }
        })

        success(f"Medication '{med_name}' scheduled.  Med ID: {med_id}")
        info(f"📬 Prescription details sent to {patient['full_name']}'s inbox.")

    except sqlite3.Error as e:
        error(f"Database error: {e}")
    finally:
        conn.close()