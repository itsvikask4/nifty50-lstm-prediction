# dashboard.py
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
import pandas as pd
from config import DASHBOARD_UPDATE_INTERVAL, DASHBOARD_WINDOW


class LiveDashboard:
    def __init__(self, buffer, shared):
        self.buffer = buffer
        self.shared = shared

        # Create figure with dark theme
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(14, 6))
        gs = self.fig.add_gridspec(1, 2, width_ratios=[3, 1])

        self.ax_price = self.fig.add_subplot(gs[0])
        self.ax_stats = self.fig.add_subplot(gs[1])

        # Set colors
        self.fig.patch.set_facecolor("#000000")
        self.ax_price.set_facecolor("#111111")
        self.ax_stats.set_facecolor("#111111")
        self.ax_stats.axis("off")

        # Initialize line object for better performance
        self.line, = self.ax_price.plot([], [], color="cyan", linewidth=2)

    def get_data(self):
        candles = self.buffer.get_last_n(DASHBOARD_WINDOW)
        if len(candles) < 2:
            return None

        df = pd.DataFrame(candles)
        df["datetime"] = pd.to_datetime(df["datetime"])
        closes = df["close"].values
        times = df["datetime"].values

        with self.shared["lock"]:
            preds = list(self.shared["predictions"])
            pred_times = list(self.shared["timestamps"])

        return df, times, closes, preds, pred_times


    def draw_stats(self, last_close, preds):
        self.ax_stats.clear()
        self.ax_stats.axis("off")
        self.ax_stats.set_facecolor("#111111")

        if len(preds) == 0:
            pred_text = diff_text = direction = "—"
        else:
            pred = preds[-1]
            diff = pred - last_close
            diff_pct = diff / last_close * 100
            direction = "UP ↑" if diff > 0 else "DOWN ↓"

            pred_text = f"{pred:.2f}"
            diff_text = f"{diff:+.2f}  ({diff_pct:+.2f}%)"

        text = (
            "LIVE METRICS\n\n"
            f"Last Close:   {last_close:.2f}\n\n"
            f"Prediction:   {pred_text}\n"
            f"Diff:         {diff_text}\n"
            f"Direction:    {direction}\n"
        )

        self.ax_stats.text(
            0.05, 0.95, text,
            fontsize=16,
            color="white",
            weight="bold",
            family="monospace",
            va="top",
            bbox=dict(facecolor="#222222", alpha=0.8, edgecolor="white")
        )


    def update(self, frame):
        data = self.get_data()
        if data is None:
            # Return empty artists if no data
            return self.line,

        df, times, closes, preds, pred_times = data

        # ---- Price chart ----
        self.ax_price.clear()
        self.ax_price.set_facecolor("#111111")
        self.ax_price.set_title(
            "Closing Price (Last N Minutes)", color="white", fontsize=14, pad=10)

        # Set labels
        self.ax_price.set_xlabel("Time", color="white", fontsize=12)
        self.ax_price.set_ylabel("Price", color="white", fontsize=12)

        # Convert to matplotlib dates and plot
        t_num = mdates.date2num(times)
        line, = self.ax_price.plot(
            t_num, closes, color="cyan", linewidth=2, label="Close Price")

        # Configure x-axis for time display
        self.ax_price.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        self.ax_price.xaxis.set_major_locator(mdates.AutoDateLocator())

        self.ax_price.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        self.ax_price.tick_params(axis="x", colors="white", labelsize=10)
        self.ax_price.tick_params(axis="y", colors="white", labelsize=10)

        for spine in self.ax_price.spines.values():
            spine.set_edgecolor('white')
            spine.set_alpha(0.3)

        self.ax_price.relim()
        self.ax_price.autoscale_view()

        last_close = closes[-1]
        self.draw_stats(last_close, preds)

        self.fig.autofmt_xdate()

        self.fig.tight_layout()

        return line,


    def run(self):
        # Create animation
        anim = FuncAnimation(
            self.fig,
            self.update,
            interval=int(DASHBOARD_UPDATE_INTERVAL * 1000),
            blit=False,
            cache_frame_data=False
        )


        plt.show()

        return anim
