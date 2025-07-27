#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import os

def contains_chinese(text):
    """检查文本是否包含中文字符"""
    if not isinstance(text, str):
        return False
    
    # 使用正则表达式匹配中文字符
    pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]')
    return bool(pattern.search(text))

def main():
    # 读取itemtips-cn.tip文件
    try:
        with open('itemtips-cn.tip', 'r', encoding='utf-8-sig') as f:  # 使用utf-8-sig处理BOM
            data = json.load(f)
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return

    # 检查items部分
    items = data.get('items', {})
    non_chinese_items = {}
    total_items = len(items)
    
    print(f"正在检查 {total_items} 个物品...")
    
    for item_id, item_data in items.items():
        # 检查notes字段是否存在且不包含中文
        if 'notes' in item_data and not contains_chinese(item_data['notes']):
            non_chinese_items[item_id] = {
                'name': item_data.get('name', '未知'),
                'notes': item_data['notes']
            }
    
    # 输出结果
    print(f"\n找到 {len(non_chinese_items)} 个没有中文notes的物品:")
    
    # 将结果写入文件
    output_file = 'etg_checker/non_chinese_notes.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(non_chinese_items, f, ensure_ascii=False, indent=2)
    
    # 打印部分结果
    for i, (item_id, item_data) in enumerate(non_chinese_items.items()):
        print(f"{i+1}. {item_id}: {item_data['name']} - {item_data['notes'][:50]}...")
        if i >= 9:  # 只打印前10个
            print(f"... 还有 {len(non_chinese_items) - 10} 个物品未显示")
            break
    
    print(f"\n完整结果已保存到 {output_file}")

if __name__ == "__main__":
    main() 