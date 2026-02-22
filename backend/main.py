"""
backend/main.py
================
Sri Lanka Tea Yield Prediction API
FastAPI backend — LightGBM model
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import pandas as pd
import pickle
import json
import shap
from pathlib import Path

app = FastAPI(title="Sri Lanka Tea Yield Forecaster")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load artifacts ─────────────────────────────────────────────────────────────
ARTIFACT_DIR = Path(__file__).parent / "ml" / "artifacts"

with open(ARTIFACT_DIR / "lgbm_model.pkl", "rb") as f:
    model = pickle.load(f)
with open(ARTIFACT_DIR / "label_encoders.pkl", "rb") as f:
    encoders = pickle.load(f)
with open(ARTIFACT_DIR / "feature_info.json") as f:
    feature_info = json.load(f)
with open(ARTIFACT_DIR / "shap_importance.json") as f:
    shap_importance = json.load(f)
with open(ARTIFACT_DIR / "metrics.json") as f:
    metrics = json.load(f)

# Initialize SHAP explainer
explainer = shap.TreeExplainer(model)
feature_names = feature_info["features"]

# ── Request schemas ────────────────────────────────────────────────────────────
class TeaYieldInput(BaseModel):
    district:            str
    elevation:           str
    monthly_rainfall_mm: float
    avg_temp_c:          float
    soil_nitrogen:       float
    soil_phosphorus:     float
    soil_potassium:      float
    soil_ph:             float
    fertilizer_type:     str
    drainage_quality:    str

# ── Helpers ────────────────────────────────────────────────────────────────────
def safe_encode(le, value: str, fallback: str = None):
    classes = list(le.classes_)
    if value in classes:
        return le.transform([value])[0]
    return 0

# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "model": "Tea Yield Forecast AI"}

@app.get("/meta")
def get_meta():
    return {
        "districts":          feature_info["districts"],
        "elevations":         feature_info["elevations"],
        "fertilizer_types":    feature_info["fertilizer_types"],
        "drainage_qualities": feature_info["drainage_qualities"],
        "metrics":            metrics["test"],
        "dataset_size":       feature_info["n_rows"],
        "shap_importance":    shap_importance,
        "yield_stats":        feature_info["yield_stats"],
    }

@app.post("/predict")
def predict(inp: TeaYieldInput):
    try:
        dist_enc  = safe_encode(encoders["district"],        inp.district)
        elev_enc  = safe_encode(encoders["elevation"],       inp.elevation)
        fert_enc  = safe_encode(encoders["fertilizer_type"], inp.fertilizer_type)
        drain_enc = safe_encode(encoders["drainage_quality"], inp.drainage_quality)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    X_df = pd.DataFrame([{
        "district":            dist_enc,
        "elevation":           elev_enc,
        "monthly_rainfall_mm": inp.monthly_rainfall_mm,
        "avg_temp_c":          inp.avg_temp_c,
        "soil_nitrogen":       inp.soil_nitrogen,
        "soil_phosphorus":     inp.soil_phosphorus,
        "soil_potassium":      inp.soil_potassium,
        "soil_ph":             inp.soil_ph,
        "fertilizer_type":     fert_enc,
        "drainage_quality":    drain_enc,
    }])

    # LightGBM predict
    yield_pred = float(model.predict(X_df)[0])
    
    # Calculate Local SHAP
    local_shap = explainer.shap_values(X_df)[0]
    
    friendly_names = {
        "district": "Location (District)",
        "elevation": "Elevation Zone",
        "monthly_rainfall_mm": "Rainfall Intensity",
        "avg_temp_c": "Ambient Temperature",
        "soil_nitrogen": "Nitrogen Level",
        "soil_phosphorus": "Phosphorus Level",
        "soil_potassium": "Potassium Level",
        "soil_ph": "Soil Acidity (pH)",
        "fertilizer_type": "Fertilization Choice",
        "drainage_quality": "Soil Drainage",
    }
    
    shap_bar = []
    for i, name in enumerate(feature_names):
        shap_bar.append({
            "feature": friendly_names.get(name, name.replace("_", " ").title()),
            "importance": float(local_shap[i])
        })
    
    shap_bar = sorted(shap_bar, key=lambda x: abs(x["importance"]), reverse=True)

    return {
        "predicted_yield":  round(yield_pred, 3),
        "yield_unit":       "Metric Tons per Hectare (MT/Hec)",
        "shap_features":    shap_bar,
        "model_r2":         round(metrics["test"]["R2"], 4),
        "model_mae":        round(metrics["test"]["MAE"], 4),
    }
