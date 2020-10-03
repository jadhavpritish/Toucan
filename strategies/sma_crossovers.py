from dataclasses import dataclass
from enum import Enum
from typing import List

import numpy as np
import pandas as pd


class CaptureTrend(Enum):

    BEARISH: str = "bearish"
    BULLISH: str = "bullish"
    ALL: str = "all"


@dataclass
class SMAStrategy:

    scrip_df: pd.DataFrame

    def compute_sma(
        self, column: str = "close", look_back_periods: List[int] = [5, 10, 20, 40]
    ):

        sma_dict = {}
        for n in look_back_periods:
            sma_values = self.scrip_df[column].rolling(window=n).mean()
            sma_values.fillna(self.scrip_df[column], inplace=True)
            sma_dict[f"sma_{n}"] = sma_values

        return pd.DataFrame(sma_dict, index=self.scrip_df.index)

    def sma_sessions(self, slow_ma=20, fast_ma=10):

        assert set([f"sma_{col}" for col in [slow_ma, fast_ma]]).issubset(
            self.scrip_df.columns
        )

        column_suffix = f"{slow_ma}_{fast_ma}"

        # identify start of a session by annotating the time when faster moving average crosses over the
        # slower moving average.
        sma_signal = self.scrip_df[f"sma_{fast_ma}"] > self.scrip_df[f"sma_{slow_ma}"]

        # Next we need to create sesssions. A sessions last as long as the faster moving average does not cross
        # above or below the slower moving average.
        # We use EXOR truth table to identify change overs.
        sma_session = (
            (sma_signal ^ sma_signal.shift(1)).fillna(False).cumsum(skipna=False)
        )

        # create a dataframe
        sma_df = pd.DataFrame(
            {
                f"sma_signal_{column_suffix}": sma_signal,
                f"sma_session_{column_suffix}": sma_session,
            }
        )

        # annotate session as either bullish or bearish
        sma_df[f"label_{column_suffix}"] = np.where(
            sma_signal == 1, "bullish", "bearish"
        )
        return sma_df

    @staticmethod
    def compute_returns(session_df: pd.DataFrame, slow_ma: int = 20, fast_ma: int = 10):

        label_column = f"label_{slow_ma}_{fast_ma}"
        assert label_column in session_df.columns, session_df.columns

        if session_df[label_column].unique()[0] == "bullish":

            buy_val = session_df["open"].iloc[0]
            sell_val = session_df["close"].iloc[-1]
        else:
            buy_val = session_df["open"].iloc[-1]
            sell_val = session_df["close"].iloc[0]

        perc_returns = ((sell_val - buy_val) / buy_val) * 100

        start_ts = session_df.index[0]
        end_ts = session_df.index[-1]

        return pd.Series(
            {"percent_returns": perc_returns, "session_details": f"{start_ts}-{end_ts}"}
        )

    def evaluate_sma_crossover(
        self,
        slow_ma: int = 20,
        fast_ma: int = 10,
        capture_trend: CaptureTrend = CaptureTrend.ALL,
    ):

        look_back_periods: List[int] = [slow_ma, fast_ma]

        sma_df = self.compute_sma(look_back_periods=look_back_periods)

        scrip_sma_df = pd.concat([self.scrip_df, sma_df], axis=1)

        scrip_sma_sessions = self.sma_sessions(slow_ma=slow_ma, fast_ma=fast_ma)
        merged_scrip_sma_sessions = pd.merge(
            scrip_sma_df, scrip_sma_sessions, left_index=True, right_index=True
        )

        column_suffix = f"{slow_ma}_{fast_ma}"
        aggregated_returns = merged_scrip_sma_sessions.groupby(
            [f"sma_session_{column_suffix}", f"label_{column_suffix}"]
        ).apply(SMAStrategy.compute_returns, slow_ma=slow_ma, fast_ma=fast_ma)

        if capture_trend in [CaptureTrend.BULLISH, CaptureTrend.BEARISH]:
            aggregated_returns = aggregated_returns.loc[
                aggregated_returns.index.get_level_values(f"label_{column_suffix}")
                == capture_trend.value
            ]

        return aggregated_returns
