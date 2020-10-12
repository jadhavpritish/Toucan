from dataclasses import dataclass
from enum import Enum
from typing import List

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

from analytics.strategies.utils import Trend
from analytics.studies.macd import MACD


class MACDCrossOverStrategy(MACD):
    def macd_crossover_sessions(self):

        macd_df = self.compute_macd()

        # identify start of a session by annotating the time when faster moving average crosses over the
        # slower moving average.
        macd_df["macd_crosover_signal"] = macd_df["macd_line"] > macd_df[f"macd_signal"]

        # Next we need to create sesssions. A sessions last as long as the macd_line does not cross
        # above or below the macd_signal line.
        # We use EX-OR truth table to identify change overs.
        macd_df[f"macd_session"] = (
            (macd_df["macd_crosover_signal"] ^ macd_df["macd_crosover_signal"].shift(1))
            .fillna(False)
            .cumsum(skipna=False)
        )

        # annotate session as either bullish or bearish
        macd_df[f"label_macd"] = np.where(
            macd_df["macd_crosover_signal"] == 1, "bullish", "bearish"
        )
        return macd_df

    @staticmethod
    def compute_returns(session_df: pd.DataFrame):
        label_column = f"label_macd"
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

        n_sessions = len(session_df)

        return pd.Series(
            {
                "percent_returns": perc_returns,
                "session_details": f"{start_ts}-{end_ts}",
                "number_of_sessions": n_sessions,
            }
        )

    @classmethod
    def evaluate_macd_crossover(
        cls,
        ticker_df: pd.DataFrame,
        capture_trend: Trend = Trend.ALL,
    ):
        """

        1. Computes historical crossovers using MACD crossover strategy and annotates sessions
        2. Aggregates data by session and trend to compute estimated resturns per session.
        """

        macd_obj = cls(ticker_df=ticker_df)

        # Annotate sessions. A session start when faster MA cross above or below the slower MA.
        ticker_macd_sessions = macd_obj.macd_crossover_sessions()

        # aggregate session to compute estimated returns per session.
        aggregated_returns = ticker_macd_sessions.groupby(
            [f"macd_session", f"label_macd"], as_index=True
        ).apply(MACDCrossOverStrategy.compute_returns)

        # Filter results for ease of decision making.
        if capture_trend in [Trend.BULLISH, Trend.BEARISH]:
            aggregated_returns = aggregated_returns.loc[
                aggregated_returns.index.get_level_values(f"label_macd")
                == capture_trend.value
            ]

        return aggregated_returns
