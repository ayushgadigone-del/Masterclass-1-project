# Salary Predictor

**GitHub:** [Open Salary Predictor on GitHub](https://github.com/ayushgadigone-del/Masterclass-1-project/tree/main/first-project/salary-predictor)

A pure-Python command-line tool that predicts salary from years of experience using a hand-rolled linear regression model — no external ML libraries required.

---

## Model Details

| Property | Value |
|---|---|
| Algorithm | Linear Regression (from scratch) |
| Formula | `Salary = 8,731.94 × YearsExperience + 28,859.53` |
| R² Score | **0.9652** (96.52% variance explained) |
| Training samples | 35 |
| Training range | 1.1 – 10.5 years |

---

## Files

| File | Description |
|---|---|
| `salary_predictor.py` | Main script — loads data, trains model, interactive prediction loop |
| `Salary.csv` | Training dataset (YearsExperience, Salary) |
| `salary_predictor.html` | Visual HTML report of the model |
| `salary-predictor-project-report.html` | Full project report |

---

## How to Run

**Requirements:** Python 3.8+ (no extra packages needed — uses only `csv` and `math` from the standard library)

```bash
cd first-project/salary-predictor
python salary_predictor.py
```

**Sample session:**
```
==================================================
   - Salary Prediction Model (Linear Regression)
==================================================

[OK] Model trained on 35 samples
   Formula : Salary = 8,731.94 x YearsExp + 28,859.53
   R2 Score : 0.9652  (96.52% variance explained)
   Training range: 1.1 - 10.5 years

--------------------------------------------------
Type a number of years of experience to get a salary prediction.
Type 'quit' or 'exit' to stop.

>> Enter years of experience: 5
   Predicted Salary : $72,519.23
```

---

## Algorithm

The model is implemented from scratch without scikit-learn:

1. **Load** — reads `Salary.csv` into two lists (`YearsExperience`, `Salary`)
2. **Train** — computes slope and intercept using the least-squares formula, then calculates R²
3. **Predict** — applies `Salary = slope × years + intercept`
4. **Loop** — interactive CLI loop with input validation and an extrapolation warning for out-of-range inputs
