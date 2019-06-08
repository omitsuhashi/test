from datetime import date
import xml.etree.ElementTree as ET
import requests
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from models.weekly_meteorological_info_model import WeeklyMeteorologicalInfoModel
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

    # link_url = 'http://www.data.jma.go.jp/developer/xml/data/399f585e-30d9-3336-ab2f-7436b878e16d.xml'
    # links = [x.find(root_prefix+'link').attrib['href'] for x in weekly]
    # weekly = WeeklyMeteorologicalInfoModel(x)
    # session.add_all(weekly.generate_input_data())
    # session.commit()

    link_url = ''

    session.close()
