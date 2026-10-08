"""
Page 6 — Severity Prediction
Sends form data to the FastAPI inference service and displays results.
"""
import streamlit as st
import pandas as pd
import requests
import datetime
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


def get_engine():
    return st.session_state.get("engine")


# ── Dropdown options ────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_dropdown_options(_engine):
    defaults = {
        'road_type':  ['Single carriageway', 'Dual carriageway', 'Roundabout',
                       'One way street', 'Slip road'],
        'surface':    ['Dry', 'Wet / damp', 'Snow', 'Frost / ice', 'Oil or diesel', 'Mud'],
        'weather':    ['Fine no high winds', 'Raining no high winds', 'Snowing no high winds',
                       'Fine + high winds', 'Raining + high winds', 'Fog or mist', 'Other'],
        'light':      ['Daylight', 'Darkness - lights lit', 'Darkness - lights unlit',
                       'Darkness - no lighting'],
        'urban_rural': ['Urban', 'Rural'],
        'junction':   ['Not at junction', 'Crossroads', 'Roundabout',
                       'T or staggered junction', 'Slip road'],
    }
    if _engine is None:
        return defaults
    try:
        with _engine.connect() as conn:
            def q(sql):
                return [r[0] for r in conn.execute(text(sql)).fetchall() if r[0]]
            options = {
                'road_type':   q("SELECT DISTINCT road_type FROM analytical.dim_road WHERE road_type IS NOT NULL ORDER BY road_type"),
                'surface':     q("SELECT DISTINCT road_surface FROM analytical.dim_road WHERE road_surface IS NOT NULL ORDER BY road_surface"),
                'weather':     q("SELECT DISTINCT weather_condition FROM analytical.dim_weather WHERE weather_condition IS NOT NULL ORDER BY weather_condition"),
                'light':       q("SELECT DISTINCT light_conditions FROM analytical.dim_road WHERE light_conditions IS NOT NULL ORDER BY light_conditions"),
                'urban_rural': q("SELECT DISTINCT urban_rural FROM analytical.dim_road WHERE urban_rural IS NOT NULL ORDER BY urban_rural"),
                'junction':    q("SELECT DISTINCT junction_type FROM analytical.dim_road WHERE junction_type IS NOT NULL ORDER BY junction_type"),
            }
            return {k: (v if v else defaults[k]) for k, v in options.items()}
    except Exception:
        return defaults


# ── Page layout ─────────────────────────────────────────────────────────────────
st.title("🔮 Accident Severity Prediction")

st.warning(
    "⚠️ **Educational Use Only** — This is a machine learning model prediction "
    "and does NOT represent a confirmed real-world accident classification. "
    "Do not use for operational decision-making."
)

engine = get_engine()
opts = get_dropdown_options(engine)

form_col, result_col = st.columns([3, 2])

with form_col:
    st.subheader("📋 Accident Details")
    with st.form("prediction_form"):

        st.markdown("##### 📍 Location & Time")
        t1, t2 = st.columns(2)
        with t1:
            acc_date = st.date_input("Date", datetime.date.today())
            lat = st.number_input("Latitude (UK: 49–61)", value=51.5074, min_value=49.0, max_value=61.0, format="%.4f")
        with t2:
            acc_time = st.time_input("Time", datetime.time(8, 30))
            lon = st.number_input("Longitude (UK: -8 to 2)", value=-0.1278, min_value=-8.0, max_value=2.0, format="%.4f")

        st.markdown("##### 🛣️ Road Conditions")
        r1, r2 = st.columns(2)
        with r1:
            road_type    = st.selectbox("Road Type",         opts['road_type'])
            road_surface = st.selectbox("Road Surface",      opts['surface'])
            junction     = st.selectbox("Junction Type",     opts['junction'])
        with r2:
            speed_limit  = st.selectbox("Speed Limit (mph)", [20, 30, 40, 50, 60, 70], index=1)
            light        = st.selectbox("Light Conditions",  opts['light'])
            urban_rural  = st.selectbox("Urban / Rural",     opts['urban_rural'])

        st.markdown("##### 🌧️ Weather")
        w1, w2 = st.columns(2)
        with w1:
            weather       = st.selectbox("Weather Condition",  opts['weather'])
            temperature   = st.number_input("Temperature (°C)", value=12.0, min_value=-20.0, max_value=45.0, step=0.5)
            wind_speed    = st.number_input("Wind Speed (km/h)", value=10.0, min_value=0.0, max_value=200.0, step=1.0)
        with w2:
            precipitation = st.number_input("Precipitation (mm)", value=0.0, min_value=0.0, max_value=300.0, step=0.5)
            rain          = st.number_input("Rain (mm)",          value=0.0, min_value=0.0, max_value=300.0, step=0.5)
            snowfall      = st.number_input("Snowfall (cm)",      value=0.0, min_value=0.0, max_value=100.0, step=0.5)

        st.markdown("##### 🚗 Incident")
        i1, i2 = st.columns(2)
        with i1:
            vehicles   = st.number_input("Number of Vehicles",   min_value=1, max_value=50,  value=2)
        with i2:
            casualties = st.number_input("Number of Casualties", min_value=0, max_value=100, value=1)

        submitted = st.form_submit_button("🔮 Predict Severity", use_container_width=True, type="primary")

# ── Result column ───────────────────────────────────────────────────────────────
with result_col:
    st.subheader("📊 Prediction Result")

    if not submitted:
        st.info("Fill in the accident details and click **Predict Severity**.")
    else:
        payload = {
            "date":                  str(acc_date),
            "time":                  acc_time.strftime("%H:%M"),
            "latitude":              lat,
            "longitude":             lon,
            "road_type":             road_type,
            "speed_limit":           speed_limit,
            "road_surface":          road_surface,
            "weather_condition":     weather,
            "light_conditions":      light,
            "urban_rural":           urban_rural,
            "number_of_vehicles":    vehicles,
            "number_of_casualties":  casualties,
            "junction_type":         junction,
            "temperature":           temperature,
            "precipitation":         precipitation,
            "rain":                  rain,
            "snowfall":              snowfall,
            "wind_speed":            wind_speed,
        }

        with st.spinner("Calling prediction service…"):
            try:
                resp = requests.post(f"{API_BASE}/predict", json=payload, timeout=10)
                resp.raise_for_status()
                result = resp.json()
                api_ok = True
            except requests.exceptions.ConnectionError:
                api_ok = False
                st.error(
                    f"Cannot connect to FastAPI at `{API_BASE}/predict`. "
                    "Start the API with:\n```\nuvicorn api.main:app --port 8000\n```\n"
                    "Or `docker-compose up fastapi`."
                )
            except requests.exceptions.HTTPError as he:
                api_ok = False
                st.error(f"API error {he.response.status_code}: {he.response.text}")
            except Exception as exc:
                api_ok = False
                st.error(f"Unexpected error: {exc}")

        if api_ok:
            label       = result.get("predicted_label", "Unknown")
            probs       = result.get("probabilities", {})
            version     = result.get("model_version", "unknown")
            request_id  = result.get("request_id", "—")

            COLORS = {"Fatal": "#e74c3c", "Serious": "#f39c12", "Slight": "#2ecc71"}
            badge_color = COLORS.get(label, "#4ECDC4")

            st.markdown(
                f"""
                <div style="background:{badge_color};padding:24px;border-radius:12px;
                            text-align:center;margin-bottom:16px;
                            box-shadow:0 4px 12px rgba(0,0,0,0.4);">
                  <div style="color:white;font-size:2rem;font-weight:700;">{label}</div>
                  <div style="color:rgba(255,255,255,0.85);font-size:0.9rem;margin-top:4px;">
                    Predicted Severity
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if probs:
                st.markdown("**Class Probabilities**")
                df_p = pd.DataFrame({
                    "Severity":    list(probs.keys()),
                    "Probability": list(probs.values()),
                })
                fig = px.bar(
                    df_p, x="Probability", y="Severity", orientation="h",
                    color="Severity",
                    color_discrete_map=COLORS,
                    text=df_p["Probability"].apply(lambda v: f"{v:.1%}"),
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font_color="white", showlegend=False,
                    xaxis=dict(range=[0, 1], tickformat=".0%"),
                    margin=dict(t=10, b=10, l=10, r=50), height=200,
                )
                st.plotly_chart(fig, use_container_width=True)

            # Confidence gauge
            top_prob = max(probs.values()) if probs else 0
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=round(top_prob * 100, 1),
                title={"text": "Confidence", "font": {"color": "white"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "white"},
                    "bar":  {"color": badge_color},
                    "bgcolor": "#1a252f",
                    "steps": [
                        {"range": [0,  40], "color": "#2C3E50"},
                        {"range": [40, 70], "color": "#2C3E50"},
                        {"range": [70, 100],"color": "#2C3E50"},
                    ],
                },
                number={"suffix": "%", "font": {"color": "white"}},
            ))
            fig_g.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", height=200,
                margin=dict(t=30, b=10, l=20, r=20),
            )
            st.plotly_chart(fig_g, use_container_width=True)

            st.caption(f"Model: `{version}` | Request: `{request_id}`")

# ── Model info expander ─────────────────────────────────────────────────────────
with st.expander("ℹ️ Model Information"):
    st.markdown("""
### XGBoost Multi-class Classifier

Trained on historical UK Road Safety data to predict accident severity:
**1 = Fatal · 2 = Serious · 3 = Slight**

| Feature Group | Features |
|---------------|---------|
| Temporal      | Hour, Day of Week, Month, Season, Is Weekend, Is Rush Hour |
| Location      | Latitude, Longitude, Urban/Rural |
| Road          | Road Type, Speed Limit, Surface, Junction Type, Light Conditions |
| Weather       | Condition, Temperature, Precipitation, Rain, Snowfall, Wind Speed |
| Incident      | Number of Vehicles, Number of Casualties |

**Class imbalance** is addressed using `compute_sample_weight('balanced')` during training.  
**Chronological split** (70 / 15 / 15) prevents temporal data leakage.  
Model performance and drift are tracked in the `monitoring` schema and via MLflow.
""")
