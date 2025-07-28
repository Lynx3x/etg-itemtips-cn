#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import codecs
import os
import re
import time
import random
import logging
from tqdm import tqdm
from etg_parser import extract_item_description, extract_item_synergies, get_page_content_selenium
import csv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('itemtips_generation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 设置常量
SAMPLE_FILE = 'itemtips-sample.tip'
OUTPUT_FILE = 'itemtips-cn.tip'
CACHE_DIR = 'cache'
WIKI_BASE_URL = 'https://etg-xd.wikidot.com/'
MAX_RETRIES = 3
DELAY_MIN = 1
DELAY_MAX = 3

# 确保缓存目录存在
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def normalize_key_for_url(key, key_to_wikikey=None):
    """
    将key标准化为wiki页面用的key（优先用key_to_wikikey映射）
    """
    # 如果有映射且key在映射中，则使用映射的值
    if key_to_wikikey and key in key_to_wikikey:
        key = key_to_wikikey[key]
        # 标准化处理（替换下划线为连字符，转小写）
        return key.replace('_', '-').lower()
    
    # 没有映射直接返回原始key
    return key

def load_itemtips_sample():
    """
    加载itemtips-sample.tip文件，创建各种映射
    
    返回:
    - sample_data: 原始sample数据
    - synergy_name_to_key: 联动名称到key的映射
    - synergy_cn_to_key: 联动中文名称到key的映射
    """
    logging.info(f"加载 {SAMPLE_FILE} 文件...")
    with codecs.open(SAMPLE_FILE, 'r', encoding='utf-8-sig') as f:
        sample_data = json.load(f)
    
    # 创建联动名称到key的映射
    synergy_name_to_key = {}
    synergy_cn_to_key = {}
    
    for key, synergy_data in sample_data['synergies'].items():
        if 'name' in synergy_data:
            # 中文名称映射
            synergy_cn_to_key[synergy_data['name']] = key
            # 英文名称映射(去掉#号)
            eng_name = key[1:] if key.startswith('#') else key
            synergy_name_to_key[eng_name] = key
            # # 转换为多种可能的形式
            # formatted_name = ' '.join(word.capitalize() for word in eng_name.split('_'))
            # synergy_name_to_key[formatted_name] = key
            # # 全部小写形式
            # synergy_name_to_key[formatted_name.lower()] = key
    
    logging.info(f"加载了 {len(synergy_name_to_key)} 个联动名称映射")
    
    return sample_data,  synergy_name_to_key, synergy_cn_to_key

def load_key_to_wikikey_mapping(csv_path='invalid_pages.csv'):
    """
    读取invalid_pages.csv，返回key到真实wikiKey的映射字典
    """
    mapping = {}
    with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row['项目ID']
            wikikey = row['正确htmlKey'].strip()
            if wikikey:
                mapping[key] = wikikey
    return mapping

def get_page_content(key, key_to_wikikey=None, retry=0):
    """
    获取物品的wiki页面内容，优先从缓存读取，没有再请求
    
    参数:
    - key: 物品key
    - key_to_wikikey: key到wikiKey的映射字典
    - retry: 当前重试次数
    
    返回:
    - 页面HTML内容
    """
    # 先标准化key，得到wikiKey
    wiki_key = normalize_key_for_url(key, key_to_wikikey)
    
    if wiki_key:
        # 先检查标准化后的缓存文件
        normalized_cache_file = os.path.join(CACHE_DIR, f"{wiki_key}.html")
        if os.path.exists(normalized_cache_file):
            logging.debug(f"从标准化缓存读取: {normalized_cache_file}")
            with open(normalized_cache_file, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # 如果没有标准化后的缓存文件，直接获取内容并保存
            logging.info(f"获取标准化页面内容: {WIKI_BASE_URL}{wiki_key}")
            html_content = get_page_content_selenium(wiki_key)
            
            # 固定延迟1秒，避免请求过快
            time.sleep(1)
            # 保存到缓存，使用标准化的文件名
            with open(normalized_cache_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            return html_content

    # 再检查原始key的缓存文件
    original_cache_file = os.path.join(CACHE_DIR, f"{key}.html")
    if os.path.exists(original_cache_file):
        logging.debug(f"从原始缓存读取: {original_cache_file}")
        with open(original_cache_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    try:
        logging.info(f"获取页面内容: {WIKI_BASE_URL}{wiki_key}")
        # 直接传递wiki_key给get_page_content_selenium
        html_content = get_page_content_selenium(wiki_key)
        
        # 随机延迟，避免请求过快
        delay = random.uniform(DELAY_MIN, DELAY_MAX)
        time.sleep(delay)
        
        # 保存到缓存，使用标准化的文件名
        with open(normalized_cache_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return html_content
    except Exception as e:
        if retry < MAX_RETRIES:
            logging.warning(f"获取页面 {WIKI_BASE_URL}{wiki_key} 失败: {e}，第 {retry+1} 次重试")
            # 增加延迟时间后重试
            time.sleep(delay * 2 if 'delay' in locals() else 5)
            return get_page_content(key, key_to_wikikey, retry + 1)
        else:
            logging.error(f"获取页面 {WIKI_BASE_URL}{wiki_key} 失败: {e}，已超过最大重试次数")
            return None

def find_synergy_key(synergy_name, eng_name, synergy_name_to_key, synergy_cn_to_key,wiki_key):
    """
    查找联动对应的键
    
    参数:
    - synergy_name: 联动名称
    - eng_name: 联动英文名称
    - synergy_name_to_key: 联动名称到键的映射
    - synergy_cn_to_key: 中文联动名称到键的映射
    - wiki_key: 物品wiki_key
    
    返回:
    - 找到的键，如果找不到则返回格式化后的键
    """
    # 0.特殊key直接替换
    special_mappings = {
        "Fairy Bow": "#ZELDA",
        "Revolution":"#REVOLUTIONARY",
        "In The Mood!": "#QUAKE",
        "The Killing Joke": "#KILLINGJOKE",
        "Dead Place": "#DEADSPACE",
        "你说什么军队？":"#ANTQUEEN",
        "Mmmmmmmmm MMMMmm!":"#MGUNS",
        '锤子和钉子 搞定':"#NAILCANNON",
        'Thorn Bath, ooh!':"#THORNPRICK",
        'I need scissors! 61!':"#NEEDSCISSORS",
        'All Out Of Law':"#OUTLAWSTAR",
        '找不出':"#MUSIC",
        "Rubenstein's Monster":"#DOUBLERUBES",
        "Fear the Old Blood":"#BLOODBORNE",
        "Cryptic Cryptids":"#FOSSILPHOENIX",
        "Powerhouse of the Cell":"#POWERHOUSE",
        "\o/":"#SOULAIR",
        "J am":"#ALPHAOMEGA",
        "Monsters and Monocles":"#MONOCLES",
        "Bacon and Eggs":"#CHICKENANDPIG",
        "Crave the Glaive":"#CRAVEGLAIVE",
        "some even larger number":"#LARGERNUMBER",
        "Kaliber k'pow uboom k'bhang":"#KALIBERKBOOM",
        "Hidden Tech Big Shotgun":"#HIDDENTECHSHOTGUN",
        "Grouch":"#GARBAGE",
        "Iron Stance":"#IRONSHOT",
        "Reload Roll":"#DODGELOAD",
        "Flat Stanley":"#POSTMAN",
        "Behold!":"#BEHOLSTER",
        "他很年轻":"#CANNONREBORN",
        "Willing To Sacrifice":"#COLDASICE",
        "Ice Cap":"#CAPTAINCOLD",
        "Heavy Jolt":"#HEAVYJOLTER",
        "Pretty Good":"#OCELOT",
        "Alas, Sniperion":"#SNIPERION",
        "Sleuth Out":"#MAGNIFYINGGLASS",
        "Hail, Satan!":"#DEMONIC",
        "Special Delivery":"#HEDWIG",
        "人民大众的枪":"#MAKPAK",
        "遵纪守法":"#ROBOCOP",
        "Vulcan Raving":"#VULCANRAVEN",
        "Iroquois":"#SNAKEPLISSKIN",
        "Keep The Change":"#MYLITTLEFRIEND",
        "Square Brace":"#CURLY_BRACE",
        "Dead Cell":"#FORTUNESFAVOR",
        "Barrage Shot":"#CHARGESHOT",
        "美人霰弹鱼":"#MERMAIDFISH",
        "Gunnerang":"#BATMAN",
        "Whale of a Time":"#WHALETIME",
        "Spengbab":"#SPONGEBOB",
        "Turret Link":"#TURRETRANDOMIZER",
        "春姐铃音":"#HOLYBELL",
        "Lumberjacked":"#WOODAXE",
        "Hacker":"#LOWER_CASE_R",
        "Gilded Bullets":"#GILDEDTABLES",
        "Soft Air":"#AIRSOFT",
        "Master's Chambers":"#MASTERCHAMBERS",
        "Rabid":"#ALPHABETANGRY",
        "Block Party":"#MARIOPARTY",
        "海盗旗":"#SKULLANDBONES",
        "Remnant":"#ALPHABETOMEGA",
        "饭海辛":"#ALPHABETSILVER",
    }
    if synergy_name in special_mappings:
        return special_mappings[synergy_name]

    # 1. 先尝试直接中文名称匹配
    if synergy_name in synergy_cn_to_key:
        return synergy_cn_to_key[synergy_name]
    
    # 2. 尝试英文直接匹配
    if synergy_name in synergy_name_to_key:
        return synergy_name_to_key[synergy_name]
    
    # 3. 尝试各种变形格式
    name_variants = [
        synergy_name,
        synergy_name.upper(),
        synergy_name.upper().replace(' ', '_').replace('-', '_'),
        synergy_name.replace(' ', '_').replace('-', '_'),
        synergy_name.lower(),
        synergy_name.lower().replace(' ', '_').replace('-', '_'),
        synergy_name.upper().replace(' ', '').replace('-', '')
    ]
    
    for variant in name_variants:
        if variant in synergy_name_to_key:
            return synergy_name_to_key[variant]
    
    # 4. 尝试通过模糊匹配查找中文名称和英文名称
    # 计算所有名称的相似度，找到最匹配的
    best_match = None
    best_match_score = 0
    
    # 先尝试中文名称模糊匹配
    for cn_name, key in synergy_cn_to_key.items():
        # 计算字符重叠率
        common_chars = set(synergy_name) & set(cn_name)
        overlap_score = len(common_chars) / max(len(synergy_name), len(cn_name))
        
        # 计算子串匹配得分
        substring_score = 0
        for i in range(min(len(synergy_name), len(cn_name)), 0, -1):
            if i >= 2:  # 至少匹配2个字符
                if synergy_name[-i:] == cn_name[:i] or synergy_name[:i] == cn_name[-i:]:
                    substring_score = i / max(len(synergy_name), len(cn_name))
                    break
        
        # 综合得分
        similarity_score = max(overlap_score, substring_score)
        
        if similarity_score > 0.5 and similarity_score > best_match_score:  # 设置一个阈值
            best_match = key
            best_match_score = similarity_score
            best_match_type = "中文"
    
    # # 再尝试英文名称模糊匹配
    # for eng_key, key in synergy_name_to_key.items():
    #     # 计算字符重叠率
    #     common_chars = set(eng_name.lower() if eng_name else synergy_name.lower()) & set(eng_key.lower())
    #     overlap_score = len(common_chars) / max(len(eng_name if eng_name else synergy_name), len(eng_key))
        
    #     # 计算子串匹配得分
    #     substring_score = 0
    #     name_to_compare = eng_name.lower() if eng_name else synergy_name.lower()
    #     for i in range(min(len(name_to_compare), len(eng_key.lower())), 0, -1):
    #         if i >= 2:  # 至少匹配2个字符
    #             if name_to_compare[-i:] == eng_key.lower()[:i] or name_to_compare[:i] == eng_key.lower()[-i:]:
    #                 substring_score = i / max(len(name_to_compare), len(eng_key))
    #                 break
        
    #     # 综合得分
    #     similarity_score = max(overlap_score, substring_score)
        
    #     if similarity_score > 0.5 and similarity_score > best_match_score:  # 设置一个阈值
    #         best_match = key
    #         best_match_score = similarity_score
    #         best_match_type = "英文"
    
    if best_match:
        # 找出匹配到的具体中文名称
        matched_name = ""
        for cn_name, key in synergy_cn_to_key.items():
            if key == best_match:
                matched_name = cn_name
                break
        
        logging.info(f"通过{best_match_type}模糊匹配找到联动键: '{synergy_name}' => '{best_match}'，匹配到 '{matched_name}'，相似度: {best_match_score:.2f}")
        return best_match
    
    # 5. 尝试反向查找：通过生成所有可能的标准形式，查找匹配的键
    formatted_name = synergy_name.upper().replace(' ', '_').replace('-', '_')
    standard_key = f"#{formatted_name}"
    
    # 记录找不到的键，确保文件存在并可写入
    try:
        with open('unmatched_synergies.txt', 'a', encoding='utf-8') as f:
            f.write(f"{wiki_key}: {synergy_name} => {standard_key}\n")
        logging.info(f"已记录未匹配的联动键: {synergy_name} => {standard_key}")
    except Exception as e:
        logging.error(f"记录未匹配的联动键时出错: {e}")
    
    logging.warning(f"未能找到联动 '{synergy_name}' 对应的标准键，使用生成的键 '{standard_key}'")
    
    # 如果都找不到，使用标准格式：#NAME格式
    return standard_key
def replace_placeholders(text, sample_data, enemy_mapping=None):
    """
    替换文本中的占位符为中文名称
    
    参数:
    - text: 包含占位符的文本
    - sample_data: 从itemtips-sample.tip读取的数据对象
    - enemy_mapping: 敌人英文名到中文名的映射字典
    
    返回:
    - 替换后的文本
    """
    # 手动补充一些不在道具表里的名称
    manual_mappings = {
        "thompson_submachinegun": "汤普森冲锋枪",
        "a.w.p.": "A.W.P.",
        "sniper_shell": "狙击弹",
        "professional": "专家狙击弹",
        "32pxsiren": "塞壬女妖",
        "status_enemy_jammed": "诅咒怪",
        "32pxbig_shotgun": "大型霰弹枪",
        "beholster_shrine": "嗜枪怪神龛",
        "32pxhexagun": "六角枪",
        "blank": "空响弹",
        "32pxknight%27s_gun": "骑士枪",
        "money": "弹壳币",
        "money_5": "银弹壳币(5)",
        "golden_shell": "金弹壳币(50)",
        "armor": "护甲",
        "32pxfightsabre": "战斗军刀",
        "32pxm16": "M16",
        "blank_companion%27s_ring": "空响弹伙伴之戒指",
        "ring_of_triggers": "扳机之戒",
        "32pxrailgun": "磁轨炮",
        "heart": "心",
        "half_heart": "半颗心",
        "insight": "洞悉怪",
        "lil%27_bomber": "里尔炸弹枪",
        "32pxrubenstein%27s_monster": "鲁宾斯坦的怪物",
        "betrayer%27s_shield": "背弃者护罩",
        "mr._accretion_jr.": "小冲积先生",
        "32pxmolotov_launcher": "燃烧弹发射器",
        "gunslinger%27s_ashes": "枪手骨灰",
        "32pxthe_exotic": "异域者",
        "32pxtrident": "三叉戟",
        "32pxstrafe_gun": "冲锋@枪",
        "32pxprototype_railgun": "磁轨炮原型机",
        "shotgrub_%28enemy%29": "机枪怪",
        "resourceful_rat": "机智老鼠",
        "master_round_i": "胜者之弹 I",
        "master_round_v": "胜者之弹 V",
        "bullet_kin": "子弹怪",
        "veteran_bullet_kin": "资深子弹怪",
        "cormorant": "枪骑士",
        "gunjurer": "枪巫师",
        "hunter_in-game": "猎人",
        "cultist_in-game": "邪教徒",
        "robot_in-game": "机器人",
        "ammo": "弹药",
        "marine_in-game": "陆战队员",
        "convict_in-game": "囚犯",
        "pilot_in-game": "飞行员",
        "heart_container": "心之容器",
        "rocket-powered_bullets": "火箭动力子弹",
        "key": "钥匙",
        "ser_junkan_1": "垃圾宝宝",
        "ser_junkan_golden": "金垃圾宝宝",
        "synergrace": "组合商人",
        "synergy_chest": "组合宝箱",
        "yv_shrine": "Y.V.神龛（花钱获得概率追击射击的能力）",
        "truth_chest": "真理宝箱",
        "junk_shrine": "垃圾宝神龛",
        "rat_chest": "老鼠宝箱",
        "old_king": "老国王",
        "prize_pistol": "奖品手枪（打靶游戏专用枪）",
        "high_dragun": "枪龙",
        "akey-47": "AKEY-47",
        "ac-15": "AC-15",
        "ak-47": "AK-47",
        "save_button": "保存按钮",
        "ancient_hero%27s_bandana": "古代英雄的头巾",
        "red-caped_bullet_kin": "红披风子弹怪",
        "rainbow_chest": "彩虹箱",
        "blood_shrine": "血液神龛（消耗心之容器获得吸血能力）",
        "mirror": "镜子",
        "red_chest": "红箱(A级)",
        "black_chest": "黑箱(S级)",
        "brown_chest": "棕箱(D级)",
        "blue_chest": "蓝箱(C级)",
        "googly-eyed_mimic": "大眼睛拟身怪",
        "spikes": "",
        "fire": "",
        "shopkeeper": "商店老板",
        "boss_resourceful_rat": "机智老鼠(Boss)",
        "serpent": "小蛇",
        "bullet_that_can_kill_the_past": "可以抹掉过去的子弹",
        "blacksmith": "铁匠姐姐",
        "arcane%20gunpowder": "神秘火药",
        "demon_face": "黑市入口",
        "bullet_in-game": "子弹人",
        "alpha_bullet": "A级子弹",
        # 添加未解析的占位符
        "32px-strafe_gun": "冲锋@枪",
        "32px-knight%27s_gun": "骑士枪",
        "32px-m16": "M16",
        "32px-railgun": "磁轨炮",
        "a": "A",
        "b": "B",
        "32px-fightsabre": "战斗军刀",
        "professor_goopton": "液体商人",
        "blank_shrine": "空响弹神龛",
        "32px-the_exotic": "异域者",
        "brick_of_cash_baby": "现金砖宝贝",
        "hegemony_credit": "帝国币",
        "jk-47": "JK-47",
        "s": "S",
        "32px-winchester_rifle": "温彻斯特步枪",
        "vertebraek-47": "脊椎K-47",
        "thesellcreep": "收破烂（卖枪的）",
        "spread_ammo": "弹药包(红的那个)",
        "heart_machine": "红心存储机",
        "32px-the_fat_line": "加粗线条",
        "glass_shrine": "玻璃神龛",
        "vampire": "吸血鬼",
        "challenge_shrine": "挑战神龛",
        "bullet_%28gun%29": "子弹枪",
        "gunslinger_in-game": "枪手",
        "clown_skin": "",
        "clown_wolf": "小丑：沃尔夫",
        "clown_hoxton": "小丑：霍斯顿",
        "clown_chains": "小丑：钱恩斯",
        "rube-adyne_prototype": "鲁布-亚达因原型",
        "rube-adyne_mk.ii": "鲁布-亚达因型二号",
        "c": "C",
        "32px-molotov_launcher": "燃烧弹发射器",
        "partially-eaten_cheese": "吃了一口的奶酪形",
        "icon_gun_gueue": "「玩家不能主动换枪，弹夹用光、装弹、或者等待30秒后，会自动换成背包中的下一把枪」",
        "muncher": "吃枪人",
    }
    
    if not text:
        return text
    # 首先查找所有{item:xxx}或{item: xxx}格式的占位符
    placeholder_pattern = r'\{item:[ ]?(.*?)\}'
    matches = re.findall(placeholder_pattern, text)
    # 对每个占位符执行替换
    for match in matches:
        # 原始占位符文本，兼容冒号后有无空格的情况
        orig_placeholder = re.search(r'(\{item:[ ]?' + re.escape(match) + r'\})', text)
        orig_placeholder = orig_placeholder.group(1) if orig_placeholder else f"{{item:{match}}}"
        # 查找匹配的物品并替换为中文名称
        replaced = False
        
        # 首先检查手动映射
        if match.lower() in manual_mappings:
            cn_name = manual_mappings[match.lower()]
            text = text.replace(orig_placeholder, cn_name)
            replaced = True
            continue
            
        # 然后检查sample_data
        if match.lower() in sample_data['items']:
            # 直接从sample_data获取中文名称
            cn_name = sample_data['items'][match.lower()]['name']
            text = text.replace(orig_placeholder, cn_name)
            replaced = True
            continue
            
        # 检查敌人映射
        if enemy_mapping and match.lower() in enemy_mapping:
            cn_name = enemy_mapping[match.lower()]
            text = text.replace(orig_placeholder, cn_name)
            replaced = True
            continue
            
        # 如果所有变体都没有找到对应的中文名称
        if not replaced:
            logging.warning(f"无法找到占位符 {orig_placeholder} 的对应中文名称，保留原样")
            # 在未处理的占位符文件中记录
            try:
                with open('unresolved_placeholders.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{orig_placeholder}\n")
                logging.info(f"已记录未解析的占位符: {orig_placeholder}")
            except Exception as e:
                logging.error(f"记录未解析的占位符时出错: {e}")
    return text

def generate_tip_file(items_data, sample_data, output_file, key_to_wikikey):
    """
    生成最终的tip文件
    
    参数:
    - items_data: 处理后的物品数据
    - sample_data: 原始sample数据
    - output_file: 输出文件名
    - key_to_wikikey: 游戏键到wiki键的映射字典
    """
    logging.info(f"生成tip文件: {output_file}")
    
    # 构建tip文件内容
    tip_content = {
        "metadata": {
            "name": "挺进地牢物品提示 - 中文",
            "url": "https://etg-xd.wikidot.com",
            "version": "1.0.0"
        },
        "items": {},
        "synergies": {}
    }
    
    # 添加物品数据，保持原始顺序
    for key in sample_data['items'].keys():
        if key in items_data:
            tip_content["items"][key] = {
                "name": items_data[key]["name"],
                "notes": items_data[key]["notes"]
            }
        elif key in key_to_wikikey and key_to_wikikey[key] in items_data:
            # 如果原始key没有，但映射后的key存在
            mapped_key = key_to_wikikey[key]
            tip_content["items"][key] = {
                "name": items_data[mapped_key]["name"],
                "notes": items_data[mapped_key]["notes"]
            }
        else:
            # 如果未处理，保留原始数据
            tip_content["items"][key] = sample_data["items"][key]
            logging.warning(f"未处理物品 {key}，保留原始数据")
    
    # 添加联动数据，保持原始顺序
    synergies_data = items_data.get("synergies", {})
    for key in sample_data['synergies'].keys():
        if key in synergies_data:
            tip_content["synergies"][key] = {
                "name": sample_data["synergies"][key].get("name") or synergies_data[key].get("name", ""),
                "notes": synergies_data[key]["notes"]
            }
        else:
            # 如果未处理，保留原始数据
            tip_content["synergies"][key] = sample_data["synergies"][key]
            logging.warning(f"未处理联动 {key}，保留原始数据")
    
    # 记录新发现的联动，但不添加到tip文件中
    for key, data in synergies_data.items():
        if key not in tip_content["synergies"]:
            logging.info(f"发现新联动但不添加: {key}")
    
    # 保存为tip文件
    with codecs.open(output_file, 'w', encoding='utf-8-sig') as f:
        json.dump(tip_content, f, indent=2, ensure_ascii=False)
    
    logging.info(f"tip文件生成完成: {output_file}")


def main():
    start_time = time.time()
    logging.info("开始生成中文物品提示文件...")
    
    # 初始化未匹配的联动键和未解析的占位符文件
    with open('unmatched_synergies.txt', 'w', encoding='utf-8') as f:
        f.write("# 未匹配的联动键\n")
    
    with open('unresolved_placeholders.txt', 'w', encoding='utf-8') as f:
        f.write("# 未解析的占位符\n")
    
    # 加载sample数据和映射
    sample_data, synergy_name_to_key, synergy_cn_to_key = load_itemtips_sample()
    key_to_wikikey = load_key_to_wikikey_mapping()

    # 加载敌人映射数据
    enemy_mapping = {}
    try:
        enemy_mapping_path = os.path.join('etg_scrapers', 'enemy_mapping.json')
        with open(enemy_mapping_path, 'r', encoding='utf-8') as f:
            enemy_mapping = json.load(f)
        logging.info(f"成功加载敌人映射数据，共 {len(enemy_mapping)} 个敌人")
    except Exception as e:
        logging.error(f"加载敌人映射数据失败: {e}")
    
    # 初始化计数器
    total_items = len(sample_data['items'])
    processed_items = 0
    failed_items = 0
    total_synergies = 0
    
    try:
        # 物品数据
        items_data = {}
        synergies_data = {}
        
        # 处理所有物品
        logging.info(f"开始处理 {total_items} 个物品...")
        for key, item_data in tqdm(sample_data['items'].items(), desc="处理物品"):
            try:
                item_name_cn = item_data.get('name', key)
                wiki_key = normalize_key_for_url(key, key_to_wikikey)
                # 获取页面内容
                html_content = get_page_content(key, key_to_wikikey)
                if not html_content:
                    logging.error(f"无法获取物品 {key} 的页面内容，跳过")
                    failed_items += 1
                    continue
                
                # 提取描述
                description = extract_item_description(html_content, wiki_key, item_name_cn)
                if not description:
                    logging.warning(f"物品 {key} 的描述提取失败，使用原始描述")
                    description = item_data.get('notes', '')
                
                # 替换物品描述中的占位符
                description = replace_placeholders(description, sample_data, enemy_mapping)
                
                # 添加到物品数据
                items_data[key] = {
                    "name": item_name_cn,
                    "notes": description
                }
                processed_items += 1
                
                # 提取联动信息
                synergies = extract_item_synergies(html_content)
                for synergy in synergies:
                    synergy_name = synergy['name']
                    eng_name = synergy['eng_name']
                    # 查找联动键
                    synergy_key = find_synergy_key(synergy_name, eng_name, synergy_name_to_key, synergy_cn_to_key,wiki_key)
                    
                    # 替换联动描述中的占位符
                    synergy_desc = synergy['description']
                    synergy_desc = replace_placeholders(synergy_desc, sample_data, enemy_mapping)
                    
                    synergies_data[synergy_key] = {
                        "notes": synergy_desc
                    }
                    total_synergies += 1
                
                # 每处理100个物品，生成一次临时文件
                if processed_items % 100 == 0:
                    logging.info(f"已处理 {processed_items} / {total_items} 个物品")
                    
            except Exception as e:
                logging.error(f"处理物品 {key} 时出错: {e}")
                failed_items += 1
        
        # 将联动数据添加到物品数据中
        items_data["synergies"] = synergies_data
        
        # 给没有名字的联动效果手动补一下名字
        items_data["synergies"]["#FOSSILPHOENIX"]["name"] = "神秘生物"
        items_data["synergies"]["#REPLETE"]["name"] = "Replate"
        items_data["synergies"]["#SOULAIR"]["name"] = "赞美太阳"

        # 修一些明明一样的但是多了一份的联动效果
        items_data["synergies"]["#HOMINGBOMBS2"] = items_data["synergies"]["#HOMINGBOMBS3"]

        # 生成最终tip文件
        generate_tip_file(items_data, sample_data, OUTPUT_FILE, key_to_wikikey)
        
        # 生成统计报告
        end_time = time.time()
        processing_time = end_time - start_time
        
        logging.info("\n处理统计:")
        logging.info(f"总物品数: {total_items}")
        logging.info(f"成功处理物品数: {processed_items}")
        logging.info(f"失败物品数: {failed_items}")
        logging.info(f"提取联动数: {total_synergies}")
        logging.info(f"处理用时: {processing_time:.2f} 秒")
        
        print("\n处理统计:")
        print(f"总物品数: {total_items}")
        print(f"成功处理物品数: {processed_items}")
        print(f"失败物品数: {failed_items}")
        print(f"提取联动数: {total_synergies}")
        print(f"处理用时: {processing_time:.2f} 秒")
        print(f"生成的文件: {OUTPUT_FILE}")
    
    except Exception as e:
        logging.error(f"程序执行出错: {e}")
    
    finally:
        logging.info("程序执行完成")

if __name__ == "__main__":
    main() 