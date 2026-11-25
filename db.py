import sqlite3
import math
import json
import hashlib
from datetime import datetime, timedelta

DB_NAME = "sarkarisewa.db"

def load_city_config():
    with open("city_config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def _hash_pwd(pwd: str) -> str:
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Main Civic Complaints Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_code TEXT UNIQUE,
            created_at TEXT,
            sla_deadline TEXT,
            ward TEXT,
            lat REAL,
            lon REAL,
            category TEXT,
            severity INTEGER,
            department TEXT,
            contractor_name TEXT,
            warranty_status TEXT,
            summary TEXT,
            work_order TEXT,
            before_img_b64 TEXT,
            after_img_b64 TEXT,
            ai_closure_note TEXT,
            impact_count INTEGER DEFAULT 1,
            status TEXT DEFAULT 'Open',
            reopen_count INTEGER DEFAULT 0
        )
    """)

    # Emergency Public Broadcast Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            ward TEXT,
            message TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    conn.commit()

    # Seed initial realistic government data if table is empty
    c.execute("SELECT COUNT(*) FROM complaints")
    if c.fetchone()[0] == 0:
        now = datetime.now()
        seeds = [
            (
                "SS-2026-101",
                (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
                (now + timedelta(hours=19)).strftime("%Y-%m-%d %H:%M"),
                "Ward 28 - Patna Junction & Fraser Road",
                25.6025, 85.1378,
                "Pothole & Road Damage", 8,
                "PWD (Public Works Dept)",
                "Patliputra Civic Works",
                "UNDER WARRANTY (Penalty Applicable)",
                "Deep crater-sized pothole near station exit causing severe traffic congestion and two-wheeler skids.",
                "WORK ORDER #PWD-101: Urgent cold-mix asphalt patching required within 24 hours. Contractor penalty notice flagged.",
                None, None, "", 16, "Critical", 0
            ),
            (
                "SS-2026-102",
                (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
                (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
                "Ward 41 - Rajendra Nagar & Hospital Zone",
                25.6010, 85.1615,
                "Hanging Electric Wire", 10,
                "Electricity Board (DISCOM)",
                "Sone Valley Constructions",
                "N/A - Utility Maintenance",
                "Low-hanging live insulated power cable near Hospital Zone gate posing immediate electrocution hazard.",
                "WORK ORDER #EL-102: EMERGENCY DISPATCH. Lineman crew assigned immediately (SLA: 2 Hours).",
                None, None, "", 24, "Critical", 0
            ),
            (
                "SS-2026-103",
                (now - timedelta(hours=10)).strftime("%Y-%m-%d %H:%M"),
                (now + timedelta(hours=14)).strftime("%Y-%m-%d %H:%M"),
                "Ward 22 - Boring Road Crossing",
                25.6118, 85.1189,
                "Garbage Overflow", 7,
                "Nagar Nigam Sanitation",
                "Magadh Roadways Corp",
                "UNDER WARRANTY",
                "Uncollected municipal solid waste spilling across pedestrian walkway near commercial market.",
                "WORK ORDER #NN-103: Deploy JCB & tipper vehicle for immediate clearance within 12 hours.",
                None, None, "", 11, "In Progress", 0
            ),
            (
                "SS-2026-104",
                (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
                (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
                "Ward 35 - Kankarbagh Main Road",
                25.5912, 85.1520,
                "Waterlogging & Drain Block", 6,
                "Water & Drainage Wing",
                "Ganga Urban Developers",
                "UNDER WARRANTY",
                "Plastic-choked storm drain cleared and desilted by municipal sanitation squad.",
                "WORK ORDER #WD-104: Desilting and manhole cover alignment completed.",
                None, None, "AI Verified: Drain blockage cleared and road surface dry.", 7, "Resolved", 0
            )
        ]
        c.executemany("""
            INSERT INTO complaints (
                ticket_code, created_at, sla_deadline, ward, lat, lon, category,
                severity, department, contractor_name, warranty_status, summary,
                work_order, before_img_b64, after_img_b64, ai_closure_note,
                impact_count, status, reopen_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, seeds)

        c.execute("""
            INSERT INTO broadcasts (created_at, ward, message, is_active)
            VALUES (?, ?, ?, 1)
        """, (
            now.strftime("%Y-%m-%d %H:%M"),
            "Ward 41 - Rajendra Nagar & Hospital Zone",
            "PUBLIC ADVISORY: Overhead electric wire repair underway near Hospital Gate. Commuters advised to use alternate lane for next 2 hours."
        ))
        conn.commit()
    conn.close()

def init_officer_auth():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS officers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            officer_id TEXT UNIQUE,
            full_name TEXT,
            department TEXT,
            designation TEXT,
            password_hash TEXT
        )
    """)
    conn.commit()

    # Seed default official government account
    c.execute("SELECT COUNT(*) FROM officers")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO officers (officer_id, full_name, department, designation, password_hash)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "PMC-ADMIN-01",
            "Rajesh Kumar Singh (IAS)",
            "All Departments",
            "Municipal Commissioner",
            _hash_pwd("Gov@2026")
        ))
        conn.commit()

    # Seed additional public notices so Top-10 ticker has rich items
    c.execute("SELECT COUNT(*) FROM broadcasts")
    if c.fetchone()[0] <= 1:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        extra_notices = [
            (now_str, "Ward 28 - Patna Junction & Fraser Road", "Traffic diversion active near Station Roundabout due to urgent pothole resurfacing work.", 1),
            (now_str, "Ward 22 - Boring Road Crossing", "Night-time mechanized garbage lifting scheduled between 10:00 PM and 5:00 AM.", 1),
            (now_str, "Ward 14 - Bailey Road & Secretariat", "Underground drainage desilting drive underway; citizens advised to report blocked manholes.", 1),
            (now_str, "Ward 35 - Kankarbagh Main Road", "Streetlight LED replacement completed; report any non-functional pole via Citizen Portal.", 1)
        ]
        c.executemany("INSERT INTO broadcasts (created_at, ward, message, is_active) VALUES (?, ?, ?, ?)", extra_notices)
        conn.commit()
    conn.close()

def register_officer(officer_id: str, full_name: str, department: str, designation: str, password: str) -> tuple[bool, str]:
    if not officer_id.strip() or not full_name.strip() or len(password) < 6:
        return False, "Officer ID, Full Name, and minimum 6-character Password are required."
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO officers (officer_id, full_name, department, designation, password_hash)
            VALUES (?, ?, ?, ?, ?)
        """, (officer_id.strip().upper(), full_name.strip(), department, designation.strip(), _hash_pwd(password)))
        conn.commit()
        conn.close()
        return True, f"Officer Account '{officer_id.strip().upper()}' registered successfully. You may now sign in."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "This Government Officer ID is already registered."

def verify_officer_login(officer_id: str, password: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT officer_id, full_name, department, designation
        FROM officers WHERE UPPER(officer_id) = UPPER(?) AND password_hash = ?
    """, (officer_id.strip(), _hash_pwd(password)))
    row = c.fetchone()
    conn.close()
    return row

def haversine_meters(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_ward_contractor_info(ward_name):
    cfg = load_city_config()
    for w in cfg["wards"]:
        if w["name"] == ward_name:
            return w
    return {"contractor": "Municipal Direct Wing", "warranty_valid_till": "2027-01-01", "sanctioned_budget": "₹25.0 Lakhs", "rating": 3.5}

def save_or_merge_complaint(ward, lat, lon, category, severity, department, summary, work_order, before_img_b64=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, ticket_code, lat, lon, impact_count, severity FROM complaints WHERE category = ? AND status != 'Resolved'", (category,))
    existing = c.fetchall()

    # Geo-Cluster Check: Merge if within 150 meters
    for row in existing:
        cid, tcode, elat, elon, count, esev = row
        if haversine_meters(lat, lon, elat, elon) <= 150:
            new_count = count + 1
            new_sev = max(esev, severity)
            c.execute("UPDATE complaints SET impact_count = ?, severity = ? WHERE id = ?", (new_count, new_sev, cid))
            conn.commit()
            conn.close()
            return {"merged": True, "ticket_code": tcode, "impact_count": new_count}

    now = datetime.now()
    sla_hours = 2 if severity >= 8 else (24 if severity >= 5 else 72)
    sla_deadline = (now + timedelta(hours=sla_hours)).strftime("%Y-%m-%d %H:%M")

    ward_info = get_ward_contractor_info(ward)
    contractor_name = ward_info["contractor"]
    warranty_status = f"UNDER WARRANTY till {ward_info['warranty_valid_till']} (Contractor Liable)"

    c.execute("SELECT MAX(id) FROM complaints")
    max_id = c.fetchone()[0] or 100
    ticket_code = f"SS-2026-{max_id + 1}"
    status = "Critical" if severity >= 8 else "Open"

    c.execute("""
        INSERT INTO complaints (
            ticket_code, created_at, sla_deadline, ward, lat, lon, category,
            severity, department, contractor_name, warranty_status, summary,
            work_order, before_img_b64, impact_count, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
    """, (
        ticket_code, now.strftime("%Y-%m-%d %H:%M"), sla_deadline, ward, lat, lon,
        category, severity, department, contractor_name, warranty_status,
        summary, work_order, before_img_b64, status
    ))
    conn.commit()
    conn.close()
    return {"merged": False, "ticket_code": ticket_code, "impact_count": 1}

def fetch_all_complaints():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, ticket_code, created_at, sla_deadline, ward, lat, lon, category,
               severity, department, contractor_name, warranty_status, summary,
               work_order, before_img_b64, after_img_b64, ai_closure_note,
               impact_count, status, reopen_count
        FROM complaints
        ORDER BY CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END, severity DESC, id DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def get_complaint_by_ticket(ticket_code):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, ticket_code, created_at, sla_deadline, ward, category, severity,
               department, contractor_name, warranty_status, summary, work_order,
               ai_closure_note, impact_count, status, reopen_count, before_img_b64, after_img_b64
        FROM complaints WHERE UPPER(ticket_code) = UPPER(?)
    """, (ticket_code.strip(),))
    row = c.fetchone()
    conn.close()
    return row

def resolve_complaint_with_proof(ticket_code, after_img_b64, ai_closure_note):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE complaints
        SET status = 'Resolved', after_img_b64 = ?, ai_closure_note = ?
        WHERE ticket_code = ?
    """, (after_img_b64, ai_closure_note, ticket_code))
    conn.commit()
    conn.close()

def reopen_complaint_by_citizen(ticket_code):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE complaints
        SET status = 'Escalated (Citizen Re-Open)', severity = 10, reopen_count = reopen_count + 1
        WHERE ticket_code = ?
    """, (ticket_code,))
    conn.commit()
    conn.close()

def create_broadcast(ward, message):
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO broadcasts (created_at, ward, message, is_active) VALUES (?, ?, ?, 1)", (now, ward, message))
    conn.commit()
    conn.close()

def get_top_10_broadcasts():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, created_at, ward, message FROM broadcasts WHERE is_active = 1 ORDER BY id DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    return rows