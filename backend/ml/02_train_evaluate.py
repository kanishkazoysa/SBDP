"""
02_train_evaluate.py
=====================
Tea Yield Prediction in Sri Lanka
Algorithm: LightGBM Regressor

This script trains a high-precision regressor to forecast the next month's 
tea harvest based on environmental and soil variables.

Outputs:
  - ml/artifacts/lgbm_model.pkl
  - ml/artifacts/label_encoders.pkl
"""

import pandas as pd
import numpy as np
import json
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    mean_absolute_percentage_error
)
import lightgbm as lgb

# ── Paths ──────────────────────────────────────────────────────────────────────
ARTIFACT_DIR = Path(__file__).parent / "artifacts"
PROCESSED    = ARTIFACT_DIR / "processed.csv"
MODEL_PKL    = ARTIFACT_DIR / "lgbm_model.pkl"
ENC_PKL      = ARTIFACT_DIR / "label_encoders.pkl"
FEAT_JSON    = ARTIFACT_DIR / "feature_info.json"

ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────────
if not PROCESSED.exists():
    print(f"ERROR: Processed data not found at {PROCESSED}")
    exit(1)

df = pd.read_csv(PROCESSED)
print(f"Loaded {len(df):,} rows")

with open(FEAT_JSON, "r") as f:
    feat_info = json.load(f)

FEATURES = feat_info["features"]
TARGET   = feat_info["target"]
cat_cols = feat_info["categorical_features"]

X = df[FEATURES].copy()
y = df[TARGET]

# ── Encode categoricals ────────────────────────────────────────────────────────
encoders = {}
for col in cat_cols:
    le = LabelEncoder()
    X[col] = le.fit_transform(X[col].astype(str))
    encoders[col] = le

with open(ENC_PKL, "wb") as f:
    pickle.dump(encoders, f)
print("Saved label encoders")

# ── Train / Validation / Test split ─────────────────────────────
X_tmp,  X_test,  y_tmp,  y_test  = train_test_split(X, y, test_size=0.15, random_state=42)
X_train, X_val,  y_train, y_val  = train_test_split(X_tmp, y_tmp, test_size=0.15/0.85, random_state=42)

print(f"\nSplit sizes:")
print(f"  Train : {len(X_train)} rows")
print(f"  Val   : {len(X_val)} rows")
print(f"  Test  : {len(X_test)} rows")

# ── LightGBM model ─────────────────────────────────────────────────────────────
params = {
    "objective":        "huber", 
    "metric":           "mae",
    "boosting_type":    "gbdt",
    "n_estimators":     2000,
    "learning_rate":    0.05,
    "num_leaves":       31,
    "max_depth":        8,
    "min_child_samples": 10,
    "feature_fraction": 0.9,
    "bagging_fraction": 0.9,
    "bagging_freq":     5,
    "random_state":     42,
    "verbose":          -1,
}

model = lgb.LGBMRegressor(**params)

model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    callbacks=[
        lgb.early_stopping(stopping_rounds=100, verbose=False),
        lgb.log_evaluation(period=100),
    ],
    categorical_feature=cat_cols,
)

print(f"\nBest iteration: {model.best_iteration_}")

# ── Evaluation ─────────────────────────────────────────────────────────────────
def evaluate(name, y_true, y_pred):
    mae   = mean_absolute_error(y_true, y_pred)
    rmse  = np.sqrt(mean_squared_error(y_true, y_pred))
    r2    = r2_score(y_true, y_pred)
    mape  = mean_absolute_percentage_error(y_true, y_pred) * 100
    print(f"\n  [{name}]")
    print(f"    MAE   : {mae:.4f} MT")
    print(f"    RMSE  : {rmse:.4f} MT")
    print(f"    R²    : {r2:.4f}")
    print(f"    MAPE  : {mape:.2f}%")
    return {"MAE": float(mae), "RMSE": float(rmse), "R2": float(r2), "MAPE": float(mape)}

print("\n=== Model Evaluation ===")
train_metrics = evaluate("Train",      y_train, model.predict(X_train))
val_metrics   = evaluate("Validation", y_val,   model.predict(X_val))
test_metrics  = evaluate("Test",       y_test,  model.predict(X_test))

# Save metrics
metrics = {
    "train": train_metrics,
    "val":   val_metrics,
    "test":  test_metrics,
    "best_iteration": int(model.best_iteration_),
    "hyperparameters": {k: v for k, v in params.items() if k != "verbose"},
}
with open(ARTIFACT_DIR / "metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

# ── Save model ─────────────────────────────────────────────────────────────────
with open(MODEL_PKL, "wb") as f:
    pickle.dump(model, f)
print(f"\nSaved model -> {MODEL_PKL}")

# ── Evaluation Summary ─────────────────────────────────────────────────────────
y_pred_test = model.predict(X_test)

print("\n=== Model Metrics Summary ===")
print(f"  MAE   : {test_metrics['MAE']:.4f}")
print(f"  RMSE  : {test_metrics['RMSE']:.4f}")
print(f"  R²    : {test_metrics['R2']:.4f}")
print(f"  MAPE  : {test_metrics['MAPE']:.2f}%")

# ── Training complete ──────────────────────────────────────────────────────────

print("\n=== Training complete ===")
print(f"Test R² : {test_metrics['R2']:.4f}")
print(f"Test MAE: {test_metrics['MAE']:.4f} MT")
