from typing import Any, Dict

import pandas as pd  # type: ignore
import requests
from requests.exceptions import HTTPError

from analytics.services.alpha_vantage_utils import (
    AVFunctions,
    OutputSize,
    QueryParams,
    TimeInterval,
    clean_column_names,
)

API_TIMEOUT = 30
API_BASE_URL = "https://www.alphavantage.co/query"


class AVTimeseries:
    def __init__(self, api_key: str):

        self.api_key = api_key

    @staticmethod
    def is_response_valid(response_json: Dict[str, Any]):
        is_valid = True
        if response_json.get("Error Message"):
            return False
        return is_valid

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
            API_BASE_URL,
            params=query_params,  # type: ignore
            timeout=API_TIMEOUT,
        )

        response.raise_for_status()

        response_json = response.json()
        if not AVTimeseries.is_response_valid(response_json):
            raise HTTPError(f"Invalid Request with params - {query_params}")

        result = response_json[f"Time Series ({interval.value})"]

        result_df = pd.DataFrame.from_dict(result, orient="index")
        result_df.columns = list(map(clean_column_names, result_df.columns))

        result_df = result_df.astype(float)

        return result_df.sort_index()

    def get_daily_data(
        self, symbol: str, outputsize: OutputSize = OutputSize.COMPACT
    ) -> pd.DataFrame:

        query_params = QueryParams(
            apikey=self.api_key,
            function=AVFunctions.DAILY.value,
            symbol=symbol,
            outputsize=outputsize.value,
        )
        response = requests.get(
            API_BASE_URL,
            params=query_params,  # type: ignore
            timeout=API_TIMEOUT,
        )

        response.raise_for_status()

        response_json = response.json()
        if not AVTimeseries.is_response_valid(response_json):
            raise HTTPError(f"Invalid Request with params - {query_params}")

        result = response_json[f"Time Series (Daily)"]

        result_df = pd.DataFrame.from_dict(result, orient="index")
        result_df.columns = list(map(clean_column_names, result_df.columns))

        result_df = result_df.astype(float)

        return result_df.sort_index()

    def get_symbol_search_results(self, search_keyword: str) -> pd.DataFrame:

        query_params = QueryParams(
            apikey=self.api_key,
            function=AVFunctions.SYMBOl_SEARCH.value,
            keywords=search_keyword,
        )

        response = requests.get(API_BASE_URL, params=query_params, timeout=API_TIMEOUT)

        response.raise_for_status()

        response_json = response.json()
        if not AVTimeseries.is_response_valid(response_json):
            raise HTTPError(f"Invalid Request with params - {query_params}")

        result = response_json.get("bestMatches")

        result_df = pd.DataFrame(result)
        result_df.columns = list(map(clean_column_names, result_df.columns))

        return result_df
