from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os

# 全局变量，存储ChromeDriver路径
CHROME_DRIVER_PATH = None

def get_page_content_selenium(url_or_key):
    """
    使用Selenium获取页面内容
    
    参数:
    - url_or_key: 完整的URL或者只是wiki_key
    
    返回:
    - 页面HTML内容
    """
    # 确保url是完整的URL
    if not url_or_key.startswith('http'):
        url = f"https://etg-xd.wikidot.com/{url_or_key}"
    else:
        url = url_or_key
        
    print(f"使用Selenium从 {url} 获取内容...")
    
    # 配置Chrome选项
    options = Options()
    options.add_argument('--headless')  # 无头模式
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # 初始化WebDriver，避免每次都下载
    global CHROME_DRIVER_PATH
    driver = None
    
    try:
        if CHROME_DRIVER_PATH and os.path.exists(CHROME_DRIVER_PATH):
            # 使用已存在的ChromeDriver
            print(f"使用已存在的ChromeDriver: {CHROME_DRIVER_PATH}")
            service = Service(CHROME_DRIVER_PATH)
        else:
            # 第一次运行时下载ChromeDriver
            print("首次运行，下载ChromeDriver...")
            CHROME_DRIVER_PATH = ChromeDriverManager().install()
            service = Service(CHROME_DRIVER_PATH)
        
        driver = webdriver.Chrome(service=service, options=options)
        
        # 访问URL
        driver.get(url)
        
        # 等待页面加载完成（等待页面主体出现）
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "page-content"))
        )
        
        # 额外等待，确保JavaScript渲染完成
        time.sleep(0.5)
        
        # 获取页面源代码
        html_content = driver.page_source
        
        print(f"成功获取页面内容，长度: {len(html_content)}")
        return html_content
    
    except Exception as e:
        print(f"获取页面时出错: {e}")
        return None
    
    finally:
        # 关闭浏览器
        if driver:
            driver.quit()
