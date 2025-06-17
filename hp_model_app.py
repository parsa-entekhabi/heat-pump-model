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
        def func1(energy_file, temp_file):
          data = pd.read_csv(energy_file)
          tempData = pd.read_csv(temp_file)
  
          
          ### Import Energy Usage
          
          
          
          # Generate datetime index. Had to use 2023 since 2024 had a leap year, but we removed leap year from meter data
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
          
          energy = data[f'{column_name}'] * 0.25
          data.insert(3, 'Energy', energy)
  
          
          
          
          
          
              ### Import Temp Data
          
          
          
          tempData['TAVG'] = ( tempData['TMAX'] + tempData['TMIN'] ) / 2
          
          
          
          
          
            ###  Manipulate Energy Data & Temp Data
          
          
          
          
          # Conver to Datetime
          data['DATE'] = pd.to_datetime(data['DATE'], format='%Y-%m-%d')
          data['TIME'] = pd.to_datetime(data['TIME'], format='%H:%M:%S')
          tempData['DATE'] = pd.to_datetime(tempData['DATE'])
          
          data['HourOfYear'] = data['TIME'].dt.hour
          data['DayOfYear'] = data['DATE'].dt.dayofyear
          
          # Group 15 minute energy data by hour in year
          hourlyEnergy = data.groupby(['DayOfYear', 'HourOfYear'])['Energy'].sum().reset_index()
          
          hourlyEnergy['DayOfYear'] = pd.to_datetime(hourlyEnergy['DayOfYear'], format='%j')
          
          hourlyEnergy['month'] = hourlyEnergy['DayOfYear'].dt.month
          
          monthlyEnergy = hourlyEnergy.groupby('month')['Energy'].mean()
          monthlyEnergyTotal = hourlyEnergy.groupby('month')['Energy'].sum()
          
          # Group temperature values by month and take average
          tempData['tempMonths'] = tempData['DATE'].dt.month
          monthlyTemp = tempData.groupby('tempMonths')['TAVG'].mean()
          
          hourlyEnergy['month_day'] = pd.to_datetime(hourlyEnergy['DayOfYear']).dt.strftime('%m-%d')
          tempData['month_day'] = pd.to_datetime(tempData['DATE']).dt.strftime('%m-%d')
          
          fig, ax = plt.subplots(figsize=(12,6))
  
          ax.scatter(monthlyTemp.values, monthlyEnergy)
          ax.set_xlabel("Monthly Average Temperature (°F)")
          ax.set_ylabel("Avg Hourly Electricity for Month (kWh)")
          ax.set_title(f'Energy Demand vs. Temperature in {year}')
          
          st.pyplot(fig)
          
              ### Separating Heating from Base Energy Usage
  
          st.subheader('Separating Heating from Base Energy Usage')
  
        
          splitTemp = st.number_input("Enter a temperature value (\u00b0F) that is between the heating and base loads:")
  
          
        
          x1 = np.array(monthlyTemp.values)
          y1 = np.array(monthlyEnergy)
          
          tempValues1 = x1[(x1 <= splitTemp)]
          energyValues1 = y1[(x1 <= splitTemp)]
          tempValues2 = x1[(x1 >= splitTemp)]
          energyValues2 = y1[(x1 >= splitTemp)]
          
          fit1 = stats.linregress(tempValues1, energyValues1)
          line1 = fit1.slope*tempValues1 + fit1.intercept
          fit2 = stats.linregress(tempValues2, energyValues2)
          line2 = fit2.slope*tempValues2 + fit2.intercept
  
  
          fig1, ax = plt.subplots(figsize=(12,6))
          ax.scatter(x1, y1, color = 'b')
          ax.plot(tempValues1, line1, label = f'Heating Load, Slope = {fit1.slope:.2f}, Intercept = {fit1.intercept:.2f}', color = 'purple')
          ax.plot(tempValues2, line2, label = f'Base Load, Slope = {fit2.slope:.2f}, Intercept = {fit2.intercept:.2f}', color = 'green')
          ax.legend()
          ax.set_xlabel("Monthly Average Temperature (°F)")
          ax.set_ylabel("Avg Hourly Electricity for Month (kWh)")
          ax.set_title(f'Energy Demand vs. Temperature in {year}')
  
          st.pyplot(fig1)
          
          hourlyEnergy['heatUsage'] = np.where(hourlyEnergy['Energy'] - fit2.intercept < 0, 0, hourlyEnergy['Energy'] - fit2.intercept)
          hourlyEnergy['lighting'] = hourlyEnergy['Energy'] - hourlyEnergy['heatUsage']
          
          hourlyEnergy['month'] = hourlyEnergy['DayOfYear'].dt.month
          
          monthlyEnergyHeating = hourlyEnergy.groupby('month')['heatUsage'].mean()
          monthlyEnergyLighting = hourlyEnergy.groupby('month')['lighting'].mean()
          
          monthlyEnergyHeatingTotal = hourlyEnergy.groupby('month')['heatUsage'].sum()
          monthlyEnergyLightingTotal = hourlyEnergy.groupby('month')['lighting'].sum()
          
          
          
          
          
          
          
            ###  Merge Temp Data to get hourly temps (just makes daily temps equal to hourly)
          
          
          
          
          merged = pd.merge(hourlyEnergy, tempData, how='left', on='month_day')
          
          
          
          
          
          
            ###  Create Sinusoidal Model of Data
          
          
          
          
          hourlyTempAvg = merged['TAVG']
          delta_Tday = merged['TMAX']- merged['TMIN']
          hoursInYear = np.arange(0, 8760, 1)
          
          sinT =  hourlyTempAvg - delta_Tday*np.cos((2*np.pi*hoursInYear)/24)
          
          fig = go.Figure()
  
          fig.add_trace(go.Scatter(
              x=hoursInYear,
              y=sinT,
              mode='markers',
              marker=dict(symbol='x', color='blue'),
              name='Sinusoidal Temp',
              hovertemplate='Hour: %{x}<br>Temp: %{y:.2f} °F'
          ))
          
          fig.update_layout(
              title='Sinusoidal Model of Hourly Outdoor Temperature',
              xaxis_title='Hour in Year',
              yaxis_title='Outside Temp (°F)',
              width=1000,
              height=500
          )
          
          st.plotly_chart(fig, use_container_width=True)
          
          
          
          
          
          
          
            ###  Create EER Function & Cooling Model
  
          from scipy.optimize import fsolve
        
          def coolingModel(T):
              return 2*abs(fit1.slope*T + fit1.intercept)
  
          def heating(T):
              return (fit1.slope*T + fit1.intercept)
  
          st.subheader("Customize Comfort Settings")
        
          x_intercept_cool = int(fsolve(coolingModel, 70))
          x_intercept_heat = int(fsolve(heating, 60))
          
          heatingTemp = st.number_input("Enter heating setpoint temperature (\u00b0F):", min_value=5, max_value=x_intercept_heat, value=x_intercept_heat)
          coolingTemp = st.number_input("Enter cooling setpoint temperature (\u00b0F):", min_value=x_intercept_cool, max_value=90, value=x_intercept_cool)
  
          
          
          
          
          
          coolingEnergy = []
          
          for temp in sinT:
              if temp <= coolingTemp:
                  coolingEnergy.append(0)
              else:
                  coolingEnergy.append(coolingModel(temp))
          
          
          coolingEnergyPump = (coolingEnergy / EER(sinT))*3.412
          merged['coolingHourlyPump'] = coolingEnergyPump
          
          monthlyCooling = merged.groupby('month')['coolingHourlyPump'].sum()
          
          
          
          
          
          
          
            #  Create COP Function & Heating Model
          
          
          
          
          
          
          
          
          
          heatingEnergy = [] # Total energy used on at heating temps
          
          for temp in sinT:
              if temp > heatingTemp:
                  heatingEnergy.append(int(fit2.intercept))
              else:
                  heatingEnergy.append(heating(temp))
          
          
          merged['heatingEnergy'] = heatingEnergy
          monthlyModelTotal = merged.groupby('month')['heatingEnergy'].sum()
          
          heatingModel  = [] # Energy used for heating 
          
          for heating in heatingEnergy:
              if heating - int(fit2.intercept) < 0:
                  heatingModel.append(0)
              else:
                  heatingModel.append(heating-int(fit2.intercept))
          
          heatingEnergy = np.array(heatingEnergy)
          heatingModel = np.array(heatingModel)
          
          merged['heatingModel'] = heatingModel
          monthlyHeating = merged.groupby('month')['heatingModel'].sum()
          
          lightingModel = heatingEnergy - heatingModel
          
          merged['lightingModel'] = lightingModel
          monthlyLightingModel = merged.groupby('month')['lightingModel'].sum()
          
          
          heatingPump = heatingModel / COP(sinT)
          merged['heatingPump'] = heatingPump
          monthlyHeatingPump = merged.groupby('month')['heatingPump'].sum()
          
          totalModelOne = monthlyHeating + monthlyLightingModel # Monthly Heating Model Total
          totalModelTwo = monthlyHeatingPump + monthlyLightingModel # Monthly Heating Model w/ heat pump, no cooling
          totalModelThree = totalModelTwo + monthlyCooling # Monthly Heating Model w/ heat pump including cooling
          
          hourlyModelOne = heatingEnergy
          hourlyModelTwo = heatingPump + lightingModel
          hourlyModelThree = hourlyModelTwo + coolingEnergyPump
          
          
          
          
          
            #  Define Comfort, costs, and retrofit values
          
         
          months = ['January', 'Febuary', 'March', 'April', 'May', 'June', 'July',
                    'August', 'September', 'October', 'November', 'December']
          
          
          noComfortHeat = hourlyEnergy['heatUsage']
          noComfortLight = hourlyEnergy['lighting']
          
          noComfortPump = noComfortHeat / COP(hourlyTempAvg)
          
          noComfortTotal = noComfortPump + noComfortLight
          
          merged['noComfortTotal'] = noComfortTotal
          monthlyNoComfort = merged.groupby('month')['noComfortTotal'].sum()
              
              
          
          
           #   Summary Plot
          
      
  
          width = 1.4
          x = np.arange(len(months)) * 6
          
          fig = go.Figure()
          
          fig.add_bar(
              x=x - 1.2 * width,
              y=monthlyEnergyTotal * cost,
              width=width,
              name='Original Electricity Usage',
              marker=dict(color='limegreen', line=dict(color='black', width=1))
          )
          
          fig.add_bar(
              x=x,
              y=monthlyNoComfort * cost,
              width=width,
              name='Electricity Usage after Installing a Heat Pump',
              marker=dict(color='salmon', line=dict(color='black', width=1))
          )
          
          fig.add_bar(
              x=x + 1.2 * width,
              y=totalModelThree * cost,
              width=width,
              name='Electricity Usage with Heat Pump & Comfort Control',
              marker=dict(color='deepskyblue', line=dict(color='black', width=1))
          )
          
          fig.update_layout(
              title='Monthly Electricity Usage Summary',
              xaxis=dict(
                  tickmode='array',
                  tickvals=x,
                  ticktext=months
              ),
              yaxis_title='Monthly Electricity Usage (kWh)',
              barmode='group',
              legend_title_text='Scenario',
              width=1000,
              height=500
          )
          
          st.plotly_chart(fig, use_container_width=True)
          
          
          
          
          
          
          
  
          st.subheader("Select Monthly Energy Scenarios to Compare")
          
          st.markdown('Comfort = Maintaining Building Between Temperature Setpoints')
          
          show_retrofit = st.checkbox("Include Retrofit")
          show_heat_pump = st.checkbox("Include Heat Pump")
          
          heat_pump_mode = None
          if show_heat_pump:
              heat_pump_mode = st.radio("Select Heat Pump Mode", ["Comfort Mode", "No Comfort Mode"])
          
          fig = go.Figure()
          
          # Original baseline
          fig.add_bar(x=months, y=monthlyEnergyTotal, name="Original Usage",
                      marker=dict(color='purple', line=dict(color='black', width=1)))
          
          # Heat pump scenarios
          if show_heat_pump:
              if heat_pump_mode == "No Comfort Mode":
                  y_vals = monthlyNoComfort * (1 - retro) if show_retrofit else monthlyNoComfort
                  label = "Heat Pump (No Comfort) " + ("w/ Retrofit" if show_retrofit else "w/o Retrofit")
                  fig.add_bar(x=months, y=y_vals, name=label,
                  marker=dict(color='salmon', line=dict(color='black', width=1)))
          
              elif heat_pump_mode == "Comfort Mode":
                  y_vals = totalModelThree * (1 - retro) if show_retrofit else totalModelThree
                  label = "Heat Pump (Comfort) " + ("w/ Retrofit" if show_retrofit else "w/o Retrofit")
                  fig.add_bar(x=months, y=y_vals, name=label,
                  marker=dict(color='deepskyblue', line=dict(color='black', width=1)))
          
          # Retrofit-only (only if heat pump NOT selected)
          if show_retrofit and not show_heat_pump:
              fig.add_bar(x=months, y=monthlyEnergyTotal * (1 - retro), name="Retrofit Only",
              marker=dict(color='deepskyblue', line=dict(color='black', width=1)))
          
          fig.update_layout(
              title='Electricity Usage Comparison',
              yaxis_title='Monthly Electricity Usage (kWh)',
              barmode='group',
              legend_title_text='Scenario'
          )
          
          st.plotly_chart(fig, use_container_width=True)
          
          
          
          
          
     
          
          st.subheader("Select Hourly Energy Scenarios to Compare")
          st.markdown("""
                      **Comfort = Maintaining Building Between Temperature Setpoints**
                      
                      **Hover over graph to see corresponding week!**
                      
                      """)
          
          show_retrofit = st.checkbox("Include Retrofit (hourly)")
          show_heat_pump = st.checkbox("Include Heat Pump (hourly)")
          
          
          hourly_timestamps = pd.date_range(start=f'{year}-01-01', periods=len(hourlyEnergy), freq='H')
          weeks = hourly_timestamps.isocalendar().week.values
  
          
          heat_pump_mode = None
          if show_heat_pump:
              heat_pump_mode = st.radio("Select Hourly Heat Pump Mode", ["Comfort Mode", "No Comfort Mode"])
          
          fig = go.Figure()
          
          # Original baseline
          fig.add_trace(go.Scatter(
              x=hoursInYear,
              y=hourlyEnergy['Energy'].values,
              mode='lines',
              name="Original Usage",
              line=dict(color='purple'),
              customdata=np.stack([weeks], axis=-1),
              hovertemplate='Hour: %{x}<br>Usage: %{y:.2f} kWh<br>Week: %{customdata[0]}<extra></extra>'
          ))
          
          # Heat pump scenarios
          if show_heat_pump:
              if heat_pump_mode == "No Comfort Mode":
                  y_vals = noComfortTotal * (1 - retro) if show_retrofit else noComfortTotal
                  label = "Heat Pump (No Comfort) " + ("w/ Retrofit" if show_retrofit else "w/o Retrofit")
                  fig.add_trace(go.Scatter(
                      x=hoursInYear,
                      y=y_vals,
                      mode='lines',
                      name=label,
                      line=dict(color='salmon'),
                      customdata=np.stack([weeks], axis=-1),
                      hovertemplate='Hour: %{x}<br>Usage: %{y:.2f} kWh<br>Week: %{customdata[0]}<extra></extra>'
                  ))
          
              elif heat_pump_mode == "Comfort Mode":
                  y_vals = hourlyModelThree * (1 - retro) if show_retrofit else hourlyModelThree
                  label = "Heat Pump (Comfort) " + ("w/ Retrofit" if show_retrofit else "w/o Retrofit")
                  fig.add_trace(go.Scatter(
                      x=hoursInYear,
                      y=y_vals,
                      mode='lines',
                      name=label,
                      line=dict(color='deepskyblue'),
                      customdata=np.stack([weeks], axis=-1),
                      hovertemplate='Hour: %{x}<br>Usage: %{y:.2f} kWh<br>Week: %{customdata[0]}<extra></extra>'
                  ))
          
          # Retrofit-only (only if heat pump NOT selected)
          if show_retrofit and not show_heat_pump:
              fig.add_trace(go.Scatter(
                  x=hoursInYear,
                  y=hourlyEnergy['Energy'] * (1 - retro),
                  mode='lines',
                  name="Retrofit Only",
                  line=dict(color='lightgreen'),
                  customdata=np.stack([weeks], axis=-1),
                  hovertemplate='Hour: %{x}<br>Usage: %{y:.2f} kWh<br>Week: %{customdata[0]}<extra></extra>'
              ))
          
          fig.update_layout(
              title='Hourly Electricity Usage Comparison',
              xaxis_title='Hour of Year',
              yaxis_title='Electricity Usage (kWh)',
              width=1000,
              height=500,
              legend_title_text='Scenario'
          )
          
          st.plotly_chart(fig, use_container_width=True)
  
          
  
  
  
  
          from plotly.subplots import make_subplots
  
  
          st.subheader("Energy + Savings: Select Scenarios to Compare")
          st.markdown("""
                      **Comfort = Maintaining Building Between Temperature Setpoints**
                      
                      Use Autoscale feature when changing configurations
                      
                      
                      """)
          
          show_retrofit = st.checkbox("Includes Retrofit")
          show_heat_pump = st.checkbox("Includes Heat Pump")
          
          heat_pump_mode = None
          if show_heat_pump:
              heat_pump_mode = st.radio("Heat Pump Mode", ["Comfort Mode", "No Comfort Mode"])
          
          # Base values
          baseline_energy = monthlyEnergyTotal
          baseline_cost = monthlyEnergyTotal * cost
          
          # Decide which model and savings to show
          selected_energy = None
          selected_label = ""
          savings = None
          
          if show_heat_pump:
              if heat_pump_mode == "Comfort Mode":
                  selected_energy = totalModelThree
                  selected_label = "Energy Usage with Heat Pump (60-75°F)"
                  savings = (monthlyEnergyTotal - totalModelThree) * cost
              elif heat_pump_mode == "No Comfort Mode":
                  selected_energy = monthlyNoComfort
                  selected_label = "Energy Usage with Heat Pump (No Comfort)"
                  savings = (monthlyEnergyTotal - monthlyNoComfort) * cost
          
              if show_retrofit:
                  selected_energy *= (1 - retro)
                  savings *= (1 - retro)
                  selected_label += " + Retrofit"
          
          elif show_retrofit and not show_heat_pump:
              selected_energy = monthlyEnergyTotal * (1 - retro)
              selected_label = "Energy Usage with Retrofit Only"
              savings = monthlyEnergyTotal * cost * retro
          
          # Build figure
          fig = make_subplots(specs=[[{"secondary_y": True}]])
          
          # Bar: Energy usage
          if selected_energy is not None:
              fig.add_trace(
                  go.Bar(
                      x=months,
                      y=selected_energy,
                      name=selected_label,
                      marker=dict(color='deepskyblue', line=dict(color='black', width=1)),
                      hovertemplate='Month: %{x}<br>Energy Usage: %{y:.1f} kWh<extra></extra>'
                  ),
                  secondary_y=False
              )
          
          percent_savings = (monthlyEnergyTotal - totalModelThree) / monthlyEnergyTotal * 100
  
          # Line: Savings
          if savings is not None:
              fig.add_trace(
                  go.Scatter(
                      x=months,
                      y=savings,
                      name="Monthly Savings",
                      mode='lines+markers',
                      line=dict(color='black', width=3),
                      marker=dict(color='blueviolet', size=10),
                      hovertemplate='Month: %{x}<br>Savings: $%{y:.2f}<extra></extra>'
                  ),
                  secondary_y=True
              )
          
          
  
          fig.update_layout(
              title='Electricity Usage & Savings Comparison',
              barmode='group',
              width=1000,
              height=600,
              legend_title_text='Scenario',
              xaxis=dict(tickmode='array', tickvals=months, ticktext=months, tickangle=45, tickfont=dict(size=15))
          )
          
          fig.update_yaxes(
              title_text="Energy Usage (kWh)",
              secondary_y=False,
              tickfont=dict(size=15),
              range=[0, 5500]
          )
          fig.update_yaxes(
              title_text="Monthly Savings ($)",
              secondary_y=True,
              tickfont=dict(size=15)
          )
          
          st.plotly_chart(fig, use_container_width=True)
        
        

    except Exception as e:
        st.error(f"Error processing files: {e}")
else:
    st.info("Please upload both CSV files and define inputs to begin.")


    
