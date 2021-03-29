import io
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd  # type: ignore
import requests
from requests.exceptions import HTTPError

from analytics.services.alpha_vantage_utils import (
    AVFunctions,
    OutputSize,
    QueryParams,
    ReportsResponse,
    TimeInterval,
    clean_column_names,
)

API_TIMEOUT = 30
API_BASE_URL = "https://www.alphavantage.co/query"


class AVAbstract:
    def __init__(self, api_key):
        self.api_key = api_key

    @staticmethod
    def is_response_valid(response_json: Dict[str, Any]):
        is_valid = True
        if response_json.get("Error Message"):
            return False
        return is_valid


class AVTimeseries(AVAbstract):
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
        result_df.index = pd.to_datetime(result_df.index)
        result_df.columns = list(map(clean_column_names, result_df.columns))

        result_df = result_df.astype(float)

        return result_df.sort_index()

    def get_intraday_data_extended(
        self,
        symbol: str,
        interval: TimeInterval,
        n_months: int = 12,
    ) -> pd.DataFrame:

        # Artificial restriction
        # TODO: resconsider this later
        assert (
            n_months < 100
        ), "a maximum of 100 months worth of data can be fetched, Mostly for safety"

        year, month = 1, 1

        base_params = {
            "apikey": self.api_key,
            "symbol": symbol,
            "interval": interval.value,
            "function": AVFunctions.INTRADAY_EXTENDED.value,
        }

        final_df = pd.DataFrame()

        throttle_count = 1
        for month in range(1, n_months + 1):
            if throttle_count == 5:
                # "Note": "Thank you for using Alpha Vantage! Our standard API call frequency
                # is 5 calls per minute and 500 calls per day.
                # Please visit https://www.alphavantage.co/premium/
                # if you would like to target a higher API call frequency."\n}'
                time.sleep(60)

            if month > 12:
                month = 1
                year += 1

            query_params = QueryParams(
                **base_params,
                slice=f"year{year}month{month}",
            )

            response = requests.get(
                API_BASE_URL,
                params=query_params,  # type: ignore
                timeout=API_TIMEOUT,
            )

            response.raise_for_status()
            result_df = pd.read_csv(io.StringIO(response.content.decode("utf-8")))
            assert "time" in result_df.columns, f"{year}_{month}"
            result_df = result_df.set_index("time")
            result_df.index.name = None

            final_df = final_df.append(result_df)

            throttle_count += 1

        return final_df.sort_index()

    def get_daily_data(
        self,
        symbol: str,
        outputsize: OutputSize = OutputSize.COMPACT,
        adjusted: bool = True,
        last_ten_years_only: bool = True,
    ) -> pd.DataFrame:

        if adjusted:
            av_function: str = AVFunctions.DAILY_ADJUSTED
        else:
            av_function = AVFunctions.DAILY

        query_params = QueryParams(
            apikey=self.api_key,
            function=av_function.value,
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
        if not super().is_response_valid(response_json):
            raise HTTPError(f"Invalid Request with params - {query_params}")

        result = response_json[f"Time Series (Daily)"]

        result_df = pd.DataFrame.from_dict(result, orient="index")
        result_df.index = pd.to_datetime(result_df.index)
        result_df.columns = list(map(clean_column_names, result_df.columns))

        result_df = result_df.astype(float)

        if last_ten_years_only:
            result_df = result_df.loc[
                result_df.index > datetime.now() - timedelta(weeks=520)
            ]

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
        if not super().is_response_valid(response_json):
            raise HTTPError(f"Invalid Request with params - {query_params}")

        result = response_json.get("bestMatches")

        result_df = pd.DataFrame(result)
        result_df.columns = list(map(clean_column_names, result_df.columns))

        return result_df


class AVFundamental(AVAbstract):
    @staticmethod
    def parse_fundamental_report(
        financial_report: Dict[str, Any],
        quarterly_key: str = "quarterlyReports",
        annual_key: str = "annualReports",
    ) -> ReportsResponse:

        quarterly_results_df = pd.DataFrame(financial_report[quarterly_key])
        annual_report_df = pd.DataFrame(financial_report[annual_key])
        return ReportsResponse(
            quarterly_reports=quarterly_results_df, annual_reports=annual_report_df
        )

    def get_balance_sheet(self, symbol: str):

        assert symbol, "symbol cannot be null"

        query_params = QueryParams(
            apikey=self.api_key, symbol=symbol, function=AVFunctions.BALANCE_SHEET.value
        )
        response = requests.get(API_BASE_URL, params=query_params, timeout=API_TIMEOUT)

        response.raise_for_status()

        response_json = response.json()
        if not super().is_response_valid(response_json):
            raise HTTPError(f"Invalid Request with params - {query_params}")

        return __class__.parse_fundamental_report(financial_report=response_json)

    def get_income_statement(self, symbol: str):

        assert symbol, "symbol cannot be null"

        query_params = QueryParams(
            apikey=self.api_key,
            symbol=symbol,
            function=AVFunctions.INCOME_STATEMENT.value,
        )
        response = requests.get(API_BASE_URL, params=query_params, timeout=API_TIMEOUT)

        response.raise_for_status()

        response_json = response.json()
        if not super().is_response_valid(response_json):
            raise HTTPError(f"Invalid Request with params - {query_params}")

        return __class__.parse_fundamental_report(financial_report=response_json)

    def get_earnings_report(self, symbol: str):

        assert symbol, "symbol cannot be null"

        query_params = QueryParams(
            apikey=self.api_key, symbol=symbol, function=AVFunctions.EARNINGS.value
        )
        response = requests.get(API_BASE_URL, params=query_params, timeout=API_TIMEOUT)

        response.raise_for_status()

        response_json = response.json()
        if not super().is_response_valid(response_json):
            raise HTTPError(f"Invalid Request with params - {query_params}")

        return __class__.parse_fundamental_report(
            financial_report=response_json,
            quarterly_key="quarterlyEarnings",
            annual_key="annualEarnings",
        )

    def get_cashflow_report(self, symbol: str):

        assert symbol, "symbol cannot be null"

        query_params = QueryParams(
            apikey=self.api_key, symbol=symbol, function=AVFunctions.CASH_FLOW.value
        )
        response = requests.get(API_BASE_URL, params=query_params, timeout=API_TIMEOUT)

        response.raise_for_status()

        response_json = response.json()
        if not super().is_response_valid(response_json):
            raise HTTPError(f"Invalid Request with params - {query_params}")

        return __class__.parse_fundamental_report(financial_report=response_json)

    def get_company_overview(self, symbol: str):

        assert symbol, "symbol cannot be null"

        query_params = QueryParams(
            apikey=self.api_key, symbol=symbol, function=AVFunctions.OVERVIEW.value
        )
        response = requests.get(API_BASE_URL, params=query_params, timeout=API_TIMEOUT)

        response.raise_for_status()

        response_json = response.json()
        if not super().is_response_valid(response_json):
            raise HTTPError(f"Invalid Request with params - {query_params}")

        return pd.DataFrame.from_dict(response_json, orient="index").T
