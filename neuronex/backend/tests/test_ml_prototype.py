import csv
import math
import os
import json
from collections import defaultdict, deque

data_dir = r"C:\Users\satya\.gemini\antigravity-ide\scratch\neuronex\backend\data\synthetic"

# 1. Gather cases
dev_cases = [f"CASE-2024-{i:03d}" for i in range(1, 54)]
held_out_cases = [f"CASE-2024-{i:03d}" for i in range(54, 61)]

# 2. Extract entities and independent labels from FIR reports
fir_path = os.path.join(data_dir, "fir_reports.csv")
fir_records = []
with open(fir_path, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        fir_records.append(r)

entity_labels = {} # entity_name -> label (0 or 1)
entity_cases = {} # entity_name -> set of cases
entity_sources = {} # entity_name -> set of source_types

for r in fir_records:
    c = r["case_ref"]
    comp = r["complainant_name"].strip()
    accs = [a.strip() for a in r["accused_names"].split(";") if a.strip()]
    
    if comp:
        entity_cases.setdefault(comp, set()).add(c)
        entity_sources.setdefault(comp, set()).add("fir")
        if comp not in entity_labels:
            entity_labels[comp] = 0
    for a in accs:
        entity_cases.setdefault(a, set()).add(c)
        entity_sources.setdefault(a, set()).add("fir")
        entity_labels[a] = 1 # Accused is priority target

# Criminal history
crim_path = os.path.join(data_dir, "criminal_history.csv")
if os.path.exists(crim_path):
    with open(crim_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            c = r.get("case_ref")
            name = r.get("name", "").strip()
            if name and c:
                entity_cases.setdefault(name, set()).add(c)
                entity_sources.setdefault(name, set()).add("criminal_history")
                entity_labels[name] = 1

# CDR records
cdr_path = os.path.join(data_dir, "cdr_records.csv")
comm_freq = {}
if os.path.exists(cdr_path):
    with open(cdr_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            caller = r.get("caller_number", "").strip()
            callee = r.get("callee_number", "").strip()
            c = r.get("case_ref")
            for p in [caller, callee]:
                if p:
                    comm_freq[p] = comm_freq.get(p, 0) + 1
                    if c:
                        entity_cases.setdefault(p, set()).add(c)
                    entity_sources.setdefault(p, set()).add("cdr")

# Financial records
fin_path = os.path.join(data_dir, "financial_transactions.csv")
txn_anomaly = {}
if os.path.exists(fin_path):
    with open(fin_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            sender = r.get("sender_account", "").strip()
            recv = r.get("receiver_account", "").strip()
            c = r.get("case_ref")
            amt = float(r.get("amount", 0) or 0)
            is_high = amt >= 100000.0
            for a in [sender, recv]:
                if a:
                    if c:
                        entity_cases.setdefault(a, set()).add(c)
                    entity_sources.setdefault(a, set()).add("financial")
                    if is_high:
                        txn_anomaly[a] = True

# Surveillance
surv_path = os.path.join(data_dir, "surveillance_reports.txt")
if os.path.exists(surv_path):
    with open(surv_path, encoding="utf-8") as f:
        surv_text = f.read()
    for ent in list(entity_labels.keys()):
        if ent in surv_text:
            entity_sources.setdefault(ent, set()).add("surveillance")

# Social media
sm_path = os.path.join(data_dir, "social_media_posts.csv")
if os.path.exists(sm_path):
    with open(sm_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            c = r.get("case_ref")
            dname = r.get("display_name", "").strip()
            if dname:
                if c:
                    entity_cases.setdefault(dname, set()).add(c)
                entity_sources.setdefault(dname, set()).add("social_media")

# Pure Python Graph
nodes = set(entity_labels.keys())
adj = defaultdict(set)
for r in fir_records:
    comp = r["complainant_name"].strip()
    accs = [a.strip() for a in r["accused_names"].split(";") if a.strip()]
    group = [comp] + accs
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            if group[i] in nodes and group[j] in nodes:
                adj[group[i]].add(group[j])
                adj[group[j]].add(group[i])

N = len(nodes)
degree_c = {n: len(adj[n]) / (N - 1) if N > 1 else 0.0 for n in nodes}

# PageRank
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

# Betweenness (Brandes)
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
    temp_prox = 1.0 if (len(sources) >= 2 and len(cases) >= 2) else 0.0
    return [deg, bet, pr_score, cc_cnt, src_div, rel_cnt, tx_anom, comm_f, temp_prox]

# Training set: Entities that appear in development cases 1-53
train_ents = [e for e in nodes if any(c in dev_cases for c in entity_cases.get(e, set()))]

# Test set: Entities exclusively in held-out cases 54-60 (ensuring train/test overlap = 0)
test_ents = [e for e in nodes if any(c in held_out_cases for c in entity_cases.get(e, set())) and not any(c in dev_cases for c in entity_cases.get(e, set()))]

# If exclusive test set is small, we can also evaluate on all entities touched by held-out cases
test_ents_all_held_out = [e for e in nodes if any(c in held_out_cases for c in entity_cases.get(e, set()))]

print(f"Train entities: {len(train_ents)}, Exclusive Test entities (overlap=0): {len(test_ents)}, All Held-out touched: {len(test_ents_all_held_out)}")

X_train = [extract_features(e) for e in train_ents]
y_train = [entity_labels[e] for e in train_ents]

# Standardize features
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
    X_std = []
    for row in X:
        X_std.append([(row[j] - means[j]) / stds[j] for j in range(n_features)])
    return X_std

X_train_std = standardize(X_train)

# Fit Logistic Regression with gradient descent and L2 penalty
weights = [0.0] * n_features
bias = 0.0
lr = 0.05
l2_lambda = 0.1
epochs = 300
m = len(X_train)

for epoch in range(epochs):
    dw = [0.0] * n_features
    db = 0.0
    for i in range(m):
        z = bias + sum(weights[j] * X_train_std[i][j] for j in range(n_features))
        # Sigmoid
        sig = 1.0 / (1.0 + math.exp(-z)) if z >= 0 else math.exp(z) / (1.0 + math.exp(z))
        err = sig - y_train[i]
        for j in range(n_features):
            dw[j] += err * X_train_std[i][j]
        db += err

    for j in range(n_features):
        weights[j] -= lr * (dw[j] / m + (l2_lambda / m) * weights[j])
    bias -= lr * (db / m)

# Evaluate on Held-Out Test Set
eval_target_ents = test_ents if len(test_ents) >= 5 else test_ents_all_held_out
overlap_cnt = len(set(train_ents) & set(eval_target_ents))
X_test = [extract_features(e) for e in eval_target_ents]
y_test = [entity_labels[e] for e in eval_target_ents]
X_test_std = standardize(X_test)

tp = fp = tn = fn = 0
for i in range(len(eval_target_ents)):
    z = bias + sum(weights[j] * X_test_std[i][j] for j in range(n_features))
    prob = 1.0 / (1.0 + math.exp(-z)) if z >= 0 else math.exp(z) / (1.0 + math.exp(z))
    pred = 1 if prob >= 0.5 else 0
    actual = y_test[i]
    if actual == 1 and pred == 1:
        tp += 1
    elif actual == 0 and pred == 1:
        fp += 1
    elif actual == 0 and pred == 0:
        tn += 1
    elif actual == 1 and pred == 0:
        fn += 1

precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

feature_importance = {}
for j, feat_name in enumerate(FEATURE_NAMES):
    w = weights[j]
    odds = math.exp(w)
    feature_importance[feat_name] = {
        "coefficient": round(w, 4),
        "odds_ratio": round(odds, 4),
        "importance": round(abs(w), 4),
    }

print("=== LOGISTIC REGRESSION HELD-OUT EVALUATION ===")
print(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")
print(f"TP: {tp}, FP: {fp}, TN: {tn}, FN: {fn}")
print(f"Confusion Matrix: [[TN={tn}, FP={fp}], [FN={fn}, TP={tp}]]")
print(f"Train cases: {len(dev_cases)}, Held-out cases: {len(held_out_cases)}")
print(f"Evaluated entities: {len(eval_target_ents)}, Overlap with train: {overlap_cnt}")
print("\nTop 3 Important Features:")
sorted_feats = sorted(feature_importance.items(), key=lambda x: x[1]["importance"], reverse=True)
for name, meta in sorted_feats[:3]:
    print(f"  {name}: coef={meta['coefficient']}, odds_ratio={meta['odds_ratio']}")
