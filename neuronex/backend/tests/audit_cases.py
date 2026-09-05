import json
import os
import sqlite3
import csv

backend_dir = r"C:\Users\satya\.gemini\antigravity-ide\scratch\neuronex\backend"
data_dir = os.path.join(backend_dir, "data", "synthetic")

print("--- 1. Synthetic Manifests ---")
for f in ["cases_manifest.json", "expanded_cases_manifest.json", "held_out_cases_manifest.json"]:
    p = os.path.join(data_dir, f)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fp:
            d = json.load(fp)
        print(f"{f}: {len(d)} cases ({d[0]['case_code']} .. {d[-1]['case_code']})")

print("\n--- 2. Cases Referenced Across Raw CSV Files ---")
cases_in_files = {}
for fname in ["fir_reports.csv", "cdr_records.csv", "financial_transactions.csv", "criminal_history.csv", "social_media_posts.csv"]:
    p = os.path.join(data_dir, fname)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fp:
            cases = set(row.get("case_ref") for row in csv.DictReader(fp) if row.get("case_ref"))
        cases_in_files[fname] = sorted(list(cases))
        print(f"{fname}: {len(cases)} cases ({cases_in_files[fname][0]} .. {cases_in_files[fname][-1]})")

all_active_cases = sorted(list(set.union(*[set(c) for c in cases_in_files.values()])))
print(f"\nTotal unique active cases across all raw data: {len(all_active_cases)}")
print(f"Range: {all_active_cases[0]} to {all_active_cases[-1]}")
