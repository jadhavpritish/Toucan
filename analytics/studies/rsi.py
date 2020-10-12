from dataclasses import dataclass
from enum import Enum

import pandas as pd

from analytics.studies.data_definition import TickerData


class RSIMethod(Enum):
    SMA: str = "sma"
    EWM: str = "ewm"


@dataclass
class RSI(TickerData):
    def compute_rsi(
        self, span: int = 14, method: RSIMethod = RSIMethod.SMA
    ) -> pd.Series:

        delta_close = self.ticker_df["close"].diff()

        delta_positive = delta_close.clip(lower=0)
        delta_negative = delta_close.clip(upper=0)

        if method.value == RSIMethod.SMA.value:
            delta_positive_rolling = delta_positive.rolling(window=span).mean()
            delta_negative_rolling = delta_negative.abs().rolling(window=span).mean()
        elif method.value == RSIMethod.EWM.value:
            delta_positive_rolling = delta_positive.ewm(
                span=span, adjust=True, ignore_na=True
            ).mean()
            delta_negative_rolling = (
                delta_negative.abs().ewm(span=span, adjust=True, ignore_na=True).mean()
            )
        else:
            raise ValueError(f"Method {method} not supported")

        relative_strength = delta_positive_rolling / delta_negative_rolling
        relative_strength.fillna(0, inplace=True)
        ticker_rsi = 100 - (100 / (1 + relative_strength))

        return ticker_rsi
