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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "mat.db")

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

# ─────────────────────────────────────────────
#  REMINDERS
# ─────────────────────────────────────────────
def send_reminders(doctor_id=None, patient_id=None):
    banner("Medication Reminders — Now Checking")
    conn  = get_connection()
    today = str(date.today())

    query  = """
        SELECT m.*, p.full_name, p.patient_id as pid
        FROM medications m
        JOIN patients p ON m.patient_id = p.patient_id
        WHERE m.start_date <= ?
          AND (m.end_date IS NULL OR m.end_date >= ?)
    """
    params = [today, today]
    if doctor_id:
        query += " AND m.doctor_id = ?"; params.append(doctor_id)
    if patient_id:
        query += " AND m.patient_id = ?"; params.append(patient_id)

    meds = [_row(r) for r in conn.execute(query, params).fetchall()]
    conn.close()

    now  = datetime.now()
    sent = 0

    for med in meds:
        for sched_time in [t.strip() for t in med["times"].split(",")]:
            try:
                sched_dt = datetime.strptime(f"{today} {sched_time}", "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            diff = abs((now - sched_dt).total_seconds() / 60)
            if diff <= 15:
                print()
                print("  ╔══════════════════════════════════════════════╗")
                print("  ║  🔔  MEDICATION REMINDER                       ║")
                print("  ╠══════════════════════════════════════════════╣")
                print(f"  ║  Patient  : {med['full_name'][:32]:<32}║")
                print(f"  ║  ID       : {med['pid']:<32}║")
                print(f"  ║  Medicine : {med['med_name'][:32]:<32}║")
                print(f"  ║  Dosage   : {med['dosage'][:32]:<32}║")
                print(f"  ║  Time     : {sched_time:<32}║")
                print("  ╚══════════════════════════════════════════════╝")
                sent += 1

    if sent == 0:
        info("No medications due within the next 15 minutes right now.")
    else:
        success(f"{sent} reminder(s) displayed.")


# ─────────────────────────────────────────────
#  ADHERENCE REPORT
# ─────────────────────────────────────────────
def view_adherence_report(doctor):
    banner("Adherence Report  [Doctor View]")
    conn     = get_connection()
    patients = [_row(r) for r in conn.execute(
        "SELECT * FROM patients WHERE doctor_id = ? ORDER BY full_name",
        (doctor["doctor_id"],)
    ).fetchall()]

    if not patients:
        info("No patients found.")
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

    logs = [_row(r) for r in conn.execute(
        "SELECT * FROM adherence WHERE patient_id = ? ORDER BY confirmed_at",
        (patient_id,)
    ).fetchall()]
    conn.close()

    print()
    info(f"Patient  : {patient['full_name']}")
    info(f"ID       : {patient['patient_id']}")
    info(f"Age/Sex  : {patient['age']} / {patient['sex']}")
    info(f"Village  : {patient['village']}")
    info(f"Country  : {patient['country']}")
    info(f"Phone    : {patient['phone']}")
    divider()

    if not logs:
        info("No adherence records found for this patient.")
        return

    total  = len(logs)
    taken  = sum(1 for l in logs if l["taken"])
    missed = total - taken
    rate   = (taken / total * 100) if total else 0

    info(f"Total confirmations : {total}")
    info(f"Doses taken         : {taken}")
    info(f"Doses missed        : {missed}")
    info(f"Adherence rate      : {rate:.1f}%")
    divider()

    print(f"  {'Date':<12} {'Time':<10} {'Medication':<20} {'Dosage':<12} {'Scheduled':<10} {'Status'}")
    print(f"  {'-'*12} {'-'*10} {'-'*20} {'-'*12} {'-'*10} {'-'*8}")
    for log in logs:
        ts     = str(log["confirmed_at"])
        d      = ts[:10]
        t      = ts[11:19] if len(ts) > 10 else "-"
        sched  = log.get("scheduled_time") or "N/A"
        status = "✔ Taken" if log["taken"] else "✘ Missed"
        print(f"  {d:<12} {t:<10} {log['med_name']:<20} {log['dosage']:<12} {sched:<10} {status}")

    divider()
    bar_len = 30
    filled  = int(bar_len * rate / 100)
    bar     = "█" * filled + "░" * (bar_len - filled)
    print(f"\n  Adherence  [{bar}]  {rate:.1f}%\n")

    if   rate >= 90: info("✅ Excellent adherence. Patient is following the treatment plan well.")
    elif rate >= 70: info("⚠️  Moderate adherence. Consider counselling or simplified schedule.")
    else:            info("🚨 Poor adherence. Immediate follow-up recommended.")

    _backup(ADHERENCE_BACKUP, {
        patient_id: [{k: str(v) for k, v in l.items()} for l in logs]
    })


# ─────────────────────────────────────────────
#  PATIENT — CONFIRM INTAKE
# ─────────────────────────────────────────────
def confirm_intake():
    banner("Medication Intake Confirmation  [Patient Portal]")
    print()
    patient_id = prompt("Enter your Patient ID").upper()

    conn    = get_connection()
    patient = _row(conn.execute(
        "SELECT * FROM patients WHERE patient_id = ?", (patient_id,)
    ).fetchone())

    if not patient:
        error("Patient ID not found. Please check with your doctor.")
        conn.close(); return

    print(f"\n  Hello, {patient['full_name']}! 👋")

    today = str(date.today())
    meds  = [_row(r) for r in conn.execute("""
        SELECT * FROM medications
        WHERE patient_id = ?
          AND start_date <= ?
          AND (end_date IS NULL OR end_date >= ?)
        ORDER BY med_name
    """, (patient_id, today, today)).fetchall()]

    if not meds:
        info("You have no active medications scheduled for today.")
        conn.close(); return

    print()
    info("Your medications for today:")
    divider()
    for idx, med in enumerate(meds, 1):
        info(f"  [{idx}] {med['med_name']}  |  {med['dosage']}  |  {med['frequency']}  |  Times: {med['times']}")
    divider()

    choice_raw = prompt("Enter medication number to confirm (or 0 to cancel)")
    if not choice_raw.isdigit() or int(choice_raw) == 0:
        info("Cancelled.")
        conn.close(); return

    choice = int(choice_raw)
    if choice < 1 or choice > len(meds):
        error("Invalid selection.")
        conn.close(); return

    selected    = meds[choice - 1]
    taken_input = prompt(
        f"Did you take {selected['med_name']} ({selected['dosage']})? (yes/no)"
    ).lower()

    if taken_input not in ("yes", "y", "no", "n"):
        error("Please enter yes or no.")
        conn.close(); return

    taken_bool   = 1 if taken_input in ("yes", "y") else 0
    confirmed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    now          = datetime.now()
    closest_time = None
    min_diff     = float("inf")
    for t in [x.strip() for x in selected["times"].split(",")]:
        try:
            sched_dt = datetime.strptime(f"{today} {t}", "%Y-%m-%d %H:%M")
            diff = abs((now - sched_dt).total_seconds())
            if diff < min_diff:
                min_diff = diff; closest_time = t
        except ValueError:
            pass

    try:
        conn.execute("""
            INSERT INTO adherence
            (patient_id, med_id, med_name, dosage, taken, scheduled_time, confirmed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (patient_id, selected["med_id"], selected["med_name"],
              selected["dosage"], taken_bool, closest_time, confirmed_at))
        conn.commit()

        _backup(ADHERENCE_BACKUP, {
            patient_id: [{
                "med_name": selected["med_name"], "dosage": selected["dosage"],
                "taken": bool(taken_bool), "scheduled_time": closest_time,
                "confirmed_at": confirmed_at,
            }]
        })

        if taken_bool:
            success(f"Thank you! Recorded at {confirmed_at}.")
            info(f"You confirmed taking {selected['med_name']} ({selected['dosage']}).")
        else:
            info(f"Recorded: {selected['med_name']} — NOT taken at {confirmed_at[11:19]}.")
            info("Please take it as soon as possible, or consult your doctor.")

    except sqlite3.Error as e:
        error(f"Database error: {e}")
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  PATIENT INBOX
# ─────────────────────────────────────────────
def _unread_count(patient_id):
    conn  = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM messages WHERE patient_id = ? AND is_read = 0",
        (patient_id,)
    ).fetchone()[0]
    conn.close()
    return count


def view_inbox():
    banner("My Inbox  [Patient Portal]")
    print()
    patient_id = prompt("Enter your Patient ID").upper()

    conn    = get_connection()
    patient = _row(conn.execute(
        "SELECT * FROM patients WHERE patient_id = ?", (patient_id,)
    ).fetchone())

    if not patient:
        error("Patient ID not found.")
        conn.close(); return

    messages = [_row(r) for r in conn.execute(
        "SELECT * FROM messages WHERE patient_id = ? ORDER BY sent_at DESC",
        (patient_id,)
    ).fetchall()]

    print(f"\n  Hello, {patient['full_name']}! 👋")
    divider()

    if not messages:
        info("Your inbox is empty.")
        conn.close(); return

    unread = sum(1 for m in messages if not m["is_read"])
    info(f"Messages: {len(messages)} total  |  {unread} unread")
    divider()

    for idx, msg in enumerate(messages, 1):
        status = "● NEW" if not msg["is_read"] else "  ✔ "
        print(f"  [{idx}] {status}  {str(msg['sent_at'])[:16]}   {msg['subject']}")

    print()
    choice_raw = prompt("Enter message number to read (or 0 to go back)")
    if not choice_raw.isdigit() or int(choice_raw) == 0:
        conn.close(); return

    choice = int(choice_raw)
    if choice < 1 or choice > len(messages):
        error("Invalid selection.")
        conn.close(); return

    msg = messages[choice - 1]
    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║  📬  MESSAGE                                      ║")
    print("  ╠══════════════════════════════════════════════════╣")
    print(f"  ║  From    : Your Healthcare Team                   ║")
    print(f"  ║  Date    : {str(msg['sent_at'])[:16]:<39}║")
    print(f"  ║  Subject : {str(msg['subject'])[:39]:<39}║")
    print("  ╠══════════════════════════════════════════════════╣")
    for line in msg["body"].split("\n"):
        print(f"  ║  {line[:49]:<49}║")
    print("  ╚══════════════════════════════════════════════════╝")

    conn.execute("UPDATE messages SET is_read = 1 WHERE msg_id = ?", (msg["msg_id"],))
    conn.commit()
    conn.close()
    info("\n  Message marked as read.")


# ─────────────────────────────────────────────
#  MENUS
# ─────────────────────────────────────────────
def doctor_menu(doctor):
    while True:
        banner(f"Doctor Portal — {doctor['title']} {doctor['full_name']}")
        print()
        info("  [1]  Register a new patient")
        info("  [2]  Set / Modify medication schedule")
        info("  [3]  View my patients")
        info("  [4]  View patient details & prescriptions")
        info("  [5]  View adherence report")
        info("  [6]  Check due reminders")
        info("  [0]  Logout")
        print()
        choice = prompt("Select an option")

        if   choice == "1": register_patient(doctor)
        elif choice == "2": set_medication_schedule(doctor)
        elif choice == "3": view_all_patients(doctor)
        elif choice == "4": view_patient_details(doctor)
        elif choice == "5": view_adherence_report(doctor)
        elif choice == "6": send_reminders(doctor_id=doctor["doctor_id"])
        elif choice == "0":
            info(f"Logged out. Goodbye, {doctor['title']} {doctor['full_name']}!")
            break
        else:
            error("Invalid option.")

        input("\n  Press Enter to continue...")


def patient_menu():
    while True:
        banner("Patient Portal")
        print()
        patient_id = prompt(
            "Enter your Patient ID to check unread messages (or Enter to skip)"
        ).upper()

        unread_badge = ""
        if patient_id:
            try:
                count = _unread_count(patient_id)
                if count > 0:
                    unread_badge = f"  📬 {count} unread"
            except Exception:
                pass

        print()
        info(f"  [1]  My Inbox{unread_badge}")
        info("  [2]  Confirm medication intake")
        info("  [3]  Check my reminders")
        info("  [0]  Back to main menu")
        print()
        choice = prompt("Select an option")

        if   choice == "1": view_inbox()
        elif choice == "2": confirm_intake()
        elif choice == "3":
            pid = patient_id if patient_id else prompt("Enter your Patient ID").upper()
            send_reminders(patient_id=pid)
        elif choice == "0": break
        else: error("Invalid option.")

        input("\n  Press Enter to continue...")


def introduction():
    print(f"\n{LINE}")
    print("      MEDICATION ADHERENCE TRACKER (MAT) v2")
    print("      SQLite Database  +  JSON Backup")
    print(LINE)
    print()
    print("  Doctor  →  Register once, login with your Doctor ID")
    print("             Manage only your own patients & reports")
    print()
    print("  Patient →  Use Patient ID to confirm doses,")
    print("             read inbox messages & check reminders")
    print()
    print(f"  Admin   →  ID: {ADMIN_ID}  |  View all registered doctors")
    print()
    print(f"  Database: mat.db      (auto-created, no setup needed)")
    print(f"  Backup  : backup/     (JSON files updated on every save)")
    print()


def main():
    setup_database()
    introduction()

    while True:
        banner("Main Menu")
        print()
        info("  [1]  Doctor Login")
        info("  [2]  Register as a new Doctor")
        info("  [3]  Patient Portal")
        info("  [4]  Admin Panel")
        info("  [0]  Exit")
        print()
        choice = prompt("Select an option")

        if choice == "1":
            doctor = doctor_login()
            if doctor:
                input("\n  Press Enter to enter your portal...")
                doctor_menu(doctor)
        elif choice == "2":
            register_doctor()
            input("\n  Press Enter to continue...")
        elif choice == "3":
            patient_menu()
        elif choice == "4":
            admin_panel()
            input("\n  Press Enter to continue...")
        elif choice == "0":
            print()
            info("Goodbye! Stay healthy. 💊")
            print()
            break
        else:
            error("Invalid option. Please type 1, 2, 3, 4, or 0.")


if __name__ == "__main__":
    main()

