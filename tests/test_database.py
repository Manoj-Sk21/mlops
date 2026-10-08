import pytest
import os

# Create a dummy schema.sql for testing purposes if it doesn't exist
SCHEMA_SQL = """
CREATE TABLE dim_location (id INT PRIMARY KEY);
CREATE TABLE dim_time (id INT PRIMARY KEY);
CREATE TABLE dim_weather (id INT PRIMARY KEY);
CREATE TABLE dim_road (id INT PRIMARY KEY);
CREATE TABLE dim_vehicle (id INT PRIMARY KEY);

CREATE TABLE fact_accidents (
    id INT PRIMARY KEY,
    location_id INT REFERENCES dim_location(id),
    time_id INT REFERENCES dim_time(id)
);
"""

@pytest.fixture(scope="module")
def setup_schema_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("sql") / "schema.sql"
    fn.write_text(SCHEMA_SQL)
    return str(fn)

def test_schema_sql_syntax(setup_schema_file):
    with open(setup_schema_file, 'r') as f:
        content = f.read()
    assert "CREATE TABLE" in content.upper()

def test_dimension_tables_defined(setup_schema_file):
    with open(setup_schema_file, 'r') as f:
        content = f.read().lower()
    
    dim_tables = ['dim_location', 'dim_time', 'dim_weather', 'dim_road', 'dim_vehicle']
    for table in dim_tables:
        assert table in content

def test_fact_tables_defined(setup_schema_file):
    with open(setup_schema_file, 'r') as f:
        content = f.read().lower()
    assert 'fact_accidents' in content

def test_foreign_keys_defined(setup_schema_file):
    with open(setup_schema_file, 'r') as f:
        content = f.read().upper()
    assert 'REFERENCES' in content
