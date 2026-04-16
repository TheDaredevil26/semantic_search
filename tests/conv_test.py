"""
Multi-turn conversation integration test.
Simulates exactly what the frontend does:
  Turn 1: fresh search
  Turn 2: narrow by location
  Turn 3: narrow by batch year
  Turn 4: narrow by company
  Turn 5: reset
"""
import urllib.request, json, sys

BASE = "http://127.0.0.1:8000"

def conv_turn(query, history, page=1, limit=20):
    body = json.dumps({
        "query": query,
        "conversation_history": history,
        "page": page,
        "limit": limit,
    }).encode()
    req = urllib.request.Request(
        f"{BASE}/api/search/conversational",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

PASS = []
FAIL = []

def check(label, condition, detail=""):
    if condition:
        print(f"  ✓  {label}")
        PASS.append(label)
    else:
        print(f"  ✗  {label}  [{detail}]")
        FAIL.append(label)

print("\n=== Multi-Turn Conversation Test ===\n")

history = []

# ── Turn 1: Fresh search ─────────────────────────────────────────────────────
print("Turn 1: Fresh search — 'Find software engineers'")
r1 = conv_turn("Find software engineers", history)
check("Returns results",         len(r1["results"]) > 0)
check("Has resolved_query",      r1.get("resolved_query") == "Find software engineers",
      f"got: {r1.get('resolved_query')}")
check("Has total_count",         r1.get("total_count", 0) > 0)
check("Has total_pages",         r1.get("total_pages", 0) >= 1)
check("No location filter yet",  r1["applied_filters"].get("location") is None)
check("No company filter yet",   r1["applied_filters"].get("company") is None)

# Append to history as frontend does
history.append({"role": "user",      "content": "Find software engineers"})
history.append({"role": "assistant", "content": f"Found {r1['total_count']} results"})

# ── Turn 2: Narrow by location ────────────────────────────────────────────────
print("\nTurn 2: Follow-up — 'in Bangalore'")
r2 = conv_turn("in Bangalore", history)
check("Resolved query inherited",   r2.get("resolved_query") == "Find software engineers",
      f"got: {r2.get('resolved_query')}")
check("Location filter set",        r2["applied_filters"].get("location") == "Bangalore",
      f"got: {r2['applied_filters'].get('location')}")
check("Results narrowed or same",   len(r2["results"]) <= r1["total_count"])

history.append({"role": "user",      "content": "in Bangalore"})
history.append({"role": "assistant", "content": f"Found {r2['total_count']} results. Location: Bangalore"})

# ── Turn 3: Further narrow by batch year ──────────────────────────────────────
print("\nTurn 3: Follow-up — 'batch 2019'")
r3 = conv_turn("batch 2019", history)
check("Resolved query still inherited", r3.get("resolved_query") == "Find software engineers",
      f"got: {r3.get('resolved_query')}")
check("Location filter preserved",  r3["applied_filters"].get("location") == "Bangalore",
      f"got: {r3['applied_filters'].get('location')}")
check("Batch year filter set",      r3["applied_filters"].get("batch_year") == "2019",
      f"got: {r3['applied_filters'].get('batch_year')}")

history.append({"role": "user",      "content": "batch 2019"})
history.append({"role": "assistant", "content": f"Found {r3['total_count']} results. Batch: 2019"})

# ── Turn 4: Further narrow by company ─────────────────────────────────────────
print("\nTurn 4: Follow-up — 'working at Google'")
r4 = conv_turn("working at Google", history)
check("Company filter set",         r4["applied_filters"].get("company") is not None,
      f"got: {r4['applied_filters'].get('company')}")
check("Location filter still held", r4["applied_filters"].get("location") == "Bangalore",
      f"got: {r4['applied_filters'].get('location')}")
check("Batch year still held",      r4["applied_filters"].get("batch_year") == "2019",
      f"got: {r4['applied_filters'].get('batch_year')}")

history.append({"role": "user",      "content": "working at Google"})
history.append({"role": "assistant", "content": f"Found {r4['total_count']} results"})

# ── Turn 5: Reset ─────────────────────────────────────────────────────────────
print("\nTurn 5: Reset — 'start over'")
r5 = conv_turn("start over", history)
check("No location after reset",  r5["applied_filters"].get("location") is None,
      f"got: {r5['applied_filters'].get('location')}")
check("No company after reset",   r5["applied_filters"].get("company") is None,
      f"got: {r5['applied_filters'].get('company')}")
check("No batch after reset",     r5["applied_filters"].get("batch_year") is None,
      f"got: {r5['applied_filters'].get('batch_year')}")

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*40}")
print(f"  Passed: {len(PASS)} / {len(PASS)+len(FAIL)}")
if FAIL:
    print(f"  FAILED: {FAIL}")
else:
    print("  ALL MULTI-TURN TESTS PASSED ✓")
print()
sys.exit(1 if FAIL else 0)
