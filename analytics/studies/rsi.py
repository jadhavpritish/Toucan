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

        """
        Investopedia https://www.investopedia.com/terms/r/rsi.asp

        Bascially,

        RSI = 100 - (100/(1  - avg_up / abs(avg_down)))

        avg_up -> avg of all up moves in the last N prices
        avg_down -> avg of all down moves
        """

        delta_close = self.ticker_df["close"].diff()

        delta_positive = delta_close.clip(lower=0)
        delta_negative = delta_close.clip(upper=0)

        if method.value == RSIMethod.SMA.value:
            delta_positive_rolling = delta_positive.rolling(window=span).mean()
            delta_negative_rolling = delta_negative.abs().rolling(window=span).mean()
        elif method.value == RSIMethod.EWM.value:
            delta_positive_rolling = delta_positive.ewm(
                adjust=False, ignore_na=True, alpha=2 / (span + 1)
            ).mean()
            delta_negative_rolling = (
                delta_negative.abs()
                .ewm(adjust=False, ignore_na=True, alpha=2 / (span + 1))
                .mean()
            )
        else:
            raise ValueError(f"Method {method} not supported")

        relative_strength = delta_positive_rolling / delta_negative_rolling
        relative_strength.fillna(0, inplace=True)
        ticker_rsi = 100 - (100 / (1 + relative_strength))

        return pd.DataFrame({"rsi": ticker_rsi})
