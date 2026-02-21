"""
05_train_forecast_model.py
===========================
Sri Lanka Property Price FORECASTING Model

Combines:
  1. Scraped ikman.lk data (with listing dates — Nov 2025 → Feb 2026)
  2. CBSL economic data (2018 – 2030)

Reconstructs estimated historical prices by district using:
  - Your scraped Feb 2026 baseline prices
  - Sri Lanka inflation / property price growth index to back-calculate 2018–2025

Trains a time-aware LightGBM model:
  INPUT:  year, month, district, property_type, bedrooms, land_size,
          inflation, lending_rate, usd_lkr, gdp_growth, property_price_index
  OUTPUT: predicted price (LKR)

Then forecasts 2027, 2028, 2029, 2030 prices per district.

Output:
  ml/artifacts/forecast_model.pkl
  ml/artifacts/forecast_encoders.pkl
  ml/artifacts/district_forecasts.json   ← precomputed per-district forecasts
  ml/artifacts/forecast_metrics.json
  ml/figures/forecast_*.png
"""

import pandas as pd
import numpy as np
import json
import pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
import lightgbm as lgb

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
FIGURE_DIR   = Path(__file__).parent / "figures"
RAW_CSV      = Path(__file__).parent.parent / "dataset" / "properties_raw.csv"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

# ── Load scraped data ──────────────────────────────────────────────────────────
print("Loading scraped property data...")
df_raw = pd.read_csv(RAW_CSV)
print(f"Raw rows: {len(df_raw):,}")
print(f"Columns: {list(df_raw.columns)}")

# ── Load economic data ─────────────────────────────────────────────────────────
df_econ_annual = pd.read_csv(ARTIFACT_DIR / "economic_data_annual.csv")
df_econ_all    = pd.read_csv(ARTIFACT_DIR / "economic_data_all.csv")
print(f"\nEconomic data: {len(df_econ_annual)} years (annual)")

# ── Check for listing dates in scraped data ─────────────────────────────────
has_listed_at = "listed_at" in df_raw.columns and df_raw["listed_at"].notna().sum() > 0
print(f"\nlisted_at column present: {'listed_at' in df_raw.columns}")
if has_listed_at:
    valid_dates = df_raw["listed_at"].notna().sum()
    print(f"Ads with listing date: {valid_dates:,} ({valid_dates*100//len(df_raw)}%)")

# ── Clean the scraped data ─────────────────────────────────────────────────────
df_raw["price_lkr"] = pd.to_numeric(df_raw["price_lkr"], errors="coerce")
df_raw = df_raw.dropna(subset=["price_lkr"])
df_raw = df_raw[(df_raw["price_lkr"] > 100_000) & (df_raw["price_lkr"] <= 1_000_000_000)]
p1, p99 = df_raw["price_lkr"].quantile(0.01), df_raw["price_lkr"].quantile(0.99)
df_raw  = df_raw[(df_raw["price_lkr"] >= p1) & (df_raw["price_lkr"] <= p99)]
print(f"After cleaning: {len(df_raw):,} rows")

# Property type normalisation
type_map = {
    "Land For Sale": "Land", "Houses For Sale": "House",
    "Apartments For Sale": "Apartment", "Land": "Land",
    "Houses": "House", "Apartments": "Apartment",
    "House": "House", "Apartment": "Apartment",
    "land": "Land", "house": "House", "apartment": "Apartment",
    "villa": "House", "Villa": "House",
}
df_raw["property_type"] = df_raw["property_type"].str.strip().map(type_map).fillna("Other")
df_raw = df_raw[df_raw["property_type"].isin(["Land", "House", "Apartment"])]
df_raw["location"] = df_raw["location"].str.strip().fillna("Unknown")
df_raw["land_size_perches"] = pd.to_numeric(df_raw["land_size_perches"], errors="coerce").clip(upper=1000)
df_raw["bedrooms"]          = pd.to_numeric(df_raw["bedrooms"],          errors="coerce").clip(upper=20)
df_raw["bathrooms"]         = pd.to_numeric(df_raw["bathrooms"],         errors="coerce").clip(upper=15)

print(f"After type filter: {len(df_raw):,} rows")

# ── Step 1: Compute Feb 2026 baseline price per district+type ─────────────────
print("\nComputing baseline prices (Feb 2026)...")
baseline = (
    df_raw.groupby(["location", "property_type"])["price_lkr"]
    .median()
    .reset_index()
    .rename(columns={"price_lkr": "baseline_price_2026"})
)
print(f"District+type combinations: {len(baseline)}")

# ── Step 2: Back-calculate prices 2018–2025 using property price index ─────────
print("\nReconstructing historical prices 2018–2025...")

# Property price index: 2026 = 280 (from economic data)
INDEX_2026 = 280.0

historical_rows = []

for year in range(2018, 2027):  # 2018 to 2026
    econ_row = df_econ_annual[df_econ_annual["year"] == year]
    if len(econ_row) == 0:
        continue
    econ_row = econ_row.iloc[0]

    price_index = econ_row["property_price_index"]
    scale_factor = price_index / INDEX_2026  # e.g. 2018: 100/280 = 0.357

    inflation     = econ_row["inflation_pct"]
    lending_rate  = econ_row["lending_rate_pct"]
    usd_lkr       = econ_row["usd_lkr"]
    gdp_growth    = econ_row["gdp_growth_pct"]
    policy_rate   = econ_row["policy_rate_pct"]
    price_idx     = econ_row["property_price_index"]

    for _, base_row in baseline.iterrows():
        est_price = base_row["baseline_price_2026"] * scale_factor
        historical_rows.append({
            "year":                  year,
            "month":                 6,        # mid-year estimate
            "location":              base_row["location"],
            "property_type":         base_row["property_type"],
            "bedrooms":              np.nan,
            "bathrooms":             np.nan,
            "land_size_perches":     np.nan,
            "price_lkr":             est_price,
            "inflation_pct":         inflation,
            "lending_rate_pct":      lending_rate,
            "usd_lkr":               usd_lkr,
            "gdp_growth_pct":        gdp_growth,
            "policy_rate_pct":       policy_rate,
            "property_price_index":  price_idx,
            "data_source":           "estimated_historical",
        })

df_historical = pd.DataFrame(historical_rows)
print(f"Estimated historical rows: {len(df_historical):,}")

# ── Step 3: Add real scraped data (2025/2026) with dates ─────────────────────
print("\nAdding real scraped data...")
df_raw["scraped_at"] = pd.to_datetime(df_raw["scraped_at"], errors="coerce")

# Extract year and month from listing date if available
if has_listed_at:
    df_raw["listed_at_parsed"] = pd.to_datetime(df_raw["listed_at"], errors="coerce")
    df_raw["year"]  = df_raw["listed_at_parsed"].dt.year.fillna(2026).astype(int)
    df_raw["month"] = df_raw["listed_at_parsed"].dt.month.fillna(2).astype(int)
else:
    # Use scraped_at date — all are Feb 2026
    df_raw["year"]  = df_raw["scraped_at"].dt.year.fillna(2026).astype(int)
    df_raw["month"] = df_raw["scraped_at"].dt.month.fillna(2).astype(int)

# Merge with economic data
df_real = df_raw.merge(
    df_econ_annual[["year","inflation_pct","lending_rate_pct","usd_lkr",
                    "gdp_growth_pct","policy_rate_pct","property_price_index"]],
    on="year", how="left"
)

# Fill any missing economic data with 2026 values
econ_2026 = df_econ_annual[df_econ_annual["year"] == 2026].iloc[0]
for col in ["inflation_pct","lending_rate_pct","usd_lkr","gdp_growth_pct",
            "policy_rate_pct","property_price_index"]:
    df_real[col] = df_real[col].fillna(econ_2026[col])

df_real["data_source"] = "real_scraped"

real_cols = ["year","month","location","property_type","bedrooms","bathrooms",
             "land_size_perches","price_lkr","inflation_pct","lending_rate_pct",
             "usd_lkr","gdp_growth_pct","policy_rate_pct","property_price_index",
             "data_source"]
df_real_clean = df_real[real_cols].copy()

# ── Step 4: Combine historical + real data ────────────────────────────────────
df_combined = pd.concat([df_historical, df_real_clean], ignore_index=True)
df_combined = df_combined.dropna(subset=["price_lkr"])
print(f"\nCombined dataset: {len(df_combined):,} rows")
print(f"  Estimated historical: {(df_combined['data_source']=='estimated_historical').sum():,}")
print(f"  Real scraped:         {(df_combined['data_source']=='real_scraped').sum():,}")
print(f"  Year range:           {df_combined['year'].min()} – {df_combined['year'].max()}")

# Save combined dataset
combined_path = ARTIFACT_DIR / "combined_timeseries.csv"
df_combined.to_csv(combined_path, index=False)
print(f"\nSaved combined dataset -> {combined_path}")

# ── Step 5: Train the forecasting model ───────────────────────────────────────
print("\nTraining forecasting model...")

FEATURES = [
    "year", "month",
    "location", "property_type",
    "bedrooms", "bathrooms", "land_size_perches",
    "inflation_pct", "lending_rate_pct", "usd_lkr",
    "gdp_growth_pct", "policy_rate_pct", "property_price_index",
]
TARGET = "price_lkr"

X = df_combined[FEATURES].copy()
y = np.log1p(df_combined[TARGET])

# Encode categoricals
cat_cols = ["location", "property_type"]
encoders = {}
for col in cat_cols:
    le = LabelEncoder()
    X[col] = le.fit_transform(X[col].astype(str))
    encoders[col] = le

# Save encoders
with open(ARTIFACT_DIR / "forecast_encoders.pkl", "wb") as f:
    pickle.dump(encoders, f)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
X_train, X_val,  y_train, y_val  = train_test_split(X_train, y_train, test_size=0.15/0.85, random_state=42)

print(f"Train: {len(X_train):,}  Val: {len(X_val):,}  Test: {len(X_test):,}")

params = {
    "objective":         "regression",
    "metric":            "rmse",
    "boosting_type":     "gbdt",
    "n_estimators":      1000,
    "learning_rate":     0.05,
    "num_leaves":        63,
    "min_child_samples": 20,
    "feature_fraction":  0.8,
    "bagging_fraction":  0.8,
    "bagging_freq":      5,
    "reg_alpha":         0.1,
    "reg_lambda":        0.1,
    "random_state":      42,
    "verbose":           -1,
}

model = lgb.LGBMRegressor(**params)
model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    callbacks=[
        lgb.early_stopping(stopping_rounds=50, verbose=False),
        lgb.log_evaluation(period=100),
    ],
    categorical_feature=cat_cols,
)

# Evaluate
y_pred_test = model.predict(X_test)
test_mae  = mean_absolute_error(np.expm1(y_test), np.expm1(y_pred_test))
test_r2   = r2_score(y_test, y_pred_test)
print(f"\nTest MAE : Rs {test_mae:,.0f}")
print(f"Test R²  : {test_r2:.4f}")

# Save model
with open(ARTIFACT_DIR / "forecast_model.pkl", "wb") as f:
    pickle.dump(model, f)
print("Saved forecast_model.pkl")

# ── Step 6: Generate per-district forecasts 2026–2030 ──────────────────────────
print("\nGenerating district forecasts...")

df_econ_future = pd.read_csv(ARTIFACT_DIR / "economic_data_all.csv")

districts     = [loc for loc in df_combined["location"].unique()
                 if loc not in ("Unknown", "") and len(df_combined[df_combined["location"]==loc]) >= 5]
property_types = ["Land", "House", "Apartment"]
forecast_years = [2026, 2027, 2028, 2029, 2030]

forecasts = {}

for district in districts:
    forecasts[district] = {}
    for ptype in property_types:
        yearly_prices = {}
        for year in forecast_years:
            econ = df_econ_future[df_econ_future["year"] == year]
            if len(econ) == 0:
                continue
            econ = econ.iloc[0]

            try:
                loc_enc  = encoders["location"].transform([district])[0]
                type_enc = encoders["property_type"].transform([ptype])[0]
            except Exception:
                continue

            row = pd.DataFrame([{
                "year":                  year,
                "month":                 6,
                "location":              loc_enc,
                "property_type":         type_enc,
                "bedrooms":              np.nan,
                "bathrooms":             np.nan,
                "land_size_perches":     np.nan,
                "inflation_pct":         econ["inflation_pct"],
                "lending_rate_pct":      econ["lending_rate_pct"],
                "usd_lkr":               econ["usd_lkr"],
                "gdp_growth_pct":        econ["gdp_growth_pct"],
                "policy_rate_pct":       econ["policy_rate_pct"],
                "property_price_index":  econ["property_price_index"],
            }])

            log_price = float(model.predict(row)[0])
            price     = float(np.expm1(log_price))
            yearly_prices[str(year)] = round(price)

        if yearly_prices:
            # Calculate expected growth
            if "2026" in yearly_prices and "2030" in yearly_prices:
                growth_4yr = (yearly_prices["2030"] - yearly_prices["2026"]) / yearly_prices["2026"] * 100
            else:
                growth_4yr = 0

            forecasts[district][ptype] = {
                "prices":       yearly_prices,
                "growth_4yr_pct": round(growth_4yr, 1),
            }

print(f"Generated forecasts for {len(forecasts)} districts")

# Save forecasts
with open(ARTIFACT_DIR / "district_forecasts.json", "w") as f:
    json.dump(forecasts, f, indent=2)
print("Saved district_forecasts.json")

# Save metrics
forecast_metrics = {
    "test_mae":  float(test_mae),
    "test_r2":   float(test_r2),
    "n_train":   int(len(X_train)),
    "n_test":    int(len(X_test)),
    "n_districts": len(forecasts),
    "year_range": "2018–2030",
    "features":  FEATURES,
}
with open(ARTIFACT_DIR / "forecast_metrics.json", "w") as f:
    json.dump(forecast_metrics, f, indent=2)

# ── Step 7: Plots ──────────────────────────────────────────────────────────────

# Plot 1: Price timeline for top 5 districts
top_districts = ["Colombo", "Gampaha", "Kalutara", "Kandy", "Galle"]
top_districts = [d for d in top_districts if d in forecasts]

fig, ax = plt.subplots(figsize=(12, 7))
colors = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]

for i, district in enumerate(top_districts[:5]):
    if "Land" not in forecasts.get(district, {}):
        continue
    data = forecasts[district]["Land"]["prices"]
    years  = [int(y) for y in sorted(data.keys())]
    prices = [data[str(y)] / 1_000_000 for y in years]

    # Solid line for historical (2026 baseline), dashed for forecast
    ax.plot([y for y in years if y <= 2026],
            [p for y, p in zip(years, prices) if y <= 2026],
            color=colors[i], linewidth=2.5, label=district)
    ax.plot([y for y in years if y >= 2026],
            [p for y, p in zip(years, prices) if y >= 2026],
            color=colors[i], linewidth=2.5, linestyle="--")

ax.axvline(x=2026, color="gray", linestyle=":", linewidth=1.5, label="Forecast starts →")
ax.set_xlabel("Year")
ax.set_ylabel("Median Land Price (Rs. Million per 10 perches)")
ax.set_title("Sri Lanka Land Price Forecast by District (2026–2030)")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(FIGURE_DIR / "forecast_districts.png", dpi=150)
plt.close()
print("Saved forecast_districts.png")

# Plot 2: Feature importance
fi = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=True)
fig, ax = plt.subplots(figsize=(10, 6))
colors_bar = ["#6366f1" if i >= len(fi) - 4 else "#94a3b8" for i in range(len(fi))]
fi.plot(kind="barh", ax=ax, color=colors_bar)
ax.set_title("Forecast Model — Feature Importance")
ax.set_xlabel("Importance (Gain)")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "forecast_feature_importance.png", dpi=150)
plt.close()
print("Saved forecast_feature_importance.png")

# Plot 3: 2026 vs 2030 price comparison bar chart
comparison_data = []
for district in top_districts:
    for ptype in ["Land", "House"]:
        if ptype in forecasts.get(district, {}):
            prices = forecasts[district][ptype]["prices"]
            if "2026" in prices and "2030" in prices:
                comparison_data.append({
                    "district": district,
                    "type": ptype,
                    "price_2026": prices["2026"] / 1_000_000,
                    "price_2030": prices["2030"] / 1_000_000,
                    "growth": forecasts[district][ptype]["growth_4yr_pct"],
                })

df_comp = pd.DataFrame(comparison_data)
if not df_comp.empty:
    fig, ax = plt.subplots(figsize=(12, 6))
    x = range(len(df_comp))
    width = 0.35
    labels = [f"{r['district']}\n({r['type']})" for _, r in df_comp.iterrows()]
    bars1 = ax.bar([i - width/2 for i in x], df_comp["price_2026"], width,
                   label="2026 (Baseline)", color="#94a3b8")
    bars2 = ax.bar([i + width/2 for i in x], df_comp["price_2030"], width,
                   label="2030 (Forecast)", color="#6366f1")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Price (Rs. Million)")
    ax.set_title("Property Price: 2026 Baseline vs 2030 Forecast")
    ax.legend()
    for i, (_, row) in enumerate(df_comp.iterrows()):
        ax.text(i + width/2, row["price_2030"] + 0.5,
                f"+{row['growth']:.0f}%", ha="center", fontsize=8, color="#6366f1")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "forecast_comparison.png", dpi=150)
    plt.close()
    print("Saved forecast_comparison.png")

print("\n=== Forecast Training Complete ===")
print(f"Test R²  : {test_r2:.4f}")
print(f"Test MAE : Rs {test_mae:,.0f}")
print(f"Districts forecasted: {len(forecasts)}")
print(f"Years forecasted: 2026 – 2030")
