#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# 添加父目录到系统路径，以便导入etg_parser模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_driver():
    """
    设置并返回Selenium WebDriver
    
    返回:
    - WebDriver实例
    """
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # 设置WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver

def get_iframe_content(url):
    """
    直接访问iframe的URL获取内容
    
    参数:
    - url: iframe的URL
    
    返回:
    - iframe的HTML内容
    """
    try:
        # 设置WebDriver
        driver = setup_driver()
        
        # 获取iframe内容
        print(f"正在获取iframe内容: {url}")
        driver.get(url)
        
        # 等待页面加载完成
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 给页面一些额外的时间来加载JavaScript内容
        time.sleep(3)
        
        # 获取页面源代码
        iframe_content = driver.page_source
        
        # 保存iframe源码供进一步分析
        filename = url.split('/')[-1] + '_source.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(iframe_content)
        print(f"iframe源码已保存到 {filename}，长度: {len(iframe_content)}")
        
        # 关闭WebDriver
        driver.quit()
        
        return iframe_content
        
    except Exception as e:
        print(f"获取iframe内容时出错: {e}")
        if 'driver' in locals():
            driver.quit()
        return None

def extract_mapping(html_content, type_name="敌人"):
    """
    从HTML内容中提取映射
    
    参数:
    - html_content: HTML内容
    - type_name: 映射类型名称（敌人或Boss）
    
    返回:
    - key到名称的映射字典
    """
    if not html_content:
        return {}
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 创建映射字典
    mapping = {}
    
    # 查找所有项目块
    item_blocks = soup.find_all('div', class_='item-block')
    print(f"找到 {len(item_blocks)} 个{type_name}项目块")
    
    if not item_blocks:
        print(f"未找到{type_name}项目块")
        return {}
    
    # 遍历所有项目块
    for block in item_blocks:
        # 获取图片元素
        img = block.find('img')
        if not img:
            continue
        
        # 获取链接元素
        link = block.find('a')
        if not link:
            continue
        
        # 获取图片的alt属性作为英文名
        name = img.get('alt', '')
        if not name:
            continue
        
        # 提取key
        key = name.lower().replace(' ', '_').replace("'", '').replace('-', '_')
        
        # 获取链接的文本作为中文名
        cn_name = link.get_text(strip=True)
        
        # 将key和名称添加到映射字典
        if cn_name:
            mapping[key] = cn_name
            print(f"找到{type_name}: {key} -> {cn_name}")
    
    return mapping

def main():
    """主函数"""
    import argparse
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='获取敌人和Boss映射')
    parser.add_argument('--type', '-t', type=str, choices=['enemy', 'boss', 'all'], default='all',
                        help='要获取的映射类型: enemy(敌人), boss(Boss), all(全部) (默认: all)')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 创建总映射字典
    mapping = {}
    
    # 根据类型获取映射
    if args.type in ['enemy', 'all']:
        print("开始获取敌人映射...")
        enemy_iframe_url = "https://etgwikisearch.xd.cn/enemy"
        enemy_content = get_iframe_content(enemy_iframe_url)
        
        if enemy_content:
            # 提取敌人映射
            enemy_mapping = extract_mapping(enemy_content, "敌人")
            
            # 添加到总映射
            mapping.update(enemy_mapping)
            print(f"\n提取了 {len(enemy_mapping)} 个敌人映射")
        else:
            print("未能获取敌人iframe内容")
    
    if args.type in ['boss', 'all']:
        print("\n开始获取Boss映射...")
        boss_iframe_url = "https://etgwikisearch.xd.cn/boss"
        boss_content = get_iframe_content(boss_iframe_url)
        
        if boss_content:
            # 提取Boss映射
            boss_mapping = extract_mapping(boss_content, "Boss")
            
            # 添加到总映射
            mapping.update(boss_mapping)
            print(f"\n提取了 {len(boss_mapping)} 个Boss映射")
        else:
            print("未能获取Boss iframe内容")
    
    # 保存总映射
    if mapping:
        with open('enemy_mapping.json', 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=4)
        print(f"\n总共提取了 {len(mapping)} 个映射，已保存到 enemy_mapping.json")
    else:
        print("\n未能提取任何映射")

if __name__ == "__main__":
    main() 