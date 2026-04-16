import urllib.request, json, sys

BASE = "http://127.0.0.1:8000"

def search(body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE+"/api/search", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def check(label, cond, got=""):
    if cond:
        print("  OK   " + label)
    else:
        print("  FAIL " + label + "  |  got: " + str(got))

print("=== Advanced Filter Audit ===\n")

# 1. Baseline
r0 = search({"query": "software engineers", "page": 1, "limit": 20})
baseline = r0["total_count"]
print("Baseline total_count:", baseline)

# 2. Company filter
r1 = search({"query": "software engineers", "company_filter": "Google", "page": 1, "limit": 20})
cos = [x["profile"]["current_company"] for x in r1["results"]]
check("company_filter: all Google", all("google" in c.lower() for c in cos), cos[:3])
check("company_filter: narrows results", r1["total_count"] <= baseline)
print("   company total_count:", r1["total_count"])

# 3. Location filter
r2 = search({"query": "software engineers", "location_filter": "Mumbai", "page": 1, "limit": 20})
cities = [x["profile"]["city"] for x in r2["results"]]
check("location_filter: all Mumbai", all("mumbai" in c.lower() for c in cities), cities[:3])
print("   location total_count:", r2["total_count"])

# 4. Batch year (single)
r3 = search({"query": "software engineers", "batch_year_filter": "2019", "page": 1, "limit": 20})
years = [x["profile"]["batch_year"] for x in r3["results"]]
check("batch_year_filter 2019: all 2019", all(y == 2019 for y in years), years[:5])
print("   batch_year total_count:", r3["total_count"])

# 5. Batch year (range)
r4 = search({"query": "software engineers", "batch_year_filter": "2018-2020", "page": 1, "limit": 20})
years4 = [x["profile"]["batch_year"] for x in r4["results"]]
check("batch_year_range 2018-2020", all(2018 <= y <= 2020 for y in years4), years4[:5])
print("   batch_range total_count:", r4["total_count"])

# 6. Skills filter
r5 = search({"query": "engineers", "skills_filter": ["Python"], "page": 1, "limit": 20})
skills_ok = all(any("python" in s.lower() for s in x["profile"]["skills"]) for x in r5["results"])
check("skills_filter Python in all", skills_ok)
print("   skills total_count:", r5["total_count"])

# 7. Combined filters
r6 = search({"query": "engineers", "company_filter": "Infosys", "location_filter": "Bangalore", "page": 1, "limit": 20})
if r6["results"]:
    cos6 = [x["profile"]["current_company"] for x in r6["results"]]
    cit6 = [x["profile"]["city"] for x in r6["results"]]
    check("combined company=Infosys", all("infosys" in c.lower() for c in cos6), cos6[:3])
    check("combined location=Bangalore", all("bangalore" in c.lower() for c in cit6), cit6[:3])
else:
    print("  INFO combined returned 0 results (may be expected)")
print("   combined total_count:", r6["total_count"])

# 8. Empty strings = no filter (must equal baseline)
r7 = search({"query": "software engineers", "company_filter": "", "location_filter": "", "page": 1, "limit": 20})
check("empty strings = no filter", r7["total_count"] == baseline,
      "baseline=" + str(baseline) + " filtered=" + str(r7["total_count"]))

# 9. Zero-match filter
r8 = search({"query": "software engineers", "company_filter": "XXXXNONEXISTENT", "page": 1, "limit": 20})
check("zero-match returns empty", r8["total_count"] == 0 and len(r8["results"]) == 0, r8["total_count"])

# 10. Pagination with filter
r9 = search({"query": "engineers", "page": 1, "limit": 5, "company_filter": "Infosys"})
r9b = search({"query": "engineers", "page": 2, "limit": 5, "company_filter": "Infosys"})
check("pagination with filter: page 1 IDs != page 2 IDs",
      set(x["id"] for x in r9["results"]).isdisjoint(set(x["id"] for x in r9b["results"])) if r9["total_count"] > 5 else True)
check("pagination with filter: page field correct", r9["page"] == 1 and r9b["page"] == 2,
      str(r9["page"]) + "/" + str(r9b["page"]))

print("\nDone")
