from dataclasses import dataclass
from enum import Enum
from typing import List

import numpy as np  # type: ignore
import pandas as pd  # type: ignore


class Trend(Enum):

    BEARISH: str = "bearish"
    BULLISH: str = "bullish"
    ALL: str = "all"


@dataclass
class SMAStrategy:
    scrip_df: pd.DataFrame
    slow_ma: int
    fast_ma: int

    def __post_init__(self):

        # sanity check to ensure that slow_ma is greater than faster_ma
        assert (
            self.slow_ma > self.fast_ma
        ), f"slow ma should be greater than fast ma- received - slow_ma - {self.slow_ma}, fast_ma-{self.fast_ma}"
        self.column_suffix = f"{self.slow_ma}_{self.fast_ma}"

    def compute_sma(
        self, column: str = "close", look_back_periods: List[int] = [5, 10, 20, 40]
    ):

        sma_dict = {}
        for n in look_back_periods:
            sma_values = self.scrip_df[column].rolling(window=n).mean()
            sma_values.fillna(self.scrip_df[column].astype(float), inplace=True)
            sma_dict[f"sma_{n}"] = sma_values

        return pd.DataFrame(sma_dict, index=self.scrip_df.index)

    def sma_sessions(self):

        look_back_periods: List[int] = [self.slow_ma, self.fast_ma]

        sma_df = pd.concat(
            [self.scrip_df, self.compute_sma(look_back_periods=look_back_periods)],
            axis=1,
        )

        expected_columns = set([f"sma_{col}" for col in [self.slow_ma, self.fast_ma]])
        assert expected_columns.issubset(
            sma_df.columns
        ), f"Expecting columns {expected_columns} for computing sma cross over sessions. Received {sma_df}"

        # identify start of a session by annotating the time when faster moving average crosses over the
        # slower moving average.
        sma_df[f"sma_signal_{self.column_suffix}"] = (
            sma_df[f"sma_{self.fast_ma}"] > sma_df[f"sma_{self.slow_ma}"]
        )

        # Next we need to create sesssions. A sessions last as long as the faster moving average does not cross
        # above or below the slower moving average.
        # We use EX-OR truth table to identify change overs.
        sma_df[f"sma_session_{self.column_suffix}"] = (
            (
                sma_df[f"sma_signal_{self.column_suffix}"]
                ^ sma_df[f"sma_signal_{self.column_suffix}"].shift(1)
            )
            .fillna(False)
            .cumsum(skipna=False)
        )

        # annotate session as either bullish or bearish
        sma_df[f"label_{self.column_suffix}"] = np.where(
            sma_df[f"sma_signal_{self.column_suffix}"] == 1, "bullish", "bearish"
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

    @classmethod
    def evaluate_sma_crossover(
        cls,
        raw_scrip_df: pd.DataFrame,
        slow_ma: int = 20,
        fast_ma: int = 10,
        capture_trend: Trend = Trend.ALL,
    ):
        """
        1. computes Simple Moving Averages
        2. Computes historical crossovers using SMA strategy and annotates sessions
        3. Aggregates data by session and trend to compute estimated resturns per session.
        """

        sma_obj = cls(scrip_df=raw_scrip_df, slow_ma=slow_ma, fast_ma=fast_ma)

        # Annotate sessions. A session start when faster MA cross above or below the slower MA.
        scrip_sma_sessions = sma_obj.sma_sessions()

        column_suffix = f"{slow_ma}_{fast_ma}"
        # aggregate session to compute estimated returns per session.
        aggregated_returns = scrip_sma_sessions.groupby(
            [f"sma_session_{column_suffix}", f"label_{column_suffix}"], as_index=True
        ).apply(SMAStrategy.compute_returns, slow_ma=slow_ma, fast_ma=fast_ma)

        # Filter results for ease of decision making.
        if capture_trend in [Trend.BULLISH, Trend.BEARISH]:
            aggregated_returns = aggregated_returns.loc[
                aggregated_returns.index.get_level_values(f"label_{column_suffix}")
                == capture_trend.value
            ]

        return aggregated_returns
