"""
backend/main.py
================
Sri Lanka Property Price Prediction API
FastAPI backend — LightGBM model + Forecast model
Run:  uvicorn main:app --reload  (from backend/ directory)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import pandas as pd
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

# Current price model
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

# Forecast model
with open(ARTIFACT_DIR / "forecast_model.pkl", "rb") as f:
    forecast_model = pickle.load(f)
with open(ARTIFACT_DIR / "forecast_encoders.pkl", "rb") as f:
    forecast_encoders = pickle.load(f)
with open(ARTIFACT_DIR / "district_forecasts.json") as f:
    district_forecasts = json.load(f)
with open(ARTIFACT_DIR / "forecast_metrics.json") as f:
    forecast_metrics = json.load(f)

df_econ_all = pd.read_csv(ARTIFACT_DIR / "economic_data_all.csv")

FEATURES = ["property_type", "location", "bedrooms", "bathrooms",
            "land_size_perches", "is_for_rent", "quality_tier", "is_furnished"]

known_locations    = list(encoders["location"].classes_)
known_types        = list(encoders["property_type"].classes_)
forecast_districts = sorted(district_forecasts.keys())

# ── Request schemas ────────────────────────────────────────────────────────────
class PropertyInput(BaseModel):
    property_type:     str
    location:          str
    bedrooms:          float | None = None
    bathrooms:         float | None = None
    land_size_perches: float | None = None
    is_for_rent:       int = 0
    quality_tier:      int = 0    # 0=Standard,1=Modern,2=Luxury,3=Super Luxury
    is_furnished:      int = 0    # 0=Unknown,1=Semi-Furnished,2=Fully Furnished

class ForecastInput(BaseModel):
    district:          str
    property_type:     str
    land_size_perches: float | None = None
    bedrooms:          float | None = None

# ── Helpers ────────────────────────────────────────────────────────────────────
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
        "locations":          known_locations,
        "property_types":     known_types,
        "metrics":            metrics["test"],
        "dataset_size":       feature_info["n_rows"],
        "shap_importance":    shap_importance,
        "price_stats":        feature_info["price_stats"],
        "forecast_districts": forecast_districts,
    }

@app.post("/predict")
def predict(prop: PropertyInput):
    try:
        pt_enc  = safe_encode(encoders["property_type"], prop.property_type)
        loc_enc = safe_encode(encoders["location"],      prop.location, "Colombo")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    X = pd.DataFrame([{
        "property_type":     pt_enc,
        "location":          loc_enc,
        "bedrooms":          prop.bedrooms          if prop.bedrooms          is not None else np.nan,
        "bathrooms":         prop.bathrooms         if prop.bathrooms         is not None else np.nan,
        "land_size_perches": prop.land_size_perches if prop.land_size_perches is not None else np.nan,
        "is_for_rent":       prop.is_for_rent,
        "quality_tier":      prop.quality_tier,
        "is_furnished":      prop.is_furnished,
    }])

    log_pred = float(model.predict(X)[0])
    price    = float(np.expm1(log_pred))
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

@app.post("/forecast")
def forecast(inp: ForecastInput):
    district = inp.district
    ptype    = inp.property_type

    # Use precomputed district forecasts (fast path)
    if district in district_forecasts and ptype in district_forecasts[district]:
        precomputed = district_forecasts[district][ptype]
        prices      = precomputed["prices"]
        growth_4yr  = precomputed["growth_4yr_pct"]
    else:
        # Live predict with forecast model
        try:
            loc_enc  = safe_encode(forecast_encoders["location"],      district, "Colombo")
            type_enc = safe_encode(forecast_encoders["property_type"], ptype,    "Land")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        prices = {}
        for year in [2026, 2027, 2028, 2029, 2030]:
            econ_row = df_econ_all[df_econ_all["year"] == year]
            if len(econ_row) == 0:
                continue
            econ = econ_row.iloc[0]
            row = pd.DataFrame([{
                "year":                 year,
                "month":                6,
                "location":             loc_enc,
                "property_type":        type_enc,
                "bedrooms":             inp.bedrooms if inp.bedrooms is not None else np.nan,
                "bathrooms":            np.nan,
                "land_size_perches":    inp.land_size_perches if inp.land_size_perches else np.nan,
                "inflation_pct":        econ["inflation_pct"],
                "lending_rate_pct":     econ["lending_rate_pct"],
                "usd_lkr":              econ["usd_lkr"],
                "gdp_growth_pct":       econ["gdp_growth_pct"],
                "policy_rate_pct":      econ["policy_rate_pct"],
                "property_price_index": econ["property_price_index"],
            }])
            log_price = float(forecast_model.predict(row)[0])
            prices[str(year)] = round(float(np.expm1(log_price)))

        p2026 = prices.get("2026", 1)
        p2030 = prices.get("2030", p2026)
        growth_4yr = round((p2030 - p2026) / p2026 * 100, 1) if p2026 > 0 else 0

    # Build year-by-year result
    yearly     = []
    base_price = prices.get("2026", list(prices.values())[0] if prices else 1)
    for yr in sorted(prices.keys()):
        p   = prices[yr]
        yoy = round((p - base_price) / base_price * 100, 1) if base_price > 0 else 0
        yearly.append({
            "year":                   int(yr),
            "price":                  p,
            "price_formatted":        fmt_price(p),
            "growth_from_2026_pct":   yoy,
        })

    # Investment signal
    if growth_4yr >= 20:
        signal  = "BUY"
        insight = f"Strong opportunity! {district} {ptype} prices forecast to grow {growth_4yr:.0f}% by 2030."
    elif growth_4yr >= 10:
        signal  = "HOLD"
        insight = f"Moderate growth expected. {district} {ptype} prices may rise {growth_4yr:.0f}% by 2030."
    else:
        signal  = "WAIT"
        insight = f"Slow growth in {district}. {ptype} prices may grow only {growth_4yr:.0f}% by 2030."

    return {
        "district":           district,
        "property_type":      ptype,
        "yearly":             yearly,
        "growth_4yr_pct":     growth_4yr,
        "investment_signal":  signal,
        "insight":            insight,
        "model_r2":           round(forecast_metrics["test_r2"], 4),
    }

@app.get("/forecast/districts")
def get_forecast_districts():
    return {
        "districts":      forecast_districts,
        "property_types": ["Land", "House", "Apartment"],
        "years":          [2026, 2027, 2028, 2029, 2030],
    }
