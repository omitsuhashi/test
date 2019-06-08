import xml.etree.ElementTree as ET
import requests

from datetime import datetime, date, timedelta
from typing import List
from sqlalchemy import Column, Integer, String, Date, Float

from models.model_base import ModelBase, Base


class MeteorologicalInfosModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(MeteorologicalInfosModel, self).__init__(root)
        time_series_infos = root.findall(self.root_prefix+'TimeSeriesInfo')
        self.times = list()
        self.items_list = list()
        for time_series_info in time_series_infos:
            time_series_info_prefix = self.get_prefix(time_series_info.tag)
            self.times.append(TimeDefinesModel(time_series_info.find(time_series_info_prefix+'TimeDefines')))
            self.items_list.append([ItemModel(x) for x in time_series_info.findall(time_series_info_prefix+'Item')])


class MeteorologicalInfoModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(MeteorologicalInfoModel, self).__init__(root)
        time_series_infos = root.findall(self.root_prefix+'TimeSeriesInfo')
        self.times = list()
        self.items_list = list()
        for time_series_info in time_series_infos:
            time_series_info_prefix = self.get_prefix(time_series_info.tag)
            self.times.append(TimeDefinesModel(time_series_info.find(time_series_info_prefix+'TimeDefines')))
            self.items_list.append([ItemModel(x) for x in time_series_info.findall(time_series_info_prefix+'Item')])


class TimeDefinesModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(TimeDefinesModel, self).__init__(root)
        self.times = [TimeDefineModel(x) for x in root.findall(self.root_prefix+'TimeDefine')]


class TimeDefineModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(TimeDefineModel, self).__init__(root)
        self.id = root.attrib['timeId']
        self.date_time = root.find(self.root_prefix+'DateTime').text
        duration = root.find(self.root_prefix+'Duration')
        self.duration = duration.text if duration else None


class ItemModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(ItemModel, self).__init__(root)
        self.kinds = [KindModel(x) for x in root.findall(self.root_prefix+'Kind')]
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
        self.properties = [PropertyModel(x) for x in root.findall(self.root_prefix+'Property')]


class PropertyModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(PropertyModel, self).__init__(root)
        self.type = root.find(self.root_prefix+'Type').text
        self.data_parts = [DataPartModel(x) for x in list(root) if self.get_tag_name(x.tag) != 'Type']


class DataPartModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(DataPartModel, self).__init__(root)
        self.type = self.get_tag_name(root.tag)
        self.data = [DataModel(x) for x in list(root) if self.get_tag_name(x.tag) != 'Type']


class DataModel(ModelBase):
    def __init__(self, root: ET.Element):
        super(DataModel, self).__init__(root)
        self.type = root.attrib.get('type')
        self.refId = root.attrib.get('refID')
        self.value = root.text


class RecentlyData(Base):
    __tablename__ = 'recently'
    id = Column(Integer, autoincrement=True, primary_key=True)
    observation_spot = Column(String(256))
    date = Column(Date)
    primary_code = Column(Integer)
    secondary_code = Column(Integer)
    min_temperature = Column(Integer, nullable=True)
    precipitation = Column(Float, nullable=True)


class RecentlyMeteorologicalInfoModel(ModelBase):
    point_predict = None
    area_predict = None

    def __init__(self, url: str):
        raw = requests.get(url).content
        root = ET.fromstring(raw)
        super(RecentlyMeteorologicalInfoModel, self).__init__(root)

        body = root[2]
        body_prefix = self.get_prefix(body.tag)
        meteorological_infos = body.findall(body_prefix+'MeteorologicalInfos')
        for x in meteorological_infos:
            type_attr = x.attrib['type']
            if type_attr == '区域予報':
                if self.area_predict is None:
                    self.area_predict = MeteorologicalInfoModel(x)
                else:
                    self.area_predict_3h = MeteorologicalInfoModel(x)
            elif type_attr == '地点予報':
                if self.point_predict is None:
                    self.point_predict = MeteorologicalInfoModel(x)
                else:
                    self.point_predict_3h = MeteorologicalInfoModel(x)

    def __get_date(self) -> List[date]:
        fmt = '%Y-%m-%dT%H:%M:%S+09:00'
        return [datetime.strptime(x.date_time, fmt).date() for x in self.area_predict.times[1].times]

    @staticmethod
    def __get_data_list(item: ItemModel, property_type: str) -> List[DataModel]:
        data = list()
        for kind in item.kinds:
            for prop in kind.properties:
                if prop.type == property_type:
                    data.append(prop.data_parts[0].data)
        return data[0]

    def generate_input_data(self) -> List[RecentlyData]:
        data = list()
        date_list = self.__get_date()
        for x, y in zip(self.area_predict.items_list[1], self.point_predict.items_list[0]):
            min_tt_list = self.__get_data_list(y, '朝の最低気温')
            precipitation_list = self.__get_data_list(x, '降水確率')
            s = date_list.index(date.today() + timedelta(days=1))
            min_tt = min_tt_list[0]
            precipitation = max([x.value for x in precipitation_list[s:]])
            data.append(RecentlyData(
                observation_spot=x.area.name,
                date=date_list[s],
                primary_code=x.area.code,
                secondary_code=y.area.code,
                min_temperature=min_tt.value,
                precipitation=precipitation
            ))
        return data
