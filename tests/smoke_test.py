import urllib.request, json, sys

BASE = "http://127.0.0.1:8000"
FAIL = []

def check(name, url, method="GET", body=None):
    try:
        if body:
            data = json.dumps(body).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        else:
            req = url
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = json.loads(r.read())
        print(f"  OK  {name}")
        return resp
    except Exception as e:
        print(f"  FAIL {name}: {e}")
        FAIL.append(name)
        return {}

print("\n=== PRD v2 API Smoke Test ===")

stats = check("GET /api/stats", f"{BASE}/api/stats")
if stats:
    print(f"       total_alumni={stats.get('total_alumni')}")

ac = check("GET /api/autocomplete", f"{BASE}/api/autocomplete?q=go")
if ac:
    print(f"       suggestions={len(ac.get('suggestions', []))}")

sr = check(
    "POST /api/search (pagination)", f"{BASE}/api/search",
    method="POST",
    body={"query": "machine learning engineers", "page": 1, "limit": 5}
)
if sr:
    print(f"       page={sr.get('page')}, total_count={sr.get('total_count')}, total_pages={sr.get('total_pages')}, intent={sr.get('intent')}")
    results = sr.get("results", [])
    if results:
        r0 = results[0]
        print(f"       #1: {r0.get('name') or r0.get('profile',{}).get('full_name')}, score={r0.get('score'):.3f}, ce={r0.get('cross_encoder_score')}")

filters = check("GET /api/search/filters", f"{BASE}/api/search/filters")
if filters:
    print(f"       companies={len(filters.get('companies', []))}, skills={len(filters.get('skills', []))}")

metrics = check("GET /api/metrics", f"{BASE}/api/metrics")
if metrics:
    print(f"       total_requests={metrics.get('total_requests')}, hit_rate={metrics.get('cache_hit_rate')}")

path = check("GET /api/path/1/5", f"{BASE}/api/path/1/5")
if path:
    print(f"       path_length={path.get('length')}")

conv = check(
    "POST /api/search/conversational", f"{BASE}/api/search/conversational",
    method="POST",
    body={"query": "ML engineers in Bangalore", "conversation_history": [], "page": 1, "limit": 5}
)
if conv:
    print(f"       resolved_query={conv.get('resolved_query')}, total={conv.get('total_count')}")

print(f"\n{'ALL PASSED' if not FAIL else f'FAILED: {FAIL}'}")
sys.exit(1 if FAIL else 0)
