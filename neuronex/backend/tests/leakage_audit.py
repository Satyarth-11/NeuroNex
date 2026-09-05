import csv
import os
from collections import defaultdict

backend_dir = r"C:\Users\satya\.gemini\antigravity-ide\scratch\neuronex\backend"
data_dir = os.path.join(backend_dir, "data", "synthetic")

active_cases_set = set()
for fname in ["fir_reports.csv", "cdr_records.csv", "financial_transactions.csv", "criminal_history.csv", "social_media_posts.csv"]:
    p = os.path.join(data_dir, fname)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fp:
            for row in csv.DictReader(fp):
                c = row.get("case_ref")
                if c:
                    active_cases_set.add(c)

all_cases = sorted(list(active_cases_set))
N = len(all_cases)
split_idx = int(round(N * 0.8))
dev_cases = all_cases[:split_idx]
held_out_cases = all_cases[split_idx:]

entity_cases = defaultdict(set)
entity_roles = {}

fir_path = os.path.join(data_dir, "fir_reports.csv")
with open(fir_path, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        c = r.get("case_ref")
        comp = r.get("complainant_name", "").strip()
        accs = [a.strip() for a in r.get("accused_names", "").split(";") if a.strip()]
        if comp:
            entity_cases[comp].add(c)
            entity_roles.setdefault(comp, {"accused": 0, "complainant": 0, "criminal_history": False})["complainant"] += 1
        for a in accs:
            entity_cases[a].add(c)
            entity_roles.setdefault(a, {"accused": 0, "complainant": 0, "criminal_history": False})["accused"] += 1

crim_path = os.path.join(data_dir, "criminal_history.csv")
with open(crim_path, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        c = r.get("case_ref")
        name = r.get("name", "").strip()
        if name:
            if c:
                entity_cases[name].add(c)
            entity_roles.setdefault(name, {"accused": 0, "complainant": 0, "criminal_history": False})["criminal_history"] = True

dev_case_set = set(dev_cases)
held_out_case_set = set(held_out_cases)

dev_entities = {e for e, cs in entity_cases.items() if cs & dev_case_set}
held_out_entities = {e for e, cs in entity_cases.items() if cs & held_out_case_set}
overlapping = dev_entities & held_out_entities
exclusive_held_out = held_out_entities - dev_entities

print("--- Exclusive Held-out Entities (Overlap = 0) ---")
for e in sorted(list(exclusive_held_out)):
    r = entity_roles.get(e, {})
    label = 1 if (r.get("accused", 0) > 0 or r.get("criminal_history")) else 0
    print(f"  {e}: label={label} (accused={r.get('accused', 0)}, comp={r.get('complainant', 0)}, crim_hist={r.get('criminal_history')})")

pos_all = sum(1 for e in held_out_entities if entity_roles[e].get("accused", 0) > 0 or entity_roles[e].get("criminal_history"))
neg_all = len(held_out_entities) - pos_all
print(f"\nAll Held-out Entities ({len(held_out_entities)}): Positives={pos_all}, Negatives={neg_all}")

pos_excl = sum(1 for e in exclusive_held_out if entity_roles[e].get("accused", 0) > 0 or entity_roles[e].get("criminal_history"))
neg_excl = len(exclusive_held_out) - pos_excl
print(f"Exclusive Held-out Entities ({len(exclusive_held_out)}): Positives={pos_excl}, Negatives={neg_excl}")
