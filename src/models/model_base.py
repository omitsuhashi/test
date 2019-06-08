import re
import xml.etree.ElementTree as ET

from sqlalchemy.ext.declarative import declarative_base

xmlns_regex = re.compile(r'({(.+)})(.+)')

Base = declarative_base()


class ModelBase:
    def __init__(self, root: ET.Element):
        self.root_prefix = self.get_prefix(root.tag)

    @staticmethod
    def get_prefix(tag: str) -> str:
        return xmlns_regex.search(tag).group(1)

    @staticmethod
    def get_tag_name(tag: str) -> str:
        return xmlns_regex.search(tag).group(3)
