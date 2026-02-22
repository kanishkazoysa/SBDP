"""
03_explainability.py
=====================
Tea Yield Prediction XAI
SHAP (SHapley Additive exPlanations) for model transparency.

Explains how environmental and soil factors contribute to the predicted
tea harvest yield.
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

# ── Paths ──────────────────────────────────────────────────────────────────────
ARTIFACT_DIR = Path(__file__).parent / "artifacts"
FIGURE_DIR   = Path(__file__).resolve().parents[2] / "report_assets"
PROCESSED    = ARTIFACT_DIR / "processed.csv"

FIGURE_DIR.mkdir(parents=True, exist_ok=True)

# ── Load model, encoders and feature info ──────────────────────────────────────
with open(ARTIFACT_DIR / "lgbm_model.pkl", "rb") as f:
    model = pickle.load(f)

with open(ARTIFACT_DIR / "label_encoders.pkl", "rb") as f:
    encoders = pickle.load(f)

with open(ARTIFACT_DIR / "feature_info.json", "r") as f:
    feat_info = json.load(f)

FEATURES = feat_info["features"]
df = pd.read_csv(PROCESSED)

# ── Encode data ───────────────────────────────────────────────────────────────
X = df[FEATURES].copy()
for col, le in encoders.items():
    X[col] = le.transform(X[col].astype(str))

# Use a sample for SHAP
sample_size = min(1500, len(X))
X_sample = X.sample(sample_size, random_state=42)
print(f"Computing SHAP values on {len(X_sample)} samples...")

# ── SHAP Analysis ─────────────────────────────────────────────────────────────
explainer   = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_sample)

# ── Visualizations ────────────────────────────────────────────────────────────
feature_labels = {
    "district":            "District",
    "elevation":           "Elevation Zone",
    "monthly_rainfall_mm": "Rainfall (mm)",
    "avg_temp_c":          "Avg Temperature (°C)",
    "soil_nitrogen":       "Soil Nitrogen (N)",
    "soil_phosphorus":     "Soil Phosphorus (P)",
    "soil_potassium":      "Soil Potassium (K)",
    "soil_ph":             "Soil pH Level",
    "fertilizer_type":     "Fertilizer Type",
    "drainage_quality":    "Drainage Quality",
}
display_names = [feature_labels.get(f, f) for f in FEATURES]

# 1. SHAP Summary Map
fig, ax = plt.subplots(figsize=(10, 6))
shap.summary_plot(
    shap_values, X_sample,
    feature_names=display_names,
    show=False,
    color_bar_label="Feature Value (Low → High)",
    max_display=10,
)
plt.title("Tea Yield Drivers — SHAP Beeswarm", pad=15, fontsize=14)
plt.tight_layout()
plt.savefig(FIGURE_DIR / "shap_summary.png", dpi=150, bbox_inches="tight")
plt.close()

# 2. SHAP Bar Chart
fig, ax = plt.subplots(figsize=(9, 5))
mean_abs_shap = np.abs(shap_values).mean(axis=0)
order = np.argsort(mean_abs_shap)
colors = ["#10b981" if i == order[-1] else "#34d399" if i == order[-2] else "#94a3b8" for i in order]
ax.barh([display_names[i] for i in order], mean_abs_shap[order], color=colors)
ax.set_xlabel("Mean |SHAP value| (Impact on Yield MT/Hec)")
ax.set_title("Global Feature Importance (SHAP)")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "shap_bar.png", dpi=150)
plt.close()

# 3. Dependence: Rainfall vs Yield
feat_idx = FEATURES.index("monthly_rainfall_mm")
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(X_sample["monthly_rainfall_mm"], shap_values[:, feat_idx], alpha=0.5, color="#059669")
ax.axhline(0, color="red", linestyle="--")
ax.set_xlabel("Monthly Rainfall (mm)")
ax.set_ylabel("SHAP Value (Impact on Yield)")
ax.set_title("Rainfall Impact Curve on Tea Yield")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "shap_dependence_rainfall.png", dpi=150)
plt.close()

# 4. Save JSON for frontend
shap_importance = {
    display_names[i]: float(np.abs(shap_values[:, i]).mean())
    for i in range(len(FEATURES))
}
with open(ARTIFACT_DIR / "shap_importance.json", "w") as f:
    json.dump(shap_importance, f, indent=2)

print("\n=== SHAP Analysis Complete ===")
print("Saved plots to report_assets/")
