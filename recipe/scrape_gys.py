import os
import re
import json
import urllib.parse
from curl_cffi import requests
from bs4 import BeautifulSoup

TARGET_BASE = "/root/1CT-Share/20260818-vegetarianism/recipe/vegan.gys.org.tw"

SAMPLE_GYS_URLS = [
    "https://vegan.gys.org.tw/three-cup-king-oyster-mushrooms20220114/",
    "https://vegan.gys.org.tw/%e6%b6%bc%e6%8b%8c%e8%8a%b1%e7%94%9f%e8%b1%86%e8%85%90%ef%bd%9c%e5%85%a8%e7%b4%a0/",
    "https://vegan.gys.org.tw/vegetable-pancakes20230113/"
]

def clean_title(raw_title):
    c = raw_title.replace('｜', ' ').replace('【', ' ').replace('】', ' ').replace('✨', '').replace('#', '').strip()
    c = re.sub(r'^(家常料理|異國蔬食|素食年菜|素食年菜食譜|年菜料理|創意蔬食|主廚推薦|素肉料理|Vegan)\s*', '', c).strip()
    c = re.sub(r'\s*(觀音山蔬食館|龍德上師|Homemade dishes|Chinese New Year dishes recipes).*$', '', c).strip()
    c = re.sub(r'\s*\(?(全素|奶素|蛋素|蛋奶素|純素)\)?\s*$', '', c).strip()
    c = re.sub(r'[\\/:*?"<>|]', '_', c).strip()
    return c or "未命名食譜"

def scrape_gys_recipe(url):
    print(f"[*] 正在抓取: {url}")
    try:
        r = requests.get(url, impersonate="chrome120")
        if r.status_code != 200:
            print(f"[!] 抓取失敗: {url} -> {r.status_code}")
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        h1 = soup.find("h1")
        raw_title = h1.text.strip() if h1 else soup.title.string.strip()
        title = clean_title(raw_title)

        diet = "全素 Vegan"
        if "奶素" in raw_title:
            diet = "奶素 Lacto-Vegetarian"
        elif "蛋素" in raw_title:
            diet = "蛋素 Ovo-Vegetarian"
        elif "蛋奶素" in raw_title:
            diet = "蛋奶素 Ovo-Lacto"

        recipe_dir = os.path.join(TARGET_BASE, title)
        os.makedirs(recipe_dir, exist_ok=True)

        og_img = soup.find("meta", property="og:image")
        img_url = og_img.get("content") if og_img else None
        
        img_filename = "cover.jpg"
        if img_url:
            try:
                img_resp = requests.get(img_url, impersonate="chrome120")
                if img_resp.status_code == 200:
                    with open(os.path.join(recipe_dir, img_filename), "wb") as f:
                        f.write(img_resp.content)
                    print(f"[✓] 封面圖下載成功: {img_url}")
            except Exception as e:
                print(f"[!] 圖片下載出錯: {e}")

        content_div = soup.find("div", class_="entry-content")
        raw_text = content_div.get_text("\n", strip=True) if content_div else ""

        md_lines = [
            f"# {title}",
            "",
            f"![{title}]({img_filename})",
            "",
            "## 📋 基本資訊",
            f"- **料理名稱**：{title}",
            f"- **素食流派**：{diet}",
            f"- **來源平台**：[觀音山 · 素食料理簡單做]({url})",
            "",
            "## 📖 食譜圖文詳情 (中英雙語)",
            "",
            raw_text,
            "",
            "---",
            f"*食譜歸檔時間：2026-08-20 · 來源：觀音山素食料理簡單做 (vegan.gys.org.tw)*"
        ]

        md_path = os.path.join(recipe_dir, "README.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        print(f"[✓] 歸檔成功: {recipe_dir}")
        return {
            "title": title,
            "diet": diet,
            "dir": recipe_dir,
            "url": url
        }
    except Exception as e:
        print(f"[!] 出錯: {url}, 原因: {e}")
        return None

if __name__ == "__main__":
    os.makedirs(TARGET_BASE, exist_ok=True)
    for u in SAMPLE_GYS_URLS:
        scrape_gys_recipe(u)
