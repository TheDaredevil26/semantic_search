
import re
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class Turn:
    role: str   # "user" | "assistant"
    content: str

def test_extraction(extract_fn):
    test_cases = [
        {
            "query": "people with python and java",
            "expected_skills": ["python", "java"]
        },
        {
            "query": "anyone knows react in delhi",
            "expected_location": "Delhi",
            "expected_skills": ["react"]
        },
        {
            "query": "engineers at google with linux expertise",
            "expected_company": "Google",
            "expected_skills": ["linux expertise"]
        },
        {
            "query": "skilled in c++ and python from the cs department",
            "expected_skills": ["c++", "python", "Cs"],
            "expected_location": None
        },
        {
            "query": "show me delhi batch 2020 with machine learning",
            "expected_location": "Delhi",
            "expected_batch": "2020",
            "expected_skills": ["machine learning"]
        },
        {
            "query": "experts in ai and ml at microsoft living in bangalore",
            "expected_company": "Microsoft",
            "expected_location": "Bangalore",
            "expected_skills": ["Ai", "Ml"]
        },
        {
            "query": "anyone in computer science from bangalore",
            "expected_location": "Bangalore",
            "expected_skills": ["Computer Science"]
        }
    ]
    
    passed = 0
    for i, tc in enumerate(test_cases):
        res = extract_fn(tc["query"])
        print(f"Test {i+1}: {tc['query']}")
        print(f"  Result: {res}")
        
        match = True
        if "expected_company" in tc and res["company"] != tc["expected_company"]:
            print(f"  FAILED Company: expected {tc['expected_company']}, got {res['company']}")
            match = False
        if "expected_location" in tc and res["location"] != tc["expected_location"]:
            print(f"  FAILED Location: expected {tc['expected_location']}, got {res['location']}")
            match = False
        if "expected_batch" in tc and res["batch_year"] != tc["expected_batch"]:
            print(f"  FAILED Batch: expected {tc['expected_batch']}, got {res['batch_year']}")
            match = False
        if "expected_skills" in tc:
            if set([s.lower() for s in res["skills"]]) != set([s.lower() for s in tc["expected_skills"]]):
                print(f"  FAILED Skills: expected {tc['expected_skills']}, got {res['skills']}")
                match = False
        
        if match:
            print("  PASSED")
            passed += 1
        print("-" * 30)
    
    print(f"Final Score: {passed}/{len(test_cases)}")

if __name__ == "__main__":
    import sys
    import os
    # Add project root to path
    sys.path.insert(0, os.getcwd())
    from backend.conversational import _extract_slots_from_query
    test_extraction(_extract_slots_from_query)
