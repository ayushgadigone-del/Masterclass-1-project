"""
Salary Prediction Model — Linear Regression
Trained on Salary.csv (35 samples)

Model:  Salary = slope * YearsExperience + intercept
        Salary = 8731.94 * YearsExperience + 28859.53
        R² = 0.9652  (96.52% variance explained)
"""

import csv
import math

# ── 1. Load data ──────────────────────────────────────────────────────────────
def load_data(filepath="Salary.csv"):
    x, y = [], []
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            x.append(float(row["YearsExperience"]))
            y.append(float(row["Salary"]))
    return x, y


# ── 2. Train linear regression ────────────────────────────────────────────────
def train(x, y):
    n = len(x)
    x_mean = sum(x) / n
    y_mean = sum(y) / n

    num = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean) ** 2 for i in range(n))

    slope = num / den
    intercept = y_mean - slope * x_mean

    # R-squared
    ss_res = sum((y[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))
    ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
    r2 = 1 - ss_res / ss_tot

    return slope, intercept, r2


# ── 3. Predict ────────────────────────────────────────────────────────────────
def predict(years, slope, intercept):
    return slope * years + intercept


# ── 4. Main interactive loop ──────────────────────────────────────────────────
def main():
    print("=" * 50)
    print("   - Salary Prediction Model (Linear Regression)")
    print("=" * 50)

    # Train
    x, y = load_data()
    slope, intercept, r2 = train(x, y)

    print(f"\n[OK] Model trained on {len(x)} samples")
    print(f"   Formula : Salary = {slope:,.2f} x YearsExp + {intercept:,.2f}")
    print(f"   R2 Score : {r2:.4f}  ({r2*100:.2f}% variance explained)")
    print(f"   Training range: {min(x):.1f} - {max(x):.1f} years\n")
    print("-" * 50)
    print("Type a number of years of experience to get a salary prediction.")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        user_input = input(">> Enter years of experience: ").strip()

        if user_input.lower() in ("quit", "exit", "q"):
            print("\nGoodbye!")
            break

        try:
            years = float(user_input)
            if years < 0:
                print("   ⚠️  Please enter a non-negative number.\n")
                continue

            salary = predict(years, slope, intercept)

            # Confidence note for out-of-training-range inputs
            note = ""
            if years < min(x) or years > max(x):
                note = "  (extrapolated -- outside training range)"

            print(f"\n   Predicted Salary : ${salary:,.2f}{note}\n")

        except ValueError:
            print("   Invalid input. Please enter a numeric value.\n")


if __name__ == "__main__":
    main()
