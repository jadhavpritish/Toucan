from enum import Enum

import pandas as pd #type: ignore
import requests
from typing_extensions import TypedDict
from typing import Optional

API_TIMEOUT = 30


class TimeInterval(Enum):

    ONE_MIN: str = "1min"
    FIVE_MIN: str = "5min"
    FIFTEEN_MIN: str = "15min"
    THIRTY_MIN: str = "30min"
    SIXTY_MIN: str = "60min"


class OutputSize(Enum):

    COMPACT: str = "compact"
    FULL: str = "full"


class QueryParams(TypedDict, total=False):
    apikey: str
    symbol: str
    interval: Optional[str]
    function: str
    outputsize: str


class AVFunctions(Enum):
    INTRADAY: str = "TIME_SERIES_INTRADAY"
    INTRADAY_EXTENDED: str = "TIME_SERIES_INTRADAY_EXTENDED"
    DAILY: str = "TIME_SERIES_DAILY"
    DAILY_ADJUSTED: str = "TIME_SERIES_DAILY_ADJUSTED"
    WEEKLY: str = "TIME_SERIES_WEEKLY"


class AVTimeseries:
    def __init__(self, api_key: str):

        self.API_BASE_URL = "https://www.alphavantage.co/query"
        self.api_key = api_key
        self._expected_columns = ["open", "high", "low", "close", "volume"]

    def get_intraday_data(
        self,
        symbol: str,
        interval: TimeInterval,
        outputsize: OutputSize = OutputSize.COMPACT,
    ) -> pd.DataFrame:

        query_params = QueryParams(
            apikey=self.api_key,
            symbol=symbol,
            interval=interval.value,
            outputsize=outputsize.value,
            function=AVFunctions.INTRADAY.value,
        )

        response = requests.get(
            self.API_BASE_URL,
            params=query_params, #type: ignore
            timeout=API_TIMEOUT,
        )

        response.raise_for_status()

        result = response.json()[f"Time Series ({interval.value})"]

        result_df = pd.DataFrame.from_dict(result, orient="index")
        result_df.columns = self._expected_columns
        result_df[self._expected_columns] = result_df[self._expected_columns].astype(
            float
        )

        return result_df.sort_index()

    def get_daily_data(self, symbol: str, outputsize: OutputSize = OutputSize.COMPACT):

        query_params = QueryParams(apikey=self.api_key,
                                   symbol=symbol,
                                   function=AVFunctions.DAILY.value,
                                   outputsize=outputsize.value)
        response = requests.get(
            self.API_BASE_URL,
            params=query_params, #type: ignore
            timeout=API_TIMEOUT,
        )

        response.raise_for_status()

        result = response.json()[f"Time Series (Daily)"]

        result_df = pd.DataFrame.from_dict(result, orient="index")
        result_df.columns = self._expected_columns

        result_df[self._expected_columns] = result_df[self._expected_columns].astype(
            float
        )

        return result_df.sort_index()
