"""
extract_quality.py
==================
Extracts quality tier and furnishing status from ikman.lk listing titles.

Quality tiers detected:
  3 = Super Luxury  (super luxury, ultra luxury, penthouse)
  2 = Luxury        (luxury, premium, high-end, upmarket)
  1 = Modern/New    (modern, newly built, brand new, architect)
  0 = Standard      (default)

Furnishing:
  2 = Fully Furnished
  1 = Semi Furnished
  0 = Unfurnished / Unknown

Run: python dataset/extract_quality.py
"""

import pandas as pd
import re
from pathlib import Path

RAW_CSV = Path(__file__).parent / "properties_raw.csv"

# ── Pattern dictionaries ──────────────────────────────────────────────────────

SUPER_LUXURY_PATTERNS = [
    r'\bsuper\s+luxury\b', r'\bsuper\s*lux\b', r'\bultra\s+luxury\b',
    r'\bpenthouse\b', r'\bultra\s+premium\b', r'\bsuper\s+premium\b',
]

LUXURY_PATTERNS = [
    r'\bluxury\b', r'\bluxe\b', r'\bpremium\b', r'\bupmarket\b',
    r'\bhigh[\s\-]end\b', r'\bexclusive\b', r'\bprestige\b',
    r'\belegant\b', r'\bvillab?\b', r'\bposh\b',
]

MODERN_PATTERNS = [
    r'\bmodern\b', r'\bnewly\s+built\b', r'\bbrand\s+new\b',
    r'\bnew\s+built\b', r'\barchitect(?:ural|s?)?\b', r'\bcontemporary\b',
    r'\bjust\s+built\b', r'\bnewly\s+constructed\b', r'\bnew\s+construction\b',
]

FULLY_FURNISHED_PATTERNS = [
    r'\bfully\s+furnished\b', r'\bfull(?:y)?\s+furnished\b',
    r'\bfully\s+furnished\b', r'\bcomplete(?:ly)?\s+furnished\b',
]

SEMI_FURNISHED_PATTERNS = [
    r'\bsemi[\s\-]furnished\b', r'\bpart(?:ly|ially)?\s+furnished\b',
    r'\bhalf[\s\-]furnished\b',
]

UNFURNISHED_PATTERNS = [
    r'\bunfurnished\b', r'\bnot\s+furnished\b', r'\bwithout\s+furniture\b',
]

FURNISHED_PATTERNS = [
    r'\bfurnished\b',  # generic "furnished" (no semi/fully prefix)
]


def classify_quality(text: str) -> int:
    """Return quality tier: 0=Standard, 1=Modern, 2=Luxury, 3=Super Luxury"""
    if not isinstance(text, str):
        return 0
    t = text.lower()
    for p in SUPER_LUXURY_PATTERNS:
        if re.search(p, t):
            return 3
    for p in LUXURY_PATTERNS:
        if re.search(p, t):
            return 2
    for p in MODERN_PATTERNS:
        if re.search(p, t):
            return 1
    return 0


def classify_furnishing(text: str) -> int:
    """Return 0=Unfurnished/Unknown, 1=Semi-Furnished, 2=Fully Furnished"""
    if not isinstance(text, str):
        return 0
    t = text.lower()
    # Check fully furnished first (most specific)
    for p in FULLY_FURNISHED_PATTERNS:
        if re.search(p, t):
            return 2
    # Semi furnished
    for p in SEMI_FURNISHED_PATTERNS:
        if re.search(p, t):
            return 1
    # Explicitly unfurnished
    for p in UNFURNISHED_PATTERNS:
        if re.search(p, t):
            return 0
    # Generic "furnished" without qualifier → treat as fully furnished
    for p in FURNISHED_PATTERNS:
        if re.search(p, t):
            return 2
    return 0


def main():
    print(f"Loading: {RAW_CSV}")
    df = pd.read_csv(RAW_CSV)
    print(f"Loaded {len(df):,} rows")

    # Combine title + description for richer signal
    text_field = df["title"].fillna("") + " " + df.get("description", pd.Series([""] * len(df))).fillna("")

    print("\nExtracting quality tier from titles...")
    df["quality_tier"] = text_field.apply(classify_quality)

    print("Extracting furnishing status from titles...")
    df["is_furnished"]  = text_field.apply(classify_furnishing)

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n=== Quality Tier Distribution ===")
    labels = {0: "Standard", 1: "Modern/New", 2: "Luxury", 3: "Super Luxury"}
    vc = df["quality_tier"].value_counts().sort_index()
    for k, count in vc.items():
        print(f"  {labels[k]:<15} ({k}): {count:>5,}  ({count/len(df)*100:.1f}%)")

    print("\n=== Furnishing Distribution ===")
    flabels = {0: "Unfurnished/Unknown", 1: "Semi-Furnished", 2: "Fully Furnished"}
    fvc = df["is_furnished"].value_counts().sort_index()
    for k, count in fvc.items():
        print(f"  {flabels[k]:<22} ({k}): {count:>5,}  ({count/len(df)*100:.1f}%)")

    # ── Sample listings for each tier (sanity check) ──────────────────────────
    print("\n=== Sample Luxury Listings ===")
    lux = df[df["quality_tier"] == 2]["title"].head(5)
    for t in lux:
        print(f"  • {t[:80]}")

    print("\n=== Sample Super Luxury Listings ===")
    slux = df[df["quality_tier"] == 3]["title"].head(5)
    for t in slux:
        print(f"  • {t[:80]}")

    print("\n=== Sample Furnished Listings ===")
    furn = df[df["is_furnished"] == 2]["title"].head(5)
    for t in furn:
        print(f"  • {t[:80]}")

    # Save
    df.to_csv(RAW_CSV, index=False)
    print(f"\n✅ Saved enriched data → {RAW_CSV}")
    print(f"   quality_tier + is_furnished columns added")


if __name__ == "__main__":
    main()
