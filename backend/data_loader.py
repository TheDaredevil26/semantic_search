"""
Data Loader — CSV ingestion, normalization, and profile text generation.
"""
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ALUMNI_CSV_PATH, PROFILE_TEMPLATE


def load_alumni_data(csv_path: str = None) -> pd.DataFrame:
    """
    Load alumni CSV into a normalized pandas DataFrame.
    
    Returns:
        DataFrame with cleaned, normalized alumni records.
    """
    path = csv_path or ALUMNI_CSV_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Alumni CSV not found at {path}. "
            "Run 'python data/generate_alumni.py' first."
        )

    df = pd.read_csv(path, encoding="utf-8")

    # --- Normalization ---
    # Strip whitespace from string columns
    str_cols = ["full_name", "department", "current_company", "current_role", "city", "skills", "bio"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    # Normalize department names
    dept_map = {
        "cs": "Computer Science",
        "cse": "Computer Science",
        "ece": "Electronics & Communication",
        "ee": "Electrical Engineering",
        "eee": "Electrical Engineering",
        "me": "Mechanical Engineering",
        "mech": "Mechanical Engineering",
        "ce": "Civil Engineering",
        "it": "Information Technology",
        "che": "Chemical Engineering",
        "bt": "Biotechnology",
        "biotech": "Biotechnology",
    }
    df["department"] = df["department"].apply(
        lambda x: dept_map.get(x.lower(), x)
    )

    # Ensure batch_year is integer
    df["batch_year"] = pd.to_numeric(df["batch_year"], errors="coerce").fillna(2020).astype(int)

    # Fill missing fields with defaults
    df["current_company"] = df["current_company"].replace("", "Unknown Company")
    df["current_role"] = df["current_role"].replace("", "Professional")
    df["city"] = df["city"].replace("", "India")
    df["skills"] = df["skills"].replace("", "General")
    df["bio"] = df["bio"].replace("", "Alumni member.")

    # Parse mentor_id
    df["mentor_id"] = df["mentor_id"].fillna("").astype(str).str.strip()

    # Keep phone and email; fill missing values gracefully
    if "phone" in df.columns:
        df["phone"] = df["phone"].fillna("N/A").astype(str).str.strip()
    else:
        df["phone"] = "N/A"
    if "email" in df.columns:
        df["email"] = df["email"].fillna("N/A").astype(str).str.strip()
    else:
        df["email"] = "N/A"

    # Ensure alumnus_id is string
    df["alumnus_id"] = df["alumnus_id"].astype(str)

    # Parse skills into lists
    df["skills_list"] = df["skills"].apply(
        lambda x: [s.strip() for s in x.split(",") if s.strip()]
    )

    # Generate profile text blobs
    df["profile_text"] = df.apply(_generate_profile_text, axis=1)

    print(f"Loaded {len(df)} alumni records from {path}")
    return df


def _generate_profile_text(row: pd.Series) -> str:
    """Generate a rich text profile blob for embedding."""
    return PROFILE_TEMPLATE.format(
        name=row["full_name"],
        batch=row["batch_year"],
        department=row["department"],
        role=row["current_role"],
        company=row["current_company"],
        location=row["city"],
        skills=row["skills"],
        bio=row["bio"]
    )


def get_unique_values(df: pd.DataFrame) -> dict:
    """Extract unique values for filters."""
    return {
        "departments": sorted(df["department"].unique().tolist()),
        "batch_years": sorted(df["batch_year"].unique().tolist()),
        "companies": sorted(df["current_company"].unique().tolist()),
        "locations": sorted(df["city"].unique().tolist()),
    }
