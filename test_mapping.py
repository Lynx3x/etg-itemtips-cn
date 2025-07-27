import generate_all_itemtips

def main():
    # 加载key到wikiKey的映射
    key_to_wikikey = generate_all_itemtips.load_key_to_wikikey_mapping()
    
    # 打印映射数量
    print(f'映射数量: {len(key_to_wikikey)}')
    
    # 打印前5个映射示例
    print('映射示例:')
    count = 0
    for key, wikikey in key_to_wikikey.items():
        print(f'{key} -> {wikikey}')
        count += 1
        if count >= 5:
            break
    
    # 测试normalize_key_for_url函数
    print('\n测试normalize_key_for_url函数:')
    test_keys = ['ak47', 'master_round_1', 'blank_companions_ring']
    for key in test_keys:
        normalized = generate_all_itemtips.normalize_key_for_url(key, key_to_wikikey)
        print(f'{key} -> {normalized}')

if __name__ == '__main__':
    main() 