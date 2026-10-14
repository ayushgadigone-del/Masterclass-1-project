# CSRBOX IBM AI — ML Projects

Two machine learning projects built with Python and IBM Watson/Scikit-learn.

---

## Projects

###  House Price Prediction App
Located in house_price_app/

A Flask web application that predicts house prices based on features like area, bedrooms, bathrooms, and location.

- **Backend:** Python / Flask (pp.py)
- **Model:** Trained linear regression model (models/house_price_model.pkl)
- **Frontend:** HTML form (house_price_frontend.html)
- **Training:** 	rain_model.py — retrain the model from data/Housing.csv

**Run locally:**
```bash
cd house_price_app
pip install -r requirements.txt
python app.py
```

---

###  Salary Predictor
Located at root level (salary_predictor.py, Salary.csv)

A simple linear regression model that predicts salary based on years of experience.

- **Script:** salary_predictor.py
- **Data:** Salary.csv
- **Report:** salary_predictor.html — visual report of the model

**Run locally:**
```bash
python salary_predictor.py
```

---

##  Requirements
- Python 3.8+
- See house_price_app/requirements.txt for the Flask app dependencies
