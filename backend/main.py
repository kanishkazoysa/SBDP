"""
FastAPI Backend — Sri Lanka Bus Delay Predictor
Run:  uvicorn main:app --reload  (from the backend/ directory)

POST /predict  — accepts trip details, returns prediction + SHAP values
GET  /health   — health check
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from datetime import date as date_type

import joblib
import numpy as np
import pandas as pd
import shap

# ── Load model & artifacts ────────────────────────────────────────────────────
ARTIFACTS = Path(__file__).parent / "artifacts"

model = joblib.load(ARTIFACTS / "lgbm_model.pkl")
art   = joblib.load(ARTIFACTS / "preprocessed_data.pkl")

FEATURES   = art["features"]
FEAT_NAMES = art["feature_display_names"]
ENCODINGS  = art["encodings"]

explainer = shap.TreeExplainer(model)

# ── Reference data ────────────────────────────────────────────────────────────
ROUTES = {
    "01":  {"distance": 116, "duration": {"Normal": 210, "Semi Luxury": 185, "Luxury": 165}},
    "32":  {"distance": 119, "duration": {"Normal": 195, "Semi Luxury": 170, "Luxury": 150}},
    "04":  {"distance": 94,  "duration": {"Normal": 150, "Semi Luxury": 130, "Luxury": 110}},
    "04-2":{"distance": 37,  "duration": {"Normal": 75,  "Semi Luxury": 65,  "Luxury": 55}},
    "98":  {"distance": 100, "duration": {"Normal": 180, "Semi Luxury": 160, "Luxury": 140}},
}

POYA_DAYS = {
    "2024-01-25","2024-02-24","2024-03-25","2024-04-23","2024-05-23","2024-06-21",
    "2024-07-21","2024-08-19","2024-09-17","2024-10-17","2024-11-15","2024-12-15",
    "2025-01-13","2025-02-12","2025-03-13","2025-04-12","2025-05-12","2025-06-11",
    "2025-07-10","2025-08-09","2025-09-07","2025-10-06","2025-11-05","2025-12-04",
}

PUBLIC_HOLIDAYS = {
    "2024-01-15","2024-02-04","2024-03-29","2024-04-11","2024-04-12","2024-04-13",
    "2024-04-14","2024-05-01","2024-05-23","2024-05-24","2024-06-17","2024-06-21",
    "2024-07-21","2024-08-19","2024-09-16","2024-09-17","2024-10-17","2024-10-31",
    "2024-11-15","2024-12-15","2024-12-25",
    "2025-01-14","2025-02-04","2025-04-14","2025-05-01","2025-05-12","2025-12-25",
}

FESTIVAL_PERIODS = [
    ("2024-04-10","2024-04-16","Sinhala New Year"),
    ("2024-05-20","2024-05-26","Vesak"),
    ("2024-06-18","2024-06-23","Poson"),
    ("2024-07-24","2024-08-10","Kandy Perahera"),
    ("2024-10-29","2024-11-02","Deepavali"),
    ("2024-12-23","2024-12-27","Christmas"),
    ("2025-04-10","2025-04-16","Sinhala New Year"),
    ("2025-05-10","2025-05-16","Vesak"),
]

CLASS_NAMES = ["On Time", "Slightly Delayed", "Heavily Delayed"]


# ── Helpers ────────────────────────────────────────────────────────────────────
def get_festival(date_str: str):
    for start, end, name in FESTIVAL_PERIODS:
        if start <= date_str <= end:
            return True, name
    return False, ""

def time_slot(hour: int) -> str:
    if 5 <= hour < 9:   return "Morning Peak"
    if 9 <= hour < 12:  return "Morning Off-Peak"
    if 12 <= hour < 16: return "Afternoon"
    if 16 <= hour < 20: return "Evening Peak"
    return "Night"


# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(title="Sri Lanka Bus Delay Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request schema ─────────────────────────────────────────────────────────────
class TripRequest(BaseModel):
    route_no: str            # "01", "32", "04", "04-2", "98"
    bus_type: str            # "Normal", "Semi Luxury", "Luxury"
    departure_date: str      # "YYYY-MM-DD"
    departure_time: str      # "HH:MM"
    weather: str             # "Clear" | "Cloudy" | "Light Rain" | "Moderate Rain" | "Heavy Rain"
    crowding_level: str      # "Low" | "Medium" | "High"
    departure_delay_min: int = 0


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "model": "LightGBM", "features": len(FEATURES)}


@app.post("/predict")
def predict(trip: TripRequest):
    # Validate route
    if trip.route_no not in ROUTES:
        raise HTTPException(400, f"Unknown route_no: {trip.route_no}")

    route_info = ROUTES[trip.route_no]
    if trip.bus_type not in route_info["duration"]:
        raise HTTPException(400, f"Unknown bus_type: {trip.bus_type}")

    # Parse date / time
    try:
        d    = trip.departure_date          # "YYYY-MM-DD"
        h, m = map(int, trip.departure_time.split(":"))
        year, mo, day = map(int, d.split("-"))
        from datetime import date as dt_date
        weekday = dt_date(year, mo, day).weekday()   # 0=Mon
    except Exception as e:
        raise HTTPException(400, f"Invalid date/time: {e}")

    # Calendar flags
    is_weekend  = int(weekday >= 5)
    is_poya     = int(d in POYA_DAYS)
    is_holiday  = int(d in PUBLIC_HOLIDAYS)
    is_fest, _  = get_festival(d)
    is_fest     = int(is_fest)

    slot = time_slot(h)
    scheduled_duration = route_info["duration"][trip.bus_type]

    # Encode
    enc = ENCODINGS
    row = {
        "route_no_enc":            enc["route_no"][trip.route_no],
        "route_distance_km":       route_info["distance"],
        "bus_type_enc":            enc["bus_type"][trip.bus_type],
        "scheduled_duration_min":  scheduled_duration,
        "dep_hour":                h,
        "dep_minute":              m,
        "departure_delay_min":     trip.departure_delay_min,
        "time_of_day_enc":         enc["time_of_day"][slot],
        "weather_enc":             enc["weather"][trip.weather],
        "crowding_level_enc":      enc["crowding_level"][trip.crowding_level],
        "is_weekend":              is_weekend,
        "is_public_holiday":       is_holiday,
        "is_poya_day":             is_poya,
        "is_festival_period":      is_fest,
        "month":                   mo,
        "day_of_week_num":         weekday,
    }

    X = pd.DataFrame([row], columns=FEATURES)

    # Predict
    proba    = model.predict_proba(X)[0]
    pred_cls = int(np.argmax(proba))

    # SHAP
    sv     = explainer.shap_values(X.rename(columns=dict(zip(FEATURES, FEAT_NAMES))))
    sv_arr = np.array(sv)

    if sv_arr.ndim == 3 and sv_arr.shape[0] == 1:
        sv_class = sv_arr[0, :, pred_cls].tolist()
    elif sv_arr.ndim == 3:
        sv_class = sv_arr[pred_cls, 0, :].tolist()
    else:
        sv_class = sv_arr[0].tolist()

    exp_vals = explainer.expected_value
    if hasattr(exp_vals, "__len__"):
        base_val = float(exp_vals[pred_cls])
    else:
        base_val = float(exp_vals)

    return {
        "prediction":     CLASS_NAMES[pred_cls],
        "pred_class_idx": pred_cls,
        "probabilities":  [round(float(p), 4) for p in proba],
        "class_names":    CLASS_NAMES,
        "shap_values":    [round(v, 4) for v in sv_class],
        "shap_base":      round(base_val, 4),
        "feature_names":  FEAT_NAMES,
        "meta": {
            "is_weekend":       bool(is_weekend),
            "is_poya":          bool(is_poya),
            "is_holiday":       bool(is_holiday),
            "is_festival":      bool(is_fest),
            "time_slot":        slot,
            "scheduled_duration_min": scheduled_duration,
        },
    }
