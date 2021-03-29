from dataclasses import dataclass

import pandas as pd

from analytics.studies.moving_averages import MovingAverages


@dataclass
class MACD(MovingAverages):

    slow_ma: int
    fast_ma: int
    signal_line_period: int

    def compute_macd(self):

        ema_df = self.compute_ema(look_back_periods=[self.slow_ma, self.fast_ma])
        self.ticker_df = pd.concat([self.ticker_df, ema_df], axis=1)
        self.ticker_df["macd_line"] = (
            self.ticker_df[f"ema_{self.fast_ma}"]
            - self.ticker_df[f"ema_{self.slow_ma}"]
        )
        self.ticker_df["macd_signal"] = self.compute_ema(
            column="macd_line", look_back_periods=[self.signal_line_period]
        )
        self.ticker_df["macd_histogram"] = (
            self.ticker_df["macd_line"] - self.ticker_df["macd_signal"]
        )

        return self.ticker_df
