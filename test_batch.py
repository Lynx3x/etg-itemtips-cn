#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import codecs
import os
import logging
from etg_parser.extract_item_tips import extract_item_description, extract_item_synergies, get_page_content_selenium
from generate_all_itemtips import load_itemtips_sample, find_synergy_key, replace_placeholders, normalize_key_for_url

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_batch.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 设置常量
SAMPLE_FILE = 'itemtips-sample.tip'
OUTPUT_FILE = 'itemtips-cn-test-batch.tip'
CACHE_DIR = 'cache'

# 确保缓存目录存在
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_page_content(key):
    """
    获取物品的wiki页面内容，优先使用缓存
    
    参数:
    - key: 物品key
    
    返回:
    - 页面HTML内容
    """
    cache_file = os.path.join(CACHE_DIR, f"{key}.html")
    
    # 如果缓存存在，直接返回缓存内容
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    # 构建URL
    url_key = normalize_key_for_url(key)
    url = f"https://etg-xd.wikidot.com/{url_key}"
    
    try:
        logging.info(f"获取页面内容: {url}")
        html_content = get_page_content_selenium(url)
        
        # 保存到缓存
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return html_content
    except Exception as e:
        logging.error(f"获取页面 {url} 失败: {e}")
        return None

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
        synergy_name.replace(' ', '_').replace('-', '_'),
        synergy_name.lower(),
        synergy_name.lower().replace(' ', '_').replace('-', '_')
    ]
    
    for variant in name_variants:
        if variant in synergy_name_to_key:
            return synergy_name_to_key[variant]
    
    # 4. 尝试通过模糊匹配查找中文名称
    # 计算所有中文名称的相似度，找到最匹配的
    best_match = None
    best_match_score = 0
    
    for cn_name, key in synergy_cn_to_key.items():
        # 计算字符重叠率
        common_chars = set(synergy_name) & set(cn_name)
        overlap_score = len(common_chars) / max(len(synergy_name), len(cn_name))
        
        # 计算子串匹配得分
        substring_score = 0
        for i in range(min(len(synergy_name), len(cn_name)), 0, -1):
            if i >= 2:  # 至少匹配2个字符
                if synergy_name[-i:] == cn_name[:i] or synergy_name[:i] == cn_name[-i:]:
                    substring_score = i / max(len(synergy_name), len(cn_name))
                    break
        
        # 综合得分
        similarity_score = max(overlap_score, substring_score)
        
        if similarity_score > 0.5 and similarity_score > best_match_score:  # 设置一个阈值
            best_match = key
            best_match_score = similarity_score
    
    if best_match:
        print(f"通过模糊匹配找到联动键: '{synergy_name}' => '{best_match}'，相似度: {best_match_score:.2f}")
        return best_match
    
    # 5. 尝试反向查找：通过生成所有可能的标准形式，查找匹配的键
    formatted_name = synergy_name.upper().replace(' ', '_').replace('-', '_')
    standard_key = f"#{formatted_name}"
    
    # 记录找不到的键
    with open('unmatched_synergies.txt', 'a', encoding='utf-8') as f:
        f.write(f"{synergy_name} => {standard_key}\n")
    
    print(f"警告：未能找到联动 '{synergy_name}' 对应的标准键，使用生成的键 '{standard_key}'")
    
    # 如果都找不到，使用标准格式：#NAME格式
    return standard_key

def generate_tip_file(items_data, output_file):
    """
    生成tip文件
    
    参数:
    - items_data: 物品数据字典，包含物品和联动信息
    - output_file: 输出文件名
    """
    # 构建tip文件内容
    tip_content = {
        "metadata": {
            "name": "挺进地牢物品提示 - 中文 - 测试批处理",
            "url": "https://etg-xd.wikidot.com",
            "version": "1.0.0"
        },
        "items": {},
        "synergies": {}
    }
    
    # 添加物品数据
    for key, item_data in items_data.items():
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

def main():
    logging.info("开始测试批量处理...")
    
    # 加载sample数据和映射
    sample_data, cn_name_to_key, placeholder_to_cn_name, synergy_name_to_key, synergy_cn_to_key = load_itemtips_sample()
    
    # 物品数据
    items_data = {}
    synergies_data = {}
    
    # 只处理前5个物品
    keys = list(sample_data['items'].keys())[:5]
    logging.info(f"将处理这些物品: {keys}")
    
    # 处理选定的物品
    for key in keys:
        try:
            item_data = sample_data['items'][key]
            item_name_cn = item_data.get('name', key)
            
            print(f"处理物品: {item_name_cn} ({key})")
            
            # 获取页面内容
            html_content = get_page_content(key)
            if not html_content:
                logging.error(f"无法获取物品 {key} 的页面内容，跳过")
                continue
            
            # 提取描述
            description = extract_item_description(html_content, item_name_cn)
            if not description:
                logging.warning(f"物品 {key} 的描述提取失败，使用原始描述")
                description = item_data.get('notes', '')
            
            print(f"提取到描述: {description[:50]}...")
            
            # 添加到物品数据
            items_data[key] = {
                "name": item_name_cn,
                "notes": description
            }
            
            # 提取联动信息
            synergies = extract_item_synergies(html_content, key)
            print(f"找到 {len(synergies)} 个联动")
            
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
                print(f"联动: {synergy_name} => {synergy_key}: {synergy_desc[:50]}...")
                
        except Exception as e:
            logging.error(f"处理物品 {key} 时出错: {e}")
    
    # 将联动数据添加到物品数据中
    items_data["synergies"] = synergies_data
    
    # 生成tip文件
    generate_tip_file(items_data, OUTPUT_FILE)
    
    # 打印处理结果
    print("\n处理结果:")
    print(f"处理物品数: {len(items_data) - 1}")  # 减去synergies键
    print(f"提取联动数: {len(synergies_data)}")

if __name__ == "__main__":
    main() 