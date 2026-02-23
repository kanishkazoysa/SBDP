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
PROCESSED    = ARTIFACT_DIR / "processed.csv"

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

# ── Summary Statistics ─────────────────────────────────────────────────────────
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

print("\n=== SHAP Importance (Mean |SHAP|) ===")
for i, name in enumerate(display_names):
    imp = np.abs(shap_values[:, i]).mean()
    print(f"  {name:25}: {imp:.4f}")

# Save JSON for frontend
shap_importance = {
    display_names[i]: float(np.abs(shap_values[:, i]).mean())
    for i in range(len(FEATURES))
}
with open(ARTIFACT_DIR / "shap_importance.json", "w") as f:
    json.dump(shap_importance, f, indent=2)

print("\n=== SHAP Analysis Complete ===")
