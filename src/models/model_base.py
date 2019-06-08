import re
import xml.etree.ElementTree as ET

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
xmlns_regex = re.compile(r'({(.*)})(\w)')


class ModelBase:
    __table__ = 'Meta'

    def __init__(self, root: ET.Element):
        tag_name = self.get_tag_name(root.tag)
        self.root_prefix = self.get_prefix(root.tag)

    @staticmethod
    def get_prefix(tag: str) -> str:
        return xmlns_regex.search(tag).group(1)

    @staticmethod
    def get_tag_name(tag: str) -> str:
        return xmlns_regex.search(tag).group(3)
