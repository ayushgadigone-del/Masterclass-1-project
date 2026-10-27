"""
train_model.py
--------------
Trains house-price models using only NumPy (no scikit-learn / scipy).
Saves:
  - models/house_price_model.pkl   (best model object via joblib)
  - models/model_metrics.json      (R2, MAE, RMSE)
  - models/eval_plot.png           (actual vs predicted + residuals)

Run once before launching the Streamlit app:
    python train_model.py
"""

import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Allow importing models_numpy when running from within house_price_app/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models_numpy import LinearRegressionNumpy, RandomForestRegressorNumpy

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DATA_PATH    = os.path.join(BASE_DIR, "data", "Housing.csv")
MODEL_DIR    = os.path.join(BASE_DIR, "models")
MODEL_PATH   = os.path.join(MODEL_DIR, "house_price_model.pkl")
METRICS_PATH = os.path.join(MODEL_DIR, "model_metrics.json")
EVAL_PLOT    = os.path.join(MODEL_DIR, "eval_plot.png")

os.makedirs(MODEL_DIR, exist_ok=True)

# ── Metric helpers ─────────────────────────────────────────────────────────────
def r2_score(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - ss_res / ss_tot if ss_tot != 0 else 0.0

def mae(y_true, y_pred):
    return float(np.mean(np.abs(y_true - y_pred)))

def rmse(y_true, y_pred):
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

# ── Load data ──────────────────────────────────────────────────────────────────
df = pd.read_csv(DATA_PATH)
print(f"Dataset shape: {df.shape}")
print(df.head())

FEATURES = ["area", "bedrooms"]
TARGET   = "price"

X_all = df[FEATURES].values.astype(float)
y_all = df[TARGET].values.astype(float)

# Standardise features (mean=0, std=1)
mu  = X_all.mean(axis=0)
std = X_all.std(axis=0) + 1e-8
X_scaled = (X_all - mu) / std

# Train / test split (80/20, deterministic)
rng    = np.random.default_rng(42)
idx    = rng.permutation(len(X_scaled))
split  = int(0.8 * len(idx))
tr, te = idx[:split], idx[split:]

X_train, y_train = X_scaled[tr], y_all[tr]
X_test,  y_test  = X_scaled[te], y_all[te]

# ── Train & evaluate models ────────────────────────────────────────────────────
models = [
    LinearRegressionNumpy(),
    RandomForestRegressorNumpy(n_estimators=80, max_depth=4, random_state=42),
]

results = {}
for mdl in models:
    mdl.fit(X_train, y_train)
    preds = mdl.predict(X_test)
    r2 = r2_score(y_test, preds)
    m  = mae(y_test, preds)
    r  = rmse(y_test, preds)
    results[mdl.name] = {"r2": round(r2, 4), "mae": round(m, 2), "rmse": round(r, 2)}
    print(f"{mdl.name:25s} | R2={r2:.4f}  MAE={m:,.0f}  RMSE={r:,.0f}")

# ── Pick best model ────────────────────────────────────────────────────────────
best_name = max(results, key=lambda n: results[n]["r2"])
print(f"\nBest model: {best_name}")
best_mdl   = next(m for m in models if m.name == best_name)
best_preds = best_mdl.predict(X_test)

# ── Save model + scaler params ─────────────────────────────────────────────────
save_obj = {
    "model":    best_mdl,
    "mu":       mu,
    "std":      std,
    "features": FEATURES,
}
joblib.dump(save_obj, MODEL_PATH)
print(f"Model saved -> {MODEL_PATH}")

# ── Save metrics JSON ──────────────────────────────────────────────────────────
metrics_out = {
    "best_model":    best_name,
    "features":      FEATURES,
    "train_samples": int(len(X_train)),
    "test_samples":  int(len(X_test)),
    "r2":            results[best_name]["r2"],
    "mae":           results[best_name]["mae"],
    "rmse":          results[best_name]["rmse"],
    "all_models":    results,
}
with open(METRICS_PATH, "w") as f:
    json.dump(metrics_out, f, indent=2)
print(f"Metrics saved -> {METRICS_PATH}")

# ── Evaluation plots ───────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle(f"Model Evaluation - {best_name}", fontsize=13, fontweight="bold")

axes[0].scatter(y_test, best_preds, color="#3b82d4", edgecolors="white", s=80, alpha=0.85)
lo = min(y_test.min(), best_preds.min()) * 0.95
hi = max(y_test.max(), best_preds.max()) * 1.05
axes[0].plot([lo, hi], [lo, hi], "r--", linewidth=1.5, label="Perfect fit")
axes[0].set_xlabel("Actual Price")
axes[0].set_ylabel("Predicted Price")
axes[0].set_title("Actual vs Predicted")
axes[0].legend()
axes[0].xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"Rs{x/1e6:.1f}M"))
axes[0].yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"Rs{x/1e6:.1f}M"))

residuals = y_test - best_preds
axes[1].hist(residuals / 1e6, bins=6, color="#7c5cd8", edgecolor="white")
axes[1].axvline(0, color="red", linestyle="--", linewidth=1.5)
axes[1].set_xlabel("Residual (Rs millions)")
axes[1].set_ylabel("Frequency")
axes[1].set_title("Residual Distribution")

plt.tight_layout()
plt.savefig(EVAL_PLOT, dpi=120)
plt.close()
print(f"Plot saved -> {EVAL_PLOT}")

print("\nTraining complete. Launch with:  streamlit run app.py")
