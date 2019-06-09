import xml.etree.ElementTree as ET
import requests
import re
import pandas as pd

from datetime import date
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker

from models.weekly_meteorological_info_model import WeeklyMeteorologicalInfoModel, WeeklyData
from models.recently_meteorological_info_model import RecentlyMeteorologicalInfoModel, RecentlyData
from models.model_base import Base

API = 'http://www.data.jma.go.jp/developer/xml/feed/regular_l.xml'
xmlns_regex = re.compile(r'({(.*)})(\w)')


def get_prefix(tag: str) -> str:
    return xmlns_regex.search(tag).group(1)


if __name__ == '__main__':
    engine = create_engine('sqlite:///forecasts.sqlite3', echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine)
    session = Session()
    res = requests.get(API)
    root = ET.fromstring(res.content)
    root_prefix = get_prefix(root.tag)

    entries = root.findall(root_prefix+'entry')
    today = date.today().strftime('%Y-%m-%d')
    today_entry = [x for x in entries if today in x.find(root_prefix+'updated').text]
    weekly = [x for x in today_entry if x.find(root_prefix+'title').text == '府県週間天気予報']
    recently = [x for x in today_entry if x.find(root_prefix+'title').text == '府県天気予報']

    weekly_stack = list()
    recently_stack = list()

    for x in weekly:
        title = x.find(root_prefix+'author').find(root_prefix+'name').text
        if title not in weekly_stack:
            link = x.find(root_prefix+'link').attrib['href']
            w = WeeklyMeteorologicalInfoModel(link)
            session.add_all(w.generate_input_data())
            weekly_stack.append(title)
    for x in recently:
        title = x.find(root_prefix+'author').find(root_prefix+'name').text
        if title not in recently_stack:
            link = x.find(root_prefix+'link').attrib['href']
            w = RecentlyMeteorologicalInfoModel(link)
            session.add_all(w.generate_input_data())
            recently_stack.append(title)
    session.commit()

    for y in session.query(RecentlyData).all():
        d = str(y.date)
        p_code = int(y.primary_code)
        s_code = int(y.secondary_code)
        x = session.query(WeeklyData).filter(and_(
            WeeklyData.date == d,
            or_(
                WeeklyData.secondary_code == s_code,
                WeeklyData.primary_code == p_code
            )
        )).first()
        if x is None:
            continue
        x.min_temperature = y.min_temperature
        x.precipitation = y.precipitation
    session.commit()

    def convert_forecast_one_hot(forecast: str) -> pd.Series:
        forecast_one_hot = {
            'sunny': 0,
            'cloud': 0,
            'rain': 0,
            'snow': 0
        }
        if '晴れ' in forecast:
            forecast_one_hot['sunny'] = 1
        if 'くもり' in forecast:
            forecast_one_hot['cloud'] = 1
        if '雨' in forecast:
            forecast_one_hot['rain'] = 1
        if '雪' in forecast:
            forecast_one_hot['snow'] = 1
        return pd.Series(forecast_one_hot, forecast_one_hot.keys())

    data = list()
    for x in session.query(WeeklyData).all():
        precipitation = x.precipitation / 100 if x.precipitation > 0 else x.precipitation
        forecasts = convert_forecast_one_hot(x.forecast)
        d = pd.Series(
            [x.date.strftime('%Y%m%d'), x.primary_code, x.secondary_code, x.min_temperature, precipitation],
            index=['date', 'pref_id_1', 'pref_id_2', 'minTT', 'precipitation']
        )
        d = pd.concat([d, forecasts])
        precipitation = x.precipitation / 100 if x.precipitation > 0 else x.precipitation
        data.append(d)
    d = pd.DataFrame(data)
    d.to_csv('./test.csv', index=False)

    session.close()
