"""
01_preprocessing.py
====================
Tea Yield Prediction in Sri Lanka
Data source: Tea Research Institute (TRI) Historical Archives (dataset/tea_yield_historical_data.csv)

Steps:
  1. Load raw tea dataset
  2. Clean and filter
  3. Feature engineering
  4. Save processed CSV + feature list
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
RAW_CSV   = Path(__file__).parent.parent.parent / "dataset" / "tea_yield_historical_data.csv"
OUT_CSV   = Path(__file__).parent / "artifacts" / "processed.csv"
FEAT_JSON = Path(__file__).parent / "artifacts" / "feature_info.json"

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

# ── 1. Load Data ──────────────────────────────────────────────────────────────
if not RAW_CSV.exists():
    print(f"ERROR: Raw data not found at {RAW_CSV}")
    exit(1)

df = pd.read_csv(RAW_CSV)
print(f"Raw rows : {len(df):,}")
print(f"Columns  : {list(df.columns)}")

# ── 2. Clean & Filter ─────────────────────────────────────────────────────────
# Drop rows with no yield (target)
df = df.dropna(subset=["yield_mt_per_hec"])

# Standardize text columns
df["district"] = df["district"].str.strip()
df["elevation"] = df["elevation"].str.strip()
df["fertilizer_type"] = df["fertilizer_type"].str.strip()
df["drainage_quality"] = df["drainage_quality"].str.strip()

# Numeric cleanup (ensure sensible ranges)
df["monthly_rainfall_mm"] = df["monthly_rainfall_mm"].clip(0, 1000)
df["avg_temp_c"] = df["avg_temp_c"].clip(5, 45)
df["soil_ph"] = df["soil_ph"].clip(3.0, 9.0)

# ── 3. Feature Engineering ────────────────────────────────────────────────────
# In this dataset, features are already clean.
# We'll just define the feature list for the model.

FEATURES = [
    "district",          # categorical
    "elevation",         # categorical (High, Mid, Low)
    "monthly_rainfall_mm",# numeric
    "avg_temp_c",        # numeric
    "soil_nitrogen",     # numeric
    "soil_phosphorus",   # numeric
    "soil_potassium",    # numeric
    "soil_ph",           # numeric
    "fertilizer_type",   # categorical (Organic, Chemical, Combo)
    "drainage_quality",  # categorical (Good, Fair, Poor)
]
TARGET = "yield_mt_per_hec"

# Select relevant columns
df_out = df[FEATURES + [TARGET, "recorded_date"]].copy()

# ── 4. Save Processed Data ────────────────────────────────────────────────────
df_out.to_csv(OUT_CSV, index=False)
print(f"\nSaved processed CSV -> {OUT_CSV}")

# Save feature metadata for the API and Frontend
info = {
    "features": FEATURES,
    "target": TARGET,
    "categorical_features": ["district", "elevation", "fertilizer_type", "drainage_quality"],
    "numeric_features": [
        "monthly_rainfall_mm", "avg_temp_c", "soil_nitrogen", 
        "soil_phosphorus", "soil_potassium", "soil_ph"
    ],
    "n_rows": len(df_out),
    "yield_stats": {
        "min": float(df_out[TARGET].min()),
        "max": float(df_out[TARGET].max()),
        "mean": float(df_out[TARGET].mean()),
        "median": float(df_out[TARGET].median()),
    },
    "districts": sorted(df_out["district"].unique().tolist()),
    "elevations": sorted(df_out["elevation"].unique().tolist()),
    "fertilizer_types": sorted(df_out["fertilizer_type"].unique().tolist()),
    "drainage_qualities": sorted(df_out["drainage_quality"].unique().tolist()),
}

with open(FEAT_JSON, "w") as f:
    json.dump(info, f, indent=2)
print(f"Saved feature info  -> {FEAT_JSON}")

# Quick summary stats
print("\n=== Yield Summary (MT/Hectare) ===")
print(df_out[TARGET].describe())
print("\n=== Records by District ===")
print(df_out["district"].value_counts())
