import json
import os
import csv

def main():
    # 读取无效页面列表
    invalid_items = []
    with open('invalid_pages.csv', 'r', encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            item_id = row['项目ID']
            invalid_items.append(item_id)
    
    # 读取itemtips-sample.tip文件
    with open('itemtips-sample.tip', 'r', encoding='utf-8') as f:
        tip_data = json.load(f)
    
    # 提取无效页面对应的项目信息
    invalid_items_data = {"items": {}}
    for item_id in invalid_items:
        if item_id in tip_data["items"]:
            invalid_items_data["items"][item_id] = tip_data["items"][item_id]
    
    # 保存到JSON文件
    with open('invalid_items.json', 'w', encoding='utf-8') as f:
        json.dump(invalid_items_data, f, ensure_ascii=False, indent=2)
    
    print(f"已将 {len(invalid_items_data['items'])} 个无效页面的项目信息保存到 invalid_items.json")

if __name__ == "__main__":
    main() 