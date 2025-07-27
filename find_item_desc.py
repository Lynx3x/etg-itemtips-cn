from bs4 import BeautifulSoup
import re

def extract_item_description():
    """从已保存的HTML文件中提取物品描述"""
    try:
        # 读取已保存的HTML文件
        with open('shelleton_key.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print("=" * 50)
        print("开始提取骷髅钥匙描述")
        print("=" * 50)
        
        # 1. 查找页面中的所有段落
        paragraphs = soup.select('p')
        for i, p in enumerate(paragraphs):
            p_text = p.get_text(strip=True)
            if p_text and len(p_text) > 10:
                print(f"段落 {i+1}: {p_text[:150]}...")
                
                # 检查是否包含关键词
                if "骷髅钥匙" in p_text or "不消耗" in p_text or "打开上锁" in p_text:
                    print("\n可能的物品描述找到:")
                    print("-" * 50)
                    print(f"完整段落: {p_text}")
                    print("-" * 50)
        
        # 2. 查找描述性div
        desc_divs = soup.select('div.description') + soup.select('div[data-title="描述"]')
        for i, div in enumerate(desc_divs):
            div_text = div.get_text(strip=True)
            if div_text:
                print(f"\n描述性div {i+1}: {div_text[:150]}...")
        
        # 3. 查找关键内容区域
        content_div = soup.select_one('#page-content')
        if content_div:
            # 打印页面内容的HTML结构，以便分析
            print("\n页面内容区HTML结构:")
            print("-" * 50)
            
            # 只打印内容区域的第一部分，重点寻找物品描述
            content_html = str(content_div)[:3000]  # 限制长度以便查看
            
            # 分析文本中可能包含物品描述的部分
            matches = re.findall(r'<p>(.*?)</p>', content_html, re.DOTALL)
            
            for i, match in enumerate(matches):
                clean_text = BeautifulSoup(match, 'html.parser').get_text(strip=True)
                if clean_text and len(clean_text) > 20:
                    print(f"\n内容区域段落 {i+1}: {clean_text[:150]}...")
            
            # 查找可能的说明列表
            list_items = content_div.select('li')
            for i, item in enumerate(list_items):
                item_text = item.get_text(strip=True)
                if "骷髅钥匙" in item_text or "不消耗" in item_text:
                    print(f"\n列表项 {i+1}: {item_text}")
        
        # 4. 直接搜索关键词出现的上下文
        all_text = soup.get_text()
        key_terms = ["骷髅钥匙", "打开上锁", "不需要消耗", "不消耗", "诅咒值"]
        
        print("\n关键词上下文:")
        for term in key_terms:
            # 查找关键词及其前后100个字符
            term_matches = re.findall(f'.{{0,100}}{term}.{{0,100}}', all_text)
            
            for match in term_matches:
                print(f"\n包含'{term}'的文本: {match}")
        
        # 5. 打印具有特定类或ID的div元素
        special_divs = soup.select('div.details') + soup.select('div.tips') + soup.select('div.trivia')
        for i, div in enumerate(special_divs):
            div_text = div.get_text(strip=True)
            if div_text:
                print(f"\n特殊div {i+1} ({div.get('class', 'no-class')}): {div_text[:150]}...")
        
        # 6. 检查特定结构的内容
        item_sections = soup.select('.item-section, .passive-section, .active-section, .item-container')
        for i, section in enumerate(item_sections):
            section_text = section.get_text(strip=True)
            if section_text:
                print(f"\n物品区块 {i+1}: {section_text[:150]}...")
                
                # 提取这个区块的HTML结构
                print("区块HTML结构:")
                print(section.prettify()[:500])
        
        # 7. 查找所有骷髅钥匙的引用
        print("\n寻找所有'骷髅钥匙'的引用:")
        for tag in soup.find_all(text=re.compile('骷髅钥匙')):
            parent = tag.parent
            if parent:
                # 打印包含引用的元素及其父元素
                print(f"在标签 <{parent.name}> 中找到: {tag}")
                print(f"父元素HTML: {parent}")
                print("-" * 30)
                
                # 如果父元素是段落或div，可能包含描述
                if parent.name in ['p', 'div', 'span']:
                    text = parent.get_text(strip=True)
                    if len(text) > 20:  # 有足够长度可能是描述
                        print(f"可能的描述: {text}")
                
    except Exception as e:
        print(f"提取过程中出现错误: {e}")

if __name__ == "__main__":
    extract_item_description() 