import json
import os
import re
import csv
import codecs

def convert_to_filename(item_id):
    """将item_id转换为可能的文件名格式"""
    # 转换为小写
    filename = item_id.lower()
    # 替换空格为下划线（如果有的话）
    filename = filename.replace(' ', '_')
    return filename

def is_invalid_page(html_content):
    """检查HTML内容是否表明页面不存在"""
    # 检查是否包含"你想访问的页面"和"不存在"这两个关键词
    if "你想访问的页面" in html_content and "不存在" in html_content:
        # 尝试提取<em>标签中的内容
        match = re.search(r'<em>(.*?)</em>', html_content)
        if match:
            return True, match.group(1)
        return True, None
    return False, None

def main():
    # 读取itemtips-sample.tip文件
    with open('itemtips-sample.tip', 'r', encoding='utf-8') as f:
        tip_data = json.load(f)
    
    # 获取cache目录下的所有html文件
    cache_dir = 'cache'
    cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.html')]
    
    print(f"Cache目录中共有 {len(cache_files)} 个HTML文件")
    print(f"itemtips-sample.tip中共有 {len(tip_data['items'])} 个物品")
    print("=" * 50)
    
    # 检查每个HTML文件是否有效
    invalid_pages = []
    for html_file in cache_files:
        file_path = os.path.join(cache_dir, html_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                is_invalid, key = is_invalid_page(content)
                if is_invalid:
                    item_id = html_file.replace('.html', '')
                    item_name = tip_data['items'].get(item_id, {}).get('name', '未知')
                    invalid_pages.append((html_file, item_id, item_name, key))
        except Exception as e:
            print(f"读取文件 {html_file} 时出错: {e}")
    
    # 打印无效页面
    if invalid_pages:
        print(f"发现 {len(invalid_pages)} 个无效页面")
        
        # 保存到CSV文件，使用带BOM的UTF-8编码
        with open('invalid_pages.csv', 'w', encoding='utf-8-sig', newline='') as csvfile:
            fieldnames = ['文件名', '项目ID', '项目名称', '错误关键词', '正确htmlKey']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for html_file, item_id, item_name, key in invalid_pages:
                writer.writerow({
                    '文件名': html_file,
                    '项目ID': item_id,
                    '项目名称': item_name,
                    '错误关键词': key if key else "未提取到关键词",
                    '正确htmlKey': ''  # 留空，供手动填写
                })
        
        print(f"无效页面列表已保存到 invalid_pages.csv")
        print("注意：CSV文件已使用UTF-8-sig编码，Excel应该可以正确打开")
    else:
        print("未发现无效页面！")

if __name__ == "__main__":
    main() 