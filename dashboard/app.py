import os
import sys
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Ensure the dashboard directory's parent is on the path for page imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

st.set_page_config(
    page_title="Traffic Accident Severity Analytics",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background-color: #0e1117;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a252f 0%, #0e1117 100%);
        border-right: 1px solid #2C3E50;
    }
    /* KPI card */
    .kpi-card {
        background-color: #1a252f;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        border-left: 5px solid #4ECDC4;
        transition: transform 0.2s ease;
    }
    .kpi-card:hover { transform: translateY(-2px); }
    .kpi-title {
        color: #a0aec0;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .kpi-value {
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .kpi-delta { font-size: 0.85rem; font-weight: 500; margin-top: 5px; }
    .kpi-delta.positive { color: #66BB6A; }
    .kpi-delta.negative { color: #FF6B6B; }
    .kpi-delta.neutral  { color: #45B7D1; }

    h1, h2, h3 { color: #ffffff !important; }

    .page-header {
        border-bottom: 2px solid;
        border-image: linear-gradient(to right, #FF6B6B, #4ECDC4, #45B7D1) 1;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    /* Sidebar section header */
    .sidebar-section {
        color: #4ECDC4;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 12px;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)


# ── Database connection ─────────────────────────────────────────────────────────
@st.cache_resource
def get_db_engine():
    try:
        engine = create_engine(
            f"postgresql+psycopg2://{os.getenv('DATABASE_USER', 'postgres')}:{os.getenv('DATABASE_PASSWORD', 'postgres')}"
            f"@{os.getenv('DATABASE_HOST', 'localhost')}:{os.getenv('DATABASE_PORT', '5432')}"
            f"/{os.getenv('DATABASE_NAME', 'traffic_accidents')}",
            pool_pre_ping=True
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as exc:
        return None


engine = get_db_engine()

# ── Sidebar: connection status + filters ───────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚦 Traffic Analytics")
    st.markdown("---")

    if engine:
        st.success("✅ Database Connected")
    else:
        st.error("❌ Database Disconnected")
        st.info("Start PostgreSQL and re-run. See README for setup instructions.")
        st.stop()

    # Render filters and store in session_state for pages to consume
    from components.filters import render_sidebar_filters
    filters = render_sidebar_filters(engine)
    st.session_state["filters"] = filters
    st.session_state["engine"] = engine   # pages can also import get_db_engine directly

# ── Page navigation ────────────────────────────────────────────────────────────
pages = {
    "📊 Analytics": [
        st.Page("pages/overview.py",         title="Overview",           icon="📊", default=True),
        st.Page("pages/time_analysis.py",    title="Time Analysis",      icon="⏰"),
        st.Page("pages/weather_road.py",     title="Weather & Road",     icon="🌧️"),
        st.Page("pages/hotspots.py",         title="Location Hotspots",  icon="🗺️"),
        st.Page("pages/vehicle_casualty.py", title="Vehicle & Casualty", icon="🚗"),
    ],
    "🤖 Machine Learning": [
        st.Page("pages/prediction.py", title="Severity Prediction", icon="🔮"),
    ],
}

pg = st.navigation(pages)
pg.run()

