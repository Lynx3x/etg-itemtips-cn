# ETG 爬虫工具

这个目录包含了用于从 Enter the Gungeon 中文维基 (https://etg-xd.wikidot.com/) 爬取游戏数据的脚本。

## 敌人与 Boss 映射爬虫

### 功能

- `enemy_scraper_iframe.py`: 直接获取 iframe 内容，提取敌人和 Boss 的 key 对应中文名的映射（推荐使用）

### 使用方法

使用`enemy_scraper_iframe.py`脚本获取敌人和 Boss 映射：

```bash
# 获取所有映射（敌人和Boss）
python enemy_scraper_iframe.py

# 只获取敌人映射
python enemy_scraper_iframe.py --type enemy

# 只获取Boss映射
python enemy_scraper_iframe.py --type boss
```

执行后，脚本会：

1. 获取相应页面 iframe 的内容
2. 提取 key 对应中文名的映射
3. 将所有映射（包括敌人和 Boss）保存到`enemy_mapping.json`文件中

### 命令行参数

- `--type`, `-t`: 指定要获取的映射类型
  - `enemy`: 只获取敌人映射
  - `boss`: 只获取 Boss 映射
  - `all`: 获取所有映射（默认值）

### 依赖项

- Python 3.6+
- requests
- beautifulsoup4
- selenium
- webdriver-manager

可以通过以下命令安装依赖：

```bash
pip install requests beautifulsoup4 selenium webdriver-manager
```

### 输出格式

生成的`enemy_mapping.json`文件是字典格式，其中：

- 键(key)是英文名，转换为小写并用下划线替换空格
- 值(value)是中文名

映射示例 (`enemy_mapping.json`):

```json
{
  "bullet_kin": "子弹怪",
  "bandana_bullet_kin": "头巾子弹怪",
  "veteran_bullet_kin": "资深子弹怪",
  "gatling_gull": "加特林鸥",
  "bullet_king": "子弹之王",
  "trigger_twins": "扳机双子"
}
```

## 注意事项

- 脚本需要网络连接才能获取数据
- 使用 Selenium 的脚本会自动下载并使用 ChromeDriver
- 如果遇到问题，可以查看生成的 HTML 文件（如`enemy_source.html`或`boss_source.html`）来分析页面结构
