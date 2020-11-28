from dataclasses import dataclass

import pandas as pd


# TODO: make TickerData richer
@dataclass
class TickerData:

    ticker_df: pd.DataFrame

    def get_ticker_data(self, offset=-1):
        return pd.DataFrame(self.ticker_df.iloc[offset]).T
