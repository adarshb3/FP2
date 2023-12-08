import streamlit as st
import requests
import json
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates


# Set up the Streamlit interface
st.title('Industrial Electricity Consumption Forecast using AutoML REST Endpoint')
st.write('View historical data and select date range for predictions')

# Initialize empty DataFrames
historical_data = pd.DataFrame()
predictions_df = pd.DataFrame()

# Fetching historical data from GitHub
github_raw_url = 'https://raw.githubusercontent.com/adarshb3/FP2/main/elec_industrial_github2.csv'
try:
    historical_data = pd.read_csv(github_raw_url)
    historical_data['Date'] = pd.to_datetime(historical_data['Date'], format='%d-%m-%Y')
except Exception as e:
    st.error(f"Failed to load historical data from GitHub. Error: {e}")

# Year and Month Selector for the start and end of the range
years = sorted(historical_data['Date'].dt.year.unique(), reverse=True)
months = list(range(1, 13))  # List of months

start_year = st.selectbox("Select Start Year", years)
start_month = st.selectbox("Select Start Month", months)
end_year = st.selectbox("Select End Year", years)
end_month = st.selectbox("Select End Month", months)

# Construct a date for the first day of the selected start and end month and year
start_date = datetime.date(start_year, start_month, 1)
# For end_date, find the last day of the month by using calendar.monthrange
import calendar
end_day = calendar.monthrange(end_year, end_month)[1]
end_date = datetime.date(end_year, end_month, end_day)

# Plotting historical data
if not historical_data.empty:
    fig, ax = plt.subplots()
    ax.plot(historical_data['Date'], historical_data['Total Energy Consumed by the Industrial Sector, Monthly'], label='Historical Data')
    
    # Format x-axis to show Year-Month
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    
    # Improve formatting of the plot
    fig.autofmt_xdate()  # Auto format the x-axis labels for better spacing

    # Setting labels and title
    ax.set_xlabel('Date')  # X-axis label
    ax.set_ylabel('Total Energy Consumed by the Industrial Sector, Monthly')  # Y-axis label
    ax.set_title('Industrial Electricity Consumption')  # Graph title
    ax.legend()

    # Display the plot
    st.pyplot(fig)

# When the user clicks the 'Predict' button
if st.button('Predict'):
    # Prepare the data for prediction with the selected month range
    # Create a list of the first day of each month in the range
    dates_range = pd.date_range(start_date, end_date, freq='MS').tolist()
    formatted_dates = [d.strftime('%Y-%m-%dT%H:%M:%S.000Z') for d in dates_range]
    
    data = {
        "Inputs": {
            "data": [{"Date": date} for date in formatted_dates]
        },
        "GlobalParameters": {
            "quantiles": [0.025, 0.975]
        }
    }

    body = json.dumps(data)

    # REST API endpoint from Azure
    url = 'http://f3a4ef57-ecd3-4b16-9100-874b20af60a3.eastus.azurecontainer.io/score'

    # Make the POST request with error handling
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data=body, headers=headers)

        # If the request is successful, parse the response into a DataFrame
        if response.status_code == 200:
            predictions = response.json()  # Assuming the response is JSON formatted
            
            # Check if 'Results' in the response and if it contains 'forecast' and 'index'
            if 'Results' in predictions and 'forecast' in predictions['Results'] and 'index' in predictions['Results']:
                forecasted_values = predictions['Results']['forecast']
                
                # Extracting the Unix timestamps and converting to datetime
                timestamps = [idx['Date'] for idx in predictions['Results']['index']]
                dates = pd.to_datetime(timestamps, unit='ms')  # Convert Unix timestamp in milliseconds to datetime
                
                # Create a DataFrame using the forecasted values and the converted dates
                predictions_df = pd.DataFrame({
                    'Forecasted Energy Consumption': forecasted_values
                }, index=dates)

                # Plotting the forecast
                if not historical_data.empty and not predictions_df.empty:
                    fig, ax = plt.subplots()
                    ax.plot(historical_data['Date'], historical_data['Total Energy Consumed by the Industrial Sector, Monthly'], label='Historical Data')
                    ax.plot(predictions_df.index, predictions_df['Forecasted Energy Consumption'], label='Forecast')
                    
                    # Format x-axis to show Year-Month
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                    
                    # Improve formatting of the plot
                    fig.autofmt_xdate()  # Auto format the x-axis labels for better spacing
                    
                    # Setting labels and title
                    ax.set_xlabel('Date')  # X-axis label
                    ax.set_ylabel('Total Energy Consumed by the Industrial Sector, Monthly')  # Y-axis label
                    ax.set_title('Industrial Electricity Consumption Forecast')  # Graph title
                    ax.legend()
                    
                    # Display the plot
                    st.pyplot(fig)

                    # Display the forecast data below the graph
                    st.write("Forecasted Energy Consumption:")
                    st.dataframe(predictions_df)
            else:
                st.error('Prediction data is not in the expected format.')
        else:
            st.error(f'Error in API response: {response.status_code}, {response.text}')
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to the API endpoint. Error: {e}")
        st.stop()
