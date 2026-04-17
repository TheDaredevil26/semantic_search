"""
Batch year range — conversational end-to-end test against live server.
Covers: single year, closed range, open-ended range, multi-turn accumulation.
"""
import urllib.request, json, sys

BASE = "http://127.0.0.1:8000"

def conv_turn(query, history, page=1, limit=10):
    body = json.dumps({"query": query, "conversation_history": history, "page": page, "limit": limit}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/search/conversational", data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

FAIL = []
def check(label, cond, got=""):
    if cond:
        print("  OK   " + label)
    else:
        print("  FAIL " + label + "  | got: " + str(got))
        FAIL.append(label)

print("=== Batch Year Range — Live E2E Tests ===\n")
history = []

# --- Single year ---
print("Turn 1: Fresh search 'Find ML engineers'")
r1 = conv_turn("Find ML engineers", history)
check("Has results", len(r1["results"]) > 0)
check("No batch filter yet", r1["applied_filters"].get("batch_year") is None)
history += [{"role": "user", "content": "Find ML engineers"},
            {"role": "assistant", "content": f"Found {r1['total_count']} results"}]

print("\nTurn 2: 'batch 2019'  (single year)")
r2 = conv_turn("batch 2019", history)
check("batch_year=2019", r2["applied_filters"].get("batch_year") == "2019",
      r2["applied_filters"].get("batch_year"))
years2 = list(set(x["profile"]["batch_year"] for x in r2["results"]))
check("Only 2019 results", all(y == 2019 for y in years2), years2)
print("   batch_year total_count:", r2["total_count"])
history += [{"role": "user", "content": "batch 2019"},
            {"role": "assistant", "content": "Batch 2019"}]

# --- Closed range via natural language ---
print("\nTurn 3 (new topic): 'from batch 2015 to 2020'  (closed range)")
r3 = conv_turn("from batch 2015 to 2020", [])   # fresh session
check("batch_year filter is range", r3["applied_filters"].get("batch_year") == "2015-2020",
      r3["applied_filters"].get("batch_year"))
years3 = list(set(x["profile"]["batch_year"] for x in r3["results"]))
check("All in 2015-2020", all(2015 <= y <= 2020 for y in years3), years3)
print("   range total_count:", r3["total_count"])

# --- between X and Y ---
print("\nTurn 4 (new topic): 'between 2018 and 2022'")
r4 = conv_turn("between 2018 and 2022", [])
check("batch_year=2018-2022", r4["applied_filters"].get("batch_year") == "2018-2022",
      r4["applied_filters"].get("batch_year"))
years4 = list(set(x["profile"]["batch_year"] for x in r4["results"]))
check("All in 2018-2022", all(2018 <= y <= 2022 for y in years4), years4)
print("   between total_count:", r4["total_count"])

# --- after X ---
print("\nTurn 5 (new topic): 'engineers after 2019'")
r5 = conv_turn("engineers after 2019", [])
check("batch_year starts 2019", r5["applied_filters"].get("batch_year", "").startswith("2019"),
      r5["applied_filters"].get("batch_year"))
years5 = list(set(x["profile"]["batch_year"] for x in r5["results"]))
check("All >= 2019", all(y >= 2019 for y in years5), years5)
print("   after total_count:", r5["total_count"])

# --- Multi-turn: range + location accumulation ---
print("\nMulti-turn: range then narrow by city")
hist = [{"role": "user", "content": "Find data scientists"},
        {"role": "assistant", "content": "Found 20 results"}]
r6a = conv_turn("from 2016 to 2021", hist)
check("T6a range set", r6a["applied_filters"].get("batch_year") == "2016-2021",
      r6a["applied_filters"].get("batch_year"))
hist += [{"role": "user", "content": "from 2016 to 2021"},
         {"role": "assistant", "content": "Batch 2016-2021"}]
r6b = conv_turn("in Mumbai", hist)
check("T6b location added", r6b["applied_filters"].get("location") == "Mumbai",
      r6b["applied_filters"].get("location"))
check("T6b range preserved", r6b["applied_filters"].get("batch_year") == "2016-2021",
      r6b["applied_filters"].get("batch_year"))
years6b = list(set(x["profile"]["batch_year"] for x in r6b["results"]))
check("T6b only 2016-2021 years", all(2016 <= y <= 2021 for y in years6b), years6b)
cities6b = list(set(x["profile"]["city"] for x in r6b["results"]))
check("T6b only Mumbai", all("mumbai" in c.lower() for c in cities6b), cities6b)
print("   combined total_count:", r6b["total_count"])

print("\n" + "="*40)
if FAIL:
    print("FAILED:", FAIL)
    sys.exit(1)
else:
    print("ALL PASSED")
