import json
import codecs
import re
from bs4 import BeautifulSoup
from etg_parser.extract_item_tips import extract_item_description, extract_item_synergies

def load_itemtips_sample():
    """
    加载itemtips-sample.tip文件，创建物品名称到key的映射
    """
    with codecs.open('itemtips-sample.tip', 'r', encoding='utf-8-sig') as f:
        sample_data = json.load(f)
    
    # 创建中文名称到key的映射
    cn_name_to_key = {}
    for key, item_data in sample_data['items'].items():
        if 'name' in item_data:
            cn_name_to_key[item_data['name']] = key
    
    # 创建英文名称到key的映射(用于物品占位符替换)
    en_name_to_key = {}
    placeholder_to_cn_name = {}
    
    for key, item_data in sample_data['items'].items():
        # 获取英文名称(通常就是key的某种形式)
        # 转换key格式：下划线变空格并首字母大写
        en_name = key.replace('_', ' ').title()
        en_name_to_key[en_name] = key
        
        # 获取转换后名称的小写形式，用于比较
        en_name_lower = en_name.lower()
        en_name_to_key[en_name_lower] = key
        
        # 创建占位符到中文名称的映射
        if 'name' in item_data:
            placeholder_to_cn_name[f"{{{{item:{key}}}}}"] = item_data['name']
    
    # 创建联动名称到key的映射
    synergy_name_to_key = {}
    synergy_cn_to_key = {}
    
    for key, synergy_data in sample_data['synergies'].items():
        if 'name' in synergy_data:
            # 中文名称映射
            synergy_cn_to_key[synergy_data['name']] = key
            # 英文名称映射(去掉#号)
            eng_name = key[1:] if key.startswith('#') else key
            synergy_name_to_key[eng_name] = key
            # 转换为首字母大写的形式
            formatted_name = ' '.join(word.capitalize() for word in eng_name.split('_'))
            synergy_name_to_key[formatted_name] = key
    
    # 输出一些调试信息
    print(f"加载了 {len(cn_name_to_key)} 个物品名称映射")
    print(f"加载了 {len(synergy_name_to_key)} 个联动名称映射")
    
    return sample_data, cn_name_to_key, en_name_to_key, placeholder_to_cn_name, synergy_name_to_key, synergy_cn_to_key

def generate_tip_file(items_data, output_file='itemtips-cn-test.tip'):
    """
    生成tip文件
    
    参数:
    - items_data: 物品数据字典，包含物品和联动信息
    - output_file: 输出文件名
    """
    # 构建tip文件内容
    tip_content = {
        "metadata": {
            "name": "挺进地牢物品提示 - 中文",
            "url": "https://etg-xd.wikidot.com",
            "version": "1.0.0"
        },
        "items": {},
        "synergies": {}
    }
    
    # 添加物品数据
    for key, item_data in items_data.items():
        # 跳过联动信息
        if key == "synergies":
            continue
            
        tip_content["items"][key] = {
            "name": item_data["name"],
            "notes": item_data["notes"]
        }
    
    # 添加联动数据
    for synergy_name, synergy_data in items_data.get("synergies", {}).items():
        tip_content["synergies"][synergy_name] = {
            "notes": synergy_data["notes"]
        }
    
    # 保存为tip文件
    with codecs.open(output_file, 'w', encoding='utf-8-sig') as f:
        json.dump(tip_content, f, indent=2, ensure_ascii=False)
    
    print(f"已生成tip文件: {output_file}")

def replace_placeholders(text, placeholder_to_cn_name):
    """
    替换文本中的占位符为中文名称
    
    参数:
    - text: 包含占位符的文本
    - placeholder_to_cn_name: 占位符到中文名称的映射
    
    返回:
    - 替换后的文本
    """
    # 首先查找所有{{item:xxx}}格式的占位符
    placeholder_pattern = r'\{\{item:(.*?)\}\}'
    matches = re.findall(placeholder_pattern, text)
    
    # 对每个占位符执行替换
    for match in matches:
        # 原始占位符文本
        orig_placeholder = f"{{{{item:{match}}}}}"
        
        # 尝试多种键格式：1. 原始 2. 下划线替换连字符 3. 移除所有分隔符
        key_variants = [
            match,  # 原始格式
            match.replace('-', '_'),  # 连字符替换为下划线
            match.replace('_', '-'),  # 下划线替换为连字符
            match.replace('-', '').replace('_', '')  # 移除所有分隔符
        ]
        
        # 查找匹配的占位符
        replaced = False
        for variant in key_variants:
            new_placeholder = f"{{{{item:{variant}}}}}"
            if new_placeholder in placeholder_to_cn_name:
                text = text.replace(orig_placeholder, placeholder_to_cn_name[new_placeholder])
                replaced = True
                break
                
        # 如果所有变体都没有找到对应的中文名称
        if not replaced:
            print(f"警告：无法找到占位符 {orig_placeholder} 的对应中文名称，保留原样")
            # 在未处理的占位符文件中记录
            with open('unresolved_placeholders.txt', 'a', encoding='utf-8') as f:
                f.write(f"{orig_placeholder}\n")
    
    return text

def find_synergy_key(synergy_name, synergy_name_to_key, synergy_cn_to_key):
    """
    查找联动对应的键
    
    参数:
    - synergy_name: 联动名称
    - synergy_name_to_key: 联动名称到键的映射
    - synergy_cn_to_key: 中文联动名称到键的映射
    
    返回:
    - 找到的键，如果找不到则返回格式化后的键
    """
    # 1. 先尝试直接中文名称匹配
    if synergy_name in synergy_cn_to_key:
        return synergy_cn_to_key[synergy_name]
    
    # 2. 尝试英文直接匹配
    if synergy_name in synergy_name_to_key:
        return synergy_name_to_key[synergy_name]
    
    # 3. 尝试各种变形格式
    name_variants = [
        synergy_name,
        synergy_name.upper(),
        synergy_name.upper().replace(' ', '_').replace('-', '_'),
        synergy_name.replace(' ', '_').replace('-', '_')
    ]
    
    for variant in name_variants:
        if variant in synergy_name_to_key:
            return synergy_name_to_key[variant]
    
    # 4. 尝试反向查找：通过生成所有可能的标准形式，查找匹配的键
    formatted_name = synergy_name.upper().replace(' ', '_').replace('-', '_')
    standard_key = f"#{formatted_name}"
    
    # 记录找不到的键
    with open('unmatched_synergies.txt', 'a', encoding='utf-8') as f:
        f.write(f"{synergy_name} => {standard_key}\n")
        
    print(f"警告：未能找到联动 '{synergy_name}' 对应的标准键，使用生成的键 '{standard_key}'")
    
    # 如果都找不到，使用标准格式：#NAME格式
    return standard_key

def main():
    # 加载sample数据和映射
    sample_data, cn_name_to_key, en_name_to_key, placeholder_to_cn_name, synergy_name_to_key, synergy_cn_to_key = load_itemtips_sample()
    
    # 测试物品数据
    items_data = {}
    synergies_data = {}
    
    # 记录未解析的占位符
    with open('unresolved_placeholders.txt', 'w', encoding='utf-8') as f:
        f.write("# 未解析的占位符\n")
        
    # 记录未匹配的联动键
    with open('unmatched_synergies.txt', 'w', encoding='utf-8') as f:
        f.write("# 未匹配的联动键\n")
    
    # 处理骷髅钥匙
    try:
        print("处理骷髅钥匙...")
        with open('shelleton_key.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 提取描述
        item_name_cn = "骷髅钥匙"
        description = extract_item_description(html_content, item_name_cn)
        
        # 查找key
        item_key = None
        for cn_name, key in cn_name_to_key.items():
            if "骷髅钥匙" in cn_name or cn_name in "骷髅钥匙":
                item_key = key
                break
        
        if not item_key:
            # 手动指定key
            item_key = "shelleton_key"
        
        # 添加到物品数据
        items_data[item_key] = {
            "name": item_name_cn,
            "notes": description
        }
        
        # 提取联动信息
        synergies = extract_item_synergies(html_content, item_key)
        for synergy in synergies:
            synergy_name = synergy['name']
            
            # 查找联动键
            synergy_key = find_synergy_key(synergy_name, synergy_name_to_key, synergy_cn_to_key)
            
            # 替换联动描述中的占位符
            synergy_desc = synergy['description']
            synergy_desc = replace_placeholders(synergy_desc, placeholder_to_cn_name)
            
            synergies_data[synergy_key] = {
                "notes": synergy_desc
            }
    except Exception as e:
        print(f"处理骷髅钥匙时出错: {e}")
    
    # 处理GuNNER
    try:
        print("处理GuNNER...")
        with open('gunner.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 提取描述
        item_name_cn = "GuNNER"
        description = extract_item_description(html_content, item_name_cn)
        
        # 查找key
        item_key = None
        for cn_name, key in cn_name_to_key.items():
            if "GuNNER" in cn_name or cn_name in "GuNNER":
                item_key = key
                break
        
        if not item_key:
            # 手动指定key
            item_key = "gunner"
        
        # 添加到物品数据
        items_data[item_key] = {
            "name": item_name_cn,
            "notes": description
        }
        
        # 提取联动信息
        synergies = extract_item_synergies(html_content, item_key)
        for synergy in synergies:
            synergy_name = synergy['name']
            
            # 查找联动键
            synergy_key = find_synergy_key(synergy_name, synergy_name_to_key, synergy_cn_to_key)
            
            # 替换联动描述中的占位符
            synergy_desc = synergy['description']
            synergy_desc = replace_placeholders(synergy_desc, placeholder_to_cn_name)
            
            synergies_data[synergy_key] = {
                "notes": synergy_desc
            }
    except Exception as e:
        print(f"处理GuNNER时出错: {e}")
    
    # 将联动数据添加到物品数据中
    items_data["synergies"] = synergies_data
    
    # 生成tip文件
    generate_tip_file(items_data)
    
    # 打印提取结果
    print("\n提取结果:")
    print("-" * 50)
    for key, item in items_data.items():
        if key != "synergies":
            print(f"物品: {item['name']} (key: {key})")
            print(f"描述: {item['notes']}")
            print()
    
    print("联动信息:")
    for name, synergy in synergies_data.items():
        print(f"{name}: {synergy['notes']}")

if __name__ == "__main__":
    main() 