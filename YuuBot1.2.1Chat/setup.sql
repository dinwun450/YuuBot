-- Set the database where the UDF and Stage are located
USE DATABASE YUUBOT_DB;
CREATE OR REPLACE SCHEMA MODEL;
USE SCHEMA MODEL;

CREATE OR REPLACE STAGE YUUBOT_DB.MODEL.EARTHQUAKE_STAGE
  COMMENT = 'Internal stage for earthquake data files and ML models';

--- Replace the file prefixes below with the correct local paths to your files ---
PUT file://./all_month.csv @YUUBOT_DB.MODEL.EARTHQUAKE_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://./earthquake_prob_model_7d.pth @YUUBOT_DB.MODEL.EARTHQUAKE_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://./yamls/jp_quake_logger.yaml @YUUBOT_DB.MODEL.EARTHQUAKE_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://./yamls/global_quake_logger.yaml @YUUBOT_DB.MODEL.EARTHQUAKE_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

CREATE OR REPLACE FUNCTION FORECAST_EARTHQUAKE_PROB (
    TARGET_LAT FLOAT,
    TARGET_LON FLOAT,
    RADIUS_KM NUMBER
)
RETURNS VARIANT -- Returns a JSON object with the forecast results
LANGUAGE PYTHON
RUNTIME_VERSION = '3.12' -- Use a supported Python version for PyTorch
PACKAGES = (
    'numpy',
    'pandas',
    'pytorch',
    'snowflake-snowpark-python'
)
-- Import the data and model files from the stage into the UDF's execution environment
IMPORTS = (
    '@EARTHQUAKE_STAGE/all_month.csv',
    '@EARTHQUAKE_STAGE/earthquake_prob_model_7d.pth'
)
HANDLER = 'forecast_handler'
AS
$$
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import os
import math
import json
import sys

# --- Global/Fixed Configurations from the Colab notebook ---
LOOKBACK_WINDOW = 5
FORECAST_HORIZON = 7
HIDDEN_SIZE = 128
LAYERS = 2
device = torch.device('cpu') # UDFs run on CPU only
MAGNITUDE_THRESHOLD = 4.5 # The original processing threshold in load_and_process_data

# --- Helper Function 1: haversine_vectorized ---
# Calculate distance between a target point and a vector of points.
def haversine_vectorized(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

# --- Class 1: EarthquakeLSTM ---
class EarthquakeLSTM(nn.Module):
    def __init__(self, input_size=1, hidden_size=HIDDEN_SIZE, num_layers=LAYERS, output_size=FORECAST_HORIZON):
        super(EarthquakeLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
        self.sigmoid = nn.Sigmoid()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(device)
        out, _ = self.lstm(x, (h0, c0))
        out = out[:, -1, :]
        out = self.fc(out)
        out = self.sigmoid(out)
        return out

# --- Helper Function 2: load_and_process_data ---
# Loads CSV, filters by location, and aggregates into daily binary target.
def load_and_process_data(filepath, target_lat, target_lon, radius_km):
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        return None, None, None

    # Clean columns: replace '_' with ''
    df.columns = [c.replace('_', '') for c in df.columns]

    # Validate essential columns
    if 'latitude' not in df.columns or 'longitude' not in df.columns or 'mag' not in df.columns:
        return None, None, None

    # Filter by radius
    distances = haversine_vectorized(target_lat, target_lon, df['latitude'], df['longitude'])
    df = df[distances <= radius_km].copy()

    if len(df) < 1:
        return None, None, None

    # Process time and create daily binary target
    df['time'] = pd.to_datetime(df['time'], unit='ms', errors='coerce')
    df.dropna(subset=['time'], inplace=True) # Remove rows with bad time data
    df = df.sort_values('time')
    df_indexed = df.set_index('time')
    
    # Binary target is 1 if magnitude >= 4.5, else 0 (as per the Colab code)
    df_indexed['significant_event'] = (df_indexed['mag'] >= MAGNITUDE_THRESHOLD).astype(int)
    
    daily_binary_target_series = df_indexed.resample('D')['significant_event'].max().fillna(0)
    binary_target = daily_binary_target_series.values.reshape(-1, 1).astype('float32')
    dates = daily_binary_target_series.index
    
    return binary_target, dates, None # Historical magnitudes not returned

# --- Main UDF Handler: forecast_handler ---
def forecast_handler(target_lat, target_lon, radius_km):
    # Determine the file paths for the imported stage files
    import_dir = sys._xoptions["snowflake_import_directory"]
    CSV_FILE_PATH = os.path.join(import_dir, 'all_month.csv')
    MODEL_PATH = os.path.join(import_dir, 'earthquake_prob_model_7d.pth')

    # 1. Load Model
    if not os.path.exists(MODEL_PATH):
        return {"error": f"Model file '{str(MODEL_PATH)}' not found in imports. Check your stage imports."}
    
    try:
        # Load the PyTorch model state dictionary
        checkpoint = torch.load(MODEL_PATH, map_location=device, weights_only=False)
        model = EarthquakeLSTM(
            hidden_size=checkpoint.get('hidden_size', HIDDEN_SIZE), 
            num_layers=checkpoint.get('num_layers', LAYERS),
            output_size=FORECAST_HORIZON
        ).to(device)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()
    except Exception as e:
        return {"error": f"Failed to load or initialize model: {str(e)}"}

    # Extract training details for metadata
    train_lat = checkpoint.get('train_lat', 'N/A')
    train_lon = checkpoint.get('train_lon', 'N/A')
    train_radius = checkpoint.get('train_radius', 'N/A')

    # 2. Load and Process Data
    binary_data, dates, _ = load_and_process_data(CSV_FILE_PATH, target_lat, target_lon, radius_km)

    if binary_data is None or len(binary_data) < LOOKBACK_WINDOW:
        return {"error": "Not enough historical data points found to create the lookback window or data loading failed."}

    # 3. Prepare Input Window and Forecast!
    last_window = binary_data[-LOOKBACK_WINDOW:]
    last_window_tensor = torch.tensor(last_window, dtype=torch.float32).unsqueeze(0).to(device)

    with torch.no_grad():
        forecast_probabilities = model(last_window_tensor).cpu().numpy().flatten()

    # 4. Format Results (No plots, only structured data)
    probabilities_list = []
    for prob in forecast_probabilities:
        probabilities_list.append(float(np.clip(prob, 0.0, 1.0)))

    # Calculate average probability
    seven_day_probabilities = probabilities_list[:FORECAST_HORIZON]
    average_decimal = np.mean(seven_day_probabilities) if seven_day_probabilities else 0.0

    # Determine forecast dates
    try:
        last_date = dates[-1]
        forecast_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=FORECAST_HORIZON)
        forecast_dates_str = [d.strftime('%Y-%m-%d') for d in forecast_dates]
    except Exception:
        forecast_dates_str = [f"Day {i+1}" for i in range(FORECAST_HORIZON)]
    
    # Combine results
    forecast_results = []
    for date_str, prob in zip(forecast_dates_str, probabilities_list):
        forecast_results.append({
            "date": date_str,
            "probability_percent": round(prob * 100, 4)
        })

    result = {
        "metadata": {
            "target_lat": round(target_lat, 4),
            "target_lon": round(target_lon, 4),
            "radius_km": radius_km,
            "lookback_window": LOOKBACK_WINDOW,
            "forecast_horizon": FORECAST_HORIZON,
            "model_trained_lat": round(train_lat, 4) if isinstance(train_lat, (float, int)) else train_lat,
            "model_trained_lon": round(train_lon, 4) if isinstance(train_lon, (float, int)) else train_lon,
            "model_trained_radius_km": train_radius
        },
        "average_7_day_probability_percent": round(average_decimal * 100, 4),
        "daily_forecast": forecast_results
    }
    
    return result
$$;

