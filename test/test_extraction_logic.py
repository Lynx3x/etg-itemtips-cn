import sys
import os
import time

# 将项目根目录添加到Python路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 使用标准的包导入方式
from etg_parser import extract_item_description, extract_item_synergies, get_page_content_selenium
import json

from generate_all_itemtips import normalize_key_for_url, replace_placeholders, get_page_content, load_key_to_wikikey_mapping

def test_with_local_file(html_file, key, item_name_cn):
    """测试使用本地HTML文件提取物品描述"""
    print(f"\n测试 {key}...")
    
    try:
        # 读取HTML文件
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        key_to_wikikey = load_key_to_wikikey_mapping()
        wiki_key = normalize_key_for_url(key, key_to_wikikey)
        
        # 把itemtips-sample当成对象加载进来
        with open('itemtips-sample.tip', 'r', encoding='utf-8') as f:
            sample_data = json.load(f)

        # 加载敌人映射数据
        enemy_mapping = {}
        try:
            enemy_mapping_path = os.path.join('etg_scrapers', 'enemy_mapping.json')
            with open(enemy_mapping_path, 'r', encoding='utf-8') as f:
                enemy_mapping = json.load(f)
        except Exception as e:
            print(f"加载敌人映射数据失败: {e}")
            enemy_mapping = {}

        # 提取描述
        description = extract_item_description(html_content, wiki_key)
        # 替换物品描述中的占位符
        description = replace_placeholders(description, sample_data, enemy_mapping)
        
        print("\n提取结果:")
        print("-" * 50)
        print(f"物品: {key}")
        print(f"描述: {description}")
        
        # 提取联动
        synergies = extract_item_synergies(html_content)
        
        print("\n联动信息:")
        for i, synergy in enumerate(synergies):
            print(f"{i+1}. {synergy['name']}: {synergy['description']}")
        
        return {
            "name": key,
            "description": description,
            "synergies": synergies
        }
    
    except Exception as e:
        print(f"测试 {key} 时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_with_url(item_key, item_name_cn=None):
    """测试使用URL提取物品描述"""
    url = f"https://etg-xd.wikidot.com/{item_key}"
    print(f"\n测试 {item_key} (URL: {url})...")
    
    try:
        # 获取页面内容
        html_content = get_page_content_selenium(url)
        
        if not html_content:
            print(f"获取 {url} 失败")
            return None
        
        # 保存HTML内容以备后用
        with open(f"{item_key}.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 如果没有提供中文名称，尝试从页面标题获取
        if not item_name_cn:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            title_element = soup.select_one('#page-title')
            
            if title_element:
                item_name_cn = title_element.get_text(strip=True)
                print(f"从页面标题获取中文名称: {item_name_cn}")
            else:
                print(f"无法从页面获取中文名称，使用key作为名称")
                item_name_cn = item_key
        
        # 把itemtips-sample当成对象加载进来
        with open('itemtips-sample.tip', 'r', encoding='utf-8') as f:
            sample_data = json.load(f)

        # 加载敌人映射数据
        enemy_mapping = {}
        try:
            enemy_mapping_path = os.path.join('etg_scrapers', 'enemy_mapping.json')
            with open(enemy_mapping_path, 'r', encoding='utf-8') as f:
                enemy_mapping = json.load(f)
        except Exception as e:
            print(f"加载敌人映射数据失败: {e}")
            enemy_mapping = {}

        # 提取描述
        description = extract_item_description(html_content, item_key)
        # 替换物品描述中的占位符
        description = replace_placeholders(description, sample_data, enemy_mapping)
        
        print("\n提取结果:")
        print("-" * 50)
        print(f"物品: {item_name_cn}")
        print(f"描述: {description}")
        
        # 提取联动
        synergies = extract_item_synergies(html_content)
        
        print("\n联动信息:")
        for i, synergy in enumerate(synergies):
            print(f"{i+1}. {synergy['name']}: {synergy['description']}")
        
        return {
            "name": item_name_cn,
            "description": description,
            "synergies": synergies
        }
    
    except Exception as e:
        print(f"测试 {item_key} 时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

key = 'clone'
# key = 'gunner'
# key = 'grasschopper'
# key = 'magic_lamp'
# key = 'winchester'
# key = 'smileys_revolver'
# key = 'rube_adyne_mk2'
# key = 'seven_leaf_clover'
# key = 'mustache'

def main():
    # 测试直接使用Selenium
    # test_direct_selenium()
    
    # 测试从缓存读取
    # test_cache_reading()
    
    # 原有的测试代码
    print("\n\n原有测试代码：")
    #把itemtips-sample当成对象加载进来
    with open('itemtips-sample.tip', 'r', encoding='utf-8') as f:
        sample_data = json.load(f)

    item_name_cn = sample_data['items'][key]['name']
    key_to_wikikey = load_key_to_wikikey_mapping()
    wiki_key = normalize_key_for_url(key, key_to_wikikey)
    html = 'cache/' + wiki_key + '.html'
    result = test_with_local_file(html,key,item_name_cn)

    # 将占位符替换
    for synergy in result['synergies']:
        print(replace_placeholders(synergy['description'],sample_data))

    # 保存测试结果
    with open('extraction_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("\n测试完成，结果已保存到 extraction_test_results.json")

if __name__ == "__main__":
    main() 