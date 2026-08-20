import os
import sys
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from curl_cffi import requests
from bs4 import BeautifulSoup

TARGET_BASE = "/root/1CT-Share/20260818-vegetarianism/recipe/vegan.gys.org.tw"

def clean_text(s):
    if not s:
        return ""
    s = s.replace('\u200b', '').replace('\ufeff', '').replace('\u3000', ' ')
    s = re.sub(r'[\r\t]', ' ', s)
    s = re.sub(r' +', ' ', s)
    return s.strip()

def clean_title(raw_title):
    c = raw_title.replace('｜', ' ').replace('【', ' ').replace('】', ' ').replace('✨', '').replace('#', '').strip()
    c = re.sub(r'^(家常料理|異國蔬食|素食年菜|素食年菜食譜|年菜料理|創意蔬食|主廚推薦|素肉料理|米飯料理|傳統料理|地方特色美食|義式料理|傳統小吃|日式料理|花椰菜米料理|燕麥奶系列|電鍋料理|湯品系列|甜品系列|烘焙甜點|涼拌料理|中式料理|輕食點心|涼拌小菜|主食種類|Vegan)\s*', '', c).strip()
    c = re.sub(r'\s*(觀音山蔬食館|龍德上師|Homemade dishes|Chinese New Year dishes recipes).*$', '', c).strip()
    c = re.sub(r'\s*\(?(全素|奶素|蛋素|蛋奶素|純素)\)?\s*$', '', c).strip()
    c = re.sub(r'[\\/:*?"<>|]', '_', c).strip()
    return c.strip() or "未命名食譜"

def scrape_category_recipe(url, category_name="蔬食料理"):
    try:
        r = requests.get(url, impersonate="chrome120", timeout=20)
        if r.status_code != 200:
            print(f"[!] 請求失敗 ({r.status_code}): {url}")
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        h1 = soup.find("h1")
        raw_title = clean_text(h1.text) if h1 else clean_text(soup.title.string if soup.title else "未命名食譜")
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

        # 封面圖 (未裁切原版大圖)
        cover_path = os.path.join(recipe_dir, "cover.jpg")
        candidate_urls = []
        og_img = soup.find("meta", property="og:image")
        if og_img and og_img.get("content"):
            candidate_urls.append(og_img.get("content"))
        
        # entry-content images
        entry_content = soup.find("div", class_="entry-content")
        if entry_content:
            for img in entry_content.find_all("img"):
                src = img.get("data-src") or img.get("src")
                if src and not "logo" in src.lower() and src not in candidate_urls:
                    candidate_urls.append(src)

        tile_img = soup.find("meta", attrs={"name": "msapplication-TileImage"})
        if tile_img and tile_img.get("content"):
            tile_url = tile_img.get("content")
            # Try removing cropped- prefix and dimension suffix
            uncropped = re.sub(r'cropped-(\d+)-\d+x\d+(\.[a-zA-Z]+)$', r'\1\2', tile_url)
            if uncropped not in candidate_urls:
                candidate_urls.append(uncropped)
            if tile_url not in candidate_urls:
                candidate_urls.append(tile_url)

        for img in soup.find_all("img"):
            src = img.get("data-src") or img.get("src")
            if src and ("/uploads/" in src or "/CDN/" in src) and not "logo" in src.lower():
                if src not in candidate_urls:
                    candidate_urls.append(src)

        img_downloaded = False
        for img_url in candidate_urls:
            try:
                clean_img_url = re.sub(r'-\d+x\d+(\.[a-zA-Z]+)$', r'\1', img_url)
                img_resp = requests.get(clean_img_url, impersonate="chrome120", timeout=15)
                if img_resp.status_code != 200:
                    img_resp = requests.get(img_url, impersonate="chrome120", timeout=15)
                
                if img_resp.status_code == 200 and len(img_resp.content) > 0:
                    with open(cover_path, "wb") as f:
                        f.write(img_resp.content)
                    img_downloaded = True
                    break
            except Exception as e:
                pass
        
        if not img_downloaded:
            print(f"[!] 圖片下載失敗或無可用圖片 ({title})")

        content_div = soup.find("div", class_="entry-content")
        raw_text = content_div.get_text("\n", strip=True) if content_div else ""

        # Markdown 結構化輸出
        md_lines = [
            f"# {title}",
            "",
            f"![{title}](cover.jpg)",
            "",
            "## 📋 基本資訊 / Recipe Overview",
            f"- **料理名稱**：{title}",
            f"- **原始標題**：{raw_title}",
            f"- **素食流派 / Diet**：{diet}",
            f"- **料理分類 / Category**：{category_name}",
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

        print(f"[✓] 成功歸檔: [{category_name}] {title}")
        return {
            "title": title,
            "raw_title": raw_title,
            "diet": diet,
            "category": category_name,
            "dir": recipe_dir,
            "url": url
        }
    except Exception as e:
        print(f"[!] 抓取出錯: {url}, 原因: {e}")
        return None

def process_category_file(json_file_path, max_workers=4):
    if not os.path.exists(json_file_path):
        print(f"File not found: {json_file_path}")
        return []
    with open(json_file_path, "r", encoding="utf-8") as f:
        cat_data = json.load(f)

    cat_name = cat_data.get("name", "蔬食料理")
    urls = cat_data.get("urls", [])

    print(f"=== 開始處理分類【{cat_name}】: 共 {len(urls)} 道食譜 ===")
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_category_recipe, u, cat_name): u for u in urls}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    print(f"=== 分類【{cat_name}】完成: 成功 {len(results)} / {len(urls)} ===")
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_category_file(sys.argv[1])
    else:
        print("Usage: python category_crawler.py <category_json_file>")
