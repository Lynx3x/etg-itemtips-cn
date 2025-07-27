
import re

from bs4 import BeautifulSoup

def extract_item_synergies(html_content):
    """
    从HTML内容中提取物品的联动信息
    
    参数:
    - html_content: 页面HTML内容
    - item_key: 物品key
    
    返回:
    - 联动信息列表，每项包含 name(联动名称) 和 description(联动描述)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    synergies = []
    
    # 查找所有联动容器
    synergy_containers = soup.find_all('div', class_='synergy-container')
    print(f"找到 {len(synergy_containers)} 个联动容器")
    
    # 首先查找传统格式的联动容器
    for i, container in enumerate(synergy_containers, 1):
        try:
            # 查找联动名称
            title_div = container.find('div', class_='foldable-list-container')
            synergy_name = None
            
            if title_div:
                # 尝试从span.cn中获取名称
                cn_span = title_div.find('span', class_='cn')
                if cn_span:
                    # 获取联动名称
                    synergy_name = cn_span.get_text(strip=True)
                    
                    # 如果span有data-title属性，也记录英文名称
                    en_span = cn_span.nextSibling.nextSibling.nextSibling
                    eng_name = en_span.get('data-title', '').strip()
                    eng_name = eng_name if eng_name != '{$en-title}' else ''
                    if eng_name and eng_name != synergy_name:
                        print(f"联动 {i}: {synergy_name} (英文: {eng_name})")
                    else:
                        print(f"联动 {i}: {synergy_name}")
                else:
                    # 尝试直接从标题div获取文本
                    synergy_name = title_div.get_text(strip=True).split('\n')[0]
                    print(f"联动 {i}: {synergy_name} (从标题div直接获取)")
            
            # 如果找到了联动名称，提取描述
            if synergy_name:
                # 查找联动描述
                tips_div = container.find('div', class_='tips')
                if not tips_div:
                    print(f"联动 {i} 不存在tips_div")
                    continue
                description = process_synergy_content(tips_div)
                if not description:
                    print(f"联动 {i} 不存在description")
                    continue
                synergies.append({
                    "name": synergy_name,
                    "eng_name": eng_name if eng_name else "",
                    "description": description
                })
        except Exception as e:
            print(f"处理联动 {i} 时出错: {e}")
    return synergies

def process_synergy_content(element):
    """
    处理联动内容，替换图片为占位符
    
    参数:
    - element: BeautifulSoup元素
    
    返回:
    - 处理后的文本
    """
    if not element:
        return ""
    
    # 创建元素的副本以避免修改原始元素
    element_copy = BeautifulSoup(str(element), 'html.parser')
    
    # 处理图片，将其替换为{item:key}格式
    for img in element_copy.find_all('img'):
        # 获取alt属性，通常包含物品名称
        img_alt = img.get('alt', '')
        
        if img_alt:
            # 提取alt中的物品名称，通常是文件名（如 AKEY-47.png）
            item_name = img_alt.replace('.png', '').strip()
            
            # 标准化物品名称为key格式
            normalized_key = item_name.lower().replace(' ', '_').replace('-', '')
            
            # 替换图片为占位符
            placeholder = f"{{item:{normalized_key}}}"
            
            # 如果图片在链接内，替换整个链接
            parent = img.parent
            if parent and parent.name == 'a':
                parent.replace_with(placeholder)
            else:
                img.replace_with(placeholder)
    
    # 处理<br>标签，替换为换行符
    for br in element_copy.find_all('br'):
        br.replace_with('\n')
    
    # 处理<hr>标签，移除
    for hr in element_copy.find_all('hr'):
        hr.decompose()
    
    # 获取处理后的文本，清理空行和多余空格
    text = element_copy.get_text()
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)
    
    return text
