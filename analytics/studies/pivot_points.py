import pandas as pd
from dataclasses import dataclass
from analytics.studies.data_definition import TickerData
import datetime
from typing import Dict

def get_todays_date() -> datetime.date:

    return datetime.date.today()

def get_last_week_session() -> Dict[str, datetime.date]:
    todays_date = get_todays_date()

    current_week_start_date = todays_date - datetime.timedelta(days = todays_date.weekday())
    last_week_start_date = current_week_start_date - datetime.timedelta(weeks =1)
    last_week_end_date = last_week_start_date + datetime.timedelta(days=5)
    return {"session_start": last_week_start_date, "session_end": last_week_end_date}

def get_last_day_session() -> Dict[str, datetime.date]:

    todays_date = get_todays_date()
    last_day_date = todays_date - datetime.timedelta(days=1)

    return {"session_start": last_day_date, "session_end": last_day_date}


@dataclass
class PivotPoints(TickerData):

    pass