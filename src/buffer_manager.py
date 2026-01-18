# buffer_manager.py
import threading
from collections import deque
from config import LOOKBACK
import pandas as pd

class CandleBuffer:
    """
    Thread-safe rolling buffer that stores minute candles as dicts:
      {'datetime': ts, 'open':..., 'high':..., 'low':..., 'close':...}
    """
    def __init__(self, lookback=LOOKBACK):
        self.lock = threading.RLock()
        self.lookback = lookback
        # Exact size needed by predictor + a bit extra for debugging
        self.deque = deque(maxlen=lookback + 5)

    def load_from_csv(self, csv_path, datetime_col='date',
                    feature_cols=['open','high','low','close'], n=None):
        """
        Warm start from CSV.
        Automatically ensures enough candles exist for:
        - LOOKBACK log-return rows → requires LOOKBACK + 1 candles.
        """
        # enforce minimum
        required = self.lookback + 1
        if n is None or n < required:
            n = required

        df = pd.read_csv(csv_path)
        df[datetime_col] = pd.to_datetime(df[datetime_col])
        df = df.sort_values(datetime_col).reset_index(drop=True)

        # take last n rows
        df_tail = df.tail(n).copy()

        candles = []
        for _, row in df_tail.iterrows():
            candles.append({
                'datetime': row[datetime_col],
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close'])
            })

        with self.lock:
            self.deque.clear()
            for c in candles:
                self.deque.append(c)

        return len(self.deque)

    def append_candle(self, candle):
        """Append a finalized candle into the buffer (thread-safe)."""
        with self.lock:
            self.deque.append(candle)

    def get_last_n(self, n=None):
        """Return list of last n candles (ascending time)."""
        with self.lock:
            if n is None:
                return list(self.deque)
            return list(self.deque)[-n:]

    def size(self):
        with self.lock:
            return len(self.deque)

    def last(self):
        """Return the most recent candle."""
        with self.lock:
            return self.deque[-1] if len(self.deque) > 0 else None