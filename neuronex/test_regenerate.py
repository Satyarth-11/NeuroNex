import urllib.request
import urllib.error
import json

print("=== TESTING REGENERATE INSIGHTS ===")
req = urllib.request.Request(
    "http://localhost:8000/api/insights/regenerate",
    data=b"{}",
    headers={"Content-Type": "application/json"},
    method="POST"
)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        print(f"Status: {resp.status}")
        print("Response:", resp.read().decode('utf-8'))
except Exception as e:
    print("Failed:", e)

print("\n=== VERIFYING INSIGHTS COUNT POST-REGENERATE ===")
req2 = urllib.request.Request("http://localhost:8000/api/insights?status=proposed")
try:
    with urllib.request.urlopen(req2, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"Status: {resp.status}, count: {len(data)}")
except Exception as e:
    print("Failed:", e)

print("\n=== CALLING REGENERATE A SECOND TIME TO TEST DUPLICATE PREVENTION ===")
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        print(f"Status: {resp.status}")
        print("Response:", resp.read().decode('utf-8'))
except Exception as e:
    print("Failed:", e)

req3 = urllib.request.Request("http://localhost:8000/api/insights?status=proposed")
try:
    with urllib.request.urlopen(req3, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"Status: {resp.status}, count after second regen: {len(data)}")
except Exception as e:
    print("Failed:", e)
