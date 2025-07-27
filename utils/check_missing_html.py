import json
import os

def convert_to_filename(item_id):
    """将item_id转换为可能的文件名格式"""
    # 转换为小写
    filename = item_id.lower()
    # 替换空格为下划线（如果有的话）
    filename = filename.replace(' ', '_')
    return filename

def main():
    # 读取itemtips-sample.tip文件
    with open('itemtips-sample.tip', 'r', encoding='utf-8') as f:
        tip_data = json.load(f)
    
    # 获取cache目录下的所有html文件
    cache_files = os.listdir('cache')
    cache_files = [f.replace('.html', '') for f in cache_files if f.endswith('.html')]
    
    print(f"Cache目录中共有 {len(cache_files)} 个HTML文件")
    print(f"itemtips-sample.tip中共有 {len(tip_data['items'])} 个物品")
    print("=" * 50)
    
    # 遍历items，检查是否有对应的html文件
    missing_items = []
    for item_id in tip_data['items'].keys():
        # 将item_id转换为文件名格式
        file_name = convert_to_filename(item_id)
        
        if file_name not in cache_files:
            item_name = tip_data['items'][item_id]['name']
            missing_items.append((item_id, item_name, file_name))
    
    # 打印缺失的项目
    if missing_items:
        print(f"在cache目录中缺少以下 {len(missing_items)} 个项目的HTML文件：")
        print("-" * 50)
        for item_id, item_name, file_name in missing_items:
            print(f"项目ID: {item_id} | 名称: {item_name} | 查找的文件名: {file_name}.html")
    else:
        print("所有项目都有对应的HTML文件！")

if __name__ == "__main__":
    main() 