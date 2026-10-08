import streamlit as st
import pandas as pd
from sqlalchemy import text

@st.cache_data(ttl=300)
def load_filter_options(_engine):
    options = {}
    try:
        with _engine.connect() as conn:
            # Date range
            date_range = conn.execute(text("SELECT MIN(full_date), MAX(full_date) FROM analytical.dim_date")).fetchone()
            options['min_date'] = date_range[0]
            options['max_date'] = date_range[1]
            
            # Severity
            severity = conn.execute(text("SELECT severity_label FROM analytical.dim_severity")).fetchall()
            options['severity'] = [r[0] for r in severity]
            
            # Weather
            weather = conn.execute(text("SELECT DISTINCT weather_condition FROM analytical.dim_weather WHERE weather_condition IS NOT NULL")).fetchall()
            options['weather'] = [r[0] for r in weather]
            
            # Road Type
            road = conn.execute(text("SELECT DISTINCT road_type FROM analytical.dim_road WHERE road_type IS NOT NULL")).fetchall()
            options['road_type'] = [r[0] for r in road]
            
            # Region
            region = conn.execute(text("SELECT DISTINCT region FROM analytical.dim_location WHERE region IS NOT NULL")).fetchall()
            options['region'] = [r[0] for r in region]
            
            # Speed Limit
            speed = conn.execute(text("SELECT DISTINCT speed_limit FROM analytical.dim_road WHERE speed_limit IS NOT NULL ORDER BY speed_limit")).fetchall()
            options['speed_limit'] = [r[0] for r in speed]
            
    except Exception as e:
        st.error(f"Error loading filter options: {e}")
        # Return defaults if error
        import datetime
        options = {
            'min_date': datetime.date(2020, 1, 1),
            'max_date': datetime.date.today(),
            'severity': ['Fatal', 'Serious', 'Slight'],
            'weather': ['Fine no high winds', 'Raining no high winds', 'Snowing no high winds'],
            'road_type': ['Single carriageway', 'Dual carriageway', 'Roundabout'],
            'region': ['London', 'North West', 'South East'],
            'speed_limit': [20, 30, 40, 50, 60, 70]
        }
    return options

def render_sidebar_filters(engine):
    st.sidebar.header('🔍 Filters')
    
    options = load_filter_options(engine)
    
    filters = {}
    
    # Date range
    date_val = st.sidebar.date_input(
        "Date Range",
        value=(options['min_date'], options['max_date']),
        min_value=options['min_date'],
        max_value=options['max_date']
    )
    if len(date_val) == 2:
        filters['start_date'] = date_val[0]
        filters['end_date'] = date_val[1]
    
    # Severity
    filters['severity'] = st.sidebar.multiselect("Severity", options['severity'], default=options['severity'])
    
    # Weather
    filters['weather'] = st.sidebar.multiselect("Weather Condition", options['weather'], default=options['weather'])
    
    # Road Type
    filters['road_type'] = st.sidebar.multiselect("Road Type", options['road_type'], default=options['road_type'])
    
    # Region
    filters['region'] = st.sidebar.multiselect("Region", options['region'], default=options['region'])
    
    # Day of Week
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    filters['day_of_week'] = st.sidebar.multiselect("Day of Week", days, default=days)
    
    # Hour Range
    filters['hour_range'] = st.sidebar.slider("Hour Range", 0, 23, (0, 23))
    
    # Speed Limit
    filters['speed_limit'] = st.sidebar.multiselect("Speed Limit", options['speed_limit'], default=options['speed_limit'])
    
    return filters

def build_filter_clause(filters):
    clauses = []
    params = {}
    
    if 'start_date' in filters and 'end_date' in filters:
        clauses.append("d.full_date BETWEEN :start_date AND :end_date")
        params['start_date'] = filters['start_date']
        params['end_date'] = filters['end_date']
        
    if filters.get('severity'):
        clauses.append("s.severity_label IN :severity")
        params['severity'] = tuple(filters['severity'])
        
    if filters.get('weather'):
        clauses.append("w.weather_condition IN :weather")
        params['weather'] = tuple(filters['weather'])
        
    if filters.get('road_type'):
        clauses.append("r.road_type IN :road_type")
        params['road_type'] = tuple(filters['road_type'])
        
    if filters.get('region'):
        clauses.append("l.region IN :region")
        params['region'] = tuple(filters['region'])
        
    if filters.get('day_of_week'):
        clauses.append("TRIM(d.day_name) IN :day_of_week")
        params['day_of_week'] = tuple(filters['day_of_week'])
        
    if 'hour_range' in filters:
        clauses.append("EXTRACT(HOUR FROM f.accident_time) BETWEEN :start_hour AND :end_hour")
        params['start_hour'] = filters['hour_range'][0]
        params['end_hour'] = filters['hour_range'][1]
        
    if filters.get('speed_limit'):
        clauses.append("r.speed_limit IN :speed_limit")
        params['speed_limit'] = tuple(filters['speed_limit'])
        
    where_clause = " AND ".join(clauses) if clauses else "1=1"
    
    return where_clause, params
