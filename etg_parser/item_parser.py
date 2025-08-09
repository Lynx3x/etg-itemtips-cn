
import re

from bs4 import BeautifulSoup,NavigableString,Tag

def extract_item_description(html_content, item_name_en, item_name_cn=None):
    """
    从HTML内容中提取物品描述
    
    参数:
    - html_content: 页面HTML内容
    - item_name_en: 物品英文名称
    - item_name_cn: 物品中文名称（可选）
    
    返回:
    - 提取的描述文本
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 找到所有infobox容器
    all_infoboxes = soup.find_all('div', class_='infobox-container')
    print(f"页面中找到 {len(all_infoboxes)} 个infobox容器")
    
    # 英文名统一小写，并将下划线和横杠替换为空格
    item_name_en_lower = item_name_en.lower().replace('_', ' ').replace('-', ' ')
    
    # 倒序查找匹配的infobox
    target_infobox = None
    for infobox in reversed(all_infoboxes):
        title_div = infobox.find('div', class_='title')
        if title_div and title_div.text:
            # 先尝试用英文名匹配
            if item_name_en_lower in title_div.text.lower():
                target_infobox = infobox
                print(f"找到物品 '{item_name_en}' 的infobox")
                break
            # 如果提供了中文名，尝试用中文名匹配
            elif item_name_cn and item_name_cn in title_div.text:
                target_infobox = infobox
                print(f"找到物品 '{item_name_cn}' 的infobox")
                break
            # 如果精确匹配失败，尝试模糊匹配
            else:
                from difflib import SequenceMatcher
                
                # 计算相似度
                def similarity(a, b):
                    return SequenceMatcher(None, a.lower(), b.lower()).ratio()
                
                title_text = title_div.text.lower()
                en_similarity = similarity(item_name_en_lower, title_text)
                cn_similarity = similarity(item_name_cn or "", title_text) if item_name_cn else 0
                
                # 如果相似度超过阈值(0.6)，认为找到了匹配
                if en_similarity > 0.6 or cn_similarity > 0.6:
                    target_infobox = infobox
                    print(f"通过模糊匹配找到物品 '{item_name_en}' 的infobox，相似度: {max(en_similarity, cn_similarity):.2f}")
                    break
    
    # 如果没找到，那直接打印并且return掉就行
    if not target_infobox:
        print(f"未能找到物品 '{item_name_en}' 的infobox")
        return ""
    
    # 1. 首先查找infobox和下一个synergy-container之间的段落
    next_synergy = target_infobox.find_next('div', class_='synergy-container')

    # 如果没有next_synergy，那就尝试找div class="unlock"
    if not next_synergy:
        unlock_div = target_infobox.find_next('div', class_='unlock')
        if unlock_div:
            next_synergy = unlock_div
            print(f"找到物品 '{item_name_en}' 的unlock")

    # 直接获取infobox和下一个目标元素之间的所有内容
    all_content = ""
    current = target_infobox.next_sibling
    
    while current:
        if next_synergy and current == next_synergy:
            break
        if getattr(current, 'name', None) == 'div':
            break

        # 处理纯文本
        if isinstance(current, NavigableString):
            text = str(current).strip()
            if text:
                all_content += text

        # 处理img、a>img、br、tt等标签
        elif isinstance(current, Tag):
            # 直接是img
            if current.name == 'img':
                alt = current.get('alt', '')
                if alt.lower().endswith('.png'):
                    key = alt[:-4].lower()
                    all_content += f"{{item:{key}}}"
            # a标签里有img
            elif current.name == 'a' and current.find('img'):
                img = current.find('img')
                alt = img.get('alt', '')
                if alt.lower().endswith('.png'):
                    key = alt[:-4].lower()
                    all_content += f"{{item:{key}}}"
            # 处理链接文本
            elif current.name == 'a' and 'link' in current.get('class', []):
                link_text = current.text.strip()
                if link_text:
                    all_content += link_text
            # 处理tt标签
            elif current.name == 'tt':
                tt_text = current.text.strip()
                if tt_text:
                    all_content += f"`{tt_text}`"
            # 处理换行标签
            elif current.name == 'br':
                all_content += "\n"
            # 其他常规内容
            elif current.name == 'p':
                content = process_content(current)
                if content and len(content.strip()) > 0:
                    all_content += ("\n" if all_content else "") + content
            elif current.name in ['ul', 'ol']:
                for li in current.find_all('li', recursive=False):
                    li_text = process_content(li)
                    if li_text and len(li_text.strip()) > 0:
                        all_content += ("\n" if all_content else "") + "- " + li_text
            else:
                # 处理容器内的p/ul/ol/br/tt
                for element in current.find_all(['p', 'ul', 'ol', 'br', 'tt']):
                    if element.name == 'p':
                        content = process_content(element)
                        if content and len(content.strip()) > 0:
                            all_content += ("\n" if all_content else "") + content
                    elif element.name in ['ul', 'ol']:
                        for li in element.find_all('li', recursive=False):
                            li_text = process_content(li)
                            if li_text and len(li_text.strip()) > 0:
                                all_content += ("\n" if all_content else "") + "- " + li_text
                    elif element.name == 'br':
                        all_content += "\n"
                    elif element.name == 'tt':
                        tt_text = element.text.strip()
                        if tt_text:
                            all_content += f"`{tt_text}`"

        current = current.next_sibling
    if all_content:
        print(f"找到物品 '{item_name_en}' 的描述内容")
        return all_content
    
    print(f"未能找到物品 '{item_name_en}' 的描述")
    return ""

def process_content(element):
    """
    处理HTML元素，提取并格式化其内容
    
    参数:
    - element: BeautifulSoup元素
    
    返回:
    - 处理后的文本内容
    """
    # 复制一个元素副本用于处理
    element_copy = BeautifulSoup(str(element), 'html.parser')
    
    # 常见物品/资源的中文名称映射
    # item_name_map = {
    #     'Key.png': '钥匙',
    #     'Money.png': '弹壳',
    #     'Ammo.png': '弹药',
    #     'Spread_Ammo.png': '散弹',
    #     'Blank.png': '空弹',
    #     'Heart.png': '心',
    #     'Half_Heart.png': '半心',
    #     'Armor.png': '护甲',
    #     'Gnawed_Key.png': '被咬的钥匙',
    #     'Rat_Chest.png': '老鼠宝箱',
    # }
    
    # 处理基础资源的图片标签，替换为占位符
    for img in element_copy.find_all('img'):
        parent = img.parent
        img_alt = img.get('alt', '')
        
        # 从alt属性中提取物品名称（去掉.png后缀）
        if '.png' in img_alt:
            item_name = img_alt.split('.png')[0].lower()
            placeholder = f'{{item:{item_name}}}'
            
            # 替换图片标签为占位符
            if parent and parent.name == 'a':
                parent.replace_with(placeholder)
            else:
                img.replace_with(element_copy.new_string(placeholder))
        else:
            # 无法识别的图片直接移除
            img.decompose()
    
    # 找到所有ul标签并临时移除，以免其内容被重复提取
    ul_tags = []
    for ul_tag in element_copy.find_all(['ul', 'ol']):
        ul_copy = ul_tag.extract()  # 从DOM中移除，但保留引用
        ul_tags.append(ul_copy)
    
    # 提取文本，保留换行符
    lines = []

    # 处理非ul/ol内容
    for content in element_copy.contents:
        if content.name == 'br':
            lines.append('\n')
        elif content.name == 'hr':
            continue  # 忽略水平线
        elif content.string:
            lines.append(content.string.strip())
        elif hasattr(content, 'find_all'):
            # 处理内部可能包含的<br>标签
            text = ''
            for item in content.contents:
                if item.name == 'br':
                    text += '\n'
                elif isinstance(item, str):
                    text += item.strip()
                else:
                    text += item.get_text(strip=True)
            lines.append(text)
        elif content.get_text(strip=True):
            lines.append(content.get_text(strip=True))
    
    # 合并文本行并处理格式
    description = ''.join(lines).strip()
    
    # 替换连续的换行符为单个换行符
    description = re.sub(r'\n\s*\n+', '\n', description)
    
    # 处理常见的格式问题
    # 在冒号后添加空格
    description = re.sub(r'([：:])(?!\s)', r'\1 ', description)
    
    # 在数字和文字之间添加空格
    description = re.sub(r'(\d)([级])(?!\s)', r'\1 \2', description)
    
    # 在句号后添加空格
    description = re.sub(r'([。])(?!\s|$)', r'\1 ', description)
    
    # 然后处理之前移除的ul/ol列表
    for ul_tag in ul_tags:
        ul_text = []
        for li in ul_tag.find_all('li'):
            # 处理li标签内的图片 (已经在之前的代码处理过了)
                
            li_text = li.get_text(strip=True)
            if li_text:
                ul_text.append(f"- {li_text}")
        
        # 将ul内容添加到描述中
        if ul_text:
            if description:  # 如果已有描述文本，添加换行
                description = f"{description}\n" + "\n".join(ul_text)
            else:  # 否则直接添加
                description = "\n".join(ul_text)
    
    # 最后的格式清理
    # 移除多余的空格
    description = re.sub(r' +', ' ', description)
    # 确保句子之间有适当的空格
    description = re.sub(r'([。！？])\s*([^\s])', r'\1 \2', description)
    # 移除行首行尾的空白字符
    description = re.sub(r'^\s+|\s+$', '', description, flags=re.MULTILINE)
    
    return description
