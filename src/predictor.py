# predictor.py
import threading
import time
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

from utils import (
    load_model_and_scaler,
    prepare_sequence_from_candles,
    inverse_log_return_to_price,
)
from config import LOOKBACK, PREDICTION_HISTORY, PREDICTION_PERIOD_SEC
import logging

logger = logging.getLogger(__name__)


class PredictorThread(threading.Thread):

    def __init__(self, buffer, shared_results, model_path=None, scaler_path=None, daemon=True):
        super().__init__(daemon=daemon)

        self.buffer = buffer
        self.shared = shared_results
        self.model, self.scaler, self.meta = load_model_and_scaler(
            model_path, scaler_path
        )

        self._stop_event = threading.Event()
        logger.info("Predictor initialized — waiting for enough live candles...")

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        """
        Wait until buffer has 61 candles (60 for LSTM + 1 for log-return drop)
        Then predict once per minute.
        """

        # Wait for real candles — avoid predicting on pure CSV warm-start
        while not self.stopped():
            if self.buffer.size() >= LOOKBACK + 1:
                break
            time.sleep(1)

        logger.info("Predictor: Buffer ready. Starting live predictions.")

        # Main loop — predict every finalized candle
        while not self.stopped():
            self.run_once_predict()
            time.sleep(PREDICTION_PERIOD_SEC)

    def run_once_predict(self):
        """
        Runs a single prediction based on last LOOKBACK+1 candles.
        """

        try:
            if self.buffer.size() < LOOKBACK + 1:
                logger.warning(
                    f"Predictor: Not enough candles yet ({self.buffer.size()})."
                )
                return

            candles = self.buffer.get_last_n(LOOKBACK + 1)

            # Prepare scaled sequence
            X_scaled, last_close, df_lr = prepare_sequence_from_candles(
                candles, self.scaler, lookback=LOOKBACK
            )

            # LSTM prediction (scaled log-return)
            pred_scaled = self.model.predict(X_scaled, verbose=0)

            # Convert back to price
            pred_price = inverse_log_return_to_price(
                pred_scaled.flatten(),
                self.scaler,
                last_close
            )[0]

            # ALWAYS use LIVE timestamp
            predict_for_ts = pd.Timestamp.now().floor("T") + pd.Timedelta(minutes=1)

            # Save prediction
            with self.shared["lock"]:
                self.shared["predictions"].append(pred_price)
                self.shared["timestamps"].append(predict_for_ts)

                # Keep history small
                if len(self.shared["predictions"]) > PREDICTION_HISTORY:
                    self.shared["predictions"].pop(0)
                    self.shared["timestamps"].pop(0)

            logger.info(
                f"✔ Predicted price for {predict_for_ts}: {pred_price:.2f}"
            )

        except Exception as e:
            logger.exception(f"Prediction error: {e}")