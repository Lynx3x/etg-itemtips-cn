#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import os
from datetime import datetime

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
        with open('itemtips-cn.tip', 'r', encoding='utf-8-sig') as f:
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
                'english_notes': item_data['notes'],
                'chinese_notes': ''  # 用于填写中文翻译
            }
    
    # 创建翻译模板
    translation_template = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_items": len(non_chinese_items),
        "items": non_chinese_items
    }
    
    # 输出结果
    print(f"\n找到 {len(non_chinese_items)} 个没有中文notes的物品")
    
    # 将结果写入文件
    output_file = 'translation_template.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translation_template, f, ensure_ascii=False, indent=2)
    
    print(f"\n翻译模板已保存到 {output_file}")
    print("请在该文件中填写每个物品的chinese_notes字段，完成翻译后运行apply_translations.py应用翻译")
    
    # 创建应用翻译的脚本
    create_apply_script()
    
def create_apply_script():
    """创建应用翻译的脚本"""
    script_content = """#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import shutil
from datetime import datetime

def main():
    # 检查翻译模板文件是否存在
    if not os.path.exists('translation_template.json'):
        print("错误: 找不到translation_template.json文件")
        return
    
    # 检查原始文件是否存在
    if not os.path.exists('itemtips-cn.tip'):
        print("错误: 找不到itemtips-cn.tip文件")
        return
    
    # 读取翻译模板
    try:
        with open('translation_template.json', 'r', encoding='utf-8') as f:
            translation_data = json.load(f)
    except Exception as e:
        print(f"读取翻译模板时出错: {e}")
        return
    
    # 读取原始文件
    try:
        with open('itemtips-cn.tip', 'r', encoding='utf-8-sig') as f:
            original_data = json.load(f)
    except Exception as e:
        print(f"读取原始文件时出错: {e}")
        return
    
    # 创建备份
    backup_file = f'itemtips-cn.tip.bak.{datetime.now().strftime("%Y%m%d%H%M%S")}'
    try:
        shutil.copy2('itemtips-cn.tip', backup_file)
        print(f"已创建备份文件: {backup_file}")
    except Exception as e:
        print(f"创建备份时出错: {e}")
        return
    
    # 应用翻译
    translated_count = 0
    empty_count = 0
    
    for item_id, item_data in translation_data.get('items', {}).items():
        if item_id in original_data.get('items', {}) and 'chinese_notes' in item_data:
            if item_data['chinese_notes'].strip():
                original_data['items'][item_id]['notes'] = item_data['chinese_notes']
                translated_count += 1
            else:
                empty_count += 1
    
    # 保存更新后的文件
    try:
        with open('itemtips-cn.tip', 'w', encoding='utf-8') as f:
            json.dump(original_data, f, ensure_ascii=False, indent=2)
        print(f"已成功应用 {translated_count} 个翻译")
        if empty_count > 0:
            print(f"警告: {empty_count} 个条目未填写翻译")
    except Exception as e:
        print(f"保存文件时出错: {e}")
        print(f"原始文件已备份为 {backup_file}")
        return
    
    print("翻译应用完成!")

if __name__ == "__main__":
    main()
"""
    
    # 写入应用翻译的脚本
    with open('apply_translations.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("已创建应用翻译的脚本: apply_translations.py")

if __name__ == "__main__":
    main() 