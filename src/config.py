from pathlib import Path

# Base project directory
ROOT = Path(__file__).resolve().parent.parent

# File paths
DATA_CSV = ROOT / "data" / "one_minute_final.csv"
MODEL_PATH = ROOT / "models" / "nifty50_lstm_model.keras"
SCALER_PATH = ROOT / "models" / "scaler.pkl"

# Model Parameters
LOOKBACK = 60
DASHBOARD_WINDOW = 100
PREDICTION_HISTORY = 300

# Timing Parameters
DASHBOARD_UPDATE_INTERVAL = 1.0
PREDICTION_PERIOD_SEC = 60

# Secret Keys Path
SMARTAPI_KEY_PATH = Path("/Users/api_keys.txt")