import csv
import math
import os
from collections import defaultdict, deque
from datetime import datetime, timedelta

backend_dir = r"C:\Users\satya\.gemini\antigravity-ide\scratch\neuronex\backend"
data_dir = os.path.join(backend_dir, "data", "synthetic")

# 1. Discover all active cases with data
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
N_cases = len(all_cases)
split_idx = int(round(N_cases * 0.8))
dev_cases = all_cases[:split_idx]
held_out_cases = all_cases[split_idx:]

print(f"Total active cases: {N_cases}")
print(f"Dev cases ({len(dev_cases)}): {dev_cases[0]} .. {dev_cases[-1]}")
print(f"Held-out cases ({len(held_out_cases)}): {held_out_cases[0]} .. {held_out_cases[-1]}")

def parse_dt(s):
    if not s:
        return None
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]:
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None

# 2. Extract entities, independent labels, and real timestamped events per entity
entity_labels = {}
entity_cases = defaultdict(set)
entity_sources = defaultdict(set)
entity_events = defaultdict(list) # entity -> list of (datetime, source_type)

# FIR
fir_path = os.path.join(data_dir, "fir_reports.csv")
fir_records = []
with open(fir_path, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        fir_records.append(r)
        c = r.get("case_ref")
        dt = parse_dt(r.get("date"))
        comp = r.get("complainant_name", "").strip()
        accs = [a.strip() for a in r.get("accused_names", "").split(";") if a.strip()]
        if comp:
            entity_cases[comp].add(c)
            entity_sources[comp].add("fir")
            if dt:
                entity_events[comp].append((dt, "fir"))
            if comp not in entity_labels:
                entity_labels[comp] = 0
        for a in accs:
            entity_cases[a].add(c)
            entity_sources[a].add("fir")
            if dt:
                entity_events[a].append((dt, "fir"))
            entity_labels[a] = 1

# Criminal history
crim_path = os.path.join(data_dir, "criminal_history.csv")
with open(crim_path, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        c = r.get("case_ref")
        name = r.get("name", "").strip()
        if name:
            if c:
                entity_cases[name].add(c)
            entity_sources[name].add("criminal_history")
            entity_labels[name] = 1

# CDR
cdr_path = os.path.join(data_dir, "cdr_records.csv")
comm_freq = defaultdict(int)
with open(cdr_path, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        caller = r.get("caller_number", "").strip()
        callee = r.get("callee_number", "").strip()
        c = r.get("case_ref")
        dt = parse_dt(r.get("call_datetime"))
        for p in [caller, callee]:
            if p:
                comm_freq[p] += 1
                if c:
                    entity_cases[p].add(c)
                entity_sources[p].add("cdr")
                if dt:
                    entity_events[p].append((dt, "cdr"))

# Financial
fin_path = os.path.join(data_dir, "financial_transactions.csv")
txn_anomaly = defaultdict(bool)
with open(fin_path, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        sender = r.get("sender_account", "").strip()
        recv = r.get("receiver_account", "").strip()
        c = r.get("case_ref")
        amt = float(r.get("amount", 0) or 0)
        dt = parse_dt(r.get("txn_datetime"))
        is_high = amt >= 100000.0
        for a in [sender, recv]:
            if a:
                if c:
                    entity_cases[a].add(c)
                entity_sources[a].add("financial")
                if dt:
                    entity_events[a].append((dt, "financial"))
                if is_high:
                    txn_anomaly[a] = True

# Surveillance
surv_path = os.path.join(data_dir, "surveillance_reports.txt")
with open(surv_path, encoding="utf-8") as f:
    surv_text = f.read()
import re
for block in surv_text.split("--- REPORT"):
    if not block.strip():
        continue
    date_m = re.search(r"DATE:\s*([^\n\r]+)", block, re.IGNORECASE)
    dt = parse_dt(date_m.group(1).strip()) if date_m else None
    for ent in list(entity_labels.keys()):
        if ent in block:
            entity_sources[ent].add("surveillance")
            if dt:
                entity_events[ent].append((dt, "surveillance"))

# Social media
sm_path = os.path.join(data_dir, "social_media_posts.csv")
with open(sm_path, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        c = r.get("case_ref")
        dname = r.get("display_name", "").strip()
        dt = parse_dt(r.get("timestamp"))
        if dname:
            if c:
                entity_cases[dname].add(c)
            entity_sources[dname].add("social_media")
            if dt:
                entity_events[dname].append((dt, "social_media"))

# Genuine Timestamp-Based Temporal Proximity Function
def check_temporal_proximity(ent_name: str, window_hours: float = 48.0) -> float:
    evts = entity_events.get(ent_name, [])
    if len(evts) < 2:
        return 0.0
    evts_sorted = sorted(evts, key=lambda x: x[0])
    win_delta = timedelta(hours=window_hours)
    for i in range(len(evts_sorted)):
        for j in range(i + 1, len(evts_sorted)):
            delta = evts_sorted[j][0] - evts_sorted[i][0]
            if delta > win_delta:
                break
            # Different source modalities within window
            if evts_sorted[i][1] != evts_sorted[j][1]:
                return 1.0
    return 0.0

# Graph features
nodes = set(entity_labels.keys())
adj = defaultdict(set)
for r in fir_records:
    comp = r.get("complainant_name", "").strip()
    accs = [a.strip() for a in r.get("accused_names", "").split(";") if a.strip()]
    group = [comp] + accs
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            if group[i] in nodes and group[j] in nodes:
                adj[group[i]].add(group[j])
                adj[group[j]].add(group[i])

N = len(nodes)
degree_c = {n: len(adj[n]) / (N - 1) if N > 1 else 0.0 for n in nodes}

pr = {n: 1.0 / N for n in nodes}
damp = 0.85
for _ in range(30):
    new_pr = {n: (1.0 - damp) / N for n in nodes}
    for n in nodes:
        deg = len(adj[n])
        if deg > 0:
            share = damp * pr[n] / deg
            for neighbor in adj[n]:
                new_pr[neighbor] += share
        else:
            share = damp * pr[n] / N
            for other in nodes:
                new_pr[other] += share
    pr = new_pr

betweenness_c = {n: 0.0 for n in nodes}
for s in nodes:
    S = []
    P = defaultdict(list)
    sigma = defaultdict(int)
    sigma[s] = 1
    d = {n: -1 for n in nodes}
    d[s] = 0
    Q = deque([s])
    while Q:
        v = Q.popleft()
        S.append(v)
        for w in adj[v]:
            if d[w] < 0:
                Q.append(w)
                d[w] = d[v] + 1
            if d[w] == d[v] + 1:
                sigma[w] += sigma[v]
                P[w].append(v)
    delta = defaultdict(float)
    while S:
        w = S.pop()
        for v in P[w]:
            delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
        if w != s:
            betweenness_c[w] += delta[w]

scale = 1.0 / ((N - 1) * (N - 2)) if N > 2 else 1.0
for n in nodes:
    betweenness_c[n] *= scale

FEATURE_NAMES = [
    "degree_centrality",
    "betweenness_centrality",
    "pagerank",
    "cross_case_count",
    "source_type_diversity",
    "relationship_count",
    "transaction_anomaly",
    "communication_frequency",
    "temporal_proximity",
]

def extract_features(ent_name: str) -> list[float]:
    cases = entity_cases.get(ent_name, set())
    sources = entity_sources.get(ent_name, set())
    deg = degree_c.get(ent_name, 0.0)
    bet = betweenness_c.get(ent_name, 0.0)
    pr_score = pr.get(ent_name, 0.0)
    rel_cnt = float(len(adj[ent_name]))
    cc_cnt = float(len(cases))
    src_div = float(len(sources))
    tx_anom = 1.0 if txn_anomaly.get(ent_name, False) else 0.0
    comm_f = float(comm_freq.get(ent_name, 0))
    # Genuine timestamp proximity
    temp_prox = check_temporal_proximity(ent_name, window_hours=48.0)
    return [deg, bet, pr_score, cc_cnt, src_div, rel_cnt, tx_anom, comm_f, temp_prox]

dev_case_set = set(dev_cases)
held_out_case_set = set(held_out_cases)

train_ents = [e for e in nodes if any(c in dev_case_set for c in entity_cases.get(e, set()))]
test_ents = [e for e in nodes if any(c in held_out_case_set for c in entity_cases.get(e, set()))]
exclusive_held_out = [e for e in test_ents if not any(c in dev_case_set for c in entity_cases.get(e, set()))]

print(f"\nTrain entities (touched by dev cases): {len(train_ents)}")
print(f"Held-out entities (touched by held-out cases): {len(test_ents)}")
print(f"Exclusive held-out entities (overlap = 0): {len(exclusive_held_out)}")

# Fit standardizer ONLY on train data
X_train = [extract_features(e) for e in train_ents]
y_train = [entity_labels[e] for e in train_ents]

n_features = len(FEATURE_NAMES)
means = [0.0] * n_features
stds = [1.0] * n_features

for j in range(n_features):
    vals = [X_train[i][j] for i in range(len(X_train))]
    m = sum(vals) / len(vals) if vals else 0.0
    var = sum((v - m) ** 2 for v in vals) / len(vals) if vals else 1.0
    s = math.sqrt(var)
    means[j] = m
    stds[j] = s if s > 1e-6 else 1.0

def standardize(X):
    return [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in X]

X_train_std = standardize(X_train)

# Fit Logistic Regression
weights = [0.0] * n_features
bias = 0.0
lr = 0.05
l2_lambda = 0.1
epochs = 300
m = len(X_train)

for _ in range(epochs):
    dw = [0.0] * n_features
    db = 0.0
    for i in range(m):
        z = bias + sum(weights[j] * X_train_std[i][j] for j in range(n_features))
        sig = 1.0 / (1.0 + math.exp(-z)) if z >= 0 else math.exp(z) / (1.0 + math.exp(z))
        err = sig - y_train[i]
        for j in range(n_features):
            dw[j] += err * X_train_std[i][j]
        db += err
    for j in range(n_features):
        weights[j] -= lr * (dw[j] / m + (l2_lambda / m) * weights[j])
    bias -= lr * (db / m)

def evaluate_set(ent_list, name="Set"):
    X_set = [extract_features(e) for e in ent_list]
    y_set = [entity_labels[e] for e in ent_list]
    X_set_std = standardize(X_set)
    tp = fp = tn = fn = 0
    for i in range(len(ent_list)):
        z = bias + sum(weights[j] * X_set_std[i][j] for j in range(n_features))
        prob = 1.0 / (1.0 + math.exp(-z)) if z >= 0 else math.exp(z) / (1.0 + math.exp(z))
        pred = 1 if prob >= 0.5 else 0
        actual = y_set[i]
        if actual == 1 and pred == 1:
            tp += 1
        elif actual == 0 and pred == 1:
            fp += 1
        elif actual == 0 and pred == 0:
            tn += 1
        elif actual == 1 and pred == 0:
            fn += 1
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
    print(f"\n--- {name} (N={len(ent_list)}) ---")
    print(f"TP: {tp}, FP: {fp}, TN: {tn}, FN: {fn}")
    print(f"Confusion Matrix: [[TN={tn}, FP={fp}], [FN={fn}, TP={tp}]]")
    print(f"Precision: {p:.4f}, Recall: {r:.4f}, F1: {f1:.4f}")
    return {"precision": p, "recall": r, "f1": f1, "tp": tp, "fp": fp, "tn": tn, "fn": fn}

evaluate_set(test_ents, "All Held-out Entities (Cases 49-60)")
evaluate_set(exclusive_held_out, "Strict Disjoint Held-out Entities (Overlap = 0)")

print("\n--- Feature Coefficients & Odds Ratios ---")
for j, fn in enumerate(FEATURE_NAMES):
    w = weights[j]
    odds = math.exp(w)
    print(f"  {fn:25s}: Coef = {w:+.4f}, Odds Ratio = {odds:.4f}x")
