import xml.etree.ElementTree as ET
import requests

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.model_base import ModelBase


class WeeklyMeteorologicalInfoModel(ModelBase):
    def __init__(self, url: str):
        raw = requests.get(url).content
        root = ET.fromstring(raw)
        super(WeeklyMeteorologicalInfoModel, self).__init__(root)

        body = root[2]
        body_prefix = self.get_prefix(body.tag)
        meteorological_infos = body.findall(body_prefix+'MeteorologicalInfos')
        for x in meteorological_infos:
            type_attr = x.attrib['type']
            if type_attr == '区域予報':
                self.area_predict = MeteorologicalInfoModel(x)
            elif type_attr == '地点予報':
                self.point_predict = MeteorologicalInfoModel(x)

    def store_data(self):
        engine = create_engine('sqlite:///meteorological.sqlite3')


class MeteorologicalInfoModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(MeteorologicalInfoModel, self).__init__(root)
        time_series_info = root.find(self.root_prefix+'TimeSeriesInfo')
        time_series_info_prefix = self.get_prefix(time_series_info.tag)
        self.time = TimeDefinesModel(time_series_info.find(time_series_info_prefix+'TimeDefines'))
        self.values = ItemModel(time_series_info.find(time_series_info_prefix+'Item'))


class TimeDefinesModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(TimeDefinesModel, self).__init__(root)
        self.values = [TimeDefineModel(x) for x in root.findall(self.root_prefix+'TimeDefine')]


class TimeDefineModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(TimeDefineModel, self).__init__(root)
        self.id = root.attrib['timeId']
        self.date_time = root.find(self.root_prefix+'DateTime').text
        self.duration = root.find(self.root_prefix+'Duration').text


class ItemModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(ItemModel, self).__init__(root)
        self.values = KindModel(root.find(self.root_prefix+'Kind'))
        area = root.find(self.root_prefix+'Station')
        area = area if area else root.find(self.root_prefix+'Area')
        self.area = AreaModel(area)


class AreaModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(AreaModel, self).__init__(root)
        self.name = root.find(self.root_prefix+'Name').text
        self.code = root.find(self.root_prefix+'Code').text


class KindModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(KindModel, self).__init__(root)
        self.values = [PropertyModel(x) for x in root.findall(self.root_prefix+'Property')]


class PropertyModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(PropertyModel, self).__init__(root)
        self.type = root.find(self.root_prefix+'Type').text
        self.values = [DataPartModel(x) for x in list(root) if self.get_prefix(x.tag) != 'Type']


class DataPartModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(DataPartModel, self).__init__(root)
        self.type = self.get_tag_name(root.tag)
        self.values = [DataModel(x) for x in list(root)]


class DataModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(DataModel, self).__init__(root)
        self.type = root.attrib['type']
        self.refId = root.attrib['refID']
        self.value = root.text
