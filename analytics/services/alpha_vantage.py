from enum import Enum

import pandas as pd
import requests

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


class AVFunctions(Enum):
    INTRADAY: str = "TIME_SERIES_INTRADAY"
    INTRADAY_EXTENDED: str = "TIME_SERIES_INTRADAY_EXTENDED"
    DAILY: str = "TIME_SERIES_DAILY"
    DAILY_ADJUSTED: str = "TIME_SERIES_DAILY_ADJUSTED"
    WEEKLY: str = "TIME_SERIES_WEEKLY"


class AVTimeseries:
    def __init__(self, api_key: str):

        self.API_BASE_URL = "https://www.alphavantage.co/query"

        self.params = {
            "apikey": api_key,
        }

        self._expected_columns = ["open", "high", "low", "close", "volume"]

    def get_intraday_data(
        self,
        symbol: str,
        interval: TimeInterval,
        outputsize: str = OutputSize.COMPACT.value,
    ) -> pd.DataFrame:

        query_params = {}

        query_params["symbol"] = symbol
        query_params["interval"] = interval.value
        query_params["function"] = AVFunctions.INTRADAY.value
        query_params["outputsize"] = outputsize
        response = requests.get(
            self.API_BASE_URL,
            params={**self.params, **query_params},
            timeout=API_TIMEOUT,
        )

        response.raise_for_status()

        result = response.json()[f"Time Series ({interval.value})"]

        result_df = pd.DataFrame.from_dict(result, orient="index")
        result_df.columns = self._expected_columns

        return result_df.sort_index()

    def get_daily_data(self, symbol: str, outputsize: str = OutputSize.COMPACT.value):

        query_params = {}
        query_params["symbol"] = symbol
        query_params["function"] = AVFunctions.DAILY.value
        query_params["outputsize"] = outputsize

        response = requests.get(
            self.API_BASE_URL,
            params={**self.params, **query_params},
            timeout=API_TIMEOUT,
        )

        response.raise_for_status()

        result = response.json()[f"Time Series (Daily)"]

        result_df = pd.DataFrame.from_dict(result, orient="index")
        result_df.columns = self._expected_columns

        return result_df.sort_index()
