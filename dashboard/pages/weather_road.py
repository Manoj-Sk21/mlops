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

st.title('🌧️ Weather & Road Condition Analysis')

engine = st.session_state.get('engine')
filters = st.session_state.get('filters', {})

if not engine:
    st.error("Database connection not found.")
    st.stop()

@st.cache_data(ttl=300)
def get_weather_road_kpi(filters_dict):
    where_str, params = build_filter_clause(filters_dict)
    query = f"""
    SELECT w.weather_condition as weather_conditions, r.road_type, r.speed_limit, s.severity_label, COUNT(*) as cnt
    FROM analytical.fact_accident f 
    JOIN analytical.dim_weather w ON f.weather_key=w.weather_key
    JOIN analytical.dim_road r ON f.road_key=r.road_key
    JOIN analytical.dim_severity s ON f.severity_key=s.severity_key
    JOIN analytical.dim_date d ON f.date_key=d.date_key 
    LEFT JOIN analytical.dim_location l ON f.location_key=l.location_key 
    WHERE {where_str} 
    GROUP BY w.weather_condition, r.road_type, r.speed_limit, s.severity_label
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Error fetching weather/road data: {e}")
        return pd.DataFrame()

df_wr = get_weather_road_kpi(filters)

if not df_wr.empty:
    most_dangerous_weather = df_wr.groupby('weather_conditions')['cnt'].sum().idxmax()
    most_dangerous_road = df_wr.groupby('road_type')['cnt'].sum().idxmax()
    
    fatal_df = df_wr[df_wr['severity_label'] == 'Fatal']
    if not fatal_df.empty:
        avg_speed_fatal = sum(pd.to_numeric(fatal_df['speed_limit'], errors='coerce').fillna(0) * fatal_df['cnt']) / fatal_df['cnt'].sum()
    else:
        avg_speed_fatal = 0
    
    render_kpi_row([
        {'title': 'Most Dangerous Weather', 'value': most_dangerous_weather, 'icon': '⛈️'},
        {'title': 'Most Dangerous Road Type', 'value': most_dangerous_road, 'icon': '🛣️'},
        {'title': 'Avg Speed Limit in Fatal', 'value': f"{avg_speed_fatal:.1f} mph", 'icon': '⏱️'}
    ])
else:
    st.info('No data available for selected filters.')

col1, col2 = st.columns(2)

with col1:
    st.subheader("Accidents by Weather")
    if not df_wr.empty:
        weather_df = df_wr.groupby(['weather_conditions', 'severity_label'])['cnt'].sum().reset_index()
        fig = px.bar(weather_df, x='weather_conditions', y='cnt', color='severity_label', barmode='stack',
                     color_discrete_map={'Fatal': '#e74c3c', 'Serious': '#f39c12', 'Slight': '#2ecc71'})
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

with col2:
    st.subheader("Accidents by Road Type")
    if not df_wr.empty:
        road_df = df_wr.groupby('road_type')['cnt'].sum().reset_index().sort_values('cnt', ascending=True)
        fig = px.bar(road_df, x='cnt', y='road_type', orientation='h')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

col3, col4 = st.columns(2)

@st.cache_data(ttl=300)
def get_road_surface_light(filters_dict):
    where_str, params = build_filter_clause(filters_dict)
    query = f"""
    SELECT r.road_surface as road_surface_conditions, r.light_conditions, COUNT(*) as cnt
    FROM analytical.fact_accident f 
    JOIN analytical.dim_road r ON f.road_key=r.road_key
    JOIN analytical.dim_weather w ON f.weather_key=w.weather_key
    JOIN analytical.dim_severity s ON f.severity_key=s.severity_key
    JOIN analytical.dim_date d ON f.date_key=d.date_key 
    LEFT JOIN analytical.dim_location l ON f.location_key=l.location_key 
    WHERE {where_str} 
    GROUP BY r.road_surface, r.light_conditions
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Error fetching road surface/light data: {e}")
        return pd.DataFrame()

df_rl = get_road_surface_light(filters)

with col3:
    st.subheader("Road Surface Conditions")
    if not df_rl.empty:
        surf_df = df_rl.groupby('road_surface_conditions')['cnt'].sum().reset_index()
        fig = px.bar(surf_df, x='road_surface_conditions', y='cnt')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

with col4:
    st.subheader("Light Conditions")
    if not df_rl.empty:
        light_df = df_rl.groupby('light_conditions')['cnt'].sum().reset_index()
        fig = px.bar(light_df, x='light_conditions', y='cnt')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

st.subheader("Speed Limit Distribution")
if not df_wr.empty:
    speed_df = df_wr.groupby('speed_limit')['cnt'].sum().reset_index()
    speed_df['speed_limit'] = pd.to_numeric(speed_df['speed_limit'], errors='coerce')
    speed_df = speed_df.dropna().sort_values('speed_limit')
    speed_df['speed_limit'] = speed_df['speed_limit'].astype(str) + " mph"
    fig = px.bar(speed_df, x='speed_limit', y='cnt')
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data available for selected filters.")

st.subheader("Weather x Severity Cross-Tabulation")
if not df_wr.empty:
    crosstab = df_wr.pivot_table(index='weather_conditions', columns='severity_label', values='cnt', aggfunc='sum', fill_value=0)
    st.dataframe(crosstab)
else:
    st.info("No data available for selected filters.")
