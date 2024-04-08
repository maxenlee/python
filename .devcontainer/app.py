import streamlit as st
import pandas as pd
import sqlalchemy
import altair as alt
import plotly.express as px
import os
import psycopg2
from scipy.stats.mstats import winsorize
import datetime

# Fetch the value of the 'CONN' environment variable
# conn_value = os.getenv('CONN', 'Not Found')
conn_value = st.secrets["CONN"]
# Database connection details
DATABASE_URL = conn_value

# Establishing a connection to the database
engine = sqlalchemy.create_engine(DATABASE_URL)

# Function to load data based on filters, adapted for date range and single selection
def load_data(ind_code, loc_code, start_date, end_date):
    query = """
    SELECT yr_mn_d AS date, biz_count, yr, mn, loc_code, naics_code::text, naics_description, ind_code, ind, loc, gr
    FROM nm_taxes.nm_tax_months
    WHERE ind_code = %s AND loc_code = %s
    AND yr BETWEEN %s AND %s
    """
    params = (ind_code, loc_code, start_date, end_date)
    return pd.read_sql_query(query, engine, params=params)

# UI Components
st.title("NM Tax Gross Receipts")

# Fetching unique locations and industries for dropdowns
loc_df = pd.read_sql_query("SELECT DISTINCT loc, loc_code FROM nm_taxes.nm_tax_months ORDER BY loc", engine)
ind_df = pd.read_sql_query("SELECT DISTINCT ind, ind_code FROM nm_taxes.nm_tax_months ORDER BY ind", engine)

# Convert loc and ind to string format with codes for selectbox
loc_options = loc_df.apply(lambda x: f"{x['loc']} ({x['loc_code']})", axis=1).tolist()
ind_options = ind_df.apply(lambda x: f"{x['ind']} ({x['ind_code']})", axis=1).tolist()

# Creating selectboxes for location and industry
selected_loc = st.selectbox("Select Location", options=loc_options, index=12)
selected_ind = st.selectbox("Select Industry", options=ind_options, index=8)

# Extracting 'loc_code' and 'ind_code' from the selections
selected_loc_code = selected_loc.split('(')[-1].rstrip(')')
selected_ind_code = selected_ind.split('(')[-1].rstrip(')')

# Select a date range
start_date, end_date = st.slider("Select Year Range", min_value=2000, max_value=2023, value=(2020, 2023))

# Loading filtered data
filtered_data = load_data(selected_ind_code, selected_loc_code, start_date, end_date)

# Assuming 'filtered_data' has been loaded and includes 'naics_code' and 'naics_description'

# Unique NAICS descriptions
unique_naics = filtered_data[['naics_code', 'naics_description']].drop_duplicates().sort_values('naics_code')

# Convert the DataFrame to a Markdown string
naics_md = "\n".join(
    [f"- **{row['naics_code']}**: {row['naics_description']}" for index, row in unique_naics.iterrows()]
)

# Use st.expander to display NAICS codes and their descriptions
with st.expander("View NAICS Codes and Descriptions"):
    st.markdown(naics_md)

# Button to toggle y-axis type
if st.button('Toggle Y-Axis Scale'):
    # Check if the session state already has the toggle value; if not, initialize it
    if 'yaxis_type' not in st.session_state:
        st.session_state['yaxis_type'] = 'log'
    # Switch between 'linear' and 'log'
    elif st.session_state['yaxis_type'] == 'linear':
        st.session_state['yaxis_type'] = 'log'
    else:
        st.session_state['yaxis_type'] = 'linear'

# Specify the default y-axis type if the toggle hasn't been used yet
yaxis_type = st.session_state.get('yaxis_type', 'linear')

# Plot generation with dynamic y-axis based on the toggle state
fig = px.bar(filtered_data,
             x="date",
             y="gr",
             color="naics_code",
             text="biz_count",
             title=f'Gross Receipts for Selected Industries in Selected Locations from {start_date} to {end_date}',
             labels={"gr": "Gross Receipts", "naics_code": "NAICS Code", "date": "Date"},
             hover_data=["date", "gr", "naics_code", "biz_count"])
fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Gross Receipts",
    yaxis_type=yaxis_type,  # Use the dynamic y-axis type
    legend_title="NAICS Code",
    barmode='stack'
)

st.plotly_chart(fig, use_container_width=True)




# Assuming 'filtered_data' is already loaded and contains the relevant data
# Aggregating data by date for the line chart
# This assumes 'date' is in a suitable format (e.g., datetime); if not, you may need to convert it

# Aggregate 'gr' by 'date', summing up the values. Adjust this aggregation based on your specific needs
agg_data = filtered_data.groupby('date')['gr'].sum().reset_index()

# Apply winsorization to the 'gr' column of your aggregated data
# Here, we're winsorizing the bottom and top 5% as an example
# Adjust the limits as needed for your dataset
agg_data['gr_winsorized'] = winsorize(agg_data['gr'], limits=[0.05, 0.05])

# Creating a line chart with Plotly, using the winsorized data
line_fig = px.line(agg_data,
                   x='date',
                   y='gr_winsorized',
                   title='Trend of Winsorized Gross Receipts Over Time',
                   labels={'gr_winsorized': 'Winsorized Gross Receipts', 'date': 'Date'})

# Customizing the layout further if needed
line_fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Winsorized Gross Receipts",
    yaxis_type="linear"  # or "log" based on your preference
)

# Displaying the line chart in Streamlit
st.plotly_chart(line_fig, use_container_width=True)