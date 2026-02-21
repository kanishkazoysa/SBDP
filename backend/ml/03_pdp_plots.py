"""
03_pdp_plots.py
================
Partial Dependence Plots (PDP) — Assignment Section 4 (Explainability)

PDPs show how each feature individually affects the predicted price,
while keeping all other features at their average values.

Required by assignment rubric:
  "Apply at least one explainability method such as:
   SHAP, LIME, Feature importance analysis, Partial Dependence Plots (PDP)"

Output: ml/figures/pdp_*.png
"""

import pandas as pd
import numpy as np
import pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
FIGURE_DIR   = Path(__file__).parent / "figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

# ── Load model and data ───────────────────────────────────────────────────────
print("Loading model and data...")
with open(ARTIFACT_DIR / "lgbm_model.pkl", "rb") as f:
    model = pickle.load(f)
with open(ARTIFACT_DIR / "label_encoders.pkl", "rb") as f:
    encoders = pickle.load(f)

df = pd.read_csv(ARTIFACT_DIR / "processed.csv")
print(f"Data loaded: {len(df):,} rows")

FEATURES = ["property_type", "location", "bedrooms", "bathrooms",
            "land_size_perches", "is_for_rent"]

X = df[FEATURES].copy()
for col in ["property_type", "location"]:
    le = encoders[col]
    X[col] = X[col].apply(lambda v: le.transform([v])[0] if v in le.classes_ else 0)

# ── Helper: compute PDP for one feature ───────────────────────────────────────
def compute_pdp(X, model, feature, grid_values):
    """
    For each value in grid_values, set all rows' feature to that value,
    predict, and take the mean. Returns mean predicted price (Rs) per grid value.
    """
    X_temp = X.copy()
    mean_prices = []
    for val in grid_values:
        X_temp[feature] = val
        log_preds = model.predict(X_temp)
        mean_price = np.expm1(log_preds).mean()
        mean_prices.append(mean_price)
    return np.array(mean_prices)


# ── Plot 1: PDP for Land Size ─────────────────────────────────────────────────
print("Generating PDP: land_size_perches...")
land_grid = np.linspace(1, 100, 50)
pdp_land  = compute_pdp(X, model, "land_size_perches", land_grid)

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(land_grid, pdp_land / 1_000_000, color="#6366f1", linewidth=2.5)
ax.fill_between(land_grid, pdp_land / 1_000_000, alpha=0.1, color="#6366f1")
ax.set_xlabel("Land Size (perches)", fontsize=12)
ax.set_ylabel("Average Predicted Price (Rs. Million)", fontsize=12)
ax.set_title("PDP — How Land Size Affects Predicted Price\n"
             "(all other features held at their average values)", fontsize=13)
ax.grid(alpha=0.3)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}p"))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"Rs {x:.1f}M"))
plt.tight_layout()
plt.savefig(FIGURE_DIR / "pdp_land_size.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Saved pdp_land_size.png")


# ── Plot 2: PDP for Bedrooms ──────────────────────────────────────────────────
print("Generating PDP: bedrooms...")
bed_grid = np.arange(1, 11)
pdp_bed  = compute_pdp(X, model, "bedrooms", bed_grid)

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(bed_grid, pdp_bed / 1_000_000, color="#10b981", alpha=0.8, width=0.6)
ax.plot(bed_grid, pdp_bed / 1_000_000, "o-", color="#065f46", linewidth=2)
ax.set_xlabel("Number of Bedrooms", fontsize=12)
ax.set_ylabel("Average Predicted Price (Rs. Million)", fontsize=12)
ax.set_title("PDP — How Number of Bedrooms Affects Predicted Price\n"
             "(all other features held at their average values)", fontsize=13)
ax.set_xticks(bed_grid)
ax.grid(axis="y", alpha=0.3)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"Rs {x:.1f}M"))
plt.tight_layout()
plt.savefig(FIGURE_DIR / "pdp_bedrooms.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Saved pdp_bedrooms.png")


# ── Plot 3: PDP for Location (top 12 districts) ───────────────────────────────
print("Generating PDP: location...")
top_locations = df["location"].value_counts().head(12).index.tolist()
loc_encoded   = []
loc_labels    = []
for loc in top_locations:
    if loc in encoders["location"].classes_:
        loc_encoded.append(encoders["location"].transform([loc])[0])
        loc_labels.append(loc)

pdp_loc = compute_pdp(X, model, "location", loc_encoded)
sorted_idx = np.argsort(pdp_loc)
sorted_labels = [loc_labels[i] for i in sorted_idx]
sorted_prices = pdp_loc[sorted_idx]

colors = ["#6366f1" if lbl == "Colombo" else
          "#10b981" if sorted_prices[i] > np.median(sorted_prices) else
          "#94a3b8"
          for i, lbl in enumerate(sorted_labels)]

fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.barh(sorted_labels, sorted_prices / 1_000_000, color=colors, height=0.6)
ax.set_xlabel("Average Predicted Price (Rs. Million)", fontsize=12)
ax.set_title("PDP — Average Predicted Price by District\n"
             "(all other features held at their average values)", fontsize=13)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"Rs {x:.0f}M"))
for bar, price in zip(bars, sorted_prices):
    ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
            f"Rs {price/1_000_000:.1f}M", va="center", fontsize=9)
plt.tight_layout()
plt.savefig(FIGURE_DIR / "pdp_location.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Saved pdp_location.png")


# ── Plot 4: PDP for Property Type ─────────────────────────────────────────────
print("Generating PDP: property_type...")
types = ["Land", "House", "Apartment"]
type_encoded = []
type_labels  = []
for t in types:
    if t in encoders["property_type"].classes_:
        type_encoded.append(encoders["property_type"].transform([t])[0])
        type_labels.append(t)

pdp_type = compute_pdp(X, model, "property_type", type_encoded)
type_colors = ["#f59e0b", "#6366f1", "#10b981"]

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(type_labels, pdp_type / 1_000_000, color=type_colors, width=0.5)
for bar, price in zip(bars, pdp_type):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f"Rs {price/1_000_000:.1f}M", ha="center", fontsize=11)
ax.set_ylabel("Average Predicted Price (Rs. Million)", fontsize=12)
ax.set_title("PDP — Average Predicted Price by Property Type\n"
             "(all other features held at their average values)", fontsize=13)
ax.grid(axis="y", alpha=0.3)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"Rs {x:.0f}M"))
plt.tight_layout()
plt.savefig(FIGURE_DIR / "pdp_property_type.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Saved pdp_property_type.png")


# ── Plot 5: Combined 2×2 PDP summary (good for report) ───────────────────────
print("Generating combined PDP summary plot...")
fig = plt.figure(figsize=(16, 12))
fig.suptitle("Partial Dependence Plots (PDP) — LightGBM Property Price Model\n"
             "Each plot shows how one feature affects predicted price, holding others constant",
             fontsize=14, y=0.98)

gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.35)

# Top-left: Land size
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(land_grid, pdp_land / 1_000_000, color="#6366f1", linewidth=2.5)
ax1.fill_between(land_grid, pdp_land / 1_000_000, alpha=0.1, color="#6366f1")
ax1.set_title("Land Size (perches)", fontsize=12, fontweight="bold")
ax1.set_xlabel("Perches")
ax1.set_ylabel("Predicted Price (Rs. M)")
ax1.grid(alpha=0.3)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"Rs {x:.0f}M"))

# Top-right: Bedrooms
ax2 = fig.add_subplot(gs[0, 1])
ax2.bar(bed_grid, pdp_bed / 1_000_000, color="#10b981", alpha=0.8, width=0.6)
ax2.plot(bed_grid, pdp_bed / 1_000_000, "o-", color="#065f46", linewidth=2)
ax2.set_title("Number of Bedrooms", fontsize=12, fontweight="bold")
ax2.set_xlabel("Bedrooms")
ax2.set_ylabel("Predicted Price (Rs. M)")
ax2.set_xticks(bed_grid)
ax2.grid(axis="y", alpha=0.3)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"Rs {x:.0f}M"))

# Bottom-left: Location
ax3 = fig.add_subplot(gs[1, 0])
ax3.barh(sorted_labels, sorted_prices / 1_000_000, color=colors, height=0.6)
ax3.set_title("District / Location", fontsize=12, fontweight="bold")
ax3.set_xlabel("Predicted Price (Rs. M)")
ax3.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"Rs {x:.0f}M"))
ax3.tick_params(labelsize=9)

# Bottom-right: Property type
ax4 = fig.add_subplot(gs[1, 1])
ax4.bar(type_labels, pdp_type / 1_000_000, color=type_colors, width=0.5)
for bar, price in zip(ax4.patches, pdp_type):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
             f"Rs {price/1_000_000:.0f}M", ha="center", fontsize=10)
ax4.set_title("Property Type", fontsize=12, fontweight="bold")
ax4.set_ylabel("Predicted Price (Rs. M)")
ax4.grid(axis="y", alpha=0.3)
ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"Rs {x:.0f}M"))

plt.savefig(FIGURE_DIR / "pdp_combined.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Saved pdp_combined.png")

print("\n" + "=" * 55)
print("  PDP Generation Complete!")
print("=" * 55)
print(f"Files saved to: {FIGURE_DIR}")
print("\nKey Insights from PDPs:")
print(f"  Land size effect  : Rs {pdp_land[0]/1e6:.1f}M (1p) → Rs {pdp_land[-1]/1e6:.1f}M (100p)")
print(f"  Bedroom effect    : Rs {pdp_bed[0]/1e6:.1f}M (1br) → Rs {pdp_bed[-1]/1e6:.1f}M (10br)")
print(f"  Cheapest district : {sorted_labels[0]}  Rs {sorted_prices[0]/1e6:.1f}M avg")
print(f"  Most expensive    : {sorted_labels[-1]}  Rs {sorted_prices[-1]/1e6:.1f}M avg")
print(f"\n  These insights to include in your report (Section 4)!")
