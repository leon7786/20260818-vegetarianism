import os
import sys
import re
import json
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from curl_cffi import requests
from bs4 import BeautifulSoup

TARGET_BASE = "/root/1CT-Share/20260818-vegetarianism/recipe/vegan.gys.org.tw"

def clean_title(raw_title):
    c = raw_title.replace('｜', ' ').replace('【', ' ').replace('】', ' ').replace('✨', '').replace('#', '').strip()
    c = re.sub(r'^(家常料理|異國蔬食|素食年菜|素食年菜食譜|年菜料理|創意蔬食|主廚推薦|素肉料理|米飯料理|傳統料理|地方特色美食|義式料理|傳統小吃|日式料理|花椰菜米料理|燕麥奶系列|電鍋料理|湯品系列|甜品系列|烘焙甜點|涼拌料理|Vegan)\s*', '', c).strip()
    c = re.sub(r'\s*(觀音山蔬食館|龍德上師|Homemade dishes|Chinese New Year dishes recipes).*$', '', c).strip()
    c = re.sub(r'\s*\(?(全素|奶素|蛋素|蛋奶素|純素)\)?\s*$', '', c).strip()
    c = re.sub(r'[\\/:*?"<>|]', '_', c).strip()
    return c.strip() or "未命名食譜"

def scrape_one_gys_recipe(url):
    try:
        r = requests.get(url, impersonate="chrome120", timeout=15)
        if r.status_code != 200:
            print(f"[!] 請求失敗 ({r.status_code}): {url}")
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        h1 = soup.find("h1")
        raw_title = h1.text.strip() if h1 else (soup.title.string.strip() if soup.title else "未命名食譜")
        title = clean_title(raw_title)

        diet = "全素 Vegan"
        if "奶素" in raw_title:
            diet = "奶素 Lacto-Vegetarian"
        elif "蛋素" in raw_title:
            diet = "蛋素 Ovo-Vegetarian"
        elif "蛋奶素" in raw_title:
            diet = "蛋奶素 Ovo-Lacto"

        folder_name = title
        recipe_dir = os.path.join(TARGET_BASE, folder_name)
        os.makedirs(recipe_dir, exist_ok=True)

        # 封面圖
        img_filename = "cover.jpg"
        cover_path = os.path.join(recipe_dir, img_filename)
        
        # 尋找高清圖源
        if not os.path.exists(cover_path) or os.path.getsize(cover_path) < 1000:
            og_img = soup.find("meta", property="og:image")
            img_url = og_img.get("content") if og_img else None
            
            if not img_url:
                for img in soup.find_all("img"):
                    src = img.get("data-src") or img.get("src")
                    if src and ("/uploads/" in src or "/CDN/" in src) and not "logo" in src.lower():
                        img_url = src
                        break

            if img_url:
                try:
                    clean_img_url = re.sub(r'-\d+x\d+(\.[a-zA-Z]+)$', r'\1', img_url)
                    img_resp = requests.get(clean_img_url, impersonate="chrome120", timeout=15)
                    if img_resp.status_code != 200:
                        img_resp = requests.get(img_url, impersonate="chrome120", timeout=15)
                    
                    if img_resp.status_code == 200:
                        with open(cover_path, "wb") as f:
                            f.write(img_resp.content)
                except Exception as e:
                    print(f"[!] 圖片下載出錯 ({url}): {e}")

        content_div = soup.find("div", class_="entry-content")
        raw_text = content_div.get_text("\n", strip=True) if content_div else ""

        md_lines = [
            f"# {title}",
            "",
            f"![{title}]({img_filename})",
            "",
            "## 📋 基本資訊 / Recipe Overview",
            f"- **料理名稱**：{title}",
            f"- **原始標題**：{raw_title}",
            f"- **素食流派 / Diet**：{diet}",
            f"- **來源平台 / Source**：[觀音山 · 素食料理簡單做]({url})",
            "",
            "## 📖 食譜圖文詳情 (中英雙語對照)",
            "",
            raw_text,
            "",
            "---",
            f"*食譜歸檔時間：2026-08-20 · 來源：觀音山素食料理簡單做 (vegan.gys.org.tw)*"
        ]

        md_path = os.path.join(recipe_dir, "README.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        print(f"[✓] 成功歸檔: {title} ({url})")
        return {
            "title": title,
            "raw_title": raw_title,
            "diet": diet,
            "dir": recipe_dir,
            "url": url
        }
    except Exception as e:
        print(f"[!] 抓取出錯: {url}, 原因: {e}")
        return None

def process_batch_file(json_file_path, max_workers=4):
    if not os.path.exists(json_file_path):
        print(f"Batch file not found: {json_file_path}")
        return []
    
    with open(json_file_path, "r", encoding="utf-8") as f:
        urls = json.load(f)

    print(f"=== 開始處理批次: {json_file_path} (共 {len(urls)} 個食譜) ===")
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(scrape_one_gys_recipe, u): u for u in urls}
        for future in as_completed(future_to_url):
            u = future_to_url[future]
            try:
                data = future.result()
                if data:
                    results.append(data)
            except Exception as exc:
                print(f"[!] 異常: {u} 生成了例外: {exc}")

    print(f"=== 批次 {json_file_path} 處理完成: 成功 {len(results)} / {len(urls)} ===")
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        batch_file = sys.argv[1]
        process_batch_file(batch_file)
    else:
        print("Usage: python batch_crawler_gys.py <batch_file.json>")
