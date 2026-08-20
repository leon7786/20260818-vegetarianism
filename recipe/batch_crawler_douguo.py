import os
import sys
import re
import json
import time
import urllib.request
import urllib.parse
from curl_cffi import requests

TARGET_BASE = "/root/1CT-Share/20260818-vegetarianism/recipe/www.douguo.com"

def clean_text(s):
    if not s:
        return ""
    s = s.replace('\u200b', '').replace('\ufeff', '').replace('\u3000', ' ')
    s = re.sub(r'[\r\t]', ' ', s)
    s = re.sub(r' +', ' ', s)
    return s.strip()

def clean_recipe_title(raw_title):
    c = re.sub(r'#.*?#', '', raw_title)
    c = re.sub(r'[【】\[\]（）()]', ' ', c)
    c = re.sub(r'^(素食——|素食|家常|简单做)\s*', '', c)
    c = re.sub(r'[\\/:*?"<>|]', '_', c)
    c = clean_text(c)
    return c.strip() or "素食精选家常菜"

def detect_diet(title, ingredients_str):
    combined = (title + " " + ingredients_str).lower()
    has_egg = any(k in combined for k in ['鸡蛋', '蛋', '蛋清', '蛋黄', '皮蛋', '咸蛋', '鹌鹑蛋', '蛋液'])
    has_milk = any(k in combined for k in ['牛奶', '奶酪', '芝士', '黄油', '鲜奶', '炼乳', '奶油', '乳酪', '酸奶', '奶粉'])
    
    if has_egg and has_milk:
        return "蛋奶素 Ovo-Lacto"
    elif has_egg:
        return "蛋素 Ovo-Vegetarian"
    elif has_milk:
        return "奶素 Lacto-Vegetarian"
    return "全素 Vegan"

def detect_category(title):
    t = title.lower()
    if any(k in t for k in ["拉麵", "麵", "冬粉", "米粉", "義大利麵", "筆管麵", "烏龍麵", "意面", "面条", "拌面", "热汤面"]):
        return "麵食料理"
    elif any(k in t for k in ["飯", "粥", "米", "壽司", "布丁", "炊飯", "燉飯", "炒饭", "八宝粥"]):
        return "米食料理"
    elif any(k in t for k in ["饅頭", "馒头", "包", "餅", "饼", "糕", "面包", "麵包", "点心", "发糕", "蛋糕"]):
        return "烘焙麵點 / 點心"
    elif any(k in t for k in ["湯", "汤", "羹", "鍋", "锅", "煲", "银耳汤", "银耳羹"]):
        return "湯品羹湯"
    elif any(k in t for k in ["涼拌", "凉拌", "泡菜", "醃漬", "沙拉", "白灼"]):
        return "涼拌前菜 / 輕食"
    elif any(k in t for k in ["饮", "茶", "汁", "露"]):
        return "養生飲品 / 甜湯"
    return "家常蔬食 / 經典熱菜"

def get_unique_recipe_dir(target_base, title, url):
    base_name = title
    dir_path = os.path.join(target_base, base_name)
    if not os.path.exists(dir_path):
        return dir_path, base_name
    
    readme_path = os.path.join(dir_path, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            if url in f.read():
                return dir_path, base_name
                
    counter = 2
    while True:
        cand_name = f"{base_name} ({counter})"
        cand_path = os.path.join(target_base, cand_name)
        if not os.path.exists(cand_path):
            return cand_path, cand_name
        readme_path = os.path.join(cand_path, "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as f:
                if url in f.read():
                    return cand_path, cand_name
        counter += 1

def fetch_recipe_api(cid):
    api_url = f"https://api.douguo.net/recipe/detail/{cid}"
    data = urllib.parse.urlencode({'client': '4', '_vs': '2305', 'id': cid}).encode('utf-8')
    req = urllib.request.Request(api_url, data=data, headers={
        'User-Agent': 'DouguoRecipe/10.0.0 (iPhone; iOS 16.6; Scale/3.00)',
        'Content-Type': 'application/x-www-form-urlencoded'
    })
    
    with urllib.request.urlopen(req, timeout=10) as response:
        res = json.loads(response.read().decode('utf-8'))
        return res.get('result', {}).get('recipe', {})

def download_cover(image_urls, cover_path):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.douguo.com/'
    }
    for img_url in image_urls:
        if not img_url:
            continue
        img_url = img_url.replace('http://', 'https://')
        try:
            r = requests.get(img_url, headers=headers, impersonate='chrome120', timeout=15)
            if r.status_code == 200 and len(r.content) > 500:
                with open(cover_path, 'wb') as f:
                    f.write(r.content)
                return True
        except Exception:
            pass
    return False

def scrape_batch(batch_json_path):
    if not os.path.exists(batch_json_path):
        print(f"Batch file not found: {batch_json_path}")
        return

    with open(batch_json_path, 'r', encoding='utf-8') as f:
        url_dict = json.load(f)

    os.makedirs(TARGET_BASE, exist_ok=True)
    print(f"=== 开始抓取批次: {batch_json_path} (共 {len(url_dict)} 道菜谱) ===")

    success_count = 0
    for idx, (url, initial_title) in enumerate(url_dict.items(), 1):
        m = re.search(r'/cookbook/(\d+)\.html', url)
        if not m:
            print(f"[{idx}/{len(url_dict)}] 无法解析菜谱ID: {url}")
            continue
        cid = m.group(1)
        
        try:
            print(f"[{idx}/{len(url_dict)}] 正在抓取: {initial_title} ({url})")
            recipe = fetch_recipe_api(cid)
            
            raw_title = clean_text(recipe.get('title') or initial_title)
            title = clean_recipe_title(raw_title)
            if not title:
                title = f"精选素食_{cid}"

            recipe_dir, folder_title = get_unique_recipe_dir(TARGET_BASE, title, url)
            os.makedirs(recipe_dir, exist_ok=True)

            # 食材提取
            ingredients = []
            for item in recipe.get('major', []):
                t = clean_text(item.get('title', ''))
                n = clean_text(item.get('note', ''))
                if t:
                    ingredients.append(f"{t}：{n}" if n else t)
            for item in recipe.get('minor', []):
                t = clean_text(item.get('title', ''))
                n = clean_text(item.get('note', ''))
                if t:
                    ingredients.append(f"{t}：{n}" if n else t)

            # 步骤提取
            steps = []
            for step in recipe.get('cookstep', []):
                content = clean_text(step.get('content', ''))
                content = re.sub(r'^步骤\s*\d+\s*', '', content)
                content = re.sub(r'^\d+[\.、\s]\s*', '', content)
                if content:
                    steps.append(content)

            # 小贴士 & 简介
            tips_text = clean_text(recipe.get('tips', ''))
            tips_text = tips_text.replace('做菜好吃都有技巧，我的每道菜都有小妙招，大家搜索“豆果”可以直接查看我的菜谱！', '').strip()
            story = clean_text(recipe.get('cookstory', '') or recipe.get('summary', '') or recipe.get('intro', ''))
            cook_time = clean_text(recipe.get('cook_time', '')) or "15-30 分鐘"
            cook_difficulty = clean_text(recipe.get('cook_difficulty', '')) or "切墩(初级)"

            # 封面图片
            cover_path = os.path.join(recipe_dir, "cover.jpg")
            img_candidates = [
                recipe.get('photo_path'),
                recipe.get('original_photo_path'),
                recipe.get('image'),
                recipe.get('thumb_path'),
            ]
            download_cover(img_candidates, cover_path)

            # 流派分类 & 料理分类
            diet = detect_diet(folder_title, " ".join(ingredients))
            category = detect_category(folder_title)

            # 生成 README.md
            md_lines = [
                f"# {folder_title}",
                "",
                f"![{folder_title}](cover.jpg)",
                "",
                "## 📋 基本資訊 / Recipe Overview",
                f"- **料理名稱**：{folder_title}",
                f"- **原始標題**：{raw_title}",
                f"- **素食流派 / Diet**：{diet}",
                f"- **料理分類 / Category**：{category}",
                f"- **難易度 / Difficulty**：{cook_difficulty}",
                f"- **烹飪時間 / Cooking Time**：{cook_time}",
                f"- **來源平台 / Source**：[豆果美食 · 素食專區]({url})",
            ]

            if story:
                md_lines.extend([
                    "",
                    "## 📝 料理故事與簡介 / Story & Introduction",
                    f"> {story}",
                ])

            md_lines.extend([
                "",
                "## 🌿 食材及佐料清單 / Ingredients",
            ])
            for ing in ingredients:
                md_lines.append(f"- {ing}")

            md_lines.extend([
                "",
                "## 🍳 烹飪步驟 / Step-by-Step Cooking Steps",
            ])
            for s_idx, st in enumerate(steps, 1):
                md_lines.append(f"{s_idx}. {st}")

            if tips_text:
                md_lines.extend([
                    "",
                    "## 💡 大廚美味秘訣 / Chef's Tips",
                    f"- {tips_text}",
                ])

            md_lines.extend([
                "",
                "---",
                "*食譜歸檔時間：2026-08-20 · 來源：豆果美食 (www.douguo.com)*"
            ])

            md_path = os.path.join(recipe_dir, "README.md")
            with open(md_path, "w", encoding="utf-8") as f_out:
                f_out.write("\n".join(md_lines))

            has_cover = os.path.exists(cover_path) and os.path.getsize(cover_path) > 500
            print(f"  [✓] 归档成功: {folder_title} ({len(ingredients)} 食材, {len(steps)} 步骤, 封面: {'✓' if has_cover else '✗'})")
            success_count += 1

        except Exception as e:
            print(f"  [!] 抓取异常 ({url}): {e}")
        
        time.sleep(0.1)

    print(f"=== 批次完成! 成功: {success_count} / {len(url_dict)} ===")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        scrape_batch(sys.argv[1])
    else:
        print("Usage: python batch_crawler_douguo.py <batch.json>")
