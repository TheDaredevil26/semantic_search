import sys, os
sys.path.insert(0, 'semantic_search')
from backend.conversational import resolve_turn, Turn, _is_follow_up, _extract_slots_from_query, _is_reset

ok = True
def check(label, cond, got=''):
    global ok
    if cond:
        print("  OK   " + label)
    else:
        print("  FAIL " + label + " | got=" + str(got))
        ok = False

print("=== Multi-Turn Bug Fix Verification ===\n")

# Bug 1: 'show me 2018' then 'show me 2015' — should OVERRIDE batch, not reset context
print("Bug 1: slot override (show me 2018 -> show me 2015)")
check("show me 2018 = follow-up", _is_follow_up("show me 2018"))
check("show me 2015 = follow-up", _is_follow_up("show me 2015"))
h = [Turn("user", "Find ML engineers"), Turn("assistant", "Found 20")]
h += [Turn("user", "show me 2018"), Turn("assistant", "Batch 2018")]
r = resolve_turn("show me 2015", h)
check("base_query inherited", r.resolved_query == "Find ML engineers", r.resolved_query)
check("batch_year OVERRIDDEN to 2015", r.batch_year_filter == "2015", r.batch_year_filter)

# Bug 2: 'only 2019' is a follow-up
print("\nBug 2: slot-only queries are follow-ups")
check("only 2019 = follow-up", _is_follow_up("only 2019"))
check("change to 2020 = follow-up", _is_follow_up("change to 2020"))
check("just 2018 = follow-up", _is_follow_up("just 2018"))
check("show me 2018 to 2022 = follow-up", _is_follow_up("show me 2018 to 2022"))

# Bug 3: no false-positive location from batch range queries
print("\nBug 3: no false-positive location from batch-range query")
s = _extract_slots_from_query("from batch 2015 to 2020")
check("batch = 2015-2020", s["batch_year"] == "2015-2020", s["batch_year"])
check("location = None (no false positive)", s["location"] is None, s["location"])

# Bug 4: reset keywords
print("\nBug 4: reset keywords")
check("start over = reset", _is_reset("start over"))
check("clear = reset", _is_reset("clear"))
check("new search = reset", _is_reset("new search"))
check("reset = reset", _is_reset("reset"))
check("forget that = reset", _is_reset("forget that"))

# Bug 5: range preserved across turns
print("\nBug 5: range filter preserved across follow-up turns")
h2 = [Turn("user", "Find software engineers"), Turn("assistant", "Found 50")]
h2 += [Turn("user", "from 2016 to 2021"), Turn("assistant", "2016-2021")]
r2 = resolve_turn("in Bangalore", h2)
check("batch preserved", r2.batch_year_filter == "2016-2021", r2.batch_year_filter)
check("location added", r2.location_filter == "Bangalore", r2.location_filter)

# Bug 6: fresh searches clear accumulated state
print("\nBug 6: fresh searches clear accumulated filters")
h3 = [Turn("user", "Find ML engineers"), Turn("assistant", "Found 30"),
      Turn("user", "in Bangalore"), Turn("assistant", "Location: Bangalore")]
r3 = resolve_turn("Find data scientists in Mumbai", h3)
check("new base query", r3.resolved_query == "Find data scientists in Mumbai", r3.resolved_query)
check("OLD location cleared", r3.location_filter == "Mumbai", r3.location_filter)

# Bug 7: filter-only query that looks misleadingly like a topic
print("\nBug 7: 'batch 2018' vs 'from 2015 to 2020' both work mid-turn")
h4 = [Turn("user", "Find software engineers"), Turn("assistant", "Found 50")]
r_single = resolve_turn("batch 2018", h4)
check("batch 2018 mid-turn works", r_single.batch_year_filter == "2018", r_single.batch_year_filter)
r_range = resolve_turn("from 2015 to 2020", h4)
check("from 2015 to 2020 mid-turn works", r_range.batch_year_filter == "2015-2020", r_range.batch_year_filter)

print()
print("ALL OK" if ok else "SOME FAILED")
