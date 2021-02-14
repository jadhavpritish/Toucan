from dataclasses import dataclass
from enum import Enum
from typing import List

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

from analytics.strategies.utils import Trend
from analytics.studies.moving_averages import MAModels, MovingAverages


@dataclass
class MAStrategy(MovingAverages):

    slow_ma: int
    fast_ma: int
    ma_model: MAModels = MAModels.SMA

    def __post_init__(self):

        # sanity check to ensure that slow_ma is greater than faster_ma
        assert (
            self.slow_ma > self.fast_ma
        ), f"slow ma should be greater than fast ma- received - slow_ma - {self.slow_ma}, fast_ma-{self.fast_ma}"
        self.column_suffix = f"{self.slow_ma}_{self.fast_ma}"

    def ma_sessions(self):

        look_back_periods: List[int] = [self.slow_ma, self.fast_ma]

        if self.ma_model == MAModels.SMA:
            ma_df = self.compute_sma(look_back_periods=look_back_periods)
        else:
            assert self.ma_model == MAModels.EWMA
            ma_df = self.compute_ema(look_back_periods=look_back_periods)

        ma_df = pd.concat(
            [self.ticker_df, ma_df],
            axis=1,
        )

        expected_columns = set([f"ma_{col}" for col in [self.slow_ma, self.fast_ma]])
        assert expected_columns.issubset(
            ma_df.columns
        ), f"Expecting columns {expected_columns} for computing ma cross over sessions. Received {ma_df}"

        # identify start of a session by annotating the time when faster moving average crosses over the
        # slower moving average.
        ma_df[f"ma_signal_{self.column_suffix}"] = (
            ma_df[f"ma_{self.fast_ma}"] > ma_df[f"ma_{self.slow_ma}"]
        )

        # Next we need to create sesssions. A sessions last as long as the faster moving average does not cross
        # above or below the slower moving average.
        # We use EX-OR truth table to identify change overs.
        ma_df[f"ma_session_{self.column_suffix}"] = (
            (
                ma_df[f"ma_signal_{self.column_suffix}"]
                ^ ma_df[f"ma_signal_{self.column_suffix}"].shift(1)
            )
            .fillna(False)
            .cumsum(skipna=False)
        )

        # annotate session as either bullish or bearish
        ma_df[f"label_{self.column_suffix}"] = np.where(
            ma_df[f"ma_signal_{self.column_suffix}"] == 1, "bullish", "bearish"
        )
        return ma_df

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
    def evaluate_ma_crossover(
        cls,
        ticker_df: pd.DataFrame,
        slow_ma: int = 20,
        fast_ma: int = 10,
        capture_trend: Trend = Trend.ALL,
        ma_model: MAModels = MAModels.SMA,
    ):
        """
        1. computes Simple Moving Averages
        2. Computes historical crossovers using MA strategy and annotates sessions
        3. Aggregates data by session and trend to compute estimated resturns per session.
        """

        ma_obj = cls(
            ticker_df=ticker_df, slow_ma=slow_ma, fast_ma=fast_ma, ma_model=ma_model
        )

        # Annotate sessions. A session start when faster MA cross above or below the slower MA.
        scrip_ma_sessions = ma_obj.ma_sessions()

        column_suffix = f"{slow_ma}_{fast_ma}"
        # aggregate session to compute estimated returns per session.
        aggregated_returns = scrip_ma_sessions.groupby(
            [f"ma_session_{column_suffix}", f"label_{column_suffix}"], as_index=True
        ).apply(MAStrategy.compute_returns, slow_ma=slow_ma, fast_ma=fast_ma)

        # Filter results for ease of decision making.
        if capture_trend in [Trend.BULLISH, Trend.BEARISH]:
            aggregated_returns = aggregated_returns.loc[
                aggregated_returns.index.get_level_values(f"label_{column_suffix}")
                == capture_trend.value
            ]

        return aggregated_returns
