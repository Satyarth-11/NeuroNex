import urllib.request
import urllib.error
import json
import sys

endpoints = [
    ("http://localhost:8000/health", "GET"),
    ("http://localhost:8000/api/health", "GET"),
    ("http://localhost:3001/api/health", "GET"),
    ("http://localhost:8000/api/analytics/centrality", "GET"),
    ("http://localhost:8000/api/analytics/key-influencers?limit=10", "GET"),
    ("http://localhost:8000/api/analytics/patterns", "GET"),
    ("http://localhost:8000/api/insights?status=proposed", "GET"),
    ("http://localhost:3001/api/insights?status=proposed", "GET"),
    ("http://localhost:8000/api/resolution/candidates?decision=pending", "GET"),
    ("http://localhost:8000/api/graph/edges/low-confidence", "GET"),
]

print("=== TESTING NEURONEX ENDPOINTS ===")
for url, method in endpoints:
    print(f"\n---> {method} {url}")
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            body = resp.read().decode('utf-8', errors='replace')
            print(f"Status: {status}")
            try:
                data = json.loads(body)
                if isinstance(data, list):
                    print(f"Body (list, len={len(data)}): {str(data)[:150].encode('ascii', errors='backslashreplace').decode('ascii')}...")
                elif isinstance(data, dict):
                    print(f"Body (dict, keys={list(data.keys())}): {str(data)[:150].encode('ascii', errors='backslashreplace').decode('ascii')}...")
                else:
                    print(f"Body: {str(data)[:150].encode('ascii', errors='backslashreplace').decode('ascii')}...")
            except Exception as ex:
                print(f"Body parse error: {ex}")
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace') if e.fp else ''
        print(f"FAILED HTTPError: {e.code} {e.reason}\nBody: {body[:300]}")
    except urllib.error.URLError as e:
        print(f"FAILED URLError: {e.reason}")
    except Exception as e:
        print(f"FAILED Exception: {type(e).__name__}: {e}")
