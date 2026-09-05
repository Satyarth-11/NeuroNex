"""
NeuroNex — Synthetic Data Generator (SYNTHETIC DATA ONLY)
============================================================
Generates 10 distinct investigative CASES with multi-source records deterministically
from a fixed random seed (42).

Shared cast of ~14 fictional persons, phones, accounts, vehicles, locations,
and 2 organisations — reused across cases with realistic name variants to exercise
cross-case entity resolution and graph connectivity.

Emits:
- cases_manifest.json (10 distinct cases with metadata & document mappings)
- fir_reports.csv (10 FIR records with case_ref)
- cdr_records.csv (20 CDR records with case_ref)
- financial_transactions.csv (10 transactions with case_ref)
- surveillance_reports.txt (4 surveillance reports with CASE_REF)
- social_media_posts.csv (8 posts with case_ref)
- criminal_history.csv (6 profiles with case_ref)
- intelligence_reports.txt (3 intelligence reports with CASE_REF)
- ground_truth_pairs.csv (20 validation ground truth pairs)

WARNING: All data is ENTIRELY FICTIONAL. No real persons, organisations,
cases, or events are referenced. Generated solely for SIH26189 prototype demo.
"""

import csv
import json
import os
import random

SEED = 42
random.seed(SEED)
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# 10 Investigation Cases
# ---------------------------------------------------------------------------
CASES = [
    {
        "case_code": "CASE-2024-001",
        "title": "[DEMO] ShadowTech Financial Fraud & UPI Diversion",
        "description": "Multi-jurisdictional inquiry into investment diversion through fake UPI payment channels operated by ShadowTech Pvt Ltd in Andheri West, Mumbai.",
    },
    {
        "case_code": "CASE-2024-002",
        "title": "[DEMO] Phoenix Traders Warehouse Consignment Theft",
        "description": "Investigation into illegal logistics movement and warehouse stock diversion across Karol Bagh and New Delhi corridors.",
    },
    {
        "case_code": "CASE-2024-003",
        "title": "[DEMO] Koramangala Commercial Contract Fraud",
        "description": "Advance payment diversion scheme involving fabricated service contracts and unauthorized vehicle transport in Bengaluru.",
    },
    {
        "case_code": "CASE-2024-004",
        "title": "[DEMO] Salt Lake Corporate Siphoning Intercept",
        "description": "Diversion of corporate funds through multiple private accounts in Salt Lake, Kolkata linking regional associates.",
    },
    {
        "case_code": "CASE-2024-005",
        "title": "[DEMO] T Nagar Forged Procurement Scheme",
        "description": "Procurement fraud utilizing forged Phoenix Traders Association documentation and vehicle transport in Chennai.",
    },
    {
        "case_code": "CASE-2024-006",
        "title": "[DEMO] Powai Cyber Gateway Impersonation",
        "description": "Investigation into fraudulent payment gateway infrastructure and digital front enterprises operated in Powai, Mumbai.",
    },
    {
        "case_code": "CASE-2024-007",
        "title": "[DEMO] Connaught Place Inventory Clearance Breach",
        "description": "Unauthorized distribution and consignment clearance by Phoenix Traders associates in New Delhi.",
    },
    {
        "case_code": "CASE-2024-008",
        "title": "[DEMO] Electronic City Corporate Laundering Scheme",
        "description": "Commercial misrepresentation and shell transaction routing through tech enterprise accounts in Bengaluru.",
    },
    {
        "case_code": "CASE-2024-009",
        "title": "[DEMO] Banjara Hills Joint Venture Diversion",
        "description": "Financial breach and unauthorized fund diversion during inter-firm joint venture enterprise in Hyderabad.",
    },
    {
        "case_code": "CASE-2024-010",
        "title": "[DEMO] Park Street Syndicate Documentation Theft",
        "description": "Organized theft of corporate proprietary documentation and transport coordination across Kolkata.",
    },
]

# ---------------------------------------------------------------------------
# Shared fictional cast — consistent across all source types
# ---------------------------------------------------------------------------
PERSONS = [
    {"id": "P001", "name": "Rajesh Kumar Sharma",   "alias": "Raju",      "handle": "@rajukumar"},
    {"id": "P002", "name": "Priya Mehta",            "alias": "Priya M",   "handle": "@priya_m"},
    {"id": "P003", "name": "Anil Verma",             "alias": "Anil V",    "handle": "@anilv99"},
    {"id": "P004", "name": "Sunita Desai",           "alias": "Sunita D",  "handle": "@sunita_d"},
    {"id": "P005", "name": "Mohammed Farooq",        "alias": "Farooq",    "handle": "@mfarooq"},
    {"id": "P006", "name": "Kavita Nair",            "alias": "Kavita N",  "handle": "@kavita_n"},
    {"id": "P007", "name": "Dinesh Patel",           "alias": "D. Patel",  "handle": "@dpatel_x"},
    {"id": "P008", "name": "Leela Krishnamurthy",   "alias": "Leela K",   "handle": "@leelak"},
    {"id": "P009", "name": "Sameer Joshi",           "alias": "Sameer J",  "handle": "@sameerj"},
    {"id": "P010", "name": "Nandita Roy",            "alias": "Nandita",   "handle": "@nanditar"},
    {"id": "P011", "name": "Vikram Singh",           "alias": "V. Singh",  "handle": "@vikrams"},
    {"id": "P012", "name": "Geeta Bose",             "alias": "G. Bose",   "handle": "@geetab"},
    {"id": "P013", "name": "Arjun Malhotra",         "alias": "Arjun M",   "handle": "@arjunm"},
    {"id": "P014", "name": "Fatima Sheikh",          "alias": "Fatima S",  "handle": "@fatimas"},
]

PHONES = {
    "P001": "+919876543210", "P002": "+919812345678", "P003": "+919823456789",
    "P004": "+919834567890", "P005": "+919845678901", "P006": "+919856789012",
    "P007": "+919867890123", "P008": "+919878901234", "P009": "+919889012345",
    "P010": "+919890123456", "P011": "+919801234567", "P012": "+919811111111",
    "P013": "+919822222222", "P014": "+919833333333",
}

ACCOUNTS = {
    "P001": "ACC001234567890", "P002": "ACC002345678901", "P003": "ACC003456789012",
    "P004": "ACC004567890123", "P005": "ACC005678901234", "P006": "ACC006789012345",
    "P007": "ACC007890123456", "P008": "ACC008901234567", "P009": "ACC009012345678",
    "P010": "ACC010123456789", "P011": "ACC011234567890", "P012": "ACC012345678901",
    "P013": "ACC013456789012", "P014": "ACC014567890123",
}

VEHICLES = {
    "P001": "MH01AB1234", "P003": "DL05CD5678", "P005": "KA03EF9012",
    "P007": "TN09GH3456", "P011": "MH02IJ7890",
}

LOCATIONS = [
    "Andheri West, Mumbai",
    "Connaught Place, New Delhi",
    "Koramangala, Bengaluru",
    "Salt Lake, Kolkata",
    "T Nagar, Chennai",
    "Banjara Hills, Hyderabad",
    "Karol Bagh, New Delhi",
    "Powai, Mumbai",
    "Electronic City, Bengaluru",
    "Park Street, Kolkata",
]

ORGS = ["ShadowTech Pvt Ltd", "Phoenix Traders Association"]

FIR_STATIONS = [
    "Andheri Police Station", "Connaught Place PS", "Koramangala PS",
    "Bhowanipore PS", "T Nagar PS",
]


# ---------------------------------------------------------------------------
# 1. Cases Manifest
# ---------------------------------------------------------------------------
def write_cases_manifest():
    path = os.path.join(OUT_DIR, "cases_manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(CASES, f, indent=2)
    print(f"[SYNTHETIC] Written: {path} ({len(CASES)} cases)")


# ---------------------------------------------------------------------------
# 2. FIR / Police Reports (10 records with case_ref)
# ---------------------------------------------------------------------------
def write_fir_reports():
    firs = [
        {
            "fir_no": "FIR/2024/MH/00123",
            "case_ref": "CASE-2024-001",
            "police_station": FIR_STATIONS[0],
            "date": "2024-03-15",
            "sections_of_law": "IPC 420, IPC 120B",
            "complainant_name": "Kavita Nair",
            "accused_names": "Rajesh Kumar Sharma; Priya Mehta; Anil Verma",
            "narrative_text": (
                "Complainant Kavita Nair reported that Rajesh Kumar Sharma, "
                "operating through ShadowTech Pvt Ltd, conspired with Priya Mehta "
                "and Anil Verma to defraud investors of Rs 45 lakhs via fake UPI "
                "transactions. Suspect vehicle MH01AB1234 was seen at Andheri West, "
                "Mumbai on 14-03-2024. FIR No FIR/2024/MH/00123 registered."
            ),
        },
        {
            "fir_no": "FIR/2024/DL/00456",
            "case_ref": "CASE-2024-002",
            "police_station": FIR_STATIONS[1],
            "date": "2024-04-02",
            "sections_of_law": "IPC 379, IPC 411",
            "complainant_name": "Leela Krishnamurthy",
            "accused_names": "Dinesh Patel; Sameer Joshi; Vikram Singh",
            "narrative_text": (
                "Leela Krishnamurthy alleged that Dinesh Patel and Sameer Joshi, "
                "members of Phoenix Traders Association, arranged theft of goods "
                "worth Rs 12 lakhs from a warehouse at Karol Bagh, New Delhi. "
                "Vehicle DL05CD5678 was identified on CCTV near the scene. "
                "Vikram Singh is believed to be the coordinator."
            ),
        },
        {
            "fir_no": "FIR/2024/KA/00789",
            "case_ref": "CASE-2024-003",
            "police_station": FIR_STATIONS[2],
            "date": "2024-05-20",
            "sections_of_law": "IPC 420, IPC 406",
            "complainant_name": "Nandita Roy",
            "accused_names": "Mohammed Farooq; Sunita Desai",
            "narrative_text": (
                "Nandita Roy reported that Mohammed Farooq and Sunita Desai "
                "collected advance payments for non-existent contracts at "
                "Koramangala, Bengaluru. Vehicle KA03EF9012 linked to Farooq. "
                "Case references FIR/2024/MH/00123 as a related matter."
            ),
        },
        {
            "fir_no": "FIR/2024/WB/01001",
            "case_ref": "CASE-2024-004",
            "police_station": FIR_STATIONS[3],
            "date": "2024-06-10",
            "sections_of_law": "IPC 420, IPC 34",
            "complainant_name": "Arjun Malhotra",
            "accused_names": "Geeta Bose; Fatima Sheikh; Rajesh Kumar Sharma",
            "narrative_text": (
                "Arjun Malhotra stated that Geeta Bose and Fatima Sheikh, "
                "acting in concert with Rajesh Kumar Sharma, diverted funds "
                "through multiple accounts at Salt Lake, Kolkata. "
                "FIR/2024/WB/01001 registered."
            ),
        },
        {
            "fir_no": "FIR/2024/TN/00215",
            "case_ref": "CASE-2024-005",
            "police_station": FIR_STATIONS[4],
            "date": "2024-06-25",
            "sections_of_law": "IPC 468, IPC 471, IPC 120B",
            "complainant_name": "Anil Verma",
            "accused_names": "Dinesh Patel; Vikram Singh; Leela Krishnamurthy",
            "narrative_text": (
                "Complainant stated that Dinesh Patel and Vikram Singh submitted forged "
                "invoices bearing Phoenix Traders Association letterhead at T Nagar, Chennai. "
                "Leela Krishnamurthy witnessed documentation processing. "
                "Vehicle TN09GH3456 observed outside commercial registry office."
            ),
        },
        {
            "fir_no": "FIR/2024/MH/00340",
            "case_ref": "CASE-2024-006",
            "police_station": FIR_STATIONS[0],
            "date": "2024-07-04",
            "sections_of_law": "IPC 420, IT Act 66D",
            "complainant_name": "Kavita Nair",
            "accused_names": "Sunita Desai; Priya Mehta",
            "narrative_text": (
                "Kavita Nair alleged that Sunita Desai and Priya Mehta established a bogus payment gateway "
                "at Powai, Mumbai. Linked to ShadowTech Pvt Ltd operations and related to earlier "
                "complaints under FIR/2024/MH/00123."
            ),
        },
        {
            "fir_no": "FIR/2024/DL/00612",
            "case_ref": "CASE-2024-007",
            "police_station": FIR_STATIONS[1],
            "date": "2024-07-18",
            "sections_of_law": "IPC 409, IPC 120B",
            "complainant_name": "Vikram Singh",
            "accused_names": "Sameer Joshi; Nandita Roy; Dinesh Patel",
            "narrative_text": (
                "Complaint filed regarding unauthorized inventory clearance at Connaught Place, New Delhi. "
                "Sameer Joshi and Nandita Roy acted on instructions from Dinesh Patel. "
                "Consignment vehicle DL05CD5678 impounded for forensic verification."
            ),
        },
        {
            "fir_no": "FIR/2024/KA/00954",
            "case_ref": "CASE-2024-008",
            "police_station": FIR_STATIONS[2],
            "date": "2024-08-02",
            "sections_of_law": "IPC 420, IPC 34",
            "complainant_name": "Sunita Desai",
            "accused_names": "Mohammed Farooq; Anil Verma; Geeta Bose",
            "narrative_text": (
                "Investigation into corporate misrepresentation at Electronic City, Bengaluru. "
                "Mohammed Farooq and Anil Verma channeled funds with assistance from Geeta Bose. "
                "Vehicle KA03EF9012 recorded at regional banking center."
            ),
        },
        {
            "fir_no": "FIR/2024/TS/00118",
            "case_ref": "CASE-2024-009",
            "police_station": FIR_STATIONS[0],
            "date": "2024-08-15",
            "sections_of_law": "IPC 406, IPC 420",
            "complainant_name": "Priya Mehta",
            "accused_names": "Arjun Malhotra; Rajesh Kumar Sharma; Fatima Sheikh",
            "narrative_text": (
                "Priya Mehta reported financial breach by Arjun Malhotra and Fatima Sheikh "
                "during joint enterprise with Rajesh Kumar Sharma at Banjara Hills, Hyderabad. "
                "Contractual agreements seized under FIR/2024/TS/00118."
            ),
        },
        {
            "fir_no": "FIR/2024/WB/01245",
            "case_ref": "CASE-2024-010",
            "police_station": FIR_STATIONS[3],
            "date": "2024-08-29",
            "sections_of_law": "IPC 379, IPC 120B",
            "complainant_name": "Geeta Bose",
            "accused_names": "Vikram Singh; Arjun Malhotra; Leela Krishnamurthy",
            "narrative_text": (
                "Theft of sensitive corporate records reported near Park Street, Kolkata. "
                "Suspects identified as Vikram Singh and Arjun Malhotra in coordination with Leela Krishnamurthy. "
                "Vehicle MH02IJ7890 seen fleeing the premises."
            ),
        },
    ]

    path = os.path.join(OUT_DIR, "fir_reports.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "fir_no", "case_ref", "police_station", "date", "sections_of_law",
            "complainant_name", "accused_names", "narrative_text"
        ])
        writer.writeheader()
        writer.writerows(firs)
    print(f"[SYNTHETIC] Written: {path} ({len(firs)} records)")


# ---------------------------------------------------------------------------
# 3. Call Detail Records (20 records distributed across 10 cases)
# ---------------------------------------------------------------------------
def write_cdr_records():
    calls = [
        # CASE-2024-001
        ("P001", "P002", "2024-03-10 09:15:00", 180, LOCATIONS[0], "voice", "CASE-2024-001"),
        ("P001", "P003", "2024-03-15 14:00:00", 300, LOCATIONS[0], "voice", "CASE-2024-001"),
        # CASE-2024-002
        ("P007", "P008", "2024-04-01 09:00:00", 180, LOCATIONS[1], "voice", "CASE-2024-002"),
        ("P007", "P009", "2024-04-05 10:00:00", 90,  LOCATIONS[3], "voice", "CASE-2024-002"),
        # CASE-2024-003
        ("P005", "P004", "2024-05-18 11:30:00", 150, LOCATIONS[2], "voice", "CASE-2024-003"),
        ("P005", "P006", "2024-05-19 12:00:00", 60,  LOCATIONS[2], "sms",   "CASE-2024-003"),
        # CASE-2024-004
        ("P012", "P014", "2024-06-08 10:00:00", 120, LOCATIONS[3], "voice", "CASE-2024-004"),
        ("P001", "P012", "2024-06-09 11:00:00", 150, LOCATIONS[3], "voice", "CASE-2024-004"),
        # CASE-2024-005
        ("P007", "P011", "2024-06-24 14:00:00", 210, LOCATIONS[4], "voice", "CASE-2024-005"),
        ("P011", "P008", "2024-06-25 15:30:00", 90,  LOCATIONS[4], "sms",   "CASE-2024-005"),
        # CASE-2024-006
        ("P004", "P002", "2024-07-02 16:00:00", 180, LOCATIONS[7], "voice", "CASE-2024-006"),
        ("P006", "P002", "2024-07-03 08:45:00", 200, LOCATIONS[7], "voice", "CASE-2024-006"),
        # CASE-2024-007
        ("P009", "P010", "2024-07-16 13:00:00", 90,  LOCATIONS[1], "sms",   "CASE-2024-007"),
        ("P010", "P007", "2024-07-17 09:30:00", 180, LOCATIONS[1], "voice", "CASE-2024-007"),
        # CASE-2024-008
        ("P005", "P003", "2024-07-30 10:30:00", 240, LOCATIONS[8], "voice", "CASE-2024-008"),
        ("P003", "P012", "2024-08-01 14:00:00", 90,  LOCATIONS[8], "sms",   "CASE-2024-008"),
        # CASE-2024-009
        ("P013", "P001", "2024-08-12 14:00:00", 90,  LOCATIONS[5], "sms",   "CASE-2024-009"),
        ("P013", "P014", "2024-08-14 16:00:00", 60,  LOCATIONS[5], "sms",   "CASE-2024-009"),
        # CASE-2024-010
        ("P011", "P013", "2024-08-27 10:00:00", 120, LOCATIONS[9], "voice", "CASE-2024-010"),
        ("P008", "P011", "2024-08-28 09:00:00", 180, LOCATIONS[9], "voice", "CASE-2024-010"),
    ]
    rows = []
    for caller_id, callee_id, dt, dur, tower, ctype, case_ref in calls:
        rows.append({
            "caller_number": PHONES[caller_id],
            "callee_number": PHONES[callee_id],
            "call_datetime": dt,
            "duration_sec": dur,
            "cell_tower_location": tower,
            "call_type": ctype,
            "case_ref": case_ref,
        })

    path = os.path.join(OUT_DIR, "cdr_records.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "caller_number", "callee_number", "call_datetime",
            "duration_sec", "cell_tower_location", "call_type", "case_ref"
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[SYNTHETIC] Written: {path} ({len(rows)} records)")


# ---------------------------------------------------------------------------
# 4. Financial Transaction Records (10 records with case_ref)
# ---------------------------------------------------------------------------
def write_financial_transactions():
    rows = [
        {
            "txn_id": "TXN2024001", "case_ref": "CASE-2024-001", "sender_account": ACCOUNTS["P001"],
            "receiver_account": ACCOUNTS["P002"], "amount": 500000,
            "txn_datetime": "2024-03-10 10:00:00", "txn_mode": "NEFT",
            "remarks": "Payment to Priya Mehta for consulting services ShadowTech",
        },
        {
            "txn_id": "TXN2024006", "case_ref": "CASE-2024-002", "sender_account": ACCOUNTS["P007"],
            "receiver_account": ACCOUNTS["P008"], "amount": 300000,
            "txn_datetime": "2024-04-01 10:00:00", "txn_mode": "NEFT",
            "remarks": "Dinesh Patel Phoenix Traders payment to Leela Krishnamurthy",
        },
        {
            "txn_id": "TXN2024003", "case_ref": "CASE-2024-003", "sender_account": ACCOUNTS["P005"],
            "receiver_account": ACCOUNTS["P004"], "amount": 100000,
            "txn_datetime": "2024-05-18 09:00:00", "txn_mode": "UPI",
            "remarks": "Sunita Desai advance for Bangalore delivery",
        },
        {
            "txn_id": "TXN2024004", "case_ref": "CASE-2024-004", "sender_account": ACCOUNTS["P012"],
            "receiver_account": ACCOUNTS["P001"], "amount": 750000,
            "txn_datetime": "2024-06-08 14:00:00", "txn_mode": "NEFT",
            "remarks": "Geeta Bose transfer to Rajesh Kumar Sharma Salt Lake",
        },
        {
            "txn_id": "TXN2024010", "case_ref": "CASE-2024-005", "sender_account": ACCOUNTS["P011"],
            "receiver_account": ACCOUNTS["P007"], "amount": 350000,
            "txn_datetime": "2024-06-24 11:00:00", "txn_mode": "UPI",
            "remarks": "Vikram Singh to Dinesh Patel Chennai clearance",
        },
        {
            "txn_id": "TXN2024005", "case_ref": "CASE-2024-006", "sender_account": ACCOUNTS["P006"],
            "receiver_account": ACCOUNTS["P002"], "amount": 200000,
            "txn_datetime": "2024-07-03 16:00:00", "txn_mode": "UPI",
            "remarks": "Kavita Nair to Priya M refund Powai gateway",
        },
        {
            "txn_id": "TXN2024007", "case_ref": "CASE-2024-007", "sender_account": ACCOUNTS["P009"],
            "receiver_account": ACCOUNTS["P010"], "amount": 150000,
            "txn_datetime": "2024-07-17 12:00:00", "txn_mode": "UPI",
            "remarks": "Sameer Joshi advance to Nandita Roy New Delhi",
        },
        {
            "txn_id": "TXN2024002", "case_ref": "CASE-2024-008", "sender_account": ACCOUNTS["P005"],
            "receiver_account": ACCOUNTS["P003"], "amount": 250000,
            "txn_datetime": "2024-07-31 11:00:00", "txn_mode": "UPI",
            "remarks": "Mohammed Farooq to Anil Verma tech account",
        },
        {
            "txn_id": "TXN2024009", "case_ref": "CASE-2024-009", "sender_account": ACCOUNTS["P013"],
            "receiver_account": ACCOUNTS["P001"], "amount": 600000,
            "txn_datetime": "2024-08-14 09:00:00", "txn_mode": "NEFT",
            "remarks": "Arjun Malhotra to Rajesh Kumar Sharma settlement Banjara Hills",
        },
        {
            "txn_id": "TXN2024008", "case_ref": "CASE-2024-010", "sender_account": ACCOUNTS["P010"],
            "receiver_account": ACCOUNTS["P011"], "amount": 400000,
            "txn_datetime": "2024-08-28 15:00:00", "txn_mode": "cash",
            "remarks": "Nandita Roy to Vikram Singh Park Street logistics",
        },
    ]

    path = os.path.join(OUT_DIR, "financial_transactions.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "txn_id", "case_ref", "sender_account", "receiver_account", "amount",
            "txn_datetime", "txn_mode", "remarks"
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[SYNTHETIC] Written: {path} ({len(rows)} records)")


# ---------------------------------------------------------------------------
# 5. Surveillance Reports (4 reports with CASE_REF)
# ---------------------------------------------------------------------------
def write_surveillance_reports():
    reports = [
        """--- REPORT
REPORT_ID: SURV-2024-MH-001
CASE_REF: CASE-2024-001
TEAM: Mumbai Mobile Surveillance Unit
LOCATION: Andheri West, Mumbai
DATE: 2024-03-14

Subjects Raju (believed to be Rajesh Kumar Sharma) and Priya M were observed
meeting at a café in Andheri West, Mumbai at approximately 11:30 hrs.
Both arrived in vehicle MH01AB1234. A third individual, identified tentatively
as Anil Verma, joined them at 12:00 hrs. A document exchange was observed.
No unlawful activity directly witnessed. Vehicle KA03EF9012 was seen parked
nearby and departed at 12:30 hrs.
""",
        """--- REPORT
REPORT_ID: SURV-2024-DL-002
CASE_REF: CASE-2024-002
TEAM: New Delhi Surveillance Team B
LOCATION: Karol Bagh, New Delhi
DATE: 2024-04-01

D. Patel (believed to be Dinesh Patel) and Sameer Joshi were observed loading
boxes into vehicle TN09GH3456 at a warehouse in Karol Bagh, New Delhi.
Phoenix Traders Association signage was visible on the warehouse exterior.
Vikram Singh arrived at 15:00 hrs in vehicle MH02IJ7890 and exchanged an
envelope with D. Patel. Both departed separately.
""",
        """--- REPORT
REPORT_ID: SURV-2024-KA-003
CASE_REF: CASE-2024-003
TEAM: Bengaluru Field Unit
LOCATION: Koramangala, Bengaluru
DATE: 2024-05-19

Mohammed Farooq and Sunita Desai were observed at an office building in
Koramangala, Bengaluru. They met with an unidentified individual for
approximately 45 minutes. Farooq was seen receiving a package.
Vehicle KA03EF9012 parked outside throughout the meeting.
Geeta Bose arrived at 14:00 hrs and joined the meeting briefly.
""",
        """--- REPORT
REPORT_ID: SURV-2024-WB-004
CASE_REF: CASE-2024-004
TEAM: Kolkata Observation Post 7
LOCATION: Salt Lake, Kolkata
DATE: 2024-06-09

Fatima Sheikh and Arjun Malhotra were observed at a hotel lobby in Salt Lake,
Kolkata. Leela K (believed to be Leela Krishnamurthy) was seen passing a
document to Fatima Sheikh. Nandita Roy arrived at 16:30 hrs.
ShadowTech Pvt Ltd branding was visible on a laptop screen during the meeting.
All subjects departed by 17:30 hrs.
""",
    ]

    path = os.path.join(OUT_DIR, "surveillance_reports.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(reports))
    print(f"[SYNTHETIC] Written: {path} ({len(reports)} records)")


# ---------------------------------------------------------------------------
# 6. Social Media Intelligence (8 posts with case_ref)
# ---------------------------------------------------------------------------
def write_social_media_posts():
    rows = [
        {
            "post_id": "SM001", "case_ref": "CASE-2024-001", "platform": "Twitter", "handle": "rajukumar",
            "display_name": "Rajesh Kumar Sharma",
            "post_text": "Great meeting with the team at ShadowTech today! Big projects ahead in Mumbai.",
            "timestamp": "2024-03-10 18:00:00",
            "mentioned_handles": "priya_m;anilv99",
        },
        {
            "post_id": "SM003", "case_ref": "CASE-2024-005", "platform": "Instagram", "handle": "dpatel_x",
            "display_name": "Dinesh Patel",
            "post_text": "Phoenix Traders Association event tonight at T Nagar. Sameer Joshi speaking!",
            "timestamp": "2024-06-24 17:00:00",
            "mentioned_handles": "sameerj;vikrams",
        },
        {
            "post_id": "SM002", "case_ref": "CASE-2024-006", "platform": "Twitter", "handle": "priya_m",
            "display_name": "Priya Mehta",
            "post_text": "Enjoyed the Powai strategy session with Raju and Anil. Exciting times!",
            "timestamp": "2024-07-02 19:30:00",
            "mentioned_handles": "rajukumar;anilv99",
        },
        {
            "post_id": "SM006", "case_ref": "CASE-2024-006", "platform": "Twitter", "handle": "kavita_n",
            "display_name": "Kavita Nair",
            "post_text": "Warning people: suspicious activity by Raju at ShadowTech. Stay alert!",
            "timestamp": "2024-07-04 10:00:00",
            "mentioned_handles": "rajukumar",
        },
        {
            "post_id": "SM007", "case_ref": "CASE-2024-007", "platform": "Instagram", "handle": "sameerj",
            "display_name": "Sameer Joshi",
            "post_text": "Logistics sorted with D. Patel and Vikram Singh for the Connaught Place consignment.",
            "timestamp": "2024-07-17 14:00:00",
            "mentioned_handles": "dpatel_x;vikrams",
        },
        {
            "post_id": "SM004", "case_ref": "CASE-2024-008", "platform": "Twitter", "handle": "mfarooq",
            "display_name": "Mohammed Farooq",
            "post_text": "Productive day in Electronic City. Thanks to Sunita D and Geeta B!",
            "timestamp": "2024-07-31 21:00:00",
            "mentioned_handles": "sunita_d;geetab",
        },
        {
            "post_id": "SM008", "case_ref": "CASE-2024-009", "platform": "Twitter", "handle": "geetab",
            "display_name": "Geeta Bose",
            "post_text": "Confirmed funds transfer for Hyderabad venture. Arjun M handling the next step.",
            "timestamp": "2024-08-14 16:00:00",
            "mentioned_handles": "arjunm;fatimas",
        },
        {
            "post_id": "SM005", "case_ref": "CASE-2024-010", "platform": "Twitter", "handle": "arjunm",
            "display_name": "Arjun Malhotra",
            "post_text": "Meeting with old associates in Kolkata. Good to reconnect with Fatima Sheikh.",
            "timestamp": "2024-08-28 22:00:00",
            "mentioned_handles": "fatimas;leelak",
        },
    ]

    path = os.path.join(OUT_DIR, "social_media_posts.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "case_ref", "platform", "handle", "display_name",
            "post_text", "timestamp", "mentioned_handles"
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[SYNTHETIC] Written: {path} ({len(rows)} records)")


# ---------------------------------------------------------------------------
# 7. Criminal History Database (6 records with case_ref)
# ---------------------------------------------------------------------------
def write_criminal_history():
    rows = [
        {
            "person_id": "P001",
            "case_ref": "CASE-2024-001",
            "name": "Rajesh Kumar Sharma",
            "aliases": "Raju;R.K. Sharma;Rajesh Sharma",
            "known_associates": "Priya Mehta;Anil Verma;Geeta Bose",
            "prior_cases": "FIR/2020/MH/00055;FIR/2022/MH/00302",
            "last_known_address": "Flat 12B, Sunrise Towers, Andheri West, Mumbai",
        },
        {
            "person_id": "P003",
            "case_ref": "CASE-2024-003",
            "name": "Anil Verma",
            "aliases": "Anil V;A. Verma",
            "known_associates": "Rajesh Kumar Sharma;Mohammed Farooq",
            "prior_cases": "FIR/2021/DL/00123",
            "last_known_address": "House No 45, Karol Bagh, New Delhi",
        },
        {
            "person_id": "P005",
            "case_ref": "CASE-2024-003",
            "name": "Mohammed Farooq",
            "aliases": "Farooq;M. Farooq",
            "known_associates": "Sunita Desai;Anil Verma",
            "prior_cases": "FIR/2019/KA/00088;FIR/2023/KA/00199",
            "last_known_address": "No 22, 3rd Block, Koramangala, Bengaluru",
        },
        {
            "person_id": "P007",
            "case_ref": "CASE-2024-005",
            "name": "Dinesh Patel",
            "aliases": "D. Patel;Dinesh P",
            "known_associates": "Sameer Joshi;Vikram Singh",
            "prior_cases": "FIR/2020/TN/00077",
            "last_known_address": "Plot 8, Industrial Area, T Nagar, Chennai",
        },
        {
            "person_id": "P011",
            "case_ref": "CASE-2024-007",
            "name": "Vikram Singh",
            "aliases": "V. Singh;Vikram S",
            "known_associates": "Dinesh Patel;Sameer Joshi;Arjun Malhotra",
            "prior_cases": "FIR/2021/DL/00200;FIR/2022/WB/00340",
            "last_known_address": "14 Kailash Colony, New Delhi",
        },
        {
            "person_id": "P013",
            "case_ref": "CASE-2024-010",
            "name": "Arjun Malhotra",
            "aliases": "Arjun M;A. Malhotra",
            "known_associates": "Geeta Bose;Fatima Sheikh;Vikram Singh",
            "prior_cases": "FIR/2023/WB/00500",
            "last_known_address": "Block C, Salt Lake, Kolkata",
        },
    ]

    path = os.path.join(OUT_DIR, "criminal_history.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "person_id", "case_ref", "name", "aliases", "known_associates",
            "prior_cases", "last_known_address"
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[SYNTHETIC] Written: {path} ({len(rows)} records)")


# ---------------------------------------------------------------------------
# 8. Intelligence Agency Reports (3 reports with CASE_REF)
# ---------------------------------------------------------------------------
def write_intelligence_reports():
    reports = """--- INTEL REPORT INTEL-2024-001 ---
REPORT_ID: INTEL-2024-001
CASE_REF: CASE-2024-001
CLASSIFICATION: RESTRICTED - DEMO (SYNTHETIC)
DATE: 2024-03-08
SUMMARY: Intelligence suggests that Rajesh Kumar Sharma (alias Raju) is the
coordinator of a financial fraud network operating through ShadowTech Pvt Ltd.
Associates Priya Mehta and Anil Verma handle fund transfers. Multiple UPI
accounts and NEFT channels are believed to be in use. Cell tower data from
Andheri West, Mumbai corroborates. [REDACTED] source confirms link to
FIR/2020/MH/00055. Recommend surveillance enhancement.

--- INTEL REPORT INTEL-2024-002 ---
REPORT_ID: INTEL-2024-002
CASE_REF: CASE-2024-002
CLASSIFICATION: RESTRICTED - DEMO (SYNTHETIC)
DATE: 2024-03-25
SUMMARY: Phoenix Traders Association is suspected of using logistics
infrastructure to move [REDACTED] across Karol Bagh, New Delhi and Salt Lake,
Kolkata corridors. Dinesh Patel and Vikram Singh are persons of interest.
Vehicle TN09GH3456 and MH02IJ7890 flagged in prior surveillance. Mohammed
Farooq may be the financial intermediary between the two primary networks.
Cross-reference with SURV-2024-DL-002.

--- INTEL REPORT INTEL-2024-003 ---
REPORT_ID: INTEL-2024-003
CASE_REF: CASE-2024-004
CLASSIFICATION: RESTRICTED - DEMO (SYNTHETIC)
DATE: 2024-05-30
SUMMARY: Arjun Malhotra and Fatima Sheikh appear to function as connectors
between the ShadowTech-linked network and the Phoenix Traders network.
Large fund movements detected between ACC013456789012 and ACC001234567890.
Geeta Bose may be facilitating document forgery. Leela Krishnamurthy's
role remains unclear. Social media intercepts from @arjunm and @fatimas
suggest coordinated activity. No direct evidence of criminal activity
confirmed at this stage — further investigation recommended.
"""

    path = os.path.join(OUT_DIR, "intelligence_reports.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(reports)
    print(f"[SYNTHETIC] Written: {path} (3 records)")


# ---------------------------------------------------------------------------
# 9. Ground Truth Pairs (for validation P/R/F1)
# ---------------------------------------------------------------------------
def write_ground_truth_pairs():
    rows = [
        {"normalized_a": "Rajesh Kumar Sharma", "normalized_b": "Raju",         "is_duplicate": "true",  "entity_type": "PERSON",   "reason": "alias"},
        {"normalized_a": "Rajesh Kumar Sharma", "normalized_b": "R.K. Sharma",  "is_duplicate": "true",  "entity_type": "PERSON",   "reason": "alias"},
        {"normalized_a": "Rajesh Kumar Sharma", "normalized_b": "Rajesh Sharma","is_duplicate": "true",  "entity_type": "PERSON",   "reason": "partial_name"},
        {"normalized_a": "Priya Mehta",         "normalized_b": "Priya M",       "is_duplicate": "true",  "entity_type": "PERSON",   "reason": "alias"},
        {"normalized_a": "Anil Verma",          "normalized_b": "Anil V",        "is_duplicate": "true",  "entity_type": "PERSON",   "reason": "alias"},
        {"normalized_a": "Anil Verma",          "normalized_b": "A. Verma",      "is_duplicate": "true",  "entity_type": "PERSON",   "reason": "alias"},
        {"normalized_a": "Dinesh Patel",        "normalized_b": "D. Patel",      "is_duplicate": "true",  "entity_type": "PERSON",   "reason": "alias"},
        {"normalized_a": "Dinesh Patel",        "normalized_b": "Dinesh P",      "is_duplicate": "true",  "entity_type": "PERSON",   "reason": "alias"},
        {"normalized_a": "Vikram Singh",        "normalized_b": "V. Singh",      "is_duplicate": "true",  "entity_type": "PERSON",   "reason": "alias"},
        {"normalized_a": "Leela Krishnamurthy", "normalized_b": "Leela K",       "is_duplicate": "true",  "entity_type": "PERSON",   "reason": "alias"},
        {"normalized_a": "Mohammed Farooq",     "normalized_b": "Farooq",        "is_duplicate": "true",  "entity_type": "PERSON",   "reason": "alias"},
        {"normalized_a": "Arjun Malhotra",      "normalized_b": "Arjun M",       "is_duplicate": "true",  "entity_type": "PERSON",   "reason": "alias"},
        {"normalized_a": "Geeta Bose",          "normalized_b": "G. Bose",       "is_duplicate": "true",  "entity_type": "PERSON",   "reason": "alias"},
        {"normalized_a": "Fatima Sheikh",       "normalized_b": "Fatima S",      "is_duplicate": "true",  "entity_type": "PERSON",   "reason": "alias"},
        {"normalized_a": "Sunita Desai",        "normalized_b": "Sunita D",      "is_duplicate": "true",  "entity_type": "PERSON",   "reason": "alias"},
        {"normalized_a": "+919876543210",       "normalized_b": "9876543210",    "is_duplicate": "true",  "entity_type": "PHONE",    "reason": "phone_format"},
        {"normalized_a": "Rajesh Kumar Sharma", "normalized_b": "Mohammed Farooq","is_duplicate": "false", "entity_type": "PERSON",  "reason": "different_entity"},
        {"normalized_a": "Priya Mehta",         "normalized_b": "Sunita Desai",  "is_duplicate": "false", "entity_type": "PERSON",   "reason": "different_entity"},
        {"normalized_a": "Dinesh Patel",        "normalized_b": "Arjun Malhotra","is_duplicate": "false", "entity_type": "PERSON",   "reason": "different_entity"},
        {"normalized_a": "Vikram Singh",        "normalized_b": "Sameer Joshi",  "is_duplicate": "false", "entity_type": "PERSON",   "reason": "different_entity"},
    ]

    path = os.path.join(OUT_DIR, "ground_truth_pairs.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "normalized_a", "normalized_b", "is_duplicate", "entity_type", "reason"
        ], quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[SYNTHETIC] Written: {path} ({len(rows)} pairs)")


def validate_generated_csvs():
    """Ensure every generated CSV parses with zero phantom None keys."""
    csv_files = [
        "fir_reports.csv",
        "cdr_records.csv",
        "financial_transactions.csv",
        "social_media_posts.csv",
        "criminal_history.csv",
        "ground_truth_pairs.csv",
    ]
    for fname in csv_files:
        path = os.path.join(OUT_DIR, fname)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing CSV file: {path}")
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if None in row:
                    raise ValueError(
                        f"Malformed CSV in {fname} at row {i}: found phantom None key with value {row[None]}"
                    )
    print("[SYNTHETIC] Validation PASSED: All 6 CSV files verified with 0 phantom None keys.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # NOTE: A larger 500-case tier is possible in the future only after further profiling
    # with the Fix 0 blocking strategy in place, and is out of scope for this pass.
    print("=" * 60)
    print("NeuroNex — Synthetic Data Generator (10 Demo Cases + 50 Expanded Cases)")
    print("ALL DATA IS FICTIONAL — SIH PS ID: SIH26189")
    print("Seed:", SEED)
    print("=" * 60)

    from generate_synthetic_data_expanded import generate_expanded_dataset
    generate_expanded_dataset()
