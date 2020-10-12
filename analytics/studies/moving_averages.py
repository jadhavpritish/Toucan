from dataclasses import dataclass
from typing import List

import pandas as pd


@dataclass
class SMA:

    ticker_df: pd.DataFrame

    def compute_sma(
        self, column: str = "close", look_back_periods: List[int] = [5, 10, 20, 40]
    ):
        sma_dict = {}
        for n in look_back_periods:
            sma_values = self.ticker_df[column].rolling(window=n).mean()
            sma_values.fillna(self.ticker_df[column].astype(float), inplace=True)
            sma_dict[f"sma_{n}"] = sma_values

        return pd.DataFrame(sma_dict, index=self.ticker_df.index)
