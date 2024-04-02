import streamlit as st
import pandas as pd
import sqlalchemy
import altair as alt
import os
import psycopg2
connection_string = os.getenv("CONN")


# Fetch the value of the 'CONN' environment variable
# with 'Not Found' as the default value if it doesn't exist
conn_value = os.getenv('CONN', 'Not Found')


# st.write(connection_string.)

# Database connection details
DATABASE_URL = conn_value  # Change this to your database connection string

# Establishing a connection to the database
engine = sqlalchemy.create_engine(DATABASE_URL)

# Function to load data based on filters
def load_data(ind_code, loc_code, year):
    query = """
    SELECT biz_count, yr, mn, loc_code, naics_code, ind_code, gr
    FROM nm_taxes.nm_tax_months
    WHERE ind_code = %s AND loc_code = %s AND yr = %s
    """
    return pd.read_sql_query(query, engine, params=(ind_code, loc_code, year))

# UI Components
st.title("Filtered Data Visualization")

# Fetching unique ind_code and loc_code for dropdowns
ind_codes = pd.read_sql_query("SELECT DISTINCT ind_code FROM nm_taxes.nm_tax_months", engine)
loc_codes = pd.read_sql_query("SELECT DISTINCT loc_code FROM nm_taxes.nm_tax_months", engine)

selected_ind_code = st.selectbox("Select Industry Code", list(ind_codes['ind_code']))
selected_loc_code = st.selectbox("Select Location Code", list(loc_codes['loc_code']))
selected_year = st.slider("Select Year", min_value=2000, max_value=2023, value=2023)

# Loading filtered data
filtered_data = load_data(selected_ind_code, selected_loc_code, selected_year)

# Visualization with Altair
chart = alt.Chart(filtered_data).mark_bar().encode(
    x='mn:N',
    y='biz_count:Q',
    color='loc_code:N',
    tooltip=['yr', 'mn', 'biz_count', 'loc_code']
).properties(
    title=f'Business Count for Industry {selected_ind_code} in Location {selected_loc_code} for Year {selected_year}'
).interactive()

st.altair_chart(chart, use_container_width=True)
