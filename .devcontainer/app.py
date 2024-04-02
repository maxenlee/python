import streamlit as st
import pandas as pd
import sqlalchemy
import altair as alt
import os
import psycopg2
import datetime

# Fetch the value of the 'CONN' environment variable
# with 'Not Found' as the default value if it doesn't exist
conn_value = os.getenv('CONN', 'Not Found')

# Database connection details
DATABASE_URL = conn_value  # Change this to your database connection string

# Establishing a connection to the database
engine = sqlalchemy.create_engine(DATABASE_URL)


# Function to load data based on filters, adapted for date range and multiple selections
def load_data(ind_codes, loc_codes, start_date, end_date):
    ind_placeholders = ', '.join(['%s'] * len(ind_codes))
    loc_placeholders = ', '.join(['%s'] * len(loc_codes))
    
    # Adjust query to use the correct date column name 'yr_mn_d'
    query = f"""
    SELECT yr_mn_d AS date, biz_count, yr, mn, loc_code, naics_code, ind_code, ind, loc, gr
    FROM nm_taxes.nm_tax_months
    WHERE ind_code IN ({ind_placeholders}) AND loc_code IN ({loc_placeholders})
    AND yr_mn_d BETWEEN %s AND %s
    """
    params = tuple(ind_codes) + tuple(loc_codes) + (start_date, end_date)
    return pd.read_sql_query(query, engine, params=params)

# UI Components
st.title("Data Visualization with Date Range")

# Fetching unique locations and industries for dropdowns
loc_df = pd.read_sql_query("SELECT DISTINCT loc, loc_code FROM nm_taxes.nm_tax_months ORDER BY loc", engine)
ind_df = pd.read_sql_query("SELECT DISTINCT ind, ind_code FROM nm_taxes.nm_tax_months ORDER BY ind", engine)

# Convert loc and ind to string format with codes for multiselect
loc_options = loc_df.apply(lambda x: f"{x['loc']} ({x['loc_code']})", axis=1)
ind_options = ind_df.apply(lambda x: f"{x['ind']} ({x['ind_code']})", axis=1)

# Creating multiselect dropdowns for locations and industries
selected_locs = st.multiselect("Select Locations", options=loc_options, default=loc_options[:1])
selected_inds = st.multiselect("Select Industries", options=ind_options, default=ind_options[:1])

# Extracting 'loc_code' and 'ind_code' from the selections
selected_loc_codes = [loc.split('(')[-1].rstrip(')') for loc in selected_locs]
selected_ind_codes = [ind.split('(')[-1].rstrip(')') for ind in selected_inds]

# Select a date range
start_date, end_date = st.date_input("Select Date Range", [datetime.date(2020, 1, 1), datetime.date(2023, 12, 31)])

# Ensure start_date and end_date are in the format expected by your SQL database
start_date = start_date.strftime('%Y-%m-%d')
end_date = end_date.strftime('%Y-%m-%d')

# Loading filtered data
filtered_data = load_data(selected_ind_codes, selected_loc_codes, start_date, end_date)

# Visualization with Altair
chart = alt.Chart(filtered_data).mark_bar().encode(
    x='date:T',  # Altair uses 'T' for temporal (date or time) data types
    y='gr:Q',
    color='naics_code:N',
    tooltip=['date:T', 'gr', 'naics_code', 'biz_count']
).properties(
    title=f'Gross Receipts for Selected Industries in Selected Locations from {start_date} to {end_date}'
).interactive()

st.altair_chart(chart, use_container_width=True)