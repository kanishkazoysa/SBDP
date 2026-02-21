"""
01_preprocessing.py
====================
Sri Lanka Property Price Prediction
Data source: ikman.lk (scraped via scrape_properties.py)

Steps:
  1. Load raw CSV
  2. Clean and filter
  3. Feature engineering
  4. Save processed CSV + feature list
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

RAW_CSV   = Path(__file__).parent.parent / "dataset" / "properties_raw.csv"
OUT_CSV   = Path(__file__).parent / "artifacts" / "processed.csv"
FEAT_JSON = Path(__file__).parent / "artifacts" / "feature_info.json"

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

# ── 1. Load ───────────────────────────────────────────────────────────────────
df = pd.read_csv(RAW_CSV)
print(f"Raw rows : {len(df):,}")
print(f"Columns  : {list(df.columns)}")

# ── 2. Clean target variable (price_lkr) ──────────────────────────────────────
df["price_lkr"] = pd.to_numeric(df["price_lkr"], errors="coerce")

# Drop rows with no price
df = df.dropna(subset=["price_lkr"])
print(f"After dropping null price : {len(df):,}")

# Remove clearly invalid prices (0 or >1 billion LKR)
df = df[(df["price_lkr"] > 100_000) & (df["price_lkr"] <= 1_000_000_000)]
print(f"After price range filter  : {len(df):,}")

# Remove extreme outliers (beyond 1st/99th percentile)
p1  = df["price_lkr"].quantile(0.01)
p99 = df["price_lkr"].quantile(0.99)
df  = df[(df["price_lkr"] >= p1) & (df["price_lkr"] <= p99)]
print(f"After 1–99 pct filter     : {len(df):,}")

# ── 3. Feature engineering ─────────────────────────────────────────────────────

# Property type — clean and group
df["property_type"] = df["property_type"].str.strip()
type_map = {
    "Land For Sale":       "Land",
    "Houses For Sale":     "House",
    "Apartments For Sale": "Apartment",
    "Land":                "Land",
    "Houses":              "House",
    "Apartments":          "Apartment",
}
df["property_type"] = df["property_type"].map(type_map).fillna("Other")

# Location — use as-is (district level from ikman)
df["location"] = df["location"].str.strip().fillna("Unknown")

# Numeric features
df["bedrooms"]          = pd.to_numeric(df["bedrooms"],          errors="coerce")
df["bathrooms"]         = pd.to_numeric(df["bathrooms"],         errors="coerce")
df["land_size_perches"] = pd.to_numeric(df["land_size_perches"], errors="coerce")

# Clip bedrooms / bathrooms to sensible max
df["bedrooms"]  = df["bedrooms"].clip(upper=20)
df["bathrooms"] = df["bathrooms"].clip(upper=15)

# Clip land size to reasonable maximum (1000 perches)
df["land_size_perches"] = df["land_size_perches"].clip(upper=1000)

# Binary: is it for rent vs sale
df["is_for_rent"] = (df["ad_type"] == "for_rent").astype(int)

# Log price (used for modelling — better distribution)
df["log_price"] = np.log1p(df["price_lkr"])

# ── 4. Select final feature columns ───────────────────────────────────────────
FEATURES = [
    "property_type",       # categorical
    "location",            # categorical (district)
    "bedrooms",            # numeric, may be NaN for land
    "bathrooms",           # numeric, may be NaN for land
    "land_size_perches",   # numeric, may be NaN for houses/apts
    "is_for_rent",         # binary
]
TARGET = "price_lkr"

df_out = df[FEATURES + [TARGET, "log_price", "title", "url"]].copy()

print(f"\nFinal dataset size : {len(df_out):,} rows")
print(f"Feature null counts:")
for f in FEATURES:
    n = df_out[f].isna().sum()
    print(f"  {f}: {n} NaN ({n*100//len(df_out)}%)")

# ── 5. Save ───────────────────────────────────────────────────────────────────
df_out.to_csv(OUT_CSV, index=False)
print(f"\nSaved processed CSV -> {OUT_CSV}")

# Save feature metadata
info = {
    "features": FEATURES,
    "target": TARGET,
    "categorical_features": ["property_type", "location"],
    "numeric_features":     ["bedrooms", "bathrooms", "land_size_perches", "is_for_rent"],
    "n_rows": len(df_out),
    "price_stats": {
        "min":    float(df_out[TARGET].min()),
        "max":    float(df_out[TARGET].max()),
        "mean":   float(df_out[TARGET].mean()),
        "median": float(df_out[TARGET].median()),
    },
    "property_type_counts": df_out["property_type"].value_counts().to_dict(),
    "location_counts":      df_out["location"].value_counts().head(20).to_dict(),
}
with open(FEAT_JSON, "w") as f:
    json.dump(info, f, indent=2)
print(f"Saved feature info  -> {FEAT_JSON}")

# Quick summary stats
print("\n=== Price Summary (LKR) ===")
print(df_out[TARGET].describe().apply(lambda x: f"{x:,.0f}"))
print("\n=== Property Types ===")
print(df_out["property_type"].value_counts())
print("\n=== Top 10 Locations ===")
print(df_out["location"].value_counts().head(10))
