# Nifty 50 Stock Price Prediction with LSTM

A real-time stock market prediction system using LSTM (Long Short-Term Memory) neural networks to forecast Nifty 50 prices. The system connects to live market data via WebSocket, processes minute-level OHLC (Open, High, Low, Close) candles, and provides real-time predictions with a live visualization dashboard.

## Features

- **LSTM-based Price Prediction**: Uses TensorFlow/Keras LSTM model trained on historical data
- **Real-time Data Processing**: WebSocket connection for live market data from Angel One SmartAPI
- **Live Dashboard**: Real-time visualization of prices and predictions using Matplotlib
- **Thread-safe Architecture**: Multi-threaded design for concurrent data processing and prediction
- **Auto-warmup**: Loads historical data for initial buffer population

## Project Structure

```
Project/
├── src/                    # Source code
│   ├── __init__.py        # Package initialization
│   ├── main.py            # Main application entry point
│   ├── config.py          # Configuration settings
│   ├── predictor.py       # LSTM prediction thread
│   ├── dashboard.py       # Live visualization dashboard
│   ├── buffer_manager.py  # Thread-safe candle buffer
│   ├── utils.py           # Utility functions for model loading & preprocessing
│   └── ws_adapter.py      # WebSocket adapter for Angel One API
├── data/                   # Data files (CSV format) - gitignored
│   └── one_minute_final.csv
├── models/                 # Trained LSTM models and scalers - gitignored
│   ├── nifty50_lstm_model.keras
│   └── scaler.pkl
├── notebooks/              # Jupyter notebooks
│   └── lstm_time_series_model.ipynb
├── .gitignore             # Git ignore rules
├── requirements.txt       # Python dependencies
├── LICENSE                # MIT License
└── README.md              # This file
```

## Prerequisites

- **Python 3.8+**
- **Angel One SmartAPI Account**: You need API credentials from Angel One
- **Trained Model Files**: The system requires pre-trained model files:
  - `models/nifty50_lstm_model.keras` - Trained LSTM model
  - `models/scaler.pkl` - Data scaler for preprocessing

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Project
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up API credentials**
   - Create your API keys file with the following format (one value per line):
     ```
     API_KEY
     FEED_TOKEN
     CLIENT_CODE
     PASSWORD
     TOTP_SECRET
     ```
   - Update `SMARTAPI_KEY_PATH` in `src/config.py` (line 21) to point to your API keys file location
   - Default path is set to `/Users/api_keys.txt` - modify this to your actual file path
   - **Note**: API key files (`*keys.txt`) are gitignored for security

5. **Prepare model files**
   - Place trained model files in `models/` directory:
     - `nifty50_lstm_model.keras`
     - `scaler.pkl`

6. **Prepare data file**
   - Place historical data CSV in `data/one_minute_final.csv`

## Usage

Run the main application:

```bash
python src/main.py
```

The application will:
1. Load historical data (if available) to warm-start the buffer
2. Connect to Angel One WebSocket for live market data
3. Start prediction thread for real-time forecasts
4. Display live dashboard with price chart and predictions


## Configuration

Edit `src/config.py` to customize:

- **`LOOKBACK`**: Number of historical candles for LSTM input (default: 60)
- **`DASHBOARD_WINDOW`**: Number of candles to display in dashboard (default: 100)
- **`PREDICTION_HISTORY`**: Maximum number of predictions to store (default: 300)
- **`PREDICTION_PERIOD_SEC`**: Prediction frequency in seconds (default: 60)
- **`DASHBOARD_UPDATE_INTERVAL`**: Dashboard refresh rate in seconds (default: 1.0)
- **`SMARTAPI_KEY_PATH`**: Path to your API credentials file

## Architecture

- **`CandleBuffer`** (`buffer_manager.py`): Thread-safe rolling buffer storing minute-level OHLC candles
- **`PredictorThread`** (`predictor.py`): Background thread that generates predictions every minute using LSTM
- **`LiveDashboard`** (`dashboard.py`): Real-time Matplotlib-based visualization of prices and predictions
- **`CandleBuilder`** (`ws_adapter.py`): Handles live data streaming and converts ticks to OHLC candles
- **`load_model_and_scaler`** (`utils.py`): Utility functions for loading trained models and data preprocessing

## Model Training

Model training notebooks are available in the repository. Train your model using historical data and save the model and scaler files to the `models/` directory.

## Dependencies

Key dependencies (see `requirements.txt` for full list):
- **TensorFlow/Keras**: Deep learning framework for LSTM model
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Matplotlib**: Data visualization
- **pyotp**: Time-based One-Time Password for API authentication
- **smartapi-python**: Angel One SmartAPI Python SDK

## Security Notes

 **Important**: This project uses `.gitignore` to prevent committing sensitive files:
- API key files (`*keys.txt`)
- Model files (large binaries: `*.keras`, `*.pkl`)
- Data files (large/sensitive: `*.csv`)
- Environment variables (`.env`)

**Never commit API keys or credentials to version control!**

## Troubleshooting

- **Model file not found**: Ensure `models/nifty50_lstm_model.keras` and `models/scaler.pkl` exist
- **API connection failed**: Verify your API credentials are correct and the path in `config.py` is accurate
- **Data file not found**: The application will work without historical data, but predictions may be delayed until enough live data is collected

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2024

## Contributing

Contributions are welcome! If you'd like to contribute to this project, please follow these guidelines:

- Follow the existing code style and conventions
- Add comments for complex logic or algorithms
- Update documentation if you're adding new features
- Ensure your code doesn't break existing functionality
- Keep commits focused and atomic (one feature/fix per commit)

### Areas for Contribution

- Model improvements and optimizations
- Additional visualization features
- Documentation improvements
- Bug fixes and performance enhancements
- Testing and code quality improvements

### Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub with:
- A clear description of the problem or feature
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Your environment details (Python version, OS, etc.)

Thank you for your interest in contributing!

## Author

**Vikas K**

- GitHub: [@itsvikask4](https://github.com/itsvikask4)
- Email: vikaskcode@gmail.com
