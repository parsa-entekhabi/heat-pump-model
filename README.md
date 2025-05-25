# Energy Modeling App (beta)

This interactive Streamlit app models and visualizes hourly and monthly electricity usage for a building, comparing retrofit and heat pump energy efficiency scenarios. Originally designed for my senior design project working with beacon united methodist church, this app allows users to upload their own energy and temperature data, customize model assumptions, and generate savings estimates.

## 🔍 Features

* Upload hourly or 15-minute interval CSV files for energy and temperature
* Separate heating and lighting energy usage
* Model heat pump operation (with and without temperature comfort constraints)
* Simulate retrofit energy reductions
* Visualize:

  * Monthly usage comparisons (bar + dual-axis savings)
  * Hourly usage comparisons (line plots)
  * Sinusoidal outside temperature models
  * Interactive controls for custom cooling/heating setpoints and scenario selection

## 🧠 How It Works

The app:

1. Reads power/energy data and NOAA-style temperature data
2. Converts 15-minute data to hourly if needed
3. Fits a sinusoidal model to average daily temperatures
4. Estimates energy usage for heating/cooling models
5. Calculates electricity savings for heat pump and retrofit scenarios
6. Plots side-by-side usage comparisons and savings

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/parsa-entekhabi/heat-pump-model.git
cd heat-pump-model
```

### 2. Install Dependencies

Create a virtual environment (optional) and install required packages:

```bash
pip install -r requirements.txt
```

### 3. Run the App

```bash
streamlit run hp_model_app.py
```

## 📁 File Structure

```
heat-pump-model/
├── hp_model_app.py       # Main Streamlit app
├── requirements.txt          # Python dependencies
├── README.md                 # This file
```

### Energy CSV

* Power (kW) column required
* 15-minute or hourly data accepted

### Temperature CSV

* Columns: `DATE`, `TMAX`, `TMIN`
* Format: US NOAA daily summaries


## 📝 License

[MIT License](LICENSE)

## 🙋‍♂️ Contact

Created by Parsa Entekhabi — feel free to reach out via [LinkedIn](https://linkedin.com/in/parsa-entekhabi/)
