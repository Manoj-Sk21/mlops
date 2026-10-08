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

st.title('⏰ Time Pattern Analysis')

engine = st.session_state.get('engine')
filters = st.session_state.get('filters', {})

if not engine:
    st.error("Database connection not found.")
    st.stop()

@st.cache_data(ttl=300)
def get_time_kpi_data(filters_dict):
    where_str, params = build_filter_clause(filters_dict)
    query = f"""
    SELECT EXTRACT(HOUR FROM f.accident_time)::int as hour, d.day_name as day_of_week, d.is_weekend, COUNT(*) as cnt
    FROM analytical.fact_accident f 
    JOIN analytical.dim_date d ON f.date_key=d.date_key 
    JOIN analytical.dim_severity s ON f.severity_key = s.severity_key
    LEFT JOIN analytical.dim_road r ON f.road_key=r.road_key 
    LEFT JOIN analytical.dim_weather w ON f.weather_key=w.weather_key 
    LEFT JOIN analytical.dim_location l ON f.location_key=l.location_key 
    WHERE {where_str} 
    GROUP BY EXTRACT(HOUR FROM f.accident_time), d.day_name, d.is_weekend
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Error fetching Time KPI data: {e}")
        return pd.DataFrame()

df_time = get_time_kpi_data(filters)

if not df_time.empty:
    peak_hour = df_time.groupby('hour')['cnt'].sum().idxmax()
    peak_day = df_time.groupby('day_of_week')['cnt'].sum().idxmax()
    weekend_pct = (df_time[df_time['is_weekend'] == True]['cnt'].sum() / df_time['cnt'].sum()) * 100
    avg_per_hour = df_time['cnt'].sum() / 24

    render_kpi_row([
        {'title': 'Peak Hour', 'value': f"{int(peak_hour)}:00", 'icon': '⌚'},
        {'title': 'Peak Day', 'value': peak_day, 'icon': '📅'},
        {'title': 'Weekend Accident %', 'value': f"{weekend_pct:.1f}%", 'icon': '🏖️'},
        {'title': 'Avg Accidents / Hour', 'value': f"{avg_per_hour:.1f}", 'icon': '📈'}
    ])
else:
    st.info('No data available for selected filters.')

col1, col2 = st.columns(2)

@st.cache_data(ttl=300)
def get_hourly_data(filters_dict):
    where_str, params = build_filter_clause(filters_dict)
    query = f"""
    SELECT EXTRACT(HOUR FROM f.accident_time)::int as hour, s.severity_label, COUNT(*) as cnt
    FROM analytical.fact_accident f 
    JOIN analytical.dim_date d ON f.date_key=d.date_key 
    JOIN analytical.dim_severity s ON f.severity_key = s.severity_key
    LEFT JOIN analytical.dim_road r ON f.road_key=r.road_key 
    LEFT JOIN analytical.dim_weather w ON f.weather_key=w.weather_key 
    LEFT JOIN analytical.dim_location l ON f.location_key=l.location_key 
    WHERE {where_str} 
    GROUP BY EXTRACT(HOUR FROM f.accident_time), s.severity_label
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Error fetching hourly data: {e}")
        return pd.DataFrame()

with col1:
    st.subheader("Accidents by Hour")
    df_hourly = get_hourly_data(filters)
    if not df_hourly.empty:
        fig = px.bar(df_hourly, x='hour', y='cnt', color='severity_label', barmode='stack',
                     color_discrete_map={'Fatal': '#e74c3c', 'Serious': '#f39c12', 'Slight': '#2ecc71'})
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

with col2:
    st.subheader("Accidents by Day of Week")
    if not df_time.empty:
        df_dow = df_time.groupby('day_of_week')['cnt'].sum().reset_index()
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df_dow['day_of_week'] = pd.Categorical(df_dow['day_of_week'], categories=days, ordered=True)
        df_dow = df_dow.sort_values('day_of_week')
        fig = px.bar(df_dow, x='day_of_week', y='cnt')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

st.subheader("Hour x Day of Week Heatmap")
if not df_time.empty:
    pivot_df = df_time.pivot_table(index='day_of_week', columns='hour', values='cnt', aggfunc='sum').fillna(0)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot_df = pivot_df.reindex(days)
    fig = px.imshow(pivot_df, labels=dict(x="Hour", y="Day of Week", color="Accidents"),
                    aspect="auto", color_continuous_scale='Viridis')
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data available for selected filters.")

st.subheader("Monthly Seasonality")
@st.cache_data(ttl=300)
def get_monthly_seasonality(filters_dict):
    where_str, params = build_filter_clause(filters_dict)
    query = f"""
    SELECT d.month, COUNT(*) as cnt
    FROM analytical.fact_accident f 
    JOIN analytical.dim_date d ON f.date_key=d.date_key 
    JOIN analytical.dim_severity s ON f.severity_key = s.severity_key
    LEFT JOIN analytical.dim_road r ON f.road_key=r.road_key 
    LEFT JOIN analytical.dim_weather w ON f.weather_key=w.weather_key 
    LEFT JOIN analytical.dim_location l ON f.location_key=l.location_key 
    WHERE {where_str} 
    GROUP BY d.month
    ORDER BY d.month
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Error fetching seasonality data: {e}")
        return pd.DataFrame()

df_seasonality = get_monthly_seasonality(filters)
if not df_seasonality.empty:
    fig = px.line(df_seasonality, x='month', y='cnt')
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data available for selected filters.")
