"""
backend/main.py
================
Sri Lanka Property Price Prediction API
FastAPI backend — LightGBM model
Run:  uvicorn main:app --reload  (from backend/ directory)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import pickle
import json
from pathlib import Path

app = FastAPI(title="Sri Lanka Property Price Predictor")

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

FEATURES = ["property_type", "location", "bedrooms", "bathrooms",
            "land_size_perches", "is_for_rent"]

known_locations = list(encoders["location"].classes_)
known_types     = list(encoders["property_type"].classes_)

# ── Request schema ─────────────────────────────────────────────────────────────
class PropertyInput(BaseModel):
    property_type:     str
    location:          str
    bedrooms:          float | None = None
    bathrooms:         float | None = None
    land_size_perches: float | None = None
    is_for_rent:       int = 0

# ── Helper ─────────────────────────────────────────────────────────────────────
def safe_encode(le, value: str, fallback: str = None):
    classes = list(le.classes_)
    if value in classes:
        return le.transform([value])[0]
    if fallback and fallback in classes:
        return le.transform([fallback])[0]
    return 0

def fmt_price(v: float) -> str:
    if v >= 1_000_000:
        return f"Rs. {v/1_000_000:.1f}M"
    return f"Rs. {v:,.0f}"

# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "model": "LightGBM Property Price Predictor"}

@app.get("/meta")
def get_meta():
    return {
        "locations":       known_locations,
        "property_types":  known_types,
        "metrics":         metrics["test"],
        "dataset_size":    feature_info["n_rows"],
        "shap_importance": shap_importance,
        "price_stats":     feature_info["price_stats"],
    }

@app.post("/predict")
def predict(prop: PropertyInput):
    try:
        pt_enc  = safe_encode(encoders["property_type"], prop.property_type)
        loc_enc = safe_encode(encoders["location"],      prop.location, "Colombo")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    import pandas as pd
    X = pd.DataFrame([{
        "property_type":     pt_enc,
        "location":          loc_enc,
        "bedrooms":          prop.bedrooms          if prop.bedrooms          is not None else np.nan,
        "bathrooms":         prop.bathrooms         if prop.bathrooms         is not None else np.nan,
        "land_size_perches": prop.land_size_perches if prop.land_size_perches is not None else np.nan,
        "is_for_rent":       prop.is_for_rent,
    }])

    log_pred = float(model.predict(X)[0])
    price    = float(np.expm1(log_pred))

    # Confidence interval: ±1 log-RMSE from validation
    log_rmse = 0.86
    price_lo = float(np.expm1(log_pred - log_rmse))
    price_hi = float(np.expm1(log_pred + log_rmse))

    shap_bar = [
        {"feature": feat, "importance": round(imp, 4)}
        for feat, imp in sorted(shap_importance.items(), key=lambda x: -x[1])
    ]

    return {
        "predicted_price":  price,
        "price_formatted":  fmt_price(price),
        "price_range_low":  price_lo,
        "price_range_high": price_hi,
        "range_low_fmt":    fmt_price(price_lo),
        "range_high_fmt":   fmt_price(price_hi),
        "shap_features":    shap_bar,
        "model_r2":         round(metrics["test"]["R2"], 4),
        "model_mae":        metrics["test"]["MAE"],
    }
