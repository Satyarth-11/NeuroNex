import json
import csv
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(backend_dir, "data", "synthetic")

with open(os.path.join(data_dir, "cases_manifest.json")) as f:
    base = json.load(f)
with open(os.path.join(data_dir, "expanded_cases_manifest.json")) as f:
    exp = json.load(f)
with open(os.path.join(data_dir, "held_out_cases_manifest.json")) as f:
    held = json.load(f)

print(f"Base: {len(base)}, Exp: {len(exp)}, Held: {len(held)}")

# Also check SQLite DB if it exists
import sqlite3
db_path = os.path.join(backend_dir, "neuronex.db")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM cases")
    print(f"SQLite cases count: {cur.fetchone()[0]}")
    cur.execute("SELECT count(*) FROM documents")
    print(f"SQLite documents count: {cur.fetchone()[0]}")
    cur.execute("SELECT count(*) FROM extracted_entities")
    print(f"SQLite extracted_entities count: {cur.fetchone()[0]}")
    conn.close()
else:
    print(f"SQLite DB not found at {db_path}")
