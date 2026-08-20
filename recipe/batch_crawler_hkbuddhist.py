import os
import sys
import re
import json
import time
import subprocess
import urllib.request
import ssl
from bs4 import BeautifulSoup

TARGET_BASE = "/root/1CT-Share/20260818-vegetarianism/recipe/www.hkbuddhist.org"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.hkbuddhist.org/zh/top_page.php?p=medical_menu&cid=7&type_id=2&id=29'
}

# Clear proxy env vars to ensure direct SSL connection with target
for k in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
    os.environ.pop(k, None)
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

from curl_cffi import requests

_session = None

def get_session():
    global _session
    if _session is None:
        _session = requests.Session(impersonate="chrome110")
    return _session

def http_get(url, timeout=15):
    global _session
    impersonates = ['chrome110', 'chrome104', 'edge99', 'safari15_5', 'safari15_3']
    for attempt in range(6):
        imp = impersonates[attempt % len(impersonates)]
        try:
            sess = get_session()
            resp = sess.get(url, headers=HEADERS, timeout=timeout)
            if resp.status_code == 200 and len(resp.content) > 0:
                return resp.content
        except Exception:
            _session = None
        try:
            resp = requests.get(url, headers=HEADERS, impersonate=imp, timeout=timeout)
            if resp.status_code == 200 and len(resp.content) > 0:
                return resp.content
        except Exception:
            pass
        time.sleep(1 + attempt * 0.5)
    return None

def clean_text(s):
    if not s:
        return ""
    s = s.replace('\u200b', '').replace('\ufeff', '').replace('\u3000', ' ')
    s = re.sub(r'[\r\t]', ' ', s)
    s = re.sub(r' +', ' ', s)
    return s.strip()

def clean_title(raw_title):
    c = re.sub(r'【.*?】', '', raw_title)
    c = re.sub(r'#.*?#', '', c)
    c = re.sub(r'[\\/:*?"<>|（）()]', ' ', c)
    c = clean_text(c)
    return c.strip() or "佛教養生素食"

def detect_diet(title, ingredients_str):
    combined = (title + " " + ingredients_str).lower()
    has_egg = any(k in combined for k in ['鸡蛋', '蛋', '蛋清', '蛋黄', '皮蛋', '鹹蛋', '雞蛋'])
    has_dairy = any(k in combined for k in ['牛奶', '奶酪', '芝士', '黄油', '奶油', '煉乳', '乳酪', '鮮奶', '淡奶', '花奶', '忌廉', '奶', '牛油'])
    if has_egg and has_dairy:
        return "蛋奶素 Ovo-Lacto"
    elif has_egg:
        return "蛋素 Ovo-Vegetarian"
    elif has_dairy:
        return "奶素 Lacto-Vegetarian"
    return "全素 Vegan (佛教純素)"

def detect_category(title, ingredients_str):
    combined = (title + " " + ingredients_str).lower()
    if any(k in combined for k in ['面', '拉面', '米粉', '意面', '米线', '粉', '乌冬', '麵', '麵線']):
        return "面食主食"
    elif any(k in combined for k in ['饭', '粥', '炊饭', '炒饭', '米糕', '飯']):
        return "米食主食"
    elif any(k in combined for k in ['汤', '羹', '煲', '炖', '湯', '茶', '水', '露']):
        return "养生汤品"
    elif any(k in combined for k in ['凉拌', '沙拉', '腌', '泡菜', '冷盘', '涼拌']):
        return "爽口凉菜"
    elif any(k in combined for k in ['饼', '饺', '包', '馒头', '糕', '点心', '酥', '卷', '餅', '餃', '點心', '批', '圓', '团', '糰', '棗']):
        return "面点小吃"
    return "佛門素齋 / 養生佳餚"

def scrape_one_recipe(url, mmid=""):
    try:
        raw = http_get(url, timeout=15)
        if not raw:
            print(f"[!] 请求失败: {url}")
            return None

        html_content = raw.decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html_content, "html.parser")

        # 1. 标题提取 (优先使用 red_title_content)
        red_title = soup.find(class_="red_title_content")
        if red_title and clean_text(red_title.text):
            title = clean_title(red_title.text)
        else:
            title = ""

        # Find main content div
        content_div = None
        for d in soup.find_all('div'):
            t = d.text.strip()
            if '材料' in t or '做法' in t or '製作' in t or '製法' in t:
                content_div = d
                break

        if not content_div:
            print(f"[!] 未找到食谱内容区块: {url}")
            return None

        full_text = content_div.text
        lines = [clean_text(l) for l in full_text.split('\n') if clean_text(l)]

        if not title:
            for l in lines[:5]:
                if l not in ['素食食譜', '下載區', '養生食療', '返回'] and not l.startswith('材料') and not title:
                    title = clean_title(l)

        if not title:
            title = f"佛門養生素食_{mmid}"

        # 份量提取
        portion = "2-4 人份"
        for l in lines[:6]:
            if re.search(r'\d+\s*[-至到~]?\s*\d*\s*人份|\d+\s*人份|份量', l) and not any(l.startswith(k) for k in ['材料', '食材']):
                portion = l
                break

        # 2. 食材与调料提取
        ingredients = []
        seasonings = []
        steps = []
        source_note = ""
        thanks_note = ""

        mode = None # "ing", "season", "step"
        for l in lines:
            if any(l.startswith(k) for k in ["資料來源：", "資料來源:", "來源：", "來源:"]):
                source_note = l
                mode = None
            elif any(l.startswith(k) for k in ["鳴謝：", "鳴謝:", "感謝：", "感謝:"]):
                thanks_note = l
                mode = None
            elif l in ["返回", "其他內容："]:
                mode = None
            elif re.match(r"^[\u4e00-\u9fa5]{0,8}(做法|步驟|烹調步驟|製作方法|製作|製法|小貼士)[：:]?", l):
                mode = "step"
                rest = re.sub(r"^[\u4e00-\u9fa5]{0,8}(做法|步驟|烹調步驟|製作方法|製作|製法|小貼士)[：:]?\s*", "", l).strip()
                if rest:
                    steps.append(rest)
            elif re.match(r"^[\u4e00-\u9fa5]{0,8}(調味料|調味|醃料)[：:]?", l):
                mode = "season"
                rest = re.sub(r"^[\u4e00-\u9fa5]{0,8}(調味料|調味|醃料)[：:]?\s*", "", l).strip()
                if rest:
                    if "、" in rest:
                        parts = [p.strip() for p in rest.split("、") if p.strip()]
                        seasonings.extend(parts)
                    else:
                        seasonings.append(rest)
            elif re.match(r"^[\u4e00-\u9fa5]{0,8}(材料|食材|主要材料)[：:]?", l):
                mode = "ing"
                rest = re.sub(r"^[\u4e00-\u9fa5]{0,8}(材料|食材|主要材料)[：:]?\s*", "", l).strip()
                if rest and not re.match(r"^[（\(].*?[）\)]$", rest):
                    if "、" in rest:
                        parts = [p.strip() for p in rest.split("、") if p.strip()]
                        ingredients.extend(parts)
                    else:
                        ingredients.append(rest)
            else:
                if mode == "ing" and l:
                    if not re.match(r"^[（\(].*?[）\)]$", l):
                        if "、" in l:
                            parts = [p.strip() for p in l.split("、") if p.strip()]
                            ingredients.extend(parts)
                        else:
                            ingredients.append(l)
                elif mode == "season" and l:
                    if "、" in l:
                        parts = [p.strip() for p in l.split("、") if p.strip()]
                        seasonings.extend(parts)
                    else:
                        seasonings.append(l)
                elif mode == "step" and l:
                    steps.append(l)

        # 3. 步骤拆分整理
        clean_steps = []
        for st in steps:
            parts = re.split(r"(?=[0-9]+[\.、\t])", st)
            for p in parts:
                p = clean_text(p)
                p = re.sub(r"^[0-9]+[\.、\t\s]*", "", p)
                if p and p not in clean_steps and not re.match(r"^[\u4e00-\u9fa5]{1,8}(製法|做法|小貼士)[：:]?$", p):
                    clean_steps.append(p)

        # 4. 封面图片提取
        cover_img_url = ""
        for img in content_div.find_all('img'):
            src = img.get('src')
            if src and ('medical_menu' in src or 'upload' in src) and not 'icon' in src:
                if not src.startswith('http'):
                    src = 'https://www.hkbuddhist.org/' + src.lstrip('./').lstrip('../')
                cover_img_url = src
                break

        # 5. 创建独立目录
        recipe_dir = os.path.join(TARGET_BASE, title)
        os.makedirs(recipe_dir, exist_ok=True)

        # 下载封面图
        cover_path = os.path.join(recipe_dir, "cover.jpg")
        if cover_img_url and (not os.path.exists(cover_path) or os.path.getsize(cover_path) < 1000):
            img_data = http_get(cover_img_url, timeout=15)
            if img_data and len(img_data) > 500:
                with open(cover_path, "wb") as f_img:
                    f_img.write(img_data)

        # 素食流派与分类
        all_ings_str = " ".join(ingredients + seasonings)
        diet = detect_diet(title, all_ings_str)
        category = detect_category(title, all_ings_str)

        # 6. 生成规范 Markdown
        md_lines = [
            f"# {title}",
            "",
            f"![{title}](cover.jpg)",
            "",
            "## 📋 基本資訊 / Recipe Overview",
            f"- **料理名稱**：{title}",
            f"- **份量 / Servings**：{portion}",
            f"- **素食流派 / Diet**：{diet}",
            f"- **料理分類 / Category**：{category}",
            f"- **來源平台 / Source**：[香港佛教聯合會 · 素食食譜]({url})",
        ]
        if source_note:
            md_lines.append(f"- **刊物出處**：{source_note}")
        if thanks_note:
            md_lines.append(f"- **功德鳴謝**：{thanks_note}")

        md_lines.extend([
            "",
            "## 🌿 食材清單 / Ingredients",
        ])
        for ing in ingredients:
            md_lines.append(f"- {ing}")

        if seasonings:
            md_lines.extend([
                "",
                "## 🧂 調味料 / Seasonings",
            ])
            for s in seasonings:
                md_lines.append(f"- {s}")

        md_lines.extend([
            "",
            "## 🍳 烹飪步驟 / Step-by-Step Cooking Steps",
        ])
        for s_idx, st in enumerate(clean_steps, 1):
            md_lines.append(f"{s_idx}. {st}")

        md_lines.extend([
            "",
            "---",
            f"*食譜歸檔時間：2026-08-20 · 來源：香港佛教聯合會 (www.hkbuddhist.org)*"
        ])

        md_path = os.path.join(recipe_dir, "README.md")
        with open(md_path, "w", encoding="utf-8") as f_out:
            f_out.write("\n".join(md_lines))

        print(f"[✓] 成功归档: [{diet}] {title} ({len(ingredients)} 食材, {len(clean_steps)} 步骤)")
        return {
            "title": title,
            "diet": diet,
            "category": category,
            "url": url
        }
    except Exception as e:
        print(f"[!] 抓取异常 ({url}): {e}")
        return None

def process_batch(batch_json_path):
    if not os.path.exists(batch_json_path):
        print(f"File not found: {batch_json_path}")
        return []

    with open(batch_json_path, 'r', encoding='utf-8') as f:
        url_dict = json.load(f)

    print(f"=== 开始处理批次: {batch_json_path} (共 {len(url_dict)} 道食谱) ===")
    results = []
    for u, mmid in url_dict.items():
        res = scrape_one_recipe(u, mmid)
        if res:
            results.append(res)
        time.sleep(0.4)

    print(f"=== 批次处理完成: 成功 {len(results)} / {len(url_dict)} ===")
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_batch(sys.argv[1])
    else:
        print("Usage: python batch_crawler_hkbuddhist.py <batch.json>")
