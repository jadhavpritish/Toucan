from dataclasses import dataclass
from enum import Enum

import pandas as pd

from analytics.studies.moving_averages import MovingAverages


@dataclass
class MACD(MovingAverages):
    def compute_macd(self):

        ema_df = self.compute_ema(look_back_periods=[12, 26])
        self.ticker_df = pd.concat([self.ticker_df, ema_df], axis=1)
        self.ticker_df["macd_line"] = (
            self.ticker_df["ema_12"] - self.ticker_df["ema_26"]
        )
        self.ticker_df["macd_signal"] = self.compute_ema(
            column="macd_line", look_back_periods=[9]
        )
        self.ticker_df["macd_histogram"] = (
            self.ticker_df["macd_line"] - self.ticker_df["macd_signal"]
        )

        return self.ticker_df
