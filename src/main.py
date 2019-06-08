from datetime import date
import xml.etree.ElementTree as ET
import requests
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from models.weekly_meteorological_info_model import WeeklyMeteorologicalInfoModel
from models.recently_meteorological_info_model import RecentlyMeteorologicalInfoModel
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

    session.close()
