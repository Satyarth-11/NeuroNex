"""
NeuroNex — Synthetic Data Generator Extension (~50 Cases Tier)
============================================================
ALL DATA IS ENTIRELY FICTIONAL — SIH PS ID: SIH26189.
Never use real persons' private information anywhere.

Produces:
  - 10 Demo Cases (CASES 1-10) in cases_manifest.json (untouched, always available)
  - 50 Expanded Cases (CASES 11-60) in expanded_cases_manifest.json
  - 15 Held-Out Evaluation Cases (CASES 61-75) in held_out_cases_manifest.json
  - Multi-source records across FIR, CDR (500+ records), Financial (300+ records),
    Surveillance, Social Media, Criminal History, Intelligence Reports.
  - ~115+ labelled ground truth pairs in ground_truth_pairs.csv with dataset_tier.

NOTE: A larger 500-case tier is possible in the future only after further profiling
with the Fix 0 blocking strategy in place, and is out of scope for this pass.
"""
import csv
import json
import os
import random

SEED = 42
random.seed(SEED)
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Import base demo data
from generate_synthetic_data import (
    CASES as BASE_CASES,
    PERSONS as BASE_PERSONS,
    PHONES as BASE_PHONES,
    ACCOUNTS as BASE_ACCOUNTS,
    VEHICLES as BASE_VEHICLES,
    LOCATIONS as BASE_LOCATIONS,
    ORGS as BASE_ORGS,
    FIR_STATIONS as BASE_FIR_STATIONS,
    write_cases_manifest as write_base_manifest,
    validate_generated_csvs as validate_csvs_base,
)

# ---------------------------------------------------------------------------
# Additional Fictional Pool for 50 Expanded Cases
# ---------------------------------------------------------------------------
EXP_CITIES = [
    "Connaught Place, New Delhi", "Karol Bagh, New Delhi", "Rohini, New Delhi",
    "Andheri West, Mumbai", "Powai, Mumbai", "Bandra Kurla Complex, Mumbai",
    "Koramangala, Bengaluru", "Electronic City, Bengaluru", "Indiranagar, Bengaluru",
    "Salt Lake, Kolkata", "Park Street, Kolkata", "Bhowanipore, Kolkata",
    "T Nagar, Chennai", "Anna Nagar, Chennai", "Guindy, Chennai",
    "Banjara Hills, Hyderabad", "Hitec City, Hyderabad", "Secunderabad, Hyderabad",
    "Navrangpura, Ahmedabad", "SG Highway, Ahmedabad",
    "Shivajinagar, Pune", "Hinjawadi, Pune",
    "Aliganj, Lucknow", "Gomti Nagar, Lucknow",
    "Civil Lines, Jaipur", "Malviya Nagar, Jaipur",
]

EXP_ORGS = [
    "ShadowTech Pvt Ltd", "Phoenix Traders Association",
    "Apex Logistics Corp", "BlueHorizon Capital Ltd", "Vanguard Infra Solutions",
    "Zenith Global Exports", "Silverline Communications", "Kaveri Trading Syndicate",
    "Deccan Security Holdings", "Maruti Freight Carriers", "Indus Valley Digital",
    "Falcon Commercial Enterprises", "Eastern Coalitions LLP", "Trident Agro Tech",
]

FIRST_NAMES = [
    "Aarav", "Aditya", "Akash", "Amit", "Anand", "Anil", "Arjun", "Ashok",
    "Bhavesh", "Chetan", "Deepak", "Devendra", "Dinesh", "Gaurav", "Girish",
    "Harish", "Hemant", "Jagdish", "Kailash", "Kamal", "Karan", "Kishore",
    "Manish", "Manoj", "Mayank", "Mohan", "Mukesh", "Naresh", "Naveen",
    "Nilesh", "Nitin", "Pankaj", "Pawan", "Pradeep", "Prakash", "Prashant",
    "Praveen", "Rahul", "Rajeev", "Rajendra", "Rajesh", "Rakesh", "Ramesh",
    "Ravi", "Sachin", "Sandeep", "Sanjay", "Santosh", "Satish", "Sharad",
    "Ananya", "Bhavna", "Deepika", "Divya", "Geeta", "Jyoti", "Kavita",
    "Lata", "Meena", "Neeta", "Pooja", "Pratibha", "Priya", "Radha",
    "Rekha", "Renu", "Ritu", "Sarita", "Seema", "Shobha", "Sunita",
]

LAST_NAMES = [
    "Agarwal", "Banerjee", "Bansal", "Bhatt", "Chakraborty", "Chauhan", "Choudhury",
    "Deshmukh", "Dixit", "Dubey", "Ganguly", "Garg", "Ghosh", "Goel",
    "Gupta", "Iyer", "Jadhav", "Jain", "Jha", "Joshi", "Kapoor",
    "Kaur", "Khan", "Kulkarni", "Kumar", "Malhotra", "Mehta", "Mishra",
    "Mittal", "Mukherjee", "Nair", "Pandey", "Patel", "Patil", "Pillai",
    "Prasad", "Rao", "Rathore", "Reddy", "Roy", "Saxena", "Sen",
    "Shah", "Sharma", "Shukla", "Singh", "Soni", "Srivastava", "Tiwari",
    "Varma", "Verma", "Yadav",
]

EXP_POLICE_STATIONS = [
    "Andheri Police Station", "Connaught Place PS", "Koramangala PS", "Park Street PS",
    "T Nagar PS", "Banjara Hills PS", "Cyber Crime PS Cyberabad", "Special Cell New Delhi",
    "Anti Corruption Branch Mumbai", "Bhowanipore PS", "Hinjawadi IT PS", "Navrangpura PS",
]


def generate_expanded_dataset():
    """Builds and writes the complete 50 expanded cases and multi-source files."""
    rng = random.Random(SEED)

    # 1. Build Expanded Cast of 90 Fictional Persons
    cast = list(BASE_PERSONS)
    phones = dict(BASE_PHONES)
    accounts = dict(BASE_ACCOUNTS)
    vehicles = dict(BASE_VEHICLES)

    cast_id_counter = len(cast) + 1
    existing_names = {p["name"] for p in cast}

    while len(cast) < 95:
        fn = rng.choice(FIRST_NAMES)
        ln = rng.choice(LAST_NAMES)
        full_name = f"{fn} {ln}"
        if full_name in existing_names:
            continue
        existing_names.add(full_name)
        pid = f"P{cast_id_counter:03d}"
        cast_id_counter += 1

        alias = f"{fn} {ln[0]}" if rng.random() > 0.5 else f"{fn[0]}. {ln}"
        handle = f"@{fn.lower()}_{ln.lower()[:4]}"
        cast.append({"id": pid, "name": full_name, "alias": alias, "handle": handle})

        # Phone
        ph_num = f"+9198{rng.randint(10000000, 99999999)}"
        phones[pid] = ph_num

        # Account
        acc_num = f"ACC{rng.randint(100000000000, 999999999999)}"
        accounts[pid] = acc_num

        # Vehicle (for 60% of cast)
        if rng.random() > 0.4:
            state_codes = ["MH", "DL", "KA", "WB", "TN", "TS", "GJ"]
            st = rng.choice(state_codes)
            dist = f"{rng.randint(1, 15):02d}"
            alpha = rng.choice(["AB", "CD", "EF", "GH", "JK", "MN", "PQ", "RS"])
            v_num = f"{st}{dist}{alpha}{rng.randint(1000, 9999)}"
            vehicles[pid] = v_num

    # 2. Build 50 Expanded Cases (CASE-2024-011 through CASE-2024-060)
    # Includes cross-case entities, financial chains, CDR clusters, and normal cases.
    exp_cases = []
    case_types = [
        ("Financial Fraud & Shell Diversion", "Unauthorized transfer of corporate escrow funds into offshore entities and domestic shell accounts."),
        ("Logistics Intercept & Consignment Theft", "Inter-state freight diversion and hijacked warehouse stock across northern transit corridors."),
        ("Procurement Bid Manipulation", "Fabricated vendor documentation and collusion in public infrastructure bidding."),
        ("Cyber Extortion & Ransom Intercept", "Distributed extortion network targeting commercial accounting platforms via phishing gateways."),
        ("Counterfeit Invoicing Network", "Generation of fake GST tax invoices without genuine movement of underlying goods."),
        ("Unauthorized Mineral Siphoning", "Illegal transit and documentation diversion across regional mining transport links."),
        ("Telecom Tower Hardware Theft", "Coordinated sabotage and removal of cellular transmission hardware from urban rooftop relays."),
        ("Real Estate Advance Token Fraud", "Fabricated land development clearance and collection of non-refundable investor advance tokens."),
        ("Corporate Data Exfiltration", "Theft and black-market distribution of proprietary algorithmic trading documentation."),
        ("Identity Fabrication Syndicate", "Forged civic documentation and unauthorized SIM card activations used for commercial evasion."),
        ("Normal Commercial Dispute", "Routine commercial inquiry regarding delayed consignment delivery; no criminal conspiracy identified."),
        ("Normal Civil Property Record", "Civilian boundary clarification and land verification request; unremarkable background record."),
        ("Normal Trade License Clearance", "Routine municipal inspection inquiry regarding commercial warehouse zoning compliance."),
    ]

    for i in range(11, 61):
        code = f"CASE-2024-{i:03d}"
        t_type, t_desc = case_types[(i - 11) % len(case_types)]
        location = EXP_CITIES[(i - 11) % len(EXP_CITIES)]
        title = f"[DEMO] {location.split(',')[0]} {t_type}"
        desc = f"Investigation in {location} regarding {t_desc.lower()}"
        exp_cases.append({
            "case_code": code,
            "title": title,
            "description": desc,
        })

    # 3. Build Held-Out Evaluation Set (15 Cases: CASE-2024-061 to CASE-2024-075)
    held_out_cases = []
    for i in range(61, 76):
        code = f"CASE-2024-{i:03d}"
        held_out_cases.append({
            "case_code": code,
            "title": f"[HELD-OUT] Case Evaluation Reference {i}",
            "description": f"Held-out benchmark case for independent validation and scoring. Case code {code}.",
        })

    # 4. Multi-Source Records Generation
    # A) FIR Reports (1 per expanded case = 50 FIR records)
    exp_firs = []
    for idx, c in enumerate(exp_cases):
        code = c["case_code"]
        ps = EXP_POLICE_STATIONS[idx % len(EXP_POLICE_STATIONS)]
        date_day = (idx % 28) + 1
        date_month = ((idx // 28) + 1) % 12 + 1
        date_str = f"2024-{date_month:02d}-{date_day:02d}"

        # Assign persons: 1 complainant, 2-3 accused
        # Include cross-case links:
        if idx in (0, 15, 26, 36):
            # Links to Rajesh Kumar Sharma (P001) / ShadowTech
            complainant = cast[(idx + 14) % len(cast)]
            accused_1 = cast[0]  # P001 Rajesh
            accused_2 = cast[(idx + 3) % len(cast)]
            org = "ShadowTech Pvt Ltd"
            veh = vehicles.get(accused_1["id"], "MH01AB1234")
            alias_mention = "R.K. Sharma" if idx == 26 else accused_1["name"]
        elif idx in (4, 18, 38):
            # Links to Dinesh Patel (P007) / Phoenix Traders
            complainant = cast[(idx + 8) % len(cast)]
            accused_1 = cast[6]  # P007 Dinesh
            accused_2 = cast[(idx + 5) % len(cast)]
            org = "Phoenix Traders Association"
            veh = vehicles.get(accused_1["id"], "TN09GH3456")
            alias_mention = "D. Patel" if idx == 18 else accused_1["name"]
        else:
            complainant = cast[(idx * 2 + 10) % len(cast)]
            accused_1 = cast[(idx * 3 + 12) % len(cast)]
            accused_2 = cast[(idx * 4 + 15) % len(cast)]
            org = EXP_ORGS[idx % len(EXP_ORGS)]
            veh = vehicles.get(accused_1["id"], f"DL0{idx % 9}CD{1000 + idx}")
            alias_mention = accused_1["name"]

        fir_no = f"FIR/2024/EXP/{idx + 100:05d}"
        sections = "IPC 420, IPC 120B" if idx % 2 == 0 else "IPC 406, IPC 379"

        narrative = (
            f"Complainant {complainant['name']} registered complaint regarding unauthorized financial and material diversion "
            f"coordinated by {alias_mention} alongside {accused_2['name']} operating under {org}. "
            f"Vehicle {veh} was observed at {EXP_CITIES[idx % len(EXP_CITIES)]}. "
            f"Matter registered under {fir_no} citing {sections}."
        )

        exp_firs.append({
            "fir_no": fir_no,
            "case_ref": code,
            "police_station": ps,
            "date": date_str,
            "sections_of_law": sections,
            "complainant_name": complainant["name"],
            "accused_names": f"{alias_mention}; {accused_2['name']}",
            "narrative_text": narrative,
        })

    # B) CDR Records (500+ records across 50 cases)
    # Dense clusters for suspicious cases, normal call activity for background cases
    exp_cdrs = []
    for idx, c in enumerate(exp_cases):
        code = c["case_code"]
        num_calls = 14 if idx % 3 == 0 else 8
        city = EXP_CITIES[idx % len(EXP_CITIES)]

        # Participants
        if idx in (0, 15, 26, 36):
            core_pids = ["P001", "P002", "P003", cast[(idx + 2) % len(cast)]["id"]]
        elif idx in (4, 18, 38):
            core_pids = ["P007", "P008", "P011", cast[(idx + 3) % len(cast)]["id"]]
        else:
            p_base = (idx * 3) % len(cast)
            core_pids = [cast[(p_base + k) % len(cast)]["id"] for k in range(4)]

        for call_i in range(num_calls):
            src_pid = rng.choice(core_pids)
            dst_pid = rng.choice([p for p in core_pids if p != src_pid])
            src_ph = phones.get(src_pid, "+919800000000")
            dst_ph = phones.get(dst_pid, "+919800000001")
            ts = f"2024-{(idx % 11) + 1:02d}-{(call_i % 27) + 1:02d} {10 + (call_i % 10):02d}:{(call_i * 7) % 60:02d}:00"
            dur = rng.randint(30, 480)
            c_type = "voice" if rng.random() > 0.25 else "sms"

            exp_cdrs.append({
                "caller_number": src_ph,
                "callee_number": dst_ph,
                "call_datetime": ts,
                "duration_sec": dur,
                "cell_tower_location": city,
                "call_type": c_type,
                "case_ref": code,
            })

    # C) Financial Transactions (300+ transactions across 50 cases)
    # Includes chains and structured amounts (Rs 49,000, Rs 50,000, Rs 95,00,000)
    exp_fins = []
    for idx, c in enumerate(exp_cases):
        code = c["case_code"]
        num_tx = 8 if idx % 2 == 0 else 5

        # Accounts pool
        if idx in (0, 15, 26, 36):
            acc_pool = ["ACC001234567890", "ACC002345678901", "ACC003456789012", accounts[cast[(idx + 4) % len(cast)]["id"]]]
        elif idx in (4, 18, 38):
            acc_pool = ["ACC007890123456", "ACC008901234567", "ACC011234567890", accounts[cast[(idx + 6) % len(cast)]["id"]]]
        else:
            p_base = (idx * 2) % len(cast)
            acc_pool = [accounts[cast[(p_base + k) % len(cast)]["id"]] for k in range(4)]

        for tx_i in range(num_tx):
            src_acc = acc_pool[tx_i % len(acc_pool)]
            dst_acc = acc_pool[(tx_i + 1) % len(acc_pool)]
            tx_date = f"2024-{(idx % 11) + 1:02d}-{(tx_i % 25) + 1:02d} 10:{tx_i * 6:02d}:00"

            # Amount patterns
            if idx % 5 == 0:
                amount = 49500  # Structuring just below 50,000
            elif idx % 7 == 0 and tx_i == 0:
                amount = 9500000  # Large spike
            else:
                amount = int(rng.randint(15, 350) * 1000)

            tx_type = rng.choice(["NEFT", "RTGS", "UPI", "IMPS"])

            exp_fins.append({
                "txn_id": f"TXN2024EXP{len(exp_fins) + 1000:06d}",
                "case_ref": code,
                "sender_account": src_acc,
                "receiver_account": dst_acc,
                "amount": amount,
                "txn_datetime": tx_date,
                "txn_mode": tx_type,
                "remarks": f"Transfer for {code} operations via {tx_type}",
            })

    # D) Surveillance Reports (26 reports across expanded cases)
    exp_survs = []
    for idx in range(0, 50, 2):
        case_code = exp_cases[idx]["case_code"]
        city = EXP_CITIES[idx % len(EXP_CITIES)]
        p = cast[(idx + 5) % len(cast)]
        v = vehicles.get(p["id"], "MH01AB1234")
        surv_text = (
            f"--- REPORT SURV-2024-EXP-{idx + 100:04d} ---\n"
            f"CASE_REF: {case_code}\n"
            f"LOCATION: {city}\n"
            f"DATE: 2024-07-{(idx % 25) + 1:02d}\n"
            f"OFFICER_ID: SURV_OFFICER_{(idx % 10) + 1:02d}\n"
            f"NOTES: Physical surveillance confirmed operative {p['name']} (alias {p['alias']}) meeting with commercial contacts. "
            f"Vehicle {v} was observed parked near commercial registry. "
            f"Subject departed toward highway ring road at 16:30 hours.\n"
        )
        exp_survs.append(surv_text)

    # E) Social Media Posts (40 posts across expanded cases)
    exp_sm = []
    for idx in range(40):
        c = exp_cases[idx]
        p = cast[(idx + 8) % len(cast)]
        loc = EXP_CITIES[idx % len(EXP_CITIES)]
        ph = phones.get(p["id"], "+919876543210")
        exp_sm.append({
            "post_id": f"SM_EXP_{idx + 100:04d}",
            "case_ref": c["case_code"],
            "platform": rng.choice(["Twitter", "Telegram", "Instagram", "WhatsApp"]),
            "handle": p["handle"].lstrip("@"),
            "display_name": p["name"],
            "post_text": f"New commercial agreements finalizing at {loc}. Coordinated with {p['name']}. Contact directly at {ph} for consignment details.",
            "timestamp": f"2024-06-{(idx % 28) + 1:02d} 14:{(idx * 3) % 60:02d}:00",
            "mentioned_handles": f"{cast[(idx + 1) % len(cast)]['handle'].lstrip('@')};{cast[(idx + 2) % len(cast)]['handle'].lstrip('@')}",
        })

    # F) Criminal History (24 profiles across expanded cases)
    exp_crim = []
    for idx in range(24):
        c = exp_cases[idx * 2]
        p = cast[(idx + 12) % len(cast)]
        loc = EXP_CITIES[idx % len(EXP_CITIES)]
        exp_crim.append({
            "person_id": p["id"],
            "case_ref": c["case_code"],
            "name": p["name"],
            "aliases": f"{p['alias']};{p['name'].split()[0]}",
            "known_associates": f"{cast[(idx + 2) % len(cast)]['name']};{cast[(idx + 3) % len(cast)]['name']}",
            "prior_cases": f"FIR/2021/EXP/{100 + idx};FIR/2023/EXP/{200 + idx}",
            "last_known_address": f"Sector {idx + 1}, {loc}",
        })

    # G) Intelligence Reports (22 reports across expanded cases)
    exp_intels = []
    for idx in range(22):
        c = exp_cases[idx * 2]
        p1 = cast[(idx + 7) % len(cast)]
        p2 = cast[(idx + 9) % len(cast)]
        org = EXP_ORGS[idx % len(EXP_ORGS)]
        memo = (
            f"--- INTEL REPORT INTEL-2024-EXP-{idx + 100:04d} ---\n"
            f"REPORT_ID: INTEL-2024-EXP-{idx + 100:04d}\n"
            f"CASE_REF: {c['case_code']}\n"
            f"CLASSIFICATION: CONFIDENTIAL - PROTOTYPE (SYNTHETIC)\n"
            f"DATE: 2024-08-{(idx % 25) + 1:02d}\n"
            f"SUMMARY: Field intelligence intercept indicates {p1['name']} operating under cover of {org} "
            f"facilitating undocumented movements with {p2['name']}. "
            f"Multiple communication intercepts corroborate movement across {EXP_CITIES[idx % len(EXP_CITIES)]}. "
            f"Cross-reference with case dossier {c['case_code']}.\n"
        )
        exp_intels.append(memo)

    # 5. Expanded Ground Truth Pairs (115+ pairs: 80 Development + 35 Held-Out)
    # Includes aliases, initials, phonetic, formatted phones, and hard negatives
    gt_pairs = [
        # Base development pairs
        {"normalized_a": "Rajesh Kumar Sharma", "normalized_b": "Raju", "is_duplicate": "true", "entity_type": "PERSON", "reason": "alias", "dataset_tier": "development"},
        {"normalized_a": "Rajesh Kumar Sharma", "normalized_b": "R.K. Sharma", "is_duplicate": "true", "entity_type": "PERSON", "reason": "initials", "dataset_tier": "development"},
        {"normalized_a": "Rajesh Kumar Sharma", "normalized_b": "Rajesh Sharma", "is_duplicate": "true", "entity_type": "PERSON", "reason": "partial_name", "dataset_tier": "development"},
        {"normalized_a": "Priya Mehta", "normalized_b": "Priya M", "is_duplicate": "true", "entity_type": "PERSON", "reason": "alias", "dataset_tier": "development"},
        {"normalized_a": "Anil Verma", "normalized_b": "Anil V", "is_duplicate": "true", "entity_type": "PERSON", "reason": "alias", "dataset_tier": "development"},
        {"normalized_a": "Anil Verma", "normalized_b": "A. Verma", "is_duplicate": "true", "entity_type": "PERSON", "reason": "initials", "dataset_tier": "development"},
        {"normalized_a": "Dinesh Patel", "normalized_b": "D. Patel", "is_duplicate": "true", "entity_type": "PERSON", "reason": "initials", "dataset_tier": "development"},
        {"normalized_a": "Dinesh Patel", "normalized_b": "Dinesh P", "is_duplicate": "true", "entity_type": "PERSON", "reason": "alias", "dataset_tier": "development"},
        {"normalized_a": "Vikram Singh", "normalized_b": "V. Singh", "is_duplicate": "true", "entity_type": "PERSON", "reason": "initials", "dataset_tier": "development"},
        {"normalized_a": "Leela Krishnamurthy", "normalized_b": "Leela K", "is_duplicate": "true", "entity_type": "PERSON", "reason": "alias", "dataset_tier": "development"},
        {"normalized_a": "Mohammed Farooq", "normalized_b": "Farooq", "is_duplicate": "true", "entity_type": "PERSON", "reason": "alias", "dataset_tier": "development"},
        {"normalized_a": "Arjun Malhotra", "normalized_b": "Arjun M", "is_duplicate": "true", "entity_type": "PERSON", "reason": "alias", "dataset_tier": "development"},
        {"normalized_a": "Geeta Bose", "normalized_b": "G. Bose", "is_duplicate": "true", "entity_type": "PERSON", "reason": "initials", "dataset_tier": "development"},
        {"normalized_a": "Fatima Sheikh", "normalized_b": "Fatima S", "is_duplicate": "true", "entity_type": "PERSON", "reason": "alias", "dataset_tier": "development"},
        {"normalized_a": "Sunita Desai", "normalized_b": "Sunita D", "is_duplicate": "true", "entity_type": "PERSON", "reason": "alias", "dataset_tier": "development"},
        {"normalized_a": "+919876543210", "normalized_b": "9876543210", "is_duplicate": "true", "entity_type": "PHONE", "reason": "phone_format", "dataset_tier": "development"},
        {"normalized_a": "+919812345678", "normalized_b": "9812345678", "is_duplicate": "true", "entity_type": "PHONE", "reason": "phone_format", "dataset_tier": "development"},
        {"normalized_a": "+919823456789", "normalized_b": "9823456789", "is_duplicate": "true", "entity_type": "PHONE", "reason": "phone_format", "dataset_tier": "development"},
        # Hard negatives (development)
        {"normalized_a": "Rajesh Kumar Sharma", "normalized_b": "Mohammed Farooq", "is_duplicate": "false", "entity_type": "PERSON", "reason": "different_entity", "dataset_tier": "development"},
        {"normalized_a": "Priya Mehta", "normalized_b": "Sunita Desai", "is_duplicate": "false", "entity_type": "PERSON", "reason": "different_entity", "dataset_tier": "development"},
        {"normalized_a": "Dinesh Patel", "normalized_b": "Arjun Malhotra", "is_duplicate": "false", "entity_type": "PERSON", "reason": "different_entity", "dataset_tier": "development"},
        {"normalized_a": "Vikram Singh", "normalized_b": "Sameer Joshi", "is_duplicate": "false", "entity_type": "PERSON", "reason": "different_entity", "dataset_tier": "development"},
        {"normalized_a": "Rajesh Kumar Sharma", "normalized_b": "Ramesh Kumar Sharma", "is_duplicate": "false", "entity_type": "PERSON", "reason": "hard_negative_similar_name", "dataset_tier": "development"},
        {"normalized_a": "Priya Mehta", "normalized_b": "Priya Verma", "is_duplicate": "false", "entity_type": "PERSON", "reason": "hard_negative_same_first", "dataset_tier": "development"},
        {"normalized_a": "Dinesh Patel", "normalized_b": "Deepak Patel", "is_duplicate": "false", "entity_type": "PERSON", "reason": "hard_negative_same_last", "dataset_tier": "development"},
    ]

    # Add proportional development pairs for expanded cast (up to 80 development pairs)
    for p in cast[14:45]:
        fn, ln = p["name"].split()[0], p["name"].split()[-1]
        gt_pairs.append({
            "normalized_a": p["name"],
            "normalized_b": f"{fn} {ln[0]}",
            "is_duplicate": "true",
            "entity_type": "PERSON",
            "reason": "alias",
            "dataset_tier": "development",
        })
        gt_pairs.append({
            "normalized_a": p["name"],
            "normalized_b": f"{fn[0]}. {ln}",
            "is_duplicate": "true",
            "entity_type": "PERSON",
            "reason": "initials",
            "dataset_tier": "development",
        })
        # Hard negative
        gt_pairs.append({
            "normalized_a": p["name"],
            "normalized_b": f"{fn} Sharma" if ln != "Sharma" else f"{fn} Verma",
            "is_duplicate": "false",
            "entity_type": "PERSON",
            "reason": "hard_negative_different_surname",
            "dataset_tier": "development",
        })

    # Add genuinely separate HELD-OUT Evaluation pairs (35 pairs: 20 positive, 15 hard negative)
    for p in cast[45:65]:
        fn, ln = p["name"].split()[0], p["name"].split()[-1]
        gt_pairs.append({
            "normalized_a": p["name"],
            "normalized_b": f"{fn[0]}. {ln}",
            "is_duplicate": "true",
            "entity_type": "PERSON",
            "reason": "held_out_initials",
            "dataset_tier": "held_out",
        })
    for p in cast[65:80]:
        fn, ln = p["name"].split()[0], p["name"].split()[-1]
        gt_pairs.append({
            "normalized_a": p["name"],
            "normalized_b": f"{fn} {ln[0]}",
            "is_duplicate": "true",
            "entity_type": "PERSON",
            "reason": "held_out_alias",
            "dataset_tier": "held_out",
        })
    for p in cast[45:60]:
        fn, ln = p["name"].split()[0], p["name"].split()[-1]
        gt_pairs.append({
            "normalized_a": p["name"],
            "normalized_b": f"Kiran {ln}",
            "is_duplicate": "false",
            "entity_type": "PERSON",
            "reason": "held_out_hard_negative",
            "dataset_tier": "held_out",
        })

    # 6. Write Files to disk
    # A) Manifests
    write_base_manifest()

    exp_manifest_path = os.path.join(OUT_DIR, "expanded_cases_manifest.json")
    with open(exp_manifest_path, "w", encoding="utf-8") as f:
        json.dump(exp_cases, f, indent=2)
    print(f"[SYNTHETIC] Written: {exp_manifest_path} ({len(exp_cases)} expanded cases)")

    held_out_manifest_path = os.path.join(OUT_DIR, "held_out_cases_manifest.json")
    with open(held_out_manifest_path, "w", encoding="utf-8") as f:
        json.dump(held_out_cases, f, indent=2)
    print(f"[SYNTHETIC] Written: {held_out_manifest_path} ({len(held_out_cases)} held-out cases)")

    # B) Combined FIRs (10 base + 50 expanded = 60 FIRs)
    base_firs_path = os.path.join(OUT_DIR, "fir_reports.csv")
    base_firs = []
    if os.path.exists(base_firs_path):
        with open(base_firs_path, "r", encoding="utf-8") as f:
            base_firs = [r for r in csv.DictReader(f) if r.get("case_ref") in [bc["case_code"] for bc in BASE_CASES]]
    all_firs = base_firs + exp_firs

    with open(base_firs_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "fir_no", "case_ref", "police_station", "date", "sections_of_law",
            "complainant_name", "accused_names", "narrative_text"
        ])
        writer.writeheader()
        writer.writerows(all_firs)
    print(f"[SYNTHETIC] Written: {base_firs_path} ({len(all_firs)} FIRs)")

    # C) Combined CDRs (20 base + 520 expanded = 540 CDRs)
    base_cdrs_path = os.path.join(OUT_DIR, "cdr_records.csv")
    base_cdrs = []
    if os.path.exists(base_cdrs_path):
        with open(base_cdrs_path, "r", encoding="utf-8") as f:
            base_cdrs = [r for r in csv.DictReader(f) if r.get("case_ref") in [bc["case_code"] for bc in BASE_CASES]]
    all_cdrs = base_cdrs + exp_cdrs

    with open(base_cdrs_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "caller_number", "callee_number", "call_datetime",
            "duration_sec", "cell_tower_location", "call_type", "case_ref"
        ])
        writer.writeheader()
        writer.writerows(all_cdrs)
    print(f"[SYNTHETIC] Written: {base_cdrs_path} ({len(all_cdrs)} CDRs)")

    # D) Combined Financial Transactions (10 base + ~320 expanded = ~330 transactions)
    base_fins_path = os.path.join(OUT_DIR, "financial_transactions.csv")
    base_fins = []
    if os.path.exists(base_fins_path):
        with open(base_fins_path, "r", encoding="utf-8") as f:
            base_fins = [r for r in csv.DictReader(f) if r.get("case_ref") in [bc["case_code"] for bc in BASE_CASES]]
    all_fins = base_fins + exp_fins

    with open(base_fins_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "txn_id", "case_ref", "sender_account", "receiver_account", "amount",
            "txn_datetime", "txn_mode", "remarks"
        ])
        writer.writeheader()
        writer.writerows(all_fins)
    print(f"[SYNTHETIC] Written: {base_fins_path} ({len(all_fins)} Financial Transactions)")

    # E) Combined Surveillance Reports (4 base + 26 expanded = 30 reports)
    base_surv_path = os.path.join(OUT_DIR, "surveillance_reports.txt")
    base_surv = ""
    if os.path.exists(base_surv_path):
        with open(base_surv_path, "r", encoding="utf-8") as f:
            base_surv = f.read()
    base_parts = [p.strip() for p in base_surv.split("--- REPORT") if p.strip()]
    base_10_surv = ["--- REPORT\n" + p for p in base_parts if any(bc["case_code"] in p for bc in BASE_CASES)]
    all_surv_text = "\n\n".join(base_10_surv + exp_survs)

    with open(base_surv_path, "w", encoding="utf-8") as f:
        f.write(all_surv_text)
    print(f"[SYNTHETIC] Written: {base_surv_path} ({len(base_10_surv) + len(exp_survs)} Surveillance Reports)")

    # F) Combined Social Media Posts (8 base + 40 expanded = 48 posts)
    base_sm_path = os.path.join(OUT_DIR, "social_media_posts.csv")
    base_sm = []
    if os.path.exists(base_sm_path):
        with open(base_sm_path, "r", encoding="utf-8") as f:
            base_sm = [r for r in csv.DictReader(f) if r.get("case_ref") in [bc["case_code"] for bc in BASE_CASES]]
    all_sm = base_sm + exp_sm

    with open(base_sm_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "case_ref", "platform", "handle", "display_name",
            "post_text", "timestamp", "mentioned_handles"
        ])
        writer.writeheader()
        writer.writerows(all_sm)
    print(f"[SYNTHETIC] Written: {base_sm_path} ({len(all_sm)} Social Media Posts)")

    # G) Combined Criminal History (6 base + 24 expanded = 30 records)
    base_crim_path = os.path.join(OUT_DIR, "criminal_history.csv")
    base_crim = []
    if os.path.exists(base_crim_path):
        with open(base_crim_path, "r", encoding="utf-8") as f:
            base_crim = [r for r in csv.DictReader(f) if r.get("case_ref") in [bc["case_code"] for bc in BASE_CASES]]
    all_crim = base_crim + exp_crim

    with open(base_crim_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "person_id", "case_ref", "name", "aliases", "known_associates",
            "prior_cases", "last_known_address"
        ])
        writer.writeheader()
        writer.writerows(all_crim)
    print(f"[SYNTHETIC] Written: {base_crim_path} ({len(all_crim)} Criminal History Records)")

    # H) Combined Intelligence Reports (3 base + 22 expanded = 25 reports)
    base_intel_path = os.path.join(OUT_DIR, "intelligence_reports.txt")
    base_intel = ""
    if os.path.exists(base_intel_path):
        with open(base_intel_path, "r", encoding="utf-8") as f:
            base_intel = f.read()
    base_parts = [p.strip() for p in base_intel.split("--- INTEL REPORT") if p.strip()]
    base_10_intel = ["--- INTEL REPORT " + p for p in base_parts if any(bc["case_code"] in p for bc in BASE_CASES)]
    all_intel_text = "\n\n".join(base_10_intel + exp_intels)

    with open(base_intel_path, "w", encoding="utf-8") as f:
        f.write(all_intel_text)
    print(f"[SYNTHETIC] Written: {base_intel_path} ({len(base_10_intel) + len(exp_intels)} Intelligence Reports)")

    # I) Ground Truth Pairs (115+ pairs)
    gt_path = os.path.join(OUT_DIR, "ground_truth_pairs.csv")
    with open(gt_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "normalized_a", "normalized_b", "is_duplicate", "entity_type", "reason", "dataset_tier"
        ])
        writer.writeheader()
        writer.writerows(gt_pairs)
    print(f"[SYNTHETIC] Written: {gt_path} ({len(gt_pairs)} pairs: {sum(1 for p in gt_pairs if p['dataset_tier']=='development')} dev, {sum(1 for p in gt_pairs if p['dataset_tier']=='held_out')} held-out)")

    # Validate CSVs
    validate_csvs_base()

    # Print actual generated counts
    total_cases = len(BASE_CASES) + len(exp_cases)
    total_docs = len(all_firs) + len(all_cdrs) + len(all_fins) + (len(base_10_surv) + len(exp_survs)) + len(all_sm) + len(all_crim) + (len(base_10_intel) + len(exp_intels))
    print("\n" + "=" * 60)
    print("ACTUAL GENERATED DATASET COUNTS:")
    print(f"  Cases Created: {total_cases} (10 Base Demo + 50 Expanded)")
    print(f"  Held-Out Evaluation Cases: {len(held_out_cases)}")
    print(f"  Documents/Source Records Created: {total_docs}")
    print(f"  FIR Reports: {len(all_firs)}")
    print(f"  Communications (CDR) Created: {len(all_cdrs)}")
    print(f"  Financial Transactions Created: {len(all_fins)}")
    print(f"  Surveillance Reports Created: {len(base_10_surv) + len(exp_survs)}")
    print(f"  Social Media Posts Created: {len(all_sm)}")
    print(f"  Criminal History Records Created: {len(all_crim)}")
    print(f"  Intelligence Reports Created: {len(base_10_intel) + len(exp_intels)}")
    print(f"  Ground Truth Pairs: {len(gt_pairs)} ({sum(1 for p in gt_pairs if p['dataset_tier']=='development')} Development / {sum(1 for p in gt_pairs if p['dataset_tier']=='held_out')} Held-Out)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    generate_expanded_dataset()
