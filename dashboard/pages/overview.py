import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import text
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.filters import build_filter_clause
from components.kpi_card import render_kpi_row

st.title("📊 Accident Overview")

engine = st.session_state.get('engine')
filters = st.session_state.get('filters', {})

if not engine:
    st.error("Database connection not found.")
    st.stop()

@st.cache_data(ttl=300)
def get_kpi_data(filters_dict):
    where_str, params = build_filter_clause(filters_dict)
    query = f"""
    SELECT s.severity_label, COUNT(*) as cnt, SUM(f.number_of_casualties) as cas 
    FROM analytical.fact_accident f 
    JOIN analytical.dim_severity s ON f.severity_key=s.severity_key 
    JOIN analytical.dim_date d ON f.date_key=d.date_key 
    LEFT JOIN analytical.dim_road r ON f.road_key=r.road_key 
    LEFT JOIN analytical.dim_weather w ON f.weather_key=w.weather_key 
    LEFT JOIN analytical.dim_location l ON f.location_key=l.location_key 
    WHERE {where_str} 
    GROUP BY s.severity_label
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Error fetching KPI data: {e}")
        return pd.DataFrame()

df_kpi = get_kpi_data(filters)
if df_kpi.empty:
    st.info('No data available for selected filters.')
else:
    total_accidents = int(df_kpi['cnt'].sum())
    total_fatal = int(df_kpi[df_kpi['severity_label'] == 'Fatal']['cnt'].sum()) if 'Fatal' in df_kpi['severity_label'].values else 0
    total_serious = int(df_kpi[df_kpi['severity_label'] == 'Serious']['cnt'].sum()) if 'Serious' in df_kpi['severity_label'].values else 0
    total_slight = int(df_kpi[df_kpi['severity_label'] == 'Slight']['cnt'].sum()) if 'Slight' in df_kpi['severity_label'].values else 0
    total_casualties = int(df_kpi['cas'].sum())

    render_kpi_row([
        {'title': 'Total Accidents', 'value': total_accidents, 'icon': '🚗'},
        {'title': 'Fatal', 'value': total_fatal, 'icon': '☠️'},
        {'title': 'Serious', 'value': total_serious, 'icon': '⚠️'},
        {'title': 'Slight', 'value': total_slight, 'icon': '🩹'},
        {'title': 'Total Casualties', 'value': total_casualties, 'icon': '👥'}
    ])

col1, col2 = st.columns(2)

with col1:
    st.subheader("Accidents by Severity")
    if not df_kpi.empty:
        fig = px.pie(df_kpi, values='cnt', names='severity_label', hole=0.4,
                     color='severity_label', 
                     color_discrete_map={'Fatal': '#e74c3c', 'Serious': '#f39c12', 'Slight': '#2ecc71'})
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)

@st.cache_data(ttl=300)
def get_monthly_trend(filters_dict):
    where_str, params = build_filter_clause(filters_dict)
    query = f"""
    SELECT d.year, d.month, COUNT(*) as cnt 
    FROM analytical.fact_accident f 
    JOIN analytical.dim_date d ON f.date_key=d.date_key 
    JOIN analytical.dim_severity s ON f.severity_key = s.severity_key
    LEFT JOIN analytical.dim_road r ON f.road_key=r.road_key 
    LEFT JOIN analytical.dim_weather w ON f.weather_key=w.weather_key 
    LEFT JOIN analytical.dim_location l ON f.location_key=l.location_key 
    WHERE {where_str} 
    GROUP BY d.year, d.month
    ORDER BY d.year, d.month
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Error fetching trend data: {e}")
        return pd.DataFrame()

with col2:
    st.subheader("Monthly Trend")
    df_trend = get_monthly_trend(filters)
    if not df_trend.empty:
        df_trend['date'] = pd.to_datetime(df_trend['year'].astype(str) + '-' + df_trend['month'].astype(str) + '-01')
        fig = px.line(df_trend, x='date', y='cnt')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

col3, col4 = st.columns(2)

@st.cache_data(ttl=300)
def get_locations(filters_dict):
    where_str, params = build_filter_clause(filters_dict)
    query = f"""
    SELECT l.local_authority, COUNT(*) as cnt 
    FROM analytical.fact_accident f 
    JOIN analytical.dim_location l ON f.location_key=l.location_key 
    JOIN analytical.dim_date d ON f.date_key=d.date_key
    JOIN analytical.dim_severity s ON f.severity_key = s.severity_key
    LEFT JOIN analytical.dim_road r ON f.road_key=r.road_key 
    LEFT JOIN analytical.dim_weather w ON f.weather_key=w.weather_key 
    WHERE {where_str} 
    GROUP BY l.local_authority
    ORDER BY cnt DESC LIMIT 10
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Error fetching locations data: {e}")
        return pd.DataFrame()

with col3:
    st.subheader("Top 10 Locations")
    df_loc = get_locations(filters)
    if not df_loc.empty:
        fig = px.bar(df_loc, x='cnt', y='local_authority', orientation='h')
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

@st.cache_data(ttl=300)
def get_dow(filters_dict):
    where_str, params = build_filter_clause(filters_dict)
    query = f"""
    SELECT d.day_name as day_of_week, COUNT(*) as cnt 
    FROM analytical.fact_accident f 
    JOIN analytical.dim_date d ON f.date_key=d.date_key 
    JOIN analytical.dim_severity s ON f.severity_key = s.severity_key
    LEFT JOIN analytical.dim_road r ON f.road_key=r.road_key 
    LEFT JOIN analytical.dim_weather w ON f.weather_key=w.weather_key 
    LEFT JOIN analytical.dim_location l ON f.location_key=l.location_key 
    WHERE {where_str} 
    GROUP BY d.day_name, d.day_of_week
    ORDER BY d.day_of_week
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Error fetching DOW data: {e}")
        return pd.DataFrame()

with col4:
    st.subheader("Accidents by Day of Week")
    df_dow = get_dow(filters)
    if not df_dow.empty:
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df_dow['day_of_week'] = pd.Categorical(df_dow['day_of_week'], categories=days, ordered=True)
        df_dow = df_dow.sort_values('day_of_week')
        fig = px.bar(df_dow, x='day_of_week', y='cnt')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters.")
