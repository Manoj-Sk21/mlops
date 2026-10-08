import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from sqlalchemy import text
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.filters import build_filter_clause
from components.kpi_card import render_kpi_row

st.title('🗺️ Accident Location Hotspots')

engine = st.session_state.get('engine')
filters = st.session_state.get('filters', {})

if not engine:
    st.error("Database connection not found.")
    st.stop()

@st.cache_data(ttl=300)
def get_location_kpi(filters_dict):
    where_str, params = build_filter_clause(filters_dict)
    query = f"""
    SELECT l.location_key, l.local_authority, s.severity_label, COUNT(*) as cnt
    FROM analytical.fact_accident f 
    JOIN analytical.dim_location l ON f.location_key=l.location_key
    JOIN analytical.dim_severity s ON f.severity_key=s.severity_key
    JOIN analytical.dim_date d ON f.date_key=d.date_key 
    LEFT JOIN analytical.dim_road r ON f.road_key=r.road_key
    LEFT JOIN analytical.dim_weather w ON f.weather_key=w.weather_key 
    WHERE {where_str} 
    GROUP BY l.location_key, l.local_authority, s.severity_label
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Error fetching location KPI data: {e}")
        return pd.DataFrame()

df_loc_kpi = get_location_kpi(filters)

if not df_loc_kpi.empty:
    total_unique_locations = df_loc_kpi['location_key'].nunique()
    most_dangerous_authority = df_loc_kpi.groupby('local_authority')['cnt'].sum().idxmax()
    top_10_hotspot_pct = (df_loc_kpi.groupby('location_key')['cnt'].sum().nlargest(10).sum() / df_loc_kpi['cnt'].sum()) * 100
    
    render_kpi_row([
        {'title': 'Total Unique Locations', 'value': total_unique_locations, 'icon': '📍'},
        {'title': 'Most Dangerous Authority', 'value': most_dangerous_authority, 'icon': '🏢'},
        {'title': 'Top 10 Hotspot %', 'value': f"{top_10_hotspot_pct:.2f}%", 'icon': '🔥'}
    ])
else:
    st.info('No data available for selected filters.')

@st.cache_data(ttl=300)
def get_map_data(filters_dict):
    where_str, params = build_filter_clause(filters_dict)
    query = f"""
    SELECT l.latitude, l.longitude, s.severity_label, COUNT(*) as cnt
    FROM analytical.fact_accident f 
    JOIN analytical.dim_location l ON f.location_key=l.location_key
    JOIN analytical.dim_severity s ON f.severity_key=s.severity_key
    JOIN analytical.dim_date d ON f.date_key=d.date_key 
    LEFT JOIN analytical.dim_road r ON f.road_key=r.road_key
    LEFT JOIN analytical.dim_weather w ON f.weather_key=w.weather_key 
    WHERE {where_str} 
    AND l.latitude IS NOT NULL AND l.longitude IS NOT NULL
    GROUP BY l.latitude, l.longitude, s.severity_label
    ORDER BY cnt DESC
    LIMIT 500
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Error fetching map data: {e}")
        return pd.DataFrame()

st.subheader("Map View (Top 500 Hotspots)")
df_map = get_map_data(filters)
if not df_map.empty:
    m = folium.Map(location=[54.0, -2.0], zoom_start=6)
    
    color_map = {'Fatal': 'red', 'Serious': 'orange', 'Slight': 'green'}
    
    from folium.plugins import HeatMap
    heat_data = [[row['latitude'], row['longitude']] for index, row in df_map.iterrows()]
    HeatMap(heat_data).add_to(m)
    
    for _, row in df_map.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=3 + row['cnt'],
            color=color_map.get(row['severity_label'], 'blue'),
            fill=True,
            fill_opacity=0.7,
            popup=f"{row['severity_label']} - {row['cnt']} accidents"
        ).add_to(m)
        
    st_folium(m, width=None, height=500)
else:
    st.info("No location data with valid coordinates available for selected filters.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 20 Hotspot Locations")
    if not df_loc_kpi.empty:
        df_hotspots = df_loc_kpi.groupby(['local_authority', 'severity_label'])['cnt'].sum().unstack(fill_value=0).reset_index()
        for col in ['Fatal', 'Serious', 'Slight']:
            if col not in df_hotspots.columns:
                df_hotspots[col] = 0
                
        df_hotspots['Total Accidents'] = df_hotspots['Fatal'] + df_hotspots['Serious'] + df_hotspots['Slight']
        df_hotspots = df_hotspots.sort_values('Total Accidents', ascending=False).head(20)
        df_hotspots = df_hotspots.rename(columns={'local_authority': 'Local Authority'})
        st.dataframe(df_hotspots[['Local Authority', 'Total Accidents', 'Fatal', 'Serious']])
    else:
        st.info("No data available for selected filters.")

with col2:
    st.subheader("Regional Breakdown")
    if not df_loc_kpi.empty:
        df_region = df_loc_kpi.groupby('local_authority')['cnt'].sum().reset_index().sort_values('cnt', ascending=False).head(15)
        fig = px.bar(df_region, x='cnt', y='local_authority', orientation='h')
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters.")
