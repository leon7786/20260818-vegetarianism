import os
import re
import json
import urllib.parse
from curl_cffi import requests
from bs4 import BeautifulSoup

TARGET_BASE = "/root/1CT-Share/20260818-vegetarianism/recipe/www.knorr.com"

SAMPLE_URLS = [
    "https://www.knorr.com/tw/r/%E8%95%88%E8%8F%87%E5%8D%97%E7%93%9C%E7%B4%A0%E9%BA%B5.html/159588",
    "https://www.knorr.com/tw/r/%E9%AE%AE%E8%8F%87%E8%B1%86%E8%85%90%E7%85%B2(%E7%B4%A0).html/176042"
]

def clean_time(time_str):
    if not time_str:
        return "未標註"
    m = re.findall(r'(\d+)M', time_str)
    if m:
        return f"{m[0]} 分鐘"
    h = re.findall(r'(\d+)H', time_str)
    if h:
        return f"{h[0]} 小時"
    return time_str.replace("PT", "").replace("M", "分鐘").replace("H", "小時")

def scrape_recipe(url):
    print(f"[*] 正在抓取: {url}")
    headers = {
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.knorr.com/tw/recipe-ideas/%E6%96%99%E7%90%86%E7%A8%AE%E9%A1%9E/%E7%B4%A0%E9%A3%9F%E9%A3%9F%E8%AD%9C.html"
    }
    r = requests.get(url, impersonate="chrome120", headers=headers)
    if r.status_code != 200:
        print(f"[!] 抓取失敗，狀態碼: {r.status_code}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    
    recipe_data = None
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string)
            if isinstance(data, dict) and data.get("@type") == "Recipe":
                recipe_data = data
                break
        except Exception:
            continue
            
    if not recipe_data:
        print(f"[!] 未找到 Schema.org Recipe 數據")
        return None

    name = recipe_data.get("name", "").strip()
    if not name:
        name = soup.title.string.strip() if soup.title else "未命名食譜"
    # 清理 Windows/Linux 檔案系統保留字元
    folder_name = re.sub(r'[\\/:*?"<>|]', '_', name)
    recipe_dir = os.path.join(TARGET_BASE, folder_name)
    os.makedirs(recipe_dir, exist_ok=True)

    images = recipe_data.get("image", [])
    if isinstance(images, str):
        images = [images]
    
    img_filename = None
    if images and len(images) > 0:
        img_url = images[0]
        try:
            print(f"[*] 正在下載封面圖: {img_url}")
            img_resp = requests.get(img_url, impersonate="chrome120")
            if img_resp.status_code == 200:
                ext = ".jpg"
                if ".png" in img_url.lower():
                    ext = ".png"
                img_filename = f"cover{ext}"
                with open(os.path.join(recipe_dir, img_filename), "wb") as f:
                    f.write(img_resp.content)
                print(f"[✓] 封面圖保存成功: {img_filename}")
        except Exception as e:
            print(f"[!] 圖片下載失敗: {e}")

    # 解析用料
    ingredients = recipe_data.get("recipeIngredient", [])
    
    # 解析步驟
    instructions = recipe_data.get("recipeInstructions", [])
    step_texts = []
    if isinstance(instructions, list):
        for item in instructions:
            if isinstance(item, dict):
                if item.get("@type") == "HowToStep":
                    step_texts.append(item.get("text", "").strip())
                elif item.get("@type") == "HowToSection":
                    for sub in item.get("itemListElement", []):
                        if isinstance(sub, dict):
                            step_texts.append(sub.get("text", "").strip())
                        elif isinstance(sub, str):
                            step_texts.append(sub.strip())
            elif isinstance(item, str):
                step_texts.append(item.strip())
    elif isinstance(instructions, str):
        step_texts = [s.strip() for s in instructions.split("\n") if s.strip()]

    # 基本信息
    prep_time = clean_time(recipe_data.get("prepTime"))
    cook_time = clean_time(recipe_data.get("cookTime"))
    total_time = clean_time(recipe_data.get("totalTime"))
    yield_servings = recipe_data.get("recipeYield", "未標註")
    desc = recipe_data.get("description", "").strip()

    # 構造 Markdown 內容
    md_lines = [
        f"# {name}",
        "",
    ]
    if img_filename:
        md_lines.extend([
            f"![{name}]({img_filename})",
            ""
        ])

    md_lines.extend([
        "## 📋 基本資訊",
        f"- **料理名稱**：{name}",
        f"- **份量**：{yield_servings} 人份" if str(yield_servings).isdigit() else f"- **份量**：{yield_servings}",
        f"- **準備時間**：{prep_time}",
        f"- **烹飪時間**：{cook_time}",
    ])
    if total_time != "未標註":
        md_lines.append(f"- **總計耗時**：{total_time}")
    md_lines.extend([
        f"- **來源網站**：[Knorr 康寶食譜官網]({url})",
        "",
        "## 🌿 食材清單"
    ])

    for ing in ingredients:
        md_lines.append(f"- {ing}")
    
    md_lines.extend([
        "",
        "## 🍳 烹飪步驟"
    ])

    for idx, step in enumerate(step_texts, 1):
        md_lines.append(f"{idx}. {step}")

    md_lines.extend([
        "",
        "## 💡 料理小貼士",
        f"- {desc}" if desc and desc != name else "- 推薦使用康寶純素 / 鮮味系列調味料，能快速提升蔬食鮮味與層次。",
        "",
        "---",
        f"*食譜歸檔時間：2026-08-20 · 來源：Knorr 康寶台灣官網*"
    ])

    md_content = "\n".join(md_lines)
    
    # 寫入 README.md 和 [食譜名].md
    md_path = os.path.join(recipe_dir, "README.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"[✓] 食譜文檔生成成功: {md_path}")
    return {
        "name": name,
        "dir": recipe_dir,
        "md_path": md_path,
        "img": img_filename,
        "ingredients": len(ingredients),
        "steps": len(step_texts)
    }

if __name__ == "__main__":
    for u in SAMPLE_URLS:
        scrape_recipe(u)
        print("-" * 50)
