# main.py
import logging
import threading
import time
import pandas as pd

from buffer_manager import CandleBuffer
from ws_adapter import register_callbacks
from predictor import PredictorThread
from dashboard import LiveDashboard
from config import DATA_CSV, LOOKBACK, SMARTAPI_KEY_PATH

# SmartAPI imports
from SmartApi.smartConnect import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from pyotp import TOTP
import warnings
warnings.filterwarnings("ignore")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nifty_live")


def create_smartapi_connection():

    # Load keys
    with open(SMARTAPI_KEY_PATH, "r") as f:
        key_secret = f.read().split()

    api_key = key_secret[0]
    client_code = key_secret[2]
    pwd = key_secret[3]
    totp_secret = key_secret[4]

    obj = SmartConnect(api_key=api_key)

    # Generate session + jwt
    session = obj.generateSession(client_code, pwd, TOTP(totp_secret).now())
    jwt = session["data"]["jwtToken"]
    feed_token = obj.getfeedToken()

    # Create websocket instance
    sws = SmartWebSocketV2(jwt, api_key, client_code, feed_token)

    return sws


def main():

    shared = {
        'lock': threading.RLock(),
        'predictions': [],
        'timestamps': [],
    }

    buffer = CandleBuffer(lookback=LOOKBACK)
    try:
        n_loaded = buffer.load_from_csv(DATA_CSV, datetime_col='date', n=LOOKBACK)
        logger.info(f"Warm-started buffer with {n_loaded} historical candles.")
    except Exception as e:
        logger.warning(f"Warm-start failed: {e}. Buffer will fill from live ticks.")


    sws = create_smartapi_connection()

    builder = register_callbacks(buffer, shared, sws)

    def on_open_override(wsapp):
        logger.info("WebSocket opened — subscribing...")
        token_list = [{"exchangeType": 1, "tokens": ["99926000"]}]
        sws.subscribe("stream_1", 1, token_list)

    sws.on_open = on_open_override

    ws_thread = threading.Thread(target=sws.connect, daemon=True)
    ws_thread.start()
    logger.info("WebSocket thread started.")

    predictor = PredictorThread(buffer=buffer, shared_results=shared)
    predictor.start()
    logger.info("Predictor thread started.")


    dashboard = LiveDashboard(buffer, shared)

    try:
        dashboard.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt — shutting down…")
    finally:
        predictor.stop()
        predictor.join(timeout=5)
        logger.info("Predictor stopped.")
        logger.info("System shutdown complete.")


if __name__ == "__main__":
    main()