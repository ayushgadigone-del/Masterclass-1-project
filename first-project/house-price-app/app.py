"""
app.py  ·  House Price Prediction — Streamlit Frontend
-------------------------------------------------------
Run with:   streamlit run app.py
Make sure train_model.py has been executed first.
"""

import json
import os
import sys

# Ensure models_numpy is importable when joblib unpickles the model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import models_numpy  # noqa: F401 — registers classes in sys.modules

import joblib
import matplotlib
matplotlib.use("Agg")          # must be set before importing pyplot
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🏠 House Price Predictor",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DATA_PATH    = os.path.join(BASE_DIR, "data", "Housing.csv")
MODEL_PATH   = os.path.join(BASE_DIR, "models", "house_price_model.pkl")
METRICS_PATH = os.path.join(BASE_DIR, "models", "model_metrics.json")
EVAL_PLOT    = os.path.join(BASE_DIR, "models", "eval_plot.png")

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .prediction-box {
        background: linear-gradient(135deg, #3b82d4 0%, #7c5cd8 100%);
        border-radius: 14px;
        padding: 32px;
        text-align: center;
        color: white;
        margin: 20px 0;
    }
    .prediction-box h2 { font-size: 20px; margin-bottom: 8px; opacity: 0.9; }
    .prediction-box .price { font-size: 42px; font-weight: 800; letter-spacing: -1px; }
</style>
""", unsafe_allow_html=True)

# ── Load resources ─────────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    return joblib.load(MODEL_PATH)   # dict: model, mu, std, features

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

@st.cache_data
def load_metrics():
    if not os.path.exists(METRICS_PATH):
        return None
    with open(METRICS_PATH) as f:
        return json.load(f)

model_obj = load_model()
df        = load_data()
metrics   = load_metrics()

# ── Guard ──────────────────────────────────────────────────────────────────────
if model_obj is None:
    st.error("⚠️  Model not found. Please run `python train_model.py` first.")
    st.stop()

model    = model_obj["model"]
mu       = model_obj["mu"]
std_vals = model_obj["std"]   # renamed to avoid shadowing built-ins

def predict_price(area, bedrooms):
    """Scale input then run model."""
    x_raw = np.array([[area, bedrooms]], dtype=float)
    x_sc  = (x_raw - mu) / std_vals
    return float(model.predict(x_sc)[0])

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏠 House Price Predictor")
    st.markdown("---")
    st.subheader("Input Features")

    area = st.slider(
        "🏗️ Area (sq ft)",
        min_value=int(df["area"].min().item()),
        max_value=int(df["area"].max().item()),
        value=int(df["area"].median().item()),
        step=50,
        help="Total area of the house in square feet",
    )

    bedrooms = st.selectbox(
        "🛏️ Bedrooms",
        options=sorted(df["bedrooms"].unique().tolist()),
        index=1,
        help="Number of bedrooms",
    )

    st.markdown("---")
    if metrics:
        st.subheader("Model Info")
        st.markdown(f"**Algorithm:** {metrics.get('best_model', 'N/A')}")
        st.markdown(f"**Training samples:** {metrics.get('train_samples', 'N/A')}")
        st.markdown(f"**Test samples:** {metrics.get('test_samples', 'N/A')}")
        st.markdown(f"**R² Score:** {metrics.get('r2', 'N/A')}")

# ── Main ───────────────────────────────────────────────────────────────────────
st.title("🏠 House Price Prediction")
st.caption("Machine Learning · Pure NumPy backend · Streamlit frontend")

tab1, tab2, tab3 = st.tabs(["🔮 Prediction", "📊 Data Insights", "📈 Model Performance"])

# ────────────────────────────────────────────────────────── TAB 1 — Prediction
with tab1:
    predicted = predict_price(area, bedrooms)

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("Selected Parameters")
        p1, p2 = st.columns(2)
        p1.metric("Area (sq ft)", f"{area:,}")
        p2.metric("Bedrooms",     bedrooms)

        st.markdown(f"""
        <div class="prediction-box">
            <h2>Estimated House Price</h2>
            <div class="price">₹ {predicted:,.0f}</div>
            <div style="opacity:0.8;margin-top:8px;font-size:14px">
                {area:,} sq ft · {bedrooms} bedroom{"s" if bedrooms > 1 else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)

        low, high = predicted * 0.90, predicted * 1.10
        st.info(f"**Estimated range:** ₹ {low:,.0f} — ₹ {high:,.0f}  *(±10%)*")

    with col_right:
        st.subheader("Price vs Area")
        fig, ax = plt.subplots(figsize=(6, 4))
        sc = ax.scatter(df["area"], df["price"],
                        c=df["bedrooms"], cmap="viridis",
                        s=70, alpha=0.8, edgecolors="white", zorder=3)
        ax.axvline(area, color="#e53e3e", linestyle="--", linewidth=1.5,
                   label=f"Your area: {area:,}")
        ax.axhline(predicted, color="#3b82d4", linestyle="--", linewidth=1.5,
                   label=f"Predicted: ₹{predicted/1e6:.2f}M")
        plt.colorbar(sc, ax=ax, label="Bedrooms")
        ax.set_xlabel("Area (sq ft)")
        ax.set_ylabel("Price (₹)")
        ax.set_title("Dataset — Price vs Area")
        ax.legend(fontsize=8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"Rs{x/1e6:.1f}M"))
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

# ─────────────────────────────────────────────────────── TAB 2 — Data Insights
with tab2:
    st.subheader("Dataset Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Records", len(df))
    c2.metric("Avg Price",     f"₹{df['price'].mean():,.0f}")
    c3.metric("Avg Area",      f"{df['area'].mean():,.0f} sq ft")
    c4.metric("Avg Bedrooms",  f"{df['bedrooms'].mean():.1f}")

    st.dataframe(
        df.style.format({"price": "₹{:,.0f}", "area": "{:,}"}),
        use_container_width=True,
        height=280,
    )

    st.markdown("---")
    st.subheader("Visual Exploration")

    col_a, col_b = st.columns(2)

    with col_a:
        fig1, ax1 = plt.subplots(figsize=(5.5, 4))
        ax1.hist(df["price"] / 1e6, bins=10, color="#3b82d4", edgecolor="white")
        ax1.set_xlabel("Price (₹ millions)")
        ax1.set_ylabel("Count")
        ax1.set_title("Price Distribution")
        plt.tight_layout()
        st.pyplot(fig1)
        plt.close()

    with col_b:
        fig2, ax2 = plt.subplots(figsize=(5.5, 4))
        bed_groups = df.groupby("bedrooms")["price"].mean() / 1e6
        colors = ["#3b82d4", "#7c5cd8", "#10b981", "#f59e0b"]
        ax2.bar(bed_groups.index.astype(str), bed_groups.values,
                color=colors[:len(bed_groups)], edgecolor="white")
        ax2.set_xlabel("Bedrooms")
        ax2.set_ylabel("Avg Price (₹ millions)")
        ax2.set_title("Avg Price by Bedrooms")
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()

    col_c, col_d = st.columns(2)

    with col_c:
        fig3, ax3 = plt.subplots(figsize=(5.5, 4))
        ax3.scatter(df["area"], df["price"] / 1e6,
                    color="#3b82d4", edgecolors="white", s=80, alpha=0.8)
        z = np.polyfit(df["area"], df["price"] / 1e6, 1)
        xline = np.linspace(df["area"].min(), df["area"].max(), 100)
        ax3.plot(xline, np.poly1d(z)(xline), "r--", linewidth=1.5, label="Trend")
        ax3.set_xlabel("Area (sq ft)")
        ax3.set_ylabel("Price (₹ millions)")
        ax3.set_title("Area vs Price")
        ax3.legend()
        plt.tight_layout()
        st.pyplot(fig3)
        plt.close()

    with col_d:
        fig4, ax4 = plt.subplots(figsize=(5.5, 4))
        corr = df[["price", "area", "bedrooms"]].corr()
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="Blues", ax=ax4,
                    linewidths=0.5, square=True,
                    xticklabels=["Price", "Area", "Beds"],
                    yticklabels=["Price", "Area", "Beds"])
        ax4.set_title("Correlation Heatmap")
        plt.tight_layout()
        st.pyplot(fig4)
        plt.close()

# ──────────────────────────────────────────────────── TAB 3 — Model Performance
with tab3:
    if metrics:
        st.subheader("Best Model Performance")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Algorithm", metrics["best_model"])
        m2.metric("R² Score",  f"{metrics['r2']:.4f}")
        m3.metric("MAE",       f"₹{metrics['mae']:,.0f}")
        m4.metric("RMSE",      f"₹{metrics['rmse']:,.0f}")

        st.markdown("---")
        st.subheader("All Models Comparison")
        comp_df = pd.DataFrame(metrics["all_models"]).T.reset_index()
        comp_df.columns = ["Model", "R2", "MAE", "RMSE"]
        comp_df["MAE"]  = comp_df["MAE"].astype(float)
        comp_df["RMSE"] = comp_df["RMSE"].astype(float)
        st.dataframe(
            comp_df.style
                .highlight_max(subset=["R2"], color="#d1fae5")
                .highlight_min(subset=["MAE", "RMSE"], color="#d1fae5")
                .format({"MAE": "Rs {:,.0f}", "RMSE": "Rs {:,.0f}"}),
            use_container_width=True,
        )

        st.markdown("---")
        if os.path.exists(EVAL_PLOT):
            st.subheader("Evaluation Plots")
            st.image(EVAL_PLOT, use_container_width=True)
    else:
        st.warning("Metrics not found. Run train_model.py first.")
