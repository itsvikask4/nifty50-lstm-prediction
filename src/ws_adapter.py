# ws_adapter.py
import datetime as dt
import pandas as pd
from logzero import logger


class CandleBuilder:
    """
    Converts SmartAPI ticks → 1-min OHLC candles.
    Immediately appends finalized candles to CandleBuffer.
    Also prints NEXT CANDLE PREDICTION cleanly.
    """

    def __init__(self, buffer, shared):
        self.buffer = buffer
        self.shared = shared

        self.current_minute = None
        self.open_price = None
        self.high_price = None
        self.low_price = None
        self.close_price = None

        logger.info("CandleBuilder initialized; waiting for first tick...")

    def finalize_candle(self):
        if self.open_price is None:
            return None

        return {
            "datetime": pd.Timestamp(self.current_minute),
            "open": float(self.open_price),
            "high": float(self.high_price),
            "low": float(self.low_price),
            "close": float(self.close_price),
        }

    def _print_prediction_if_available(self):
        """Prints prediction for the NEXT candle (clean & correct)."""
        with self.shared["lock"]:
            if len(self.shared["predictions"]) == 0:
                return

            pred_price = self.shared["predictions"][-1]
            pred_ts = self.shared["timestamps"][-1]

        logger.info(f" NEXT CANDLE PREDICTION ({pred_ts}): {pred_price:.2f}")

    def on_data(self, wsapp, message):
        try:
            price = message["last_traded_price"] / 100.0
            ts = dt.datetime.fromtimestamp(message["exchange_timestamp"] / 1000)
            minute = ts.replace(second=0, microsecond=0)

        except Exception as e:
            logger.error(f"Tick parse error: {e}")
            return

        # Minute change → finalize candle
        if self.current_minute and minute != self.current_minute:
            candle = self.finalize_candle()

            if candle:
                logger.info(f"Final Candle: {candle}")
                self.buffer.append_candle(candle)
                self._print_prediction_if_available()

            # Start new candle
            self.open_price = price
            self.high_price = price
            self.low_price = price
            self.close_price = price
            self.current_minute = minute
            return

        # First tick
        if self.current_minute is None:
            self.current_minute = minute
            self.open_price = self.high_price = self.low_price = self.close_price = price
            logger.info(f"Started first candle at {minute} with price {price}")
            return

        # Candle update
        self.close_price = price
        if price > self.high_price:
            self.high_price = price
        if price < self.low_price:
            self.low_price = price

    def on_open(self, wsapp):
        logger.info("WebSocket opened.")

    def on_error(self, wsapp, error):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, wsapp):
        logger.info("WebSocket closed")


def register_callbacks(buffer, shared, sws):
    builder = CandleBuilder(buffer, shared)
    sws.on_data = builder.on_data
    sws.on_open = builder.on_open
    sws.on_error = builder.on_error
    sws.on_close = builder.on_close
    return builder