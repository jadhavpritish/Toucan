import datetime
from dataclasses import dataclass
from typing import Dict

import pandas as pd
from mypy_extensions import TypedDict

from analytics.studies.data_definition import TickerData


class Session(TypedDict):
    start: datetime.date
    end: datetime.date


@dataclass
class PivotPoints(TickerData):
    """
    https://school.stockcharts.com/doku.php?id=technical_indicators:pivot_points
    """

    @staticmethod
    def get_todays_date() -> datetime.date:
        return datetime.date.today()

    @staticmethod
    def get_last_week_session() -> Session:
        todays_date = __class__.get_todays_date()

        current_week_start_date = todays_date - datetime.timedelta(
            days=todays_date.weekday()
        )
        last_week_start_date = current_week_start_date - datetime.timedelta(weeks=1)
        last_week_end_date = last_week_start_date + datetime.timedelta(days=4)
        return Session(start=last_week_start_date, end=last_week_end_date)

    @staticmethod
    def get_last_day_session() -> Session:

        todays_date = __class__.get_todays_date()
        last_day_date = todays_date - datetime.timedelta(days=1)

        return Session(start=last_day_date, end=last_day_date)

    # @staticmethod
    # def get_last_month_session() -> Session:
