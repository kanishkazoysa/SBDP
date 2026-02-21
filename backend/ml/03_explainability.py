"""
03_explainability.py
=====================
Sri Lanka Property Price Prediction
XAI: SHAP (SHapley Additive exPlanations)

Outputs:
  - ml/figures/shap_summary.png
  - ml/figures/shap_beeswarm.png
  - ml/figures/shap_dependence_*.png
  - ml/artifacts/shap_values.pkl
"""

import pandas as pd
import numpy as np
import pickle
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
import shap

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
FIGURE_DIR   = Path(__file__).parent / "figures"
PROCESSED    = ARTIFACT_DIR / "processed.csv"

FIGURE_DIR.mkdir(parents=True, exist_ok=True)

# ── Load model and encoders ────────────────────────────────────────────────────
with open(ARTIFACT_DIR / "lgbm_model.pkl", "rb") as f:
    model = pickle.load(f)

with open(ARTIFACT_DIR / "label_encoders.pkl", "rb") as f:
    encoders = pickle.load(f)

# ── Load and encode data ───────────────────────────────────────────────────────
df = pd.read_csv(PROCESSED)

FEATURES = ["property_type", "location", "bedrooms", "bathrooms",
            "land_size_perches", "is_for_rent", "quality_tier", "is_furnished"]

X = df[FEATURES].copy()
for col, le in encoders.items():
    X[col] = le.transform(X[col].astype(str))

# Use a sample for SHAP (full set can be slow)
sample_size = min(1500, len(X))
X_sample = X.sample(sample_size, random_state=42)
print(f"Computing SHAP values on {len(X_sample)} samples...")

# ── SHAP TreeExplainer ─────────────────────────────────────────────────────────
explainer   = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_sample)

with open(ARTIFACT_DIR / "shap_values.pkl", "wb") as f:
    pickle.dump({"shap_values": shap_values, "X_sample": X_sample}, f)
print("Saved shap_values.pkl")

# ── Plot 1: SHAP Summary Bar ───────────────────────────────────────────────────
feature_labels = {
    "property_type":     "Property Type",
    "location":          "District / Location",
    "bedrooms":          "Number of Bedrooms",
    "bathrooms":         "Number of Bathrooms",
    "land_size_perches": "Land Size (Perches)",
    "is_for_rent":       "Rental vs Sale",
    "quality_tier":      "Quality Tier (Luxury)",
    "is_furnished":      "Furnishing Status",
}
display_names = [feature_labels.get(f, f) for f in FEATURES]

fig, ax = plt.subplots(figsize=(9, 5))
mean_abs_shap = np.abs(shap_values).mean(axis=0)
order = np.argsort(mean_abs_shap)
ax.barh(
    [display_names[i] for i in order],
    mean_abs_shap[order],
    color=["#6366f1" if i == order[-1] else
           "#818cf8" if i == order[-2] else "#94a3b8" for i in order],
)
ax.set_xlabel("Mean |SHAP value| (log-price units)")
ax.set_title("Feature Importance — SHAP Summary\n(Impact on Predicted Property Price)")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "shap_summary.png", dpi=150)
plt.close()
print("Saved shap_summary.png")

# ── Plot 2: SHAP Beeswarm ──────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
shap.summary_plot(
    shap_values, X_sample,
    feature_names=display_names,
    show=False,
    plot_size=None,
    max_display=6,
)
plt.title("SHAP Beeswarm — Feature Effect on Price", pad=12)
plt.tight_layout()
plt.savefig(FIGURE_DIR / "shap_beeswarm.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved shap_beeswarm.png")

# ── Plot 3: SHAP Dependence — Land Size ───────────────────────────────────────
feat_idx = FEATURES.index("land_size_perches")
land_mask = X_sample["land_size_perches"].notna()
if land_mask.sum() > 100:
    fig, ax = plt.subplots(figsize=(8, 5))
    sc = ax.scatter(
        X_sample.loc[land_mask, "land_size_perches"],
        shap_values[land_mask, feat_idx],
        c=X_sample.loc[land_mask, "property_type"],
        cmap="viridis", alpha=0.4, s=12,
    )
    plt.colorbar(sc, ax=ax, label="Property Type (encoded)")
    ax.set_xlabel("Land Size (Perches)")
    ax.set_ylabel("SHAP value (log-price units)")
    ax.set_title("SHAP Dependence Plot — Land Size vs Price Impact")
    ax.axhline(0, color="red", linestyle="--", linewidth=1)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "shap_dependence_landsize.png", dpi=150)
    plt.close()
    print("Saved shap_dependence_landsize.png")

# ── Plot 4: SHAP Dependence — Bedrooms ────────────────────────────────────────
feat_idx = FEATURES.index("bedrooms")
bed_mask = X_sample["bedrooms"].notna()
if bed_mask.sum() > 100:
    bed_shap = pd.DataFrame({
        "bedrooms": X_sample.loc[bed_mask, "bedrooms"].values,
        "shap":     shap_values[bed_mask.values, feat_idx],
    })
    bed_grouped = bed_shap.groupby("bedrooms")["shap"].median()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(bed_grouped.index, bed_grouped.values, color="#6366f1", alpha=0.8)
    ax.set_xlabel("Number of Bedrooms")
    ax.set_ylabel("Median SHAP value (log-price units)")
    ax.set_title("SHAP Dependence — Bedrooms vs Price Impact")
    ax.axhline(0, color="red", linestyle="--", linewidth=1)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "shap_dependence_bedrooms.png", dpi=150)
    plt.close()
    print("Saved shap_dependence_bedrooms.png")

# ── Plot 5: Top 3 individual explanations (waterfall) ─────────────────────────
# Pick 3 diverse examples for the report
examples_idx = [
    X_sample[X_sample["property_type"] == encoders["property_type"].transform(["Land"])[0]].index[0],
    X_sample[X_sample["property_type"] == encoders["property_type"].transform(["House"])[0]].index[0],
    X_sample[X_sample["property_type"] == encoders["property_type"].transform(["Apartment"])[0]].index[0],
]
for i, idx in enumerate(examples_idx):
    row_pos = X_sample.index.get_loc(idx)
    exp = shap.Explanation(
        values=shap_values[row_pos],
        base_values=explainer.expected_value,
        data=X_sample.iloc[row_pos],
        feature_names=display_names,
    )
    fig, ax = plt.subplots(figsize=(9, 4))
    shap.waterfall_plot(exp, show=False, max_display=6)
    plt.title(f"SHAP Waterfall — Individual Prediction Example {i+1}")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / f"shap_waterfall_{i+1}.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved shap_waterfall_{i+1}.png")

# ── Save SHAP mean importances as JSON for frontend ───────────────────────────
shap_importance = {
    display_names[i]: float(np.abs(shap_values[:, i]).mean())
    for i in range(len(FEATURES))
}
with open(ARTIFACT_DIR / "shap_importance.json", "w") as f:
    json.dump(shap_importance, f, indent=2)
print("Saved shap_importance.json")

print("\n=== SHAP Analysis Complete ===")
print("Mean |SHAP| (Rs. Million):")
for name, val in sorted(shap_importance.items(), key=lambda x: -x[1]):
    print(f"  {name:30s}: {val:.3f}")
