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
import matplotlib.ticker as mticker
import numpy as np
import streamlit as st

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="💼 Salary Predictor",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Result card */
    .result-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #3b82d4 60%, #7c5cd8 100%);
        border-radius: 16px;
        padding: 36px 28px;
        text-align: center;
        color: white;
        margin: 8px 0 20px 0;
    }
    .result-card .label  { font-size: 13px; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.75; margin-bottom: 6px; }
    .result-card .amount { font-size: 52px; font-weight: 800; letter-spacing: -2px; line-height: 1; }
    .result-card .sub    { font-size: 13px; opacity: 0.75; margin-top: 10px; }

    /* Warning pill */
    .extrap-pill {
        display: inline-block;
        background: #fef3c7;
        color: #92400e;
        border: 1px solid #fcd34d;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 12px;
        font-weight: 600;
        margin-top: 10px;
    }

    /* Stat strip */
    .stat-row { display: flex; gap: 16px; margin-bottom: 16px; }
    .stat-box {
        flex: 1;
        background: #f7f8fa;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 14px 18px;
    }
    .stat-box .s-label { font-size: 11px; color: #57606a; text-transform: uppercase; letter-spacing: 1px; }
    .stat-box .s-value { font-size: 22px; font-weight: 700; color: #1f2328; margin-top: 2px; }

    /* Range band */
    .range-band {
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 10px;
        padding: 14px 20px;
        font-size: 14px;
        color: #166534;
        margin-top: 10px;
    }

    /* Section heading tweak */
    h3 { margin-top: 0 !important; }
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

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("💼 Salary Predictor")
    st.markdown("---")
    st.subheader("Your Experience")
    years = st.slider(
        "Years of experience",
        min_value=0.0,
        max_value=15.0,
        value=5.0,
        step=0.5,
        help="Drag to select years of experience",
    )
    st.markdown("---")
    st.subheader("Model Info")
    st.markdown(f"**Algorithm:** Linear Regression")
    st.markdown(f"**R² Score:** `{r2:.4f}`")
    st.markdown(f"**Samples:** `{len(x_data)}`")
    st.markdown(f"**Training range:** `{min(x_data):.1f} – {max(x_data):.1f} yrs`")
    st.markdown(f"**Formula:**")
    st.code(f"Salary =\n  {slope:,.2f} × Years\n+ {intercept:,.2f}", language="python")

# ── Prediction ─────────────────────────────────────────────────────────────────
predicted = slope * years + intercept
low, high = predicted * 0.90, predicted * 1.10
is_extrapolated = years < min(x_data) or years > max(x_data)

# ── Page title ─────────────────────────────────────────────────────────────────
st.title("💼 Salary Predictor")
st.caption("Linear Regression · Pure Python · No external ML libraries")
st.markdown("---")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🔮 Prediction", "📊 Data Explorer", "📐 Model Details"])

# ─────────────────────────────────────────────────────────── TAB 1 — Prediction
with tab1:
    col_left, col_right = st.columns([1, 1.4], gap="large")

    with col_left:
        # Result card
        extrap_html = '<div class="extrap-pill">⚠️ Outside training range — extrapolated</div>' if is_extrapolated else ""
        st.markdown(f"""
        <div class="result-card">
            <div class="label">Predicted Salary</div>
            <div class="amount">${predicted:,.0f}</div>
            <div class="sub">{years:.1f} year{"s" if years != 1 else ""} of experience</div>
            {extrap_html}
        </div>
        """, unsafe_allow_html=True)

        # Range band
        st.markdown(f"""
        <div class="range-band">
            📈 &nbsp;<strong>Estimated range (±10%):</strong> &nbsp; ${low:,.0f} &mdash; ${high:,.0f}
        </div>
        """, unsafe_allow_html=True)

        # Stat strip
        st.markdown("<br>", unsafe_allow_html=True)
        s1, s2, s3 = st.columns(3)
        s1.metric("Your input", f"{years:.1f} yrs")
        s2.metric("Predicted", f"${predicted/1000:.1f}k")
        s3.metric("R² Score", f"{r2:.4f}")

    with col_right:
        # Chart
        fig, ax = plt.subplots(figsize=(7, 4.5))
        fig.patch.set_facecolor("#fafafa")
        ax.set_facecolor("#fafafa")

        ax.scatter(x_data, y_data,
                   color="#3b82d4", edgecolors="white", s=90,
                   alpha=0.9, zorder=3, label="Training data")

        x_line = np.linspace(0, 15, 300)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, color="#7c5cd8", linewidth=2.5,
                label="Regression line")

        ax.axvline(years, color="#e53e3e", linestyle="--",
                   linewidth=1.5, alpha=0.8, label=f"Input: {years:.1f} yrs")
        ax.axhline(predicted, color="#10b981", linestyle="--",
                   linewidth=1.5, alpha=0.8, label=f"Predicted: ${predicted/1000:.1f}k")
        ax.scatter([years], [predicted], color="#e53e3e", s=140,
                   zorder=6, edgecolors="white", linewidths=1.5)

        ax.set_xlabel("Years of Experience", fontsize=11)
        ax.set_ylabel("Salary ($)", fontsize=11)
        ax.set_title("Salary vs Years of Experience", fontsize=13, fontweight="bold", pad=12)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v/1000:.0f}k"))
        ax.set_xlim(0, 15)
        ax.legend(fontsize=9, framealpha=0.9)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.spines[["top", "right"]].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

# ──────────────────────────────────────────────────── TAB 2 — Data Explorer
with tab2:
    import pandas as pd
    df = pd.DataFrame({"YearsExperience": x_data, "Salary": y_data})

    st.subheader("Dataset Overview")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Samples",      len(df))
    d2.metric("Avg Salary",   f"${df['Salary'].mean():,.0f}")
    d3.metric("Min Salary",   f"${df['Salary'].min():,.0f}")
    d4.metric("Max Salary",   f"${df['Salary'].max():,.0f}")

    st.markdown("---")

    col_a, col_b = st.columns([1, 1], gap="large")

    with col_a:
        st.subheader("Raw Data")
        st.dataframe(
            df.style.format({"Salary": "${:,.0f}", "YearsExperience": "{:.1f}"}),
            use_container_width=True,
            height=350,
        )

    with col_b:
        st.subheader("Salary Distribution")
        fig2, ax2 = plt.subplots(figsize=(5.5, 4))
        fig2.patch.set_facecolor("#fafafa")
        ax2.set_facecolor("#fafafa")
        ax2.hist(df["Salary"] / 1000, bins=8, color="#3b82d4",
                 edgecolor="white", linewidth=0.8)
        ax2.set_xlabel("Salary ($k)", fontsize=10)
        ax2.set_ylabel("Count", fontsize=10)
        ax2.set_title("Salary Distribution", fontsize=12, fontweight="bold")
        ax2.grid(True, linestyle="--", alpha=0.4, axis="y")
        ax2.spines[["top", "right"]].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()

# ──────────────────────────────────────────────────── TAB 3 — Model Details
with tab3:
    st.subheader("Model Formula")
    st.code(f"Salary = {slope:,.2f} × YearsExperience + {intercept:,.2f}", language="python")

    st.markdown("---")
    st.subheader("Performance Metrics")
    m1, m2, m3 = st.columns(3)
    m1.metric("R² Score",        f"{r2:.4f}")
    m2.metric("Training samples", len(x_data))
    m3.metric("Training range",  f"{min(x_data):.1f} – {max(x_data):.1f} yrs")

    st.markdown("---")
    st.subheader("Residuals")
    import pandas as pd
    preds = [slope * xi + intercept for xi in x_data]
    residuals = [y_data[i] - preds[i] for i in range(len(x_data))]

    fig3, ax3 = plt.subplots(figsize=(7, 3.5))
    fig3.patch.set_facecolor("#fafafa")
    ax3.set_facecolor("#fafafa")
    ax3.scatter(x_data, residuals, color="#7c5cd8",
                edgecolors="white", s=80, alpha=0.85, zorder=3)
    ax3.axhline(0, color="#e53e3e", linestyle="--", linewidth=1.5)
    ax3.set_xlabel("Years of Experience", fontsize=10)
    ax3.set_ylabel("Residual ($)", fontsize=10)
    ax3.set_title("Residual Plot (Actual − Predicted)", fontsize=12, fontweight="bold")
    ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v/1000:.0f}k"))
    ax3.grid(True, linestyle="--", alpha=0.4)
    ax3.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close()
