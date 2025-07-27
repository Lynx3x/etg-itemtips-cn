# ETG Item Tips 中文迁移项目

本项目旨在批量提取、整理并迁移《Enter the Gungeon》（挺进地牢）物品提示（Item Tips）及相关内容至中文环境，便于汉化、查阅和二次开发。

## 主要功能

- 批量解析和提取物品、敌人、Boss 等的描述信息
- 支持多种格式的原始数据（HTML、JSON 等）
- 自动生成翻译模板和校验缺失项
- 提供测试脚本，辅助校验提取和翻译完整性

## 目录结构

- `cache/`：原始 HTML 缓存，包含各类物品、敌人、Boss 页面
- `etg_parser/`：核心解析与提取脚本
- `etg_checker/`：校验与辅助工具
- `etg_scrapers/`：爬虫与数据采集脚本
- `output/`：最终生成的中文物品提示文件
- `test/`：测试脚本

## 依赖环境

- Python 3.7+
- 依赖包见 `requirements.txt`

安装依赖：

```bash
pip install -r requirements.txt
```

## 用法示例

以生成全部物品提示为例：

```bash
python generate_all_itemtips.py
```

或单独生成：

```bash
python generate_itemtips.py
```

## 贡献

欢迎提交 PR 或 Issue，完善数据和功能。

## 许可证

MIT License
