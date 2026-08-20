import os
import sys
import re
import json
import time
import urllib.parse
import urllib.request
import hashlib
from curl_cffi import requests
from bs4 import BeautifulSoup

TARGET_BASE = "/root/1CT-Share/20260818-vegetarianism/recipe/www.douguo.com"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.douguo.com/'
}

def clean_text(s):
    if not s:
        return ""
    s = s.replace('\u200b', '').replace('\ufeff', '').replace('\u3000', ' ')
    s = re.sub(r'[\r\t]', ' ', s)
    s = re.sub(r' +', ' ', s)
    return s.strip()

def clean_recipe_title(raw_title):
    c = re.sub(r'【.*?】', '', raw_title)
    c = re.sub(r'#.*?#', '', c)
    c = re.sub(r'的做法.*$', '', c)
    c = re.sub(r'[\\/:*?"<>|]', ' ', c)
    c = clean_text(c)
    return c.strip()

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

def fetch_recipe_api(cid):
    api_url = f"https://api.douguo.net/recipe/detail/{cid}"
    data = urllib.parse.urlencode({'client': '4', '_vs': '2305', 'id': cid}).encode('utf-8')
    req = urllib.request.Request(api_url, data=data, headers={
        'User-Agent': 'DouguoRecipe/10.0.0 (iPhone; iOS 16.6; Scale/3.00)',
        'Content-Type': 'application/x-www-form-urlencoded'
    })
    
    with urllib.request.urlopen(req, timeout=12) as response:
        res = json.loads(response.read().decode('utf-8'))
        return res.get('result', {}).get('recipe', {})

def refetch_and_fix_all():
    folders = sorted(os.listdir(TARGET_BASE))
    total = len(folders)
    print(f"=== 开始全量精准重构 Douguo 食谱与封面图 (共 {total} 道，严格限速 1秒1菜) ===")
    
    success = 0
    hashes = set()
    
    for idx, folder in enumerate(folders, 1):
        f_dir = os.path.join(TARGET_BASE, folder)
        if not os.path.isdir(f_dir):
            continue
            
        md_path = os.path.join(f_dir, "README.md")
        cover_path = os.path.join(f_dir, "cover.jpg")
        
        if not os.path.exists(md_path):
            continue
            
        with open(md_path, "r", encoding="utf-8") as f_in:
            old_md = f_in.read()
            
        cid_m = re.search(r'/cookbook/(\d+)\.html', old_md)
        if not cid_m:
            print(f"[{idx}/{total}] 无法提取 CID: {folder}")
            continue
        cid = cid_m.group(1)
        
        try:
            print(f"[{idx}/{total}] 正在精准抓取 CID={cid}: {folder}")
            recipe = fetch_recipe_api(cid)
            
            raw_title = clean_text(recipe.get('title') or folder)
            title = clean_recipe_title(raw_title) or folder
            
            # 食材提取
            ingredients = []
            for item in recipe.get('major', []):
                t = clean_text(item.get('title', ''))
                n = clean_text(item.get('note', ''))
                if t:
                    ingredients.append(f"{t} {n}".strip())
            for item in recipe.get('minor', []):
                t = clean_text(item.get('title', ''))
                n = clean_text(item.get('note', ''))
                if t:
                    ingredients.append(f"{t} {n}".strip())
                    
            # 步骤提取
            steps = []
            for step in recipe.get('cookstep', []):
                content = clean_text(step.get('content', ''))
                content = re.sub(r'^步骤\s*\d+\s*', '', content)
                content = re.sub(r'^\d+[\.、\s]\s*', '', content)
                if content and len(content) > 1 and not any(k in content for k in ['展开阅读全文', '点击查看']):
                    steps.append(content)
                    
            # 小贴士
            tips_text = clean_text(recipe.get('tips', ''))
            tips_text = tips_text.replace('做菜好吃都有技巧，我的每道菜都有小妙招，大家搜索“豆果”可以直接查看我的菜谱！', '').strip()
            
            # 封面图片下载
            photo_url = recipe.get('photo_path') or recipe.get('original_photo_path') or recipe.get('image') or recipe.get('thumb_path')
            
            if photo_url:
                photo_url = photo_url.replace('http://', 'https://')
                try:
                    r_img = requests.get(photo_url, headers=HEADERS, impersonate='chrome120', timeout=15)
                    if r_img.status_code == 200 and len(r_img.content) > 1000:
                        with open(cover_path, "wb") as f_cov:
                            f_cov.write(r_img.content)
                        h = hashlib.md5(r_img.content).hexdigest()
                        hashes.add(h)
                except Exception as e:
                    print(f"   [!] 图片下载失败 ({title}): {e}")
                    
            # 流派与分类
            ings_str = " ".join(ingredients)
            diet = detect_diet(title, ings_str)
            category = detect_category(title)
            
            # 生成新 README.md
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
                f"- **來源平台 / Source**：[豆果美食 · 素食專區](https://www.douguo.com/cookbook/{cid}.html)",
                "",
                "## 🌿 食材及佐料清單 / Ingredients",
            ]
            for ing in ingredients:
                md_lines.append(f"- {ing}")
                
            md_lines.extend([
                "",
                "## 🍳 烹飪步驟 / Step-by-Step Cooking Steps",
            ])
            for s_i, st in enumerate(steps, 1):
                md_lines.append(f"{s_i}. {st}")
                
            if tips_text:
                md_lines.extend([
                    "",
                    "## 💡 大廚美味秘訣 / Chef's Tips",
                    f"- {tips_text}",
                ])
                
            md_lines.extend([
                "",
                "---",
                "*食譜歸檔時間：2026-08-21 · 來源：豆果美食 (www.douguo.com)*"
            ])
            
            with open(md_path, "w", encoding="utf-8") as f_out:
                f_out.write("\n".join(md_lines))
                
            print(f"   [✓] 成功更新: [{diet}] {title} ({len(ingredients)} 食材, {len(steps)} 步骤)")
            success += 1
            
        except Exception as e:
            print(f"   [!] 处理异常 ({folder}): {e}")
            
        # 严格限速：每抓取一个菜谱至少等待 1.1 秒，绝不小于 1 秒
        time.sleep(1.1)
        
    print(f"=== 修复完成！成功更新 {success} / {total} 道食谱，独立唯一封面图数: {len(hashes)} ===")

if __name__ == "__main__":
    refetch_and_fix_all()
