"""
02_train_evaluate.py
=====================
Sri Lanka Property Price Prediction
Algorithm: LightGBM Regressor (gradient-boosted decision trees)

Why LightGBM?
  - Not covered in standard ML lectures (which teach DT, LR, k-NN, SVM)
  - Handles categorical features natively (no one-hot needed)
  - Handles missing values natively
  - Extremely fast on tabular data
  - State-of-the-art performance for structured regression tasks

Outputs:
  - ml/artifacts/lgbm_model.pkl
  - ml/artifacts/label_encoders.pkl
  - ml/figures/  (evaluation plots)
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
df = pd.read_csv(PROCESSED)
print(f"Loaded {len(df):,} rows")

FEATURES = ["property_type", "location", "bedrooms", "bathrooms",
            "land_size_perches", "is_for_rent", "quality_tier", "is_furnished"]
TARGET   = "price_lkr"

X = df[FEATURES].copy()
y = np.log1p(df[TARGET])   # train on log-price for better distribution

# ── Encode categoricals ────────────────────────────────────────────────────────
cat_cols = ["property_type", "location"]
encoders = {}
for col in cat_cols:
    le = LabelEncoder()
    X[col] = le.fit_transform(X[col].astype(str))
    encoders[col] = le

with open(ENC_PKL, "wb") as f:
    pickle.dump(encoders, f)
print("Saved label encoders")

# ── Train / Validation / Test split  70 / 15 / 15 ─────────────────────────────
X_tmp,  X_test,  y_tmp,  y_test  = train_test_split(X, y, test_size=0.15, random_state=42)
X_train, X_val,  y_train, y_val  = train_test_split(X_tmp, y_tmp, test_size=0.15/0.85, random_state=42)

print(f"\nSplit sizes:")
print(f"  Train : {len(X_train):>5} ({len(X_train)*100//len(X):.0f}%)")
print(f"  Val   : {len(X_val):>5} ({len(X_val)*100//len(X):.0f}%)")
print(f"  Test  : {len(X_test):>5} ({len(X_test)*100//len(X):.0f}%)")

# ── LightGBM model ─────────────────────────────────────────────────────────────
# Hyperparameters chosen via domain knowledge + validation performance
params = {
    "objective":        "regression",
    "metric":           "rmse",
    "boosting_type":    "gbdt",
    "n_estimators":     1000,
    "learning_rate":    0.05,
    "num_leaves":       63,
    "max_depth":        -1,
    "min_child_samples": 20,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq":     5,
    "reg_alpha":        0.1,
    "reg_lambda":       0.1,
    "random_state":     42,
    "verbose":          -1,
}

model = lgb.LGBMRegressor(**params)

model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    callbacks=[
        lgb.early_stopping(stopping_rounds=50, verbose=False),
        lgb.log_evaluation(period=100),
    ],
    categorical_feature=cat_cols,
)

print(f"\nBest iteration: {model.best_iteration_}")

# ── Evaluation ─────────────────────────────────────────────────────────────────
def evaluate(name, y_true_log, y_pred_log):
    # Convert back to LKR for interpretable metrics
    y_true = np.expm1(y_true_log)
    y_pred = np.expm1(y_pred_log)
    mae   = mean_absolute_error(y_true, y_pred)
    rmse  = np.sqrt(mean_squared_error(y_true, y_pred))
    r2    = r2_score(y_true_log, y_pred_log)   # R² in log space
    mape  = mean_absolute_percentage_error(y_true, y_pred) * 100
    print(f"\n  [{name}]")
    print(f"    MAE   : Rs {mae:>15,.0f}")
    print(f"    RMSE  : Rs {rmse:>15,.0f}")
    print(f"    R² (log-space): {r2:.4f}")
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

y_pred_test_log = model.predict(X_test)
y_pred_test = np.expm1(y_pred_test_log)
y_test_lkr  = np.expm1(y_test)

# 1. Actual vs Predicted
fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(y_test_lkr / 1e6, y_pred_test / 1e6, alpha=0.3, s=15, color="#6366f1")
lims = [0, max(y_test_lkr.max(), y_pred_test.max()) / 1e6]
ax.plot(lims, lims, "r--", linewidth=1.5, label="Perfect prediction")
ax.set_xlabel("Actual Price (Rs. Million)")
ax.set_ylabel("Predicted Price (Rs. Million)")
ax.set_title("Actual vs Predicted Property Price (LKR)")
ax.legend()
ax.set_xlim(0, lims[1])
ax.set_ylim(0, lims[1])
plt.tight_layout()
plt.savefig(FIGURE_DIR / "actual_vs_predicted.png", dpi=150)
plt.close()
print("Saved actual_vs_predicted.png")

# 2. Residuals distribution
residuals = y_pred_test - y_test_lkr
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(residuals / 1e6, bins=60, color="#6366f1", alpha=0.7, edgecolor="white")
ax.axvline(0, color="red", linestyle="--", linewidth=1.5)
ax.set_xlabel("Residual (Predicted - Actual, Rs. Million)")
ax.set_ylabel("Frequency")
ax.set_title("Residual Distribution")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "residuals.png", dpi=150)
plt.close()
print("Saved residuals.png")

# 3. Feature importance
fi = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=True)
fig, ax = plt.subplots(figsize=(8, 5))
colors = ["#6366f1" if i >= len(fi) - 3 else "#94a3b8" for i in range(len(fi))]
fi.plot(kind="barh", ax=ax, color=colors)
ax.set_title("LightGBM Feature Importance (Gain)")
ax.set_xlabel("Importance")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "feature_importance.png", dpi=150)
plt.close()
print("Saved feature_importance.png")

# 4. Price distribution by property type
fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=False)
prop_types = ["Land", "House", "Apartment"]
colors_map = {"Land": "#10b981", "House": "#6366f1", "Apartment": "#f59e0b"}
for ax, pt in zip(axes, prop_types):
    subset = df[df["property_type"] == pt]["price_lkr"] / 1e6
    ax.hist(subset, bins=40, color=colors_map[pt], alpha=0.8, edgecolor="white")
    ax.set_title(f"{pt} Prices")
    ax.set_xlabel("Price (Rs. Million)")
    ax.set_ylabel("Count")
plt.suptitle("Property Price Distribution by Type", y=1.02)
plt.tight_layout()
plt.savefig(FIGURE_DIR / "price_by_type.png", dpi=150)
plt.close()
print("Saved price_by_type.png")

# 5. Metrics comparison table plot
fig, ax = plt.subplots(figsize=(8, 3))
ax.axis("off")
table_data = [
    ["Metric",    "Train",                       "Validation",                 "Test"],
    ["MAE",       f"Rs {train_metrics['MAE']/1e6:.2f}M", f"Rs {val_metrics['MAE']/1e6:.2f}M", f"Rs {test_metrics['MAE']/1e6:.2f}M"],
    ["RMSE",      f"Rs {train_metrics['RMSE']/1e6:.2f}M", f"Rs {val_metrics['RMSE']/1e6:.2f}M", f"Rs {test_metrics['RMSE']/1e6:.2f}M"],
    ["R²",        f"{train_metrics['R2']:.4f}",  f"{val_metrics['R2']:.4f}",   f"{test_metrics['R2']:.4f}"],
    ["MAPE",      f"{train_metrics['MAPE']:.1f}%", f"{val_metrics['MAPE']:.1f}%", f"{test_metrics['MAPE']:.1f}%"],
]
table = ax.table(cellText=table_data[1:], colLabels=table_data[0],
                 loc="center", cellLoc="center")
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1.4, 2)
for j in range(4):
    table[(0, j)].set_facecolor("#6366f1")
    table[(0, j)].set_text_props(color="white", fontweight="bold")
plt.title("Model Performance Metrics", pad=20, fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "metrics_table.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved metrics_table.png")

print("\n=== Training complete ===")
print(f"Test R² : {test_metrics['R2']:.4f}")
print(f"Test MAE: Rs {test_metrics['MAE']:,.0f}")
