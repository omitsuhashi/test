from datetime import date
import xml.etree.ElementTree as ET
import requests
import re

from models.weekly_meteorological_info_model import WeeklyMeteorologicalInfoModel


API = 'http://www.data.jma.go.jp/developer/xml/feed/regular_l.xml'

xmlns_regex = re.compile(r'({(.*)})(\w)')


def get_prefix(tag: str) -> str:
    return xmlns_regex.search(tag).group(1)


if __name__ == '__main__':
    res = requests.get(API)
    root = ET.fromstring(res.content)
    root_prefix = get_prefix(root.tag)

    entries = root.findall(root_prefix+'entry')
    today = date.today().strftime('%Y-%m-%d')
    today_entry = [x for x in entries if today in x.find(root_prefix+'updated').text]
    weekly = [x for x in today_entry if x.find(root_prefix+'title').text == '府県週間天気予報']
    recently = [x for x in today_entry if x.find(root_prefix+'title').text == '府県天気予報']

    x = weekly[0]
    link_url = x.find(root_prefix+'link').attrib['href']
    WeeklyMeteorologicalInfoModel(link_url)
