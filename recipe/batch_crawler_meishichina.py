import os
import sys
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from curl_cffi import requests
from bs4 import BeautifulSoup

TARGET_BASE = "/root/1CT-Share/20260818-vegetarianism/recipe/home.meishichina.com"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://home.meishichina.com/recipe/sushi/elite/'
}

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
    c = re.sub(r'的做法.*$', '', c)
    c = re.sub(r'[\\/:*?"<>|（）()]', ' ', c)
    c = clean_text(c)
    return c.strip() or "素食精選料理"

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
    elif any(k in combined for k in ['饼', '饺', '包', '馒头', '糕', '点心', '酥', '卷']):
        return "面点小吃"
    return "家常蔬食 / 经典热菜"

def scrape_one_recipe(url, default_title=""):
    try:
        r = requests.get(url, headers=HEADERS, impersonate="chrome120", timeout=15)
        if r.status_code != 200:
            print(f"[!] 请求失败 ({r.status_code}): {url}")
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        # 1. 标题
        h1 = soup.find('h1', class_='title') or soup.find('h1', class_='recipe_De_title') or soup.find('h1')
        raw_title = clean_text(h1.text) if h1 and h1.text.strip() != '菜谱' else clean_text(default_title)
        title = clean_title(raw_title)

        recipe_dir = os.path.join(TARGET_BASE, title)
        os.makedirs(recipe_dir, exist_ok=True)

        # 2. 食材提取
        ingredients = []
        for fs in soup.find_all('fieldset', class_='particulars') + soup.find_all('div', class_='particulars'):
            legend = fs.find('legend')
            prefix = clean_text(legend.text) if legend else ""
            for li in fs.find_all('li'):
                t = clean_text(li.text.replace('\n', ' '))
                if t:
                    ing_item = f"{t} ({prefix})" if prefix and prefix not in t else t
                    ingredients.append(ing_item)

        if not ingredients:
            for tr in soup.find_all('tr'):
                tds = [clean_text(td.text) for td in tr.find_all('td') if clean_text(td.text)]
                if len(tds) >= 2:
                    ingredients.append(f"{tds[0]} {tds[1]}")

        # 3. 步骤提取
        steps = []
        step_container = soup.find('div', class_='recipeStep') or soup.find('div', class_='recipe_De_step') or soup.find('div', class_='step')
        if step_container:
            for li in step_container.find_all('li'):
                w = li.find('div', class_='recipeStep_word') or li.find('p') or li
                if w:
                    st = clean_text(w.text)
                    st = re.sub(r'^\d+[\.、\s]*', '', st)
                    if st and st not in steps:
                        steps.append(st)

        if not steps:
            for p in soup.find_all('p', class_=re.compile(r'step', re.I)):
                st = clean_text(p.text)
                st = re.sub(r'^\d+[\.、\s]*', '', st)
                if st and st not in steps:
                    steps.append(st)

        # 4. 小贴士
        tips_div = soup.find('div', class_='recipeTip') or soup.find('div', class_='recipe_De_tip')
        tips = ""
        if tips_div:
            tips = clean_text(tips_div.text.replace('烹饪技巧', '：').replace('小贴士', '：'))
            tips = re.sub(r'^[：:\s]+', '', tips)

        # 5. 封面图片下载
        cover_path = os.path.join(recipe_dir, "cover.jpg")
        img_url = ""
        for img in soup.find_all('img'):
            src = img.get('data-src') or img.get('src') or ""
            if src and ('meishitx.com' in src or 'meishichina.com' in src) and ('atta' in src or 'recipe' in src or 'p800' in src) and not 'space' in src and not 'logo' in src and not 'blank.gif' in src:
                if 'step' not in src:
                    img_url = src
                    break

        if not img_url:
            step_imgs = []
            for img in soup.find_all('img'):
                src = img.get('data-src') or img.get('src') or ""
                if src and ('atta/step' in src or 'step' in src) and not 'blank.gif' in src:
                    step_imgs.append(src)
            if step_imgs:
                img_url = step_imgs[-1]

        if img_url and (not os.path.exists(cover_path) or os.path.getsize(cover_path) < 1000):
            if not img_url.startswith('http'):
                img_url = 'https:' + img_url if img_url.startswith('//') else 'https://home.meishichina.com' + img_url
            hd_img_url = re.sub(r'style/p\d+', 'style/p800', img_url)
            try:
                r_img = requests.get(hd_img_url, headers=HEADERS, impersonate="chrome120", timeout=15)
                if r_img.status_code != 200:
                    r_img = requests.get(img_url, headers=HEADERS, impersonate="chrome120", timeout=15)
                if r_img.status_code == 200:
                    with open(cover_path, "wb") as f_img:
                        f_img.write(r_img.content)
            except Exception as e:
                print(f"[!] 封面下载出错 ({title}): {e}")

        # 流派与分类
        ings_str = " ".join(ingredients)
        diet = detect_diet(title, ings_str)
        category = detect_category(title, ings_str)

        # 生成 Markdown
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
            f"- **來源平台 / Source**：[美食天下 · 精華素食專區]({url})",
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
            f"*食譜歸檔時間：2026-08-20 · 來源：美食天下 (home.meishichina.com)*"
        ])

        md_path = os.path.join(recipe_dir, "README.md")
        with open(md_path, "w", encoding="utf-8") as f_out:
            f_out.write("\n".join(md_lines))

        print(f"[✓] 成功归档: [{diet}] {title} ({len(ingredients)} 食材, {len(steps)} 步骤)")
        return {
            "title": title,
            "diet": diet,
            "category": category,
            "url": url
        }
    except Exception as e:
        print(f"[!] 抓取异常 ({url}): {e}")
        return None

def process_batch(batch_json_path, max_workers=4):
    if not os.path.exists(batch_json_path):
        print(f"File not found: {batch_json_path}")
        return []

    with open(batch_json_path, 'r', encoding='utf-8') as f:
        url_dict = json.load(f)

    print(f"=== 开始并发处理批次: {batch_json_path} (共 {len(url_dict)} 道食谱) ===")
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_one_recipe, u, t): u for u, t in url_dict.items()}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    print(f"=== 批次处理完成: 成功 {len(results)} / {len(url_dict)} ===")
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_batch(sys.argv[1])
    else:
        print("Usage: python batch_crawler_meishichina.py <batch.json>")
