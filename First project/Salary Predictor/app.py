"""
app.py · Salary Predictor — Streamlit Frontend
-----------------------------------------------
Run with:   streamlit run app.py
"""

import csv
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="💼 Salary Predictor",
    page_icon="💼",
    layout="centered",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .result-box {
        background: linear-gradient(135deg, #3b82d4 0%, #7c5cd8 100%);
        border-radius: 14px;
        padding: 32px;
        text-align: center;
        color: white;
        margin: 20px 0;
    }
    .result-box h3 { font-size: 18px; margin-bottom: 8px; opacity: 0.9; }
    .result-box .salary { font-size: 42px; font-weight: 800; letter-spacing: -1px; }
    .result-box .note { font-size: 13px; opacity: 0.8; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

# ── Load data + train ──────────────────────────────────────────────────────────
@st.cache_data
def load_and_train():
    base = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base, "Salary.csv")
    x, y = [], []
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            x.append(float(row["YearsExperience"]))
            y.append(float(row["Salary"]))

    n = len(x)
    x_mean = sum(x) / n
    y_mean = sum(y) / n
    num = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean) ** 2 for i in range(n))
    slope = num / den
    intercept = y_mean - slope * x_mean

    ss_res = sum((y[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))
    ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
    r2 = 1 - ss_res / ss_tot

    return x, y, slope, intercept, r2

x_data, y_data, slope, intercept, r2 = load_and_train()

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("💼 Salary Predictor")
st.caption("Linear Regression · Pure Python · No ML libraries")

st.markdown("---")

# ── Model info strip ───────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("R² Score", f"{r2:.4f}")
c2.metric("Training samples", len(x_data))
c3.metric("Training range", f"{min(x_data):.1f} – {max(x_data):.1f} yrs")

st.markdown("---")

# ── Input ──────────────────────────────────────────────────────────────────────
st.subheader("Enter Years of Experience")
years = st.slider(
    "Years of experience",
    min_value=0.0,
    max_value=15.0,
    value=5.0,
    step=0.5,
    help="Drag to select years of experience",
)

# ── Prediction ─────────────────────────────────────────────────────────────────
predicted = slope * years + intercept
is_extrapolated = years < min(x_data) or years > max(x_data)
note = "⚠️ Outside training range — extrapolated estimate" if is_extrapolated else ""

st.markdown(f"""
<div class="result-box">
    <h3>Predicted Salary</h3>
    <div class="salary">${predicted:,.0f}</div>
    <div class="note">{years:.1f} year{"s" if years != 1 else ""} of experience{" · " + note if note else ""}</div>
</div>
""", unsafe_allow_html=True)

low, high = predicted * 0.90, predicted * 1.10
st.info(f"**Estimated range:** ${low:,.0f} — ${high:,.0f}  *(±10%)*")

st.markdown("---")

# ── Chart ──────────────────────────────────────────────────────────────────────
st.subheader("Salary vs Experience")

fig, ax = plt.subplots(figsize=(7, 4))
ax.scatter(x_data, y_data, color="#3b82d4", edgecolors="white", s=80, alpha=0.85, zorder=3, label="Training data")

import numpy as np
x_line = np.linspace(min(x_data) * 0.8, max(x_data) * 1.1, 200)
y_line = slope * x_line + intercept
ax.plot(x_line, y_line, color="#7c5cd8", linewidth=2, label="Regression line")

ax.axvline(years, color="#e53e3e", linestyle="--", linewidth=1.5, label=f"Your input: {years:.1f} yrs")
ax.axhline(predicted, color="#10b981", linestyle="--", linewidth=1.5, label=f"Predicted: ${predicted:,.0f}")
ax.scatter([years], [predicted], color="#e53e3e", s=120, zorder=5)

ax.set_xlabel("Years of Experience")
ax.set_ylabel("Salary ($)")
ax.set_title("Salary Prediction — Linear Regression")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v/1000:.0f}k"))
ax.legend(fontsize=8)
plt.tight_layout()
st.pyplot(fig)
plt.close()

st.markdown("---")

# ── Formula ───────────────────────────────────────────────────────────────────
st.subheader("Model Formula")
st.code(f"Salary = {slope:,.2f} × YearsExperience + {intercept:,.2f}", language="python")
