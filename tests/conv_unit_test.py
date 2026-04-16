import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.conversational import resolve_turn, Turn, _is_follow_up

print("=== Unit Tests: _is_follow_up ===")
unit_fail = []
tests = [
    ("in Bangalore", True),
    ("batch 2019", True),
    ("working at Google", True),
    ("filter to Microsoft", True),
    ("Find software engineers", False),
    ("Find ML engineers", False),
    ("Machine learning engineers in India", False),
]
for q, expected in tests:
    got = _is_follow_up(q)
    ok = got == expected
    status = "OK  " if ok else "FAIL"
    print(f"  {status} _is_follow_up({q!r}) -> {got} (expected {expected})")
    if not ok:
        unit_fail.append(q)

print()
print("=== Integration: 4-turn conversation ===")
fail = []

def check(label, cond, got=""):
    if cond:
        print("  OK   " + label)
    else:
        print("  FAIL " + label + " | got: " + str(got))
        fail.append(label)

history = [
    Turn("user", "Find software engineers"),
    Turn("assistant", "Found 20 results"),
]

r2 = resolve_turn("in Bangalore", history)
check("T2 resolved_query inherited", r2.resolved_query == "Find software engineers", r2.resolved_query)
check("T2 location=Bangalore", r2.location_filter == "Bangalore", r2.location_filter)

history += [Turn("user", "in Bangalore"), Turn("assistant", "Location: Bangalore")]
r3 = resolve_turn("batch 2019", history)
check("T3 location preserved", r3.location_filter == "Bangalore", r3.location_filter)
check("T3 batch_year=2019", r3.batch_year_filter == "2019", r3.batch_year_filter)
check("T3 resolved_query inherited", r3.resolved_query == "Find software engineers", r3.resolved_query)

history += [Turn("user", "batch 2019"), Turn("assistant", "Batch: 2019")]
r4 = resolve_turn("working at Google", history)
check("T4 query inherited", r4.resolved_query == "Find software engineers", r4.resolved_query)
check("T4 company set", r4.company_filter is not None, r4.company_filter)
check("T4 location held", r4.location_filter == "Bangalore", r4.location_filter)
check("T4 batch held", r4.batch_year_filter == "2019", r4.batch_year_filter)

history += [Turn("user", "working at Google"), Turn("assistant", "Company: Google")]
r5 = resolve_turn("start over", history)
check("T5 reset: no location", r5.location_filter is None, r5.location_filter)
check("T5 reset: no company", r5.company_filter is None, r5.company_filter)
check("T5 reset: no batch", r5.batch_year_filter is None, r5.batch_year_filter)

print()
all_fail = unit_fail + fail
if all_fail:
    print("FAILED:", all_fail)
    sys.exit(1)
else:
    print("ALL PASSED")
