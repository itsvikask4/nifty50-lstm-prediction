# utils.py
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
import config   # <-- use dynamic import instead of static bindings
import warnings
warnings.filterwarnings("ignore")


def load_model_and_scaler(model_path=None, scaler_path=None):
    """
    Load trained LSTM model (.keras) and scaler metadata dict.
    Always reads latest paths from config unless explicitly provided.
    """
    import tensorflow as tf

    model_path = model_path or config.MODEL_PATH
    scaler_path = scaler_path or config.SCALER_PATH

    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    if not Path(scaler_path).exists():
        raise FileNotFoundError(f"Scaler file not found: {scaler_path}")

    model = tf.keras.models.load_model(str(model_path))

    with open(scaler_path, "rb") as f:
        save_dict = pickle.load(f)

    # save_dict should contain scaler + metadata
    if isinstance(save_dict, dict):
        scaler = save_dict.get("scaler")
        meta = {
            "log_return_cols": save_dict.get("log_return_cols"),
            "lookback_period": save_dict.get("lookback_period"),
            "feature_columns": save_dict.get("feature_columns"),
        }
    else:
        scaler = save_dict
        meta = {}

    if scaler is None:
        raise ValueError("Scaler missing in scaler.pkl — cannot continue.")

    return model, scaler, meta


def candles_to_dataframe(candles):
    df = pd.DataFrame(candles)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)
    return df


def compute_log_returns_from_df(df, feature_columns=['open','high','low','close']):
    df_lr = df.copy().reset_index(drop=True)
    for col in feature_columns:
        df_lr[f"{col}_log_return"] = np.log(df_lr[col] / df_lr[col].shift(1))
    df_lr = df_lr.dropna().reset_index(drop=True)

    log_return_cols = [f"{c}_log_return" for c in feature_columns]
    return df_lr, log_return_cols


def prepare_sequence_from_candles(
    candles,
    scaler,
    lookback=None,
    feature_columns=['open','high','low','close']
):
    """
    Convert list-of-candles into a scaled LSTM input sequence.
    """
    lookback = lookback or config.LOOKBACK

    df = candles_to_dataframe(candles)

    if len(df) < lookback + 1:
        raise ValueError(f"Need at least {lookback+1} candles; got {len(df)}")

    df_lr, log_return_cols = compute_log_returns_from_df(df, feature_columns)

    if len(df_lr) < lookback:
        raise ValueError(f"Not enough log-return rows: need {lookback}, got {len(df_lr)}")

    # last 60 rows of log returns
    X_lr = df_lr[log_return_cols].values[-lookback:]

    # scaling
    X_scaled = scaler.transform(X_lr)

    # reshape for LSTM: (1, timesteps, features)
    X_scaled = X_scaled.reshape(1, lookback, len(log_return_cols))

    # last real close price
    previous_close = df["close"].iloc[-1]

    return X_scaled, previous_close, df_lr


def inverse_log_return_to_price(pred_log_return_scaled, scaler, previous_price, feature_count=None):
    """
    Convert model output (scaled log-return for close) back to actual price.
    """
    arr = np.array(pred_log_return_scaled).reshape(-1)

    # Determine feature count automatically from scaler
    feature_count = feature_count or scaler.n_features_in_

    dummy = np.zeros((arr.shape[0], feature_count))
    dummy[:, -1] = arr

    actual_log_returns = scaler.inverse_transform(dummy)[:, -1]

    predicted_prices = previous_price * np.exp(actual_log_returns)

    return predicted_prices


def mae(a, b): return np.mean(np.abs(a - b))
def mape(a, b): return np.mean(np.abs((a - b) / a)) * 100