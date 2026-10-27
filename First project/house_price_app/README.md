# 🏠 House Price Prediction App

**GitHub:** [Open on GitHub](https://github.com/ayushgadigone-del/Masterclass-1-project/tree/main/First%20project/house_price_app)

A Streamlit web app that predicts house prices based on area and number of bedrooms. The ML models are built from scratch using only NumPy — no scikit-learn used for training.

---

## Features

- **Interactive sliders** — adjust area (sq ft) and bedrooms in the sidebar, get an instant price prediction
- **Price range estimate** — ±10% confidence band shown alongside every prediction
- **Data Insights tab** — dataset overview, price distribution, area vs price scatter, correlation heatmap
- **Model Performance tab** — R², MAE, RMSE metrics and a comparison table across all trained models
- **Evaluation plots** — actual vs predicted and residual distribution charts

---

## Project Structure

```
house_price_app/
├── app.py                              # Streamlit frontend
├── train_model.py                      # Model training script
├── models_numpy.py                     # LinearRegression & RandomForest from scratch (NumPy)
├── intro.py                            # Standalone intro/demo script
├── requirements.txt                    # Python dependencies
├── Housing.csv                         # Raw dataset (root-level copy)
├── data/
│   └── Housing.csv                     # Training dataset
├── models/
│   ├── house_price_model.pkl           # Saved best model (joblib)
│   ├── model_metrics.json              # R², MAE, RMSE for all models
│   ├── eval_plot.png                   # Actual vs predicted + residual plot
│   ├── dataset.json                    # Dataset metadata
│   └── lookup.json                     # Feature lookup table
└── house-price-prediction-project-report.html   # Full project report
```

---

## Model Details

| Property | Value |
|---|---|
| Algorithm | Linear Regression & Random Forest (NumPy, from scratch) |
| Features | `area` (sq ft), `bedrooms` |
| Target | `price` (₹) |
| Train / Test split | 80 / 20 (seed = 42) |
| Feature scaling | Standardisation (mean = 0, std = 1) |
| Best model selection | Highest R² on test set |
| Saved artefacts | `models/house_price_model.pkl`, `models/model_metrics.json` |

---

## Getting Started

### 1. Install dependencies

```bash
cd "First project/house_price_app"
pip install -r requirements.txt
```

### 2. Train the model

Run this once before launching the app. It saves the model, metrics, and evaluation plot into the `models/` folder.

```bash
python train_model.py
```

Expected output:
```
Dataset shape: (545, 13)
LinearRegressionNumpy      | R2=0.xxxx  MAE=...  RMSE=...
RandomForestRegressorNumpy | R2=0.xxxx  MAE=...  RMSE=...

Best model: RandomForestRegressorNumpy
Model saved  -> models/house_price_model.pkl
Metrics saved -> models/model_metrics.json
Plot saved   -> models/eval_plot.png

Training complete. Launch with:  streamlit run app.py
```

### 3. Launch the app

```bash
streamlit run app.py
```

Then open **http://localhost:8501** in your browser.

---

## Dependencies

```
pandas>=2.0
numpy>=1.24
scikit-learn>=1.3
matplotlib>=3.7
seaborn>=0.12
streamlit>=1.32
joblib>=1.3
```

Install all at once:

```bash
pip install -r requirements.txt
```

---

## Requirements

- Python 3.8+
- pip
