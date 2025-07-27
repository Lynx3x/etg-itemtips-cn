import generate_all_itemtips
import logging
import os

# 设置日志
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

def test_cache_reading():
    """测试从缓存读取页面内容"""
    # 加载key到wikiKey的映射
    key_to_wikikey = generate_all_itemtips.load_key_to_wikikey_mapping()
    
    # 检查cache目录是否存在
    cache_dir = generate_all_itemtips.CACHE_DIR
    if not os.path.exists(cache_dir):
        print(f"缓存目录 {cache_dir} 不存在!")
        return
    
    # 获取cache目录下的所有html文件
    cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.html')]
    print(f"缓存目录中共有 {len(cache_files)} 个HTML文件")
    
    # 测试几个已知有缓存的key
    test_keys = ['ak47', 'magic_lamp', 'master_round_1']
    
    for key in test_keys:
        print(f"\n测试key: {key}")
        
        # 标准化key
        wiki_key = generate_all_itemtips.normalize_key_for_url(key, key_to_wikikey)
        print(f"标准化后的wiki_key: {wiki_key}")
        
        # 检查原始文件名的缓存是否存在
        original_cache_file = os.path.join(cache_dir, f"{key}.html")
        if os.path.exists(original_cache_file):
            print(f"原始缓存文件存在: {original_cache_file}")
            
            # 获取缓存文件大小
            file_size = os.path.getsize(original_cache_file)
            print(f"原始缓存文件大小: {file_size} 字节")
        else:
            print(f"原始缓存文件不存在: {original_cache_file}")
            
        # 检查标准化后的文件名缓存是否存在
        normalized_cache_file = os.path.join(cache_dir, f"{wiki_key}.html")
        if os.path.exists(normalized_cache_file):
            print(f"标准化缓存文件存在: {normalized_cache_file}")
            
            # 获取缓存文件大小
            file_size = os.path.getsize(normalized_cache_file)
            print(f"标准化缓存文件大小: {file_size} 字节")
        else:
            print(f"标准化缓存文件不存在: {normalized_cache_file}")
        
        # 尝试读取内容
        content = generate_all_itemtips.get_page_content(key, key_to_wikikey)
        if content:
            print(f"成功读取缓存内容，长度: {len(content)} 字符")
        else:
            print("读取缓存内容失败!")

if __name__ == "__main__":
    test_cache_reading() 