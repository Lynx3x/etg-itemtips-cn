# 使etg_parser目录成为一个有效的Python包
# 导出extract_item_tips模块中的函数
from .extract_item_tips import get_page_content_selenium 
from .synergy_parser import extract_item_synergies
from .item_parser import extract_item_description

__all__ = ['extract_item_description', 'extract_item_synergies', 'get_page_content_selenium']