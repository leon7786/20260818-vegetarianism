import os
import sys
import re
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from curl_cffi import requests
from bs4 import BeautifulSoup

TARGET_BASE = "/root/1CT-Share/20260818-vegetarianism/recipe/www.xiachufang.com"

HEADERS_LIST = [
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    },
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    },
    {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    },
    {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
]

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
    return c.strip() or "精選素食料理"

def detect_diet(title, ingredients_str):
    combined = (title + " " + ingredients_str).lower()
    has_egg = any(k in combined for k in ['鸡蛋', '蛋', '蛋清', '蛋黄', '皮蛋', '咸蛋'])
    has_dairy = any(k in combined for k in ['牛奶', '奶酪', '芝士', '黄油', '奶油', '炼乳', '乳酪'])
    if has_egg and has_dairy:
        return "蛋奶素 Ovo-Lacto"
    elif has_egg:
        return "蛋素 Ovo-Vegetarian"
    elif has_dairy:
        return "奶素 Lacto-Vegetarian"
    return "全素 Vegan"

def detect_category(title, ingredients_str):
    combined = (title + " " + ingredients_str).lower()
    if any(k in combined for k in ['面', '拉面', '米粉', '意面', '米线', '粉', '乌冬']):
        return "面食主食"
    elif any(k in combined for k in ['饭', '粥', '炊饭', '炒饭', '米糕']):
        return "米食主食"
    elif any(k in combined for k in ['汤', '羹', '煲', '炖']):
        return "养生汤品"
    elif any(k in combined for k in ['凉拌', '沙拉', '腌', '泡菜', '冷盘']):
        return "爽口凉菜"
    elif any(k in combined for k in ['饼', '饺', '包', '馒头', '糕', '点心', '酥', '卷', '曲奇', '蛋糕', '大福']):
        return "面点小吃"
    return "家常蔬食 / 经典热菜"

def fetch_html_with_retry(m_url, max_retries=6):
    for attempt in range(max_retries):
        headers = HEADERS_LIST[attempt % len(HEADERS_LIST)]
        try:
            r = requests.get(m_url, headers=headers, impersonate="chrome120", timeout=15)
            if r.status_code == 200 and len(r.text) > 1000:
                return r.text
            elif r.status_code in [429, 503]:
                time.sleep(2.5 * (attempt + 1))
        except Exception:
            time.sleep(2.0)
        time.sleep(random.uniform(1.0, 2.0))
    return None

def scrape_one_recipe(url, default_title=""):
    try:
        if default_title:
            cand_folder = clean_title(default_title)
            cand_dir = os.path.join(TARGET_BASE, cand_folder)
            if os.path.exists(os.path.join(cand_dir, "README.md")) and os.path.exists(os.path.join(cand_dir, "cover.jpg")):
                if os.path.getsize(os.path.join(cand_dir, "README.md")) > 100 and os.path.getsize(os.path.join(cand_dir, "cover.jpg")) > 1000:
                    print(f"[✓] 已存在完整归档: {cand_folder}")
                    return {"title": cand_folder, "url": url}

        recipe_id_m = re.search(r'/recipe/(\d+)', url)
        if not recipe_id_m:
            return None
        recipe_id = recipe_id_m.group(1)
        m_url = f"https://m.xiachufang.com/recipe/{recipe_id}/"

        html = fetch_html_with_retry(m_url)
        if not html:
            print(f"[!] 请求失败: {url}")
            return None

        soup = BeautifulSoup(html, "html.parser")
        
        h1 = soup.find('h1')
        raw_title = clean_text(h1.text) if h1 else clean_text(default_title)
        title = clean_title(raw_title)

        ingredients = []
        steps = []
        cover_img_url = ""
        tips = ""

        schema = soup.find('script', type='application/ld+json')
        if schema:
            try:
                data = json.loads(schema.string)
                if 'recipeIngredient' in data and isinstance(data['recipeIngredient'], list):
                    ingredients = [clean_text(i) for i in data['recipeIngredient'] if clean_text(i)]
                if 'image' in data:
                    cover_img_url = data['image']
                if 'description' in data:
                    tips = clean_text(data['description'])
            except Exception:
                pass

        if not ingredients:
            for tr in soup.find_all('tr'):
                name_td = tr.find('td', class_='name')
                unit_td = tr.find('td', class_='unit')
                if name_td:
                    n = clean_text(name_td.text)
                    u = clean_text(unit_td.text) if unit_td else ''
                    if n:
                        ingredients.append(f"{n} {u}".strip())

        recipe_steps = soup.find(class_='recipe-steps')
        if recipe_steps:
            for st_el in recipe_steps.find_all(class_=re.compile(r'\bstep\b')):
                st_text = clean_text(st_el.get_text(separator=' ', strip=True))
                st_text = re.sub(r'^步骤\s*\d+\s*', '', st_text)
                if st_text and len(st_text) > 1 and st_text not in steps:
                    steps.append(st_text)

        if not steps:
            step_divs = soup.find_all('div', class_=re.compile(r'step|instruction', re.I))
            for d in step_divs:
                for p in d.find_all('p'):
                    st = clean_text(p.text)
                    if st and len(st) > 2 and not st.startswith('步骤') and st not in steps:
                        steps.append(st)

        if not steps:
            for li in soup.find_all('li', class_=re.compile(r'step', re.I)):
                st = clean_text(li.text)
                st = re.sub(r'^步骤\s*\d+\s*', '', st)
                if st and st not in steps:
                    steps.append(st)

        h3_tips = soup.find(lambda e: e.name in ['h2', 'h3', 'h4'] and '贴士' in e.get_text())
        if h3_tips:
            next_p = h3_tips.find_next_sibling('p')
            if next_p:
                tips_text = clean_text(next_p.get_text(strip=True))
                if tips_text:
                    tips = tips_text
            elif h3_tips.parent:
                t_text = clean_text(h3_tips.parent.get_text(strip=True))
                t_text = re.sub(r'^.*?(?:小贴士|贴士)', '', t_text).strip()
                if t_text:
                    tips = t_text

        folder_name = title
        recipe_dir = os.path.join(TARGET_BASE, folder_name)
        os.makedirs(recipe_dir, exist_ok=True)

        cover_path = os.path.join(recipe_dir, "cover.jpg")
        if cover_img_url and (not os.path.exists(cover_path) or os.path.getsize(cover_path) < 1000):
            clean_cover_url = re.sub(r'\?imageView2.*$', '', cover_img_url)
            for attempt in range(3):
                headers = HEADERS_LIST[attempt % len(HEADERS_LIST)]
                try:
                    r_img = requests.get(clean_cover_url, headers=headers, impersonate="chrome120", timeout=15)
                    if r_img.status_code != 200:
                        r_img = requests.get(cover_img_url, headers=headers, impersonate="chrome120", timeout=15)
                    if r_img.status_code == 200 and len(r_img.content) > 500:
                        with open(cover_path, "wb") as f_img:
                            f_img.write(r_img.content)
                        break
                except Exception:
                    pass
                time.sleep(0.5)

        ings_str = " ".join(ingredients)
        diet = detect_diet(title, ings_str)
        category = detect_category(title, ings_str)

        md_lines = [
            f"# {title}",
            "",
            f"![{title}](cover.jpg)",
            "",
            "## 📋 基本資訊 / Recipe Overview",
            f"- **料理名稱**：{title}",
            f"- **原始標題**：{raw_title}",
            f"- **素食流派 / Diet**：{diet}",
            f"- **料理分類 / Category**：{category}",
            f"- **來源平台 / Source**：[下廚房 · 素食主義專區](https://www.xiachufang.com/recipe/{recipe_id}/)",
            "",
            "## 🌿 食材及佐料清單 / Ingredients",
        ]
        for ing in ingredients:
            md_lines.append(f"- {ing}")

        md_lines.extend([
            "",
            "## 🍳 烹飪步驟 / Step-by-Step Cooking Steps",
        ])
        for s_idx, st in enumerate(steps, 1):
            md_lines.append(f"{s_idx}. {st}")

        if tips:
            md_lines.extend([
                "",
                "## 💡 大廚美味秘訣 / Chef's Tips",
                f"- {tips}",
            ])

        md_lines.extend([
            "",
            "---",
            f"*食譜歸檔時間：{time.strftime('%Y-%m-%d')} · 來源：下廚房 (www.xiachufang.com)*"
        ])

        with open(os.path.join(recipe_dir, "README.md"), "w", encoding="utf-8") as f_out:
            f_out.write("\n".join(md_lines))

        print(f"[✓] 成功归档: [{diet}] {title}")
        return {"title": title, "diet": diet, "category": category, "url": url}
    except Exception as e:
        print(f"[!] 抓取异常 ({url}): {e}")
        return None

def process_batch(batch_json_path, max_workers=2):
    if not os.path.exists(batch_json_path):
        print(f"File not found: {batch_json_path}")
        return []

    with open(batch_json_path, 'r', encoding='utf-8') as f:
        url_dict = json.load(f)

    print(f"=== 开始处理批次: {batch_json_path} (共 {len(url_dict)} 道食谱) ===")
    results = {}

    for idx, (u, t) in enumerate(url_dict.items(), 1):
        res = scrape_one_recipe(u, t)
        if res:
            results[u] = res
        time.sleep(1.8)

    # Multi-round retries for any missing
    for retry_round in range(1, 6):
        failed_items = {u: t for u, t in url_dict.items() if u not in results}
        if not failed_items:
            break
        print(f"\n--- 正在第 {retry_round} 轮重试未成功项 (共 {len(failed_items)} 道) ---")
        time.sleep(3)
        for u, t in failed_items.items():
            time.sleep(2.5)
            res = scrape_one_recipe(u, t)
            if res:
                results[u] = res

    print(f"=== 批次处理完成: 成功 {len(results)} / {len(url_dict)} ===")
    return list(results.values())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_batch(sys.argv[1])
    else:
        print("Usage: python batch_crawler_xiachufang.py <batch.json>")
