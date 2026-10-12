# 🏠 House Price Prediction App

A machine-learning web app built with **Python**, **Scikit-learn**, and **Streamlit** that predicts house prices from the Housing dataset.

## Project Structure

```
house_price_app/
├── data/
│   └── Housing.csv          # Dataset (price, area, bedrooms)
├── models/
│   ├── house_price_model.pkl  # Trained model pipeline (auto-generated)
│   ├── model_metrics.json     # Evaluation metrics   (auto-generated)
│   └── eval_plot.png          # Evaluation chart     (auto-generated)
├── train_model.py             # ML backend: trains & saves the model
├── app.py                     # Streamlit frontend
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Train the model
```bash
python train_model.py
```
This will compare **Linear Regression**, **Random Forest**, and **Gradient Boosting**, pick the best one, and save it to `models/`.

### 3. Launch the app
```bash
streamlit run app.py
```
Open **http://localhost:8501** in your browser.

## Features

| Tab | Content |
|-----|---------|
| 🔮 Prediction | Adjust area & bedrooms with sliders → instant price prediction with ±10% range |
| 📊 Data Insights | Distribution plots, avg price by bedrooms, area vs price scatter, correlation heatmap |
| 📈 Model Performance | R², MAE, RMSE comparison table, actual vs predicted scatter, residual histogram |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit, Matplotlib, Seaborn |
| Backend / ML | Scikit-learn (RandomForest / GradientBoosting / LinearRegression) |
| Data | Pandas, NumPy |
| Model serialisation | Joblib |
