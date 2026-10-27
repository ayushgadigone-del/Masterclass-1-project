CSRBOX IBM AI — ML Projects
Two machine learning projects built with Python and Scikit-learn.

Projects
House Price Prediction App
Salary Predictor
🏠 House Price Prediction App
GitHub: Open House Price App on GitHub

A Flask web application that predicts house prices based on features like area, bedrooms, bathrooms, and location.

Files
File	Description
app.py	Flask backend — loads model, serves prediction API
train_model.py	Retrains the model from data/Housing.csv
house_price_frontend.html	HTML form frontend
models/house_price_model.pkl	Trained linear regression model
data/Housing.csv	Training dataset
requirements.txt	Python dependencies
house-price-prediction-project-report.html	Full project report
Model Details
Property	Value
Algorithm	Linear Regression (scikit-learn)
Features	Area, Bedrooms, Bathrooms, Stories, Location, etc.
Training data	data/Housing.csv
Dependencies
pandas>=2.0
numpy>=1.24
scikit-learn>=1.3
matplotlib>=3.7
seaborn>=0.12
streamlit>=1.32
joblib>=1.3
How to Run
Requirements: Python 3.8+

cd "First project/house_price_app"
pip install -r requirements.txt
python app.py
Then open http://localhost:5000 in your browser.

To retrain the model:

python train_model.py
💼 Salary Predictor
GitHub: Open Salary Predictor on GitHub

A pure-Python command-line tool that predicts salary from years of experience using a hand-rolled linear regression model — no external ML libraries required.

Files
File	Description
salary_predictor.py	Main script — loads data, trains model, interactive prediction loop
Salary.csv	Training dataset (YearsExperience, Salary)
salary_predictor.html	Visual HTML report of the model
salary-predictor-project-report.html	Full project report
Model Details
Property	Value
Algorithm	Linear Regression (from scratch, no ML libraries)
Formula	Salary = 8,731.94 × YearsExperience + 28,859.53
R² Score	0.9652 (96.52% variance explained)
Training samples	35
Training range	1.1 – 10.5 years
How to Run
Requirements: Python 3.8+ (uses only csv and math from the standard library — no pip install needed)

cd "First project/Salary Predictor"
python salary_predictor.py
Sample session:

==================================================
   - Salary Prediction Model (Linear Regression)
==================================================

[OK] Model trained on 35 samples
   Formula : Salary = 8,731.94 x YearsExp + 28,859.53
   R2 Score : 0.9652  (96.52% variance explained)
   Training range: 1.1 - 10.5 years

--------------------------------------------------
>> Enter years of experience: 5
   Predicted Salary : $72,519.23
Requirements Summary
Project	Python	Extra dependencies
House Price App	3.8+	pip install -r requirements.txt
Salary Predictor	3.8+	None (standard library only)
