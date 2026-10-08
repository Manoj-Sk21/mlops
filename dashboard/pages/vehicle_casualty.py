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

st.title('🚗 Vehicle & Casualty Analysis')

engine = st.session_state.get('engine')
filters = st.session_state.get('filters', {})

if not engine:
    st.error("Database connection not found.")
    st.stop()

@st.cache_data(ttl=300)
def get_vc_kpi(filters_dict):
    where_str, params = build_filter_clause(filters_dict)
    query_acc = f"""
    SELECT f.accident_id 
    FROM analytical.fact_accident f 
    JOIN analytical.dim_date d ON f.date_key=d.date_key 
    JOIN analytical.dim_severity s ON f.severity_key = s.severity_key
    LEFT JOIN analytical.dim_road r ON f.road_key=r.road_key 
    LEFT JOIN analytical.dim_weather w ON f.weather_key=w.weather_key 
    LEFT JOIN analytical.dim_location l ON f.location_key=l.location_key 
    WHERE {where_str}
    """
    
    query_v = f"SELECT COUNT(*) as v_cnt, mode() WITHIN GROUP (ORDER BY vehicle_type) as common_v FROM analytical.fact_vehicle WHERE accident_id IN ({query_acc})"
    query_c = f"SELECT COUNT(*) as c_cnt, SUM(CASE WHEN casualty_class='Pedestrian' THEN 1 ELSE 0 END) as ped_cnt FROM analytical.fact_casualty WHERE accident_id IN ({query_acc})"
    
    try:
        with engine.connect() as conn:
            df_v = pd.read_sql(text(query_v), conn, params=params)
            df_c = pd.read_sql(text(query_c), conn, params=params)
            return df_v, df_c
    except Exception as e:
        st.error(f"Error fetching Vehicle/Casualty KPI data: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_v, df_c = get_vc_kpi(filters)

if not df_v.empty and not df_c.empty:
    total_vehicles = df_v['v_cnt'].iloc[0]
    most_common_v = df_v['common_v'].iloc[0]
    total_casualties = df_c['c_cnt'].iloc[0]
    ped_casualties = df_c['ped_cnt'].iloc[0]
    
    render_kpi_row([
        {'title': 'Total Vehicles', 'value': f"{total_vehicles:,}", 'icon': '🚗'},
        {'title': 'Total Casualties', 'value': f"{total_casualties:,}", 'icon': '👥'},
        {'title': 'Most Common Vehicle', 'value': str(most_common_v)[:20], 'icon': '🏆'},
        {'title': 'Pedestrian Casualties', 'value': f"{ped_casualties:,}", 'icon': '🚶'}
    ])
else:
    st.info('No data available for selected filters.')

col1, col2 = st.columns(2)

@st.cache_data(ttl=300)
def get_vehicle_type(filters_dict):
    where_str, params = build_filter_clause(filters_dict)
    query = f"""
    SELECT vehicle_type, COUNT(*) as cnt 
    FROM analytical.fact_vehicle 
    WHERE accident_id IN (
        SELECT f.accident_id 
        FROM analytical.fact_accident f 
        JOIN analytical.dim_date d ON f.date_key=d.date_key 
        JOIN analytical.dim_severity s ON f.severity_key = s.severity_key
        LEFT JOIN analytical.dim_road r ON f.road_key=r.road_key 
        LEFT JOIN analytical.dim_weather w ON f.weather_key=w.weather_key 
        LEFT JOIN analytical.dim_location l ON f.location_key=l.location_key 
        WHERE {where_str}
    )
    GROUP BY vehicle_type
    ORDER BY cnt DESC
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Error fetching vehicle types: {e}")
        return pd.DataFrame()

with col1:
    st.subheader("Vehicle Type Distribution")
    df_vtype = get_vehicle_type(filters)
    if not df_vtype.empty:
        fig = px.bar(df_vtype.head(15), x='cnt', y='vehicle_type', orientation='h')
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

@st.cache_data(ttl=300)
def get_casualty_class(filters_dict):
    where_str, params = build_filter_clause(filters_dict)
    query = f"""
    SELECT casualty_class, COUNT(*) as cnt 
    FROM analytical.fact_casualty 
    WHERE accident_id IN (
        SELECT f.accident_id 
        FROM analytical.fact_accident f 
        JOIN analytical.dim_date d ON f.date_key=d.date_key 
        JOIN analytical.dim_severity s ON f.severity_key = s.severity_key
        LEFT JOIN analytical.dim_road r ON f.road_key=r.road_key 
        LEFT JOIN analytical.dim_weather w ON f.weather_key=w.weather_key 
        LEFT JOIN analytical.dim_location l ON f.location_key=l.location_key 
        WHERE {where_str}
    )
    GROUP BY casualty_class
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Error fetching casualty classes: {e}")
        return pd.DataFrame()

with col2:
    st.subheader("Casualty Class Breakdown")
    df_cclass = get_casualty_class(filters)
    if not df_cclass.empty:
        fig = px.pie(df_cclass, values='cnt', names='casualty_class', hole=0.4)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

col3, col4 = st.columns(2)

@st.cache_data(ttl=300)
def get_casualty_age_sex(filters_dict):
    where_str, params = build_filter_clause(filters_dict)
    query = f"""
    SELECT age_of_casualty, sex_of_casualty 
    FROM analytical.fact_casualty 
    WHERE accident_id IN (
        SELECT f.accident_id 
        FROM analytical.fact_accident f 
        JOIN analytical.dim_date d ON f.date_key=d.date_key 
        JOIN analytical.dim_severity s ON f.severity_key = s.severity_key
        LEFT JOIN analytical.dim_road r ON f.road_key=r.road_key 
        LEFT JOIN analytical.dim_weather w ON f.weather_key=w.weather_key 
        LEFT JOIN analytical.dim_location l ON f.location_key=l.location_key 
        WHERE {where_str}
    )
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Error fetching casualty age/sex: {e}")
        return pd.DataFrame()

df_case = get_casualty_age_sex(filters)

with col3:
    st.subheader("Casualty Age Distribution")
    if not df_case.empty:
        df_case['age_of_casualty'] = pd.to_numeric(df_case['age_of_casualty'], errors='coerce')
        fig = px.histogram(df_case, x='age_of_casualty', nbins=20)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

with col4:
    st.subheader("Sex of Casualties")
    if not df_case.empty:
        sex_df = df_case['sex_of_casualty'].value_counts().reset_index()
        sex_df.columns = ['sex_of_casualty', 'cnt']
        fig = px.bar(sex_df, x='sex_of_casualty', y='cnt')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

st.subheader("Driver Age Band Analysis")
@st.cache_data(ttl=300)
def get_driver_age_band(filters_dict):
    where_str, params = build_filter_clause(filters_dict)
    query = f"""
    SELECT age_band_of_driver, COUNT(*) as cnt 
    FROM analytical.fact_vehicle 
    WHERE accident_id IN (
        SELECT f.accident_id 
        FROM analytical.fact_accident f 
        JOIN analytical.dim_date d ON f.date_key=d.date_key 
        JOIN analytical.dim_severity s ON f.severity_key = s.severity_key
        LEFT JOIN analytical.dim_road r ON f.road_key=r.road_key 
        LEFT JOIN analytical.dim_weather w ON f.weather_key=w.weather_key 
        LEFT JOIN analytical.dim_location l ON f.location_key=l.location_key 
        WHERE {where_str}
    )
    GROUP BY age_band_of_driver
    ORDER BY age_band_of_driver
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Error fetching driver age band: {e}")
        return pd.DataFrame()

df_dage = get_driver_age_band(filters)
if not df_dage.empty:
    fig = px.bar(df_dage, x='age_band_of_driver', y='cnt')
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data available for selected filters.")
