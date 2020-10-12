from dataclasses import dataclass

import pandas as pd


# TODO: make TickerData richer
@dataclass
class TickerData:

    ticker_df: pd.DataFrame
