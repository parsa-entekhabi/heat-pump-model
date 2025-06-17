import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Heat Pump Model", layout="wide", page_icon='⚡')
st.title("Heat Pump Building Modeling")

st.markdown("""
**Welcome to the Heat Pump Model App!**

This app allows you to:
- Upload power usage data (hourly or 15-minute intervals)
- Upload NOAA temperature data
- Adjust heating and cooling setpoints
- Use custom heat pump performance data
- Simulate and compare energy usage with a heat pump/retrofit under different desired temperature conditions 

**Supported Inputs**:
- Energy CSV with **only one** column that represents power in kW
- Temperature CSV from NOAA with daily high/low
- Heat Pump COP and EER CSV performance parameters

**Current Assumptions/Limitations**
- Current building only uses resistive heating for temp control
- No heat accumulation in building
- Building must not currently have cooling
- Cooling model is 2x the usage of the heating model
- Cannot support energy (kWh) input
- Energy cost is fixed

**Email me with any bugs!**
- parsanick11@gmail.com

""")


# Declare placeholder variables to fill based on the data type
energy_file = None
temp_file = None
date_range = None
power_column = None
hourlyEnergy = None
dataType = None
gasUnit = None

dataType = st.selectbox(
  "Which bill are we analyzing? (gas doesn't currently work)",
  ('Electric', 'Gas')
)

if dataType == 'Gas':
  gasUnit = st.radio("Select Energy Unit", ["CCF", "Btu", "Therms", "MJ", "kWh"])

if gasUnit == "CCF":
  gasConv = 30.36
elif gasUnit == "Btu":
  gasConv = (30.36/103,600)
elif gasUnit == "Therms":
  gasConv = (30.36/1.036)
elif gasUnit == "MJ":
  gasConv = (30.36/109.3)
elif gasUnit == "kWh":
  gasConv = 1
elif gasUnit == None:
  gasConv = 1

year = st.number_input("Enter year data is from (ie. 2023). Leap years currently don't work.", 
                       value=2023)

column_name = st.text_input("Enter exact header name of column for power data (case sensitive!)",
                            value='Power')

retro = st.number_input("Enter % building retrofit",
                            value=30)

retro = retro/100

cost = st.number_input("Enter energy cost per kWh in $",
                       value = 0.1241)

hp_input = st.selectbox(
    "Do you want to import custom heat pump performance data, or just use a deafult one (DZ17VSA361B* + DV36FECC14A*)",
    ('Default','Custom')
)

customCOP = None
customEER = None

if hp_input == 'Default':
    from CustomHP import EER
    from CustomHP import COP
    

elif hp_input == 'Custom':
    st.write('COP Data')
    customCOP = st.file_uploader("Upload CSV with two columns named 'Temp' and 'COP' (case sensitive)", type='csv')
    if customCOP is not None:
        customCOPfile = pd.read_csv(customCOP)
        
        temp = customCOPfile['Temp']
        COP = customCOPfile['COP']
        
        COP_line = stats.linregress(temp,COP)
        
        def COP(T):
            return COP_line.slope*T + COP_line.intercept
    
    st.write('EER Data')
    customEER = st.file_uploader("Upload CSV with three columns named 'totalBTU' 'totalWATT' and 'temp' (case sensitive)", type='csv')
    if customEER is not None:
        customEERfile = pd.read_csv(customEER)
        
        totalBTU = customEERfile['totalBTU']
        totalWATT = customEERfile['totalWATT']
        temp =  customEERfile['temp']
        
        EER = []

        for i, j in zip(totalBTU, totalWATT):
            sol = i/j
            EER.append(sol)

        EER_line = stats.linregress(temp, EER)

        def EER(T):
            return (EER_line.slope*T + EER_line.intercept)

freq = st.selectbox(
    "What type of data are you using?",
    ("Hourly", "15-Minute")
)

if freq == 'Hourly':
    #data_type = st.selectbox('Select Data Type',('Energy (kWh)','Power (kW'))
    st.write('Upload Hourly Power CSV')
    energy_file = st.file_uploader('Upload CSV File', type='csv')
    date_range = pd.date_range(start=f'{year}-01-01', periods=8760, freq='h')
    if energy_file is not None and temp_file is not None:
        data = pd.read_csv(energy_file)

        if date_range is not None:
            data.insert(0, 'DATE', date_range.date)
            data.insert(1, 'TIME', date_range.time)
            
            data['DATE'] = pd.to_datetime(data['DATE'], format='%Y-%m-%d')
            data['TIME'] = pd.to_datetime(data['TIME'], format='%H:%M:%S')

            
            data['HourOfYear'] = data['TIME'].dt.hour
            data['DayOfYear'] = data['DATE'].dt.dayofyear
            
            # Remove Unnamed Columns
            cols_to_drop = [3,4,5,6,7,8]
            cols_to_drop = [i for i in cols_to_drop if i < len(data.columns)]
            data.drop(data.columns[cols_to_drop], axis=1, inplace=True)
            
            energy = data[f'{column_name}']
            data.insert(3, 'Energy', energy)

            
            hourlyEnergy = energy
            

elif freq == "15-Minute":
    st.write('Upload 15-Min Power CSV')
    energy_file = st.file_uploader('Upload CSV File', type='csv')
    date_range = pd.date_range(start=f'{year}-01-01', periods=35040, freq='15min')
    if energy_file is not None and temp_file is not None:
        data = pd.read_csv(energy_file)

        if date_range is not None:
            data.insert(0, 'DATE', date_range.date)
            data.insert(1, 'TIME', date_range.time)
            
            # Remove Unnamed Columns
            cols_to_drop = [3,4,5,6,7,8]
            cols_to_drop = [i for i in cols_to_drop if i < len(data.columns)]
            data.drop(data.columns[cols_to_drop], axis=1, inplace=True)
            
            energy = data[f'{column_name}'] * 0.25
            data.insert(3, 'Energy', energy)
            
            # Group 15 minute energy data by hour in year
            hourlyEnergy = data.groupby(['DayOfYear', 'HourOfYear'])['Energy'].sum().reset_index()


temp_file = st.file_uploader("Upload Temperature CSV File, use NOAA databases",
                             type="csv")





if energy_file is not None and temp_file is not None and year is not None and column_name is not None:
    try:
        from electricDataProcessing import electricModel

        electricModel(energy_file, temp_file, date_range, column_name, retro, cost, year)
        
        

    except Exception as e:
        st.error(f"Error processing files: {e}")
else:
    st.info("Please upload both CSV files and define inputs to begin.")


    
