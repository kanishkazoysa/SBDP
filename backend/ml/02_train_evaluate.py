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
  - report_assets/ (evaluation plots)
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
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    mean_absolute_percentage_error
)
import lightgbm as lgb

# ── Paths ──────────────────────────────────────────────────────────────────────
ARTIFACT_DIR = Path(__file__).parent / "artifacts"
FIGURE_DIR   = Path(__file__).resolve().parents[2] / "report_assets"
PROCESSED    = ARTIFACT_DIR / "processed.csv"
MODEL_PKL    = ARTIFACT_DIR / "lgbm_model.pkl"
ENC_PKL      = ARTIFACT_DIR / "label_encoders.pkl"
FEAT_JSON    = ARTIFACT_DIR / "feature_info.json"

ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

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

# ── Plots ─────────────────────────────────────────────────────────────────────
y_pred_test = model.predict(X_test)

# 1. Actual vs Predicted
fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(y_test, y_pred_test, alpha=0.5, s=20, color="#10b981")
lims = [min(y_test.min(), y_pred_test.min()), max(y_test.max(), y_pred_test.max())]
ax.plot(lims, lims, "r--", linewidth=2, label="Perfect Forecast")
ax.set_xlabel("Actual Yield (MT / Hectare)")
ax.set_ylabel("Predicted Yield (MT / Hectare)")
ax.set_title("Tea Yield Forecasting Accuracy")
ax.legend()
plt.tight_layout()
plt.savefig(FIGURE_DIR / "actual_vs_predicted.png", dpi=150)
plt.close()

# 2. Residuals
residuals = y_pred_test - y_test
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(residuals, bins=50, color="#10b981", alpha=0.7, edgecolor="white")
ax.axvline(0, color="red", linestyle="--")
ax.set_xlabel("Residual (Prediction Error, MT)")
ax.set_ylabel("Frequency")
ax.set_title("Yield Prediction Error Distribution")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "residuals.png", dpi=150)
plt.close()

# 3. Feature importance
fi = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=True)
fig, ax = plt.subplots(figsize=(8, 6))
fi.plot(kind="barh", ax=ax, color="#10b981")
ax.set_title("Key Drivers of Tea Yield (Feature Importance)")
ax.set_xlabel("Importance (Gain)")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "feature_importance.png", dpi=150)
plt.close()

# 4. Metrics table
fig, ax = plt.subplots(figsize=(8, 4))
ax.axis("off")
table_data = [
    ["Metric",    "Train",           "Validation",      "Test"],
    ["MAE",       f"{train_metrics['MAE']:.4f}", f"{val_metrics['MAE']:.4f}", f"{test_metrics['MAE']:.4f}"],
    ["R2",        f"{train_metrics['R2']:.4f}",  f"{val_metrics['R2']:.4f}",   f"{test_metrics['R2']:.4f}"],
    ["MAPE",      f"{train_metrics['MAPE']:.2f}%", f"{val_metrics['MAPE']:.1f}%", f"{test_metrics['MAPE']:.1f}%"],
]
table = ax.table(cellText=table_data[1:], colLabels=table_data[0], loc="center", cellLoc="center")
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1.2, 2.5)
for j in range(4):
    table[(0, j)].set_facecolor("#10b981")
    table[(0, j)].set_text_props(color="white", fontweight="bold")
plt.title("Tea Yield Prediction Model Metrics", pad=20, fontsize=14, fontweight="bold")
plt.savefig(FIGURE_DIR / "metrics_table.png", dpi=150, bbox_inches="tight")
plt.close()

# 5. Correlation Heatmap
import seaborn as sns
plt.figure(figsize=(10, 8))
numeric_cols = df.select_dtypes(include=[np.number]).columns
corr = df[numeric_cols].corr()
sns.heatmap(corr, annot=True, cmap='RdYlGn', fmt=".2f", linewidths=0.5)
plt.title("Feature Correlation Heatmap")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "correlation_heatmap.png", dpi=150)
plt.close()

# 6. Learning Curve (Simulation from metrics if simple)
# LightGBM actually has evals_result_ but for now let's use the fit history if we had it.
# We will use the metrics to show the gap.
print("\n=== Additional Plots Generated ===")

print("\n=== Training complete ===")
print(f"Test R² : {test_metrics['R2']:.4f}")
print(f"Test MAE: {test_metrics['MAE']:.4f} MT")
