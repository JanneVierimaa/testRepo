import streamlit as st
import pandas as pd

# Page configuration
st.set_page_config(page_title="Electricity Consumption & Price Analysis", layout="wide")

st.title("Electricity Consumption and Price Analysis")

# 1. DATA LOADING AND PREPROCESSING
@st.cache_data
def load_data():
    df_cons = pd.read_csv("Electricity_consumption_2015-2025.csv", sep=",")
    df_cons.columns = df_cons.columns.str.strip()
    df_cons['time'] = pd.to_datetime(df_cons['time'])

    df_price = pd.read_csv("Electricity_price_2015-2025.csv", sep=";", decimal=",")
    df_price.columns = df_price.columns.str.strip()
    df_price['time'] = pd.to_datetime(df_price['timestamp'], format='%H:%M %m/%d/%Y')

    df = pd.merge(df_cons, df_price[['time', 'Price']], on='time', how='inner')
    df['Bill_EUR'] = df['kWh'] * (df['Price'] / 100)

    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading files: {e}")
    st.stop()

# 2. USER INTERFACE / FILTERS
st.sidebar.header("Settings")

min_date = df['time'].dt.date.min()
max_date = df['time'].dt.date.max()

start_date = st.sidebar.date_input(
    "Start time",
    value=min_date,
    min_value=min_date,
    max_value=max_date,
    format="YYYY/MM/DD"
)

end_date = st.sidebar.date_input(
    "End time",
    value=max_date,
    min_value=min_date,
    max_value=max_date,
    format="YYYY/MM/DD"
)

grouping_option = st.sidebar.selectbox(
    "Select Grouping Interval",
    options=['Daily', 'Weekly', 'Monthly']
)

freq_map = {
    'Daily': 'D',
    'Weekly': 'W',
    'Monthly': 'ME'   # käytä 'M', jos pandas < 2.2
}
freq = freq_map[grouping_option]

# 3. DATA PROCESSING AND DISPLAY
if start_date <= end_date:
    mask = (df['time'].dt.date >= start_date) & (df['time'].dt.date <= end_date)
    filtered_df = df.loc[mask].copy()

    if filtered_df.empty:
        st.warning("No data available for the selected period.")
    else:
        total_consumption = filtered_df['kWh'].sum()
        total_bill = filtered_df['Bill_EUR'].sum()
        avg_hourly_price = filtered_df['Price'].mean()
        avg_temp = filtered_df['Temperature'].mean()

        if total_consumption > 0:
            avg_paid_price = (total_bill * 100) / total_consumption
        else:
            avg_paid_price = 0.0

        st.write(f"Showing range: `{start_date}` - `{end_date}`")
        st.write("")

        st.subheader("Summary for Selected Period")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Consumption", f"{total_consumption:.1f} kWh")
        col2.metric("Total Bill", f"{total_bill:.2f} €")
        col3.metric("Avg Hourly Price", f"{avg_hourly_price:.2f} c/kWh")
        col4.metric("Avg Paid Price", f"{avg_paid_price:.2f} c/kWh")
        col5.metric("Avg Temperature", f"{avg_temp:.1f} °C")

        st.markdown("---")

        grouped_df = (
            filtered_df.set_index('time')
            .resample(freq)
            .agg({
                'kWh': 'sum',
                'Bill_EUR': 'sum',
                'Price': 'mean',
                'Temperature': 'mean'
            })
        )

        st.subheader(f"Line Graphs ({grouping_option})")

        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.write("**Electricity Consumption**")
            st.line_chart(
                grouped_df['kWh'],
                x_label="Time",
                y_label="Electricity consumption (kWh)"
            )

            st.write("**Average Price**")
            st.line_chart(
                grouped_df['Price'],
                x_label="Time",
                y_label="Electricity price (c/kWh)"
            )

        with col_chart2:
            st.write("**Electricity Bill**")
            st.line_chart(
                grouped_df['Bill_EUR'],
                x_label="Time",
                y_label="Electricity bill (€)"
            )

            st.write("**Average Temperature**")
            st.line_chart(
                grouped_df['Temperature'],
                x_label="Time",
                y_label="Temperature (°C)"
            )
else:
    st.error("Error: Start time must be before or equal to End time.")