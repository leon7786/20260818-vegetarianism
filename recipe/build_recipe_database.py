import os
import re
import json
from curl_cffi import requests
from bs4 import BeautifulSoup

TARGET_BASE = "/root/1CT-Share/20260818-vegetarianism/recipe/www.knorr.com"
RECIPE_ROOT = "/root/1CT-Share/20260818-vegetarianism/recipe"

ALL_KNORR_URLS = [
    "https://www.knorr.com/tw/r/%E8%95%88%E8%8F%87%E5%8D%97%E7%93%9C%E7%B4%A0%E9%BA%B5.html/159588",
    "https://www.knorr.com/tw/r/%E9%AE%AE%E8%8F%87%E8%B1%86%E8%85%90%E7%85%B2(%E7%B4%A0).html/176042",
    "https://www.knorr.com/tw/r/%E4%B8%89%E7%B5%B2%E8%B1%86%E8%85%90%E7%BE%B9(%E7%B4%A0).html/176044",
    "https://www.knorr.com/tw/r/%E6%B6%BC%E6%8B%8C%E7%B4%A0%E4%BB%80%E9%8C%A6(%E7%B4%A0).html/176045",
    "https://www.knorr.com/tw/r/%E7%82%B8%E6%B5%B7%E8%8B%94%E8%85%90%E7%9A%AE%E5%8D%B7-(%E5%85%A8%E7%B4%A0).html/179568",
    "https://www.knorr.com/tw/r/%E9%B9%B9%E9%85%A5%E8%8F%87%E8%8F%87-(%E8%9B%8B%E5%A5%B6%E7%B4%A0).html/188824",
    "https://www.knorr.com/tw/r/%E8%8F%87%E8%8F%87%E7%B4%A0%E7%B1%B3%E7%B3%95.html/255111",
    "https://www.knorr.com/tw/r/%E8%8F%8C%E8%8F%87%E5%8D%97%E7%93%9C%E6%B9%AF(%E7%B4%A0).html/229648",
    "https://www.knorr.com/tw/r/%E5%A6%82%E6%84%8F%E5%86%AC%E7%93%9C%E5%8D%B7.html/255110",
    "https://www.knorr.com/tw/r/%E9%87%91%E6%B2%99%E8%B1%86%E8%85%90.html/232937"
]

MULTILINGUAL_MAP = {
    "蕈菇南瓜素麵": {
        "name_zh_hans": "蕈菇南瓜素面",
        "name_en": "Mushroom Pumpkin Vegetarian Noodles",
        "keywords_en": "mushroom pumpkin vegetarian noodle soba soup noodles",
        "category": "麵食 / 主食",
        "diet": "全素 Vegan"
    },
    "鮮菇豆腐煲(素)": {
        "name_zh_hans": "鲜菇豆腐煲(素)",
        "name_en": "Fresh Mushroom Tofu Claypot",
        "keywords_en": "fresh mushroom tofu claypot casserole braised tofu stew",
        "category": "煲仔 / 熱炒",
        "diet": "奶素 Lacto-Vegetarian"
    },
    "三絲豆腐羹(素)": {
        "name_zh_hans": "三丝豆腐羹(素)",
        "name_en": "Three Shreds Tofu Thick Soup",
        "keywords_en": "three shreds tofu thick soup broth羹",
        "category": "羹湯 / 湯品",
        "diet": "全素 Vegan"
    },
    "涼拌素什錦(素)": {
        "name_zh_hans": "凉拌素什锦(素)",
        "name_en": "Cold Tossed Assorted Vegetarian Salad",
        "keywords_en": "cold dressed tossed assorted vegetarian vegetable salad appetizers",
        "category": "涼拌 / 前菜",
        "diet": "全素 Vegan"
    },
    "炸海苔腐皮卷 (全素)": {
        "name_zh_hans": "炸海苔腐皮卷(全素)",
        "name_en": "Crispy Nori Bean Curd Skin Rolls (Vegan)",
        "keywords_en": "crispy fried seaweed nori bean curd skin tofu skin roll dim sum vegan fupi",
        "category": "炸物 / 點心",
        "diet": "純素 Vegan"
    },
    "鹹酥菇菇 (蛋奶素)": {
        "name_zh_hans": "咸酥菇菇(蛋奶素)",
        "name_en": "Taiwanese Crispy Fried Mushrooms (Ovo-Lacto)",
        "keywords_en": "taiwanese crispy salt and pepper fried mushrooms street food xiansu gugu",
        "category": "炸物 / 小吃",
        "diet": "蛋奶素 Ovo-Lacto"
    },
    "菇菇素米糕": {
        "name_zh_hans": "菇菇素米糕",
        "name_en": "Savory Mushroom Vegetarian Sticky Rice Cake",
        "keywords_en": "mushroom vegetarian sticky glutinous rice cake traditional",
        "category": "米食 / 點心",
        "diet": "全素 Vegan"
    },
    "菌菇南瓜湯(素)": {
        "name_zh_hans": "菌菇南瓜汤(素)",
        "name_en": "Creamy Mushroom Pumpkin Soup (Vegetarian)",
        "keywords_en": "creamy mushroom pumpkin puree soup potage",
        "category": "湯品 / 西式濃湯",
        "diet": "奶素 Lacto-Vegetarian"
    },
    "如意冬瓜卷": {
        "name_zh_hans": "如意冬瓜卷",
        "name_en": "Ruyi Winter Melon Rolls with Mushroom Stuffing",
        "keywords_en": "ruyi winter melon roll stuffed banquet vegetarian gourmet",
        "category": "精緻熱菜 / 宴席料理",
        "diet": "全素 Vegan"
    },
    "金沙豆腐": {
        "name_zh_hans": "金沙豆腐",
        "name_en": "Golden Salted Egg Tofu",
        "keywords_en": "golden yolk salted egg tofu crispy soft stir fry",
        "category": "熱炒 / 經典家常",
        "diet": "蛋素 Ovo-Vegetarian"
    }
}

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

def scrape_all():
    os.makedirs(TARGET_BASE, exist_ok=True)
    all_recipes = []

    for url in ALL_KNORR_URLS:
        print(f"[*] 正在抓取: {url}")
        headers = {
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.knorr.com/tw/recipe-ideas/%E6%96%99%E7%90%86%E7%A8%AE%E9%A1%9E/%E7%B4%A0%E9%A3%9F%E9%A3%9F%E8%AD%9C.html"
        }
        try:
            r = requests.get(url, impersonate="chrome120", headers=headers)
            if r.status_code != 200:
                print(f"[!] 抓取失敗: {url} -> {r.status_code}")
                continue

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
                continue

            name = recipe_data.get("name", "").strip()
            if not name:
                name = soup.title.string.strip() if soup.title else "未命名食譜"

            folder_name = re.sub(r'[\\/:*?"<>|]', '_', name)
            recipe_dir = os.path.join(TARGET_BASE, folder_name)
            os.makedirs(recipe_dir, exist_ok=True)

            images = recipe_data.get("image", [])
            if isinstance(images, str):
                images = [images]
            
            img_filename = "cover.jpg"
            img_rel_path = f"recipe/www.knorr.com/{folder_name}/cover.jpg"
            if images and len(images) > 0:
                img_url = images[0]
                try:
                    img_resp = requests.get(img_url, impersonate="chrome120")
                    if img_resp.status_code == 200:
                        with open(os.path.join(recipe_dir, img_filename), "wb") as f:
                            f.write(img_resp.content)
                except Exception as e:
                    print(f"[!] 圖片下載錯誤: {e}")

            ingredients = recipe_data.get("recipeIngredient", [])
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

            prep_time = clean_time(recipe_data.get("prepTime"))
            cook_time = clean_time(recipe_data.get("cookTime"))
            total_time = clean_time(recipe_data.get("totalTime"))
            yield_servings = recipe_data.get("recipeYield", "2-4 人份")
            desc = recipe_data.get("description", "").strip()

            meta = MULTILINGUAL_MAP.get(name, {
                "name_zh_hans": name,
                "name_en": name,
                "keywords_en": "vegetarian recipe",
                "category": "蔬食料理",
                "diet": "素食 Vegetarian"
            })

            # 寫入單個食譜 Markdown
            md_lines = [
                f"# {name} ({meta['name_en']})",
                "",
                f"![{name}]({img_filename})",
                "",
                "## 📋 基本資訊 / Recipe Overview",
                f"- **料理名稱 (繁體)**：{name}",
                f"- **料理名称 (简体)**：{meta['name_zh_hans']}",
                f"- **English Title**：{meta['name_en']}",
                f"- **素食流派 / Diet**：{meta['diet']}",
                f"- **料理分類 / Category**：{meta['category']}",
                f"- **份量 / Servings**：{yield_servings} 人份" if str(yield_servings).isdigit() else f"- **份量 / Servings**：{yield_servings}",
                f"- **準備時間 / Prep Time**：{prep_time}",
                f"- **烹飪時間 / Cook Time**：{cook_time}",
            ]
            if total_time != "未標註":
                md_lines.append(f"- **總計耗時 / Total Time**：{total_time}")
            md_lines.extend([
                f"- **來源網站 / Source**：[Knorr 康寶食譜官網]({url})",
                "",
                "## 🌿 食材清單 / Ingredients",
            ])
            for ing in ingredients:
                md_lines.append(f"- {ing}")

            md_lines.extend([
                "",
                "## 🍳 烹飪步驟 / Step-by-Step Cooking Steps",
            ])
            for idx, step in enumerate(step_texts, 1):
                md_lines.append(f"{idx}. {step}")

            md_lines.extend([
                "",
                "## 💡 料理小貼士 / Chef's Tips",
                f"- {desc}" if desc and desc != name else "- 推薦使用康寶鮮味高湯或素食調味料，快速提鮮提升料理層次。",
                "",
                "---",
                "*食譜歸檔時間：2026-08-20 · 收錄於 20260818-vegetarianism 本地菜譜庫*"
            ])

            md_path = os.path.join(recipe_dir, "README.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("\n".join(md_lines))

            recipe_record = {
                "id": folder_name,
                "name": name,
                "name_hans": meta["name_zh_hans"],
                "name_en": meta["name_en"],
                "keywords_en": meta["keywords_en"],
                "category": meta["category"],
                "diet": meta["diet"],
                "servings": str(yield_servings),
                "prep_time": prep_time,
                "cook_time": cook_time,
                "total_time": total_time,
                "ingredients": ingredients,
                "steps": step_texts,
                "desc": desc,
                "source_url": url,
                "image": img_rel_path,
                "local_dir": f"www.knorr.com/{folder_name}"
            }
            all_recipes.append(recipe_record)
            print(f"[✓] 已成功歸檔: {name}")
        except Exception as e:
            print(f"[!] 處理食譜失敗: {url}, 原因: {e}")

    # 生成 master index JSON
    index_json_path = os.path.join(RECIPE_ROOT, "recipes_data.json")
    with open(index_json_path, "w", encoding="utf-8") as f:
        json.dump(all_recipes, f, ensure_ascii=False, indent=2)
    print(f"[✓] 已輸出 recipes_data.json: {len(all_recipes)} 條食譜")

    # 生成方便搜尋引擎檢索的 master README.md / INDEX.md
    generate_master_readme(all_recipes)

def generate_master_readme(recipes):
    readme_path = os.path.join(RECIPE_ROOT, "README.md")
    lines = [
        "# 🌱 全球蔬食與素食精選食譜庫檢索索引 (Vegetarian & Vegan Recipe Master Index)",
        "",
        "> **說明**：本目錄為 Antigravity 素食導航項目的本地食譜庫，提供結構化 Markdown、高清成品圖與多語言（簡體 / 繁體 / 英文）檢索支援，方便搜尋引擎快速抓取索引與使用者本地查詢。",
        "",
        f"**當前已歸檔食譜數量**：`{len(recipes)}` 道精選素食料理",
        "",
        "---",
        "",
        "## 📚 食譜目錄總覽 (Master Recipe Catalog)",
        "",
        "| 序號 | 食譜名稱 (繁/簡/英) | 分類 / 流派 | 耗時 | 食材精選摘要 | 食譜詳情與圖文 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for idx, r in enumerate(recipes, 1):
        ing_summary = "、".join([i.split(" ")[0] for i in r["ingredients"][:4]])
        time_display = f"備料{r['prep_time']} / 烹飪{r['cook_time']}"
        link_md = f"[{r['name']}](www.knorr.com/{r['id']}/README.md)"
        lines.append(
            f"| {idx} | **{r['name']}**<br>*{r['name_hans']}*<br>`{r['name_en']}` | {r['category']}<br><span style='color:#15803d;'>{r['diet']}</span> | {time_display} | {ing_summary}... | {link_md} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 🔍 多語言關鍵字速查表 (Multilingual Search Matrix)",
        "",
        "| 中文繁體 (Traditional) | 中文简体 (Simplified) | English Keywords & Ingredients | 相關食譜連結 |",
        "| :--- | :--- | :--- | :--- |"
    ])

    for r in recipes:
        ing_all = ", ".join(r["ingredients"][:3])
        lines.append(
            f"| {r['name']} | {r['name_hans']} | {r['name_en']} ({r['keywords_en']}) | [{r['name']}](www.knorr.com/{r['id']}/README.md) |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 📂 資料夾目錄結構",
        "",
        "```text",
        "recipe/",
        "├── README.md               # 本檢索索引文件（提供搜索引擎爬蟲與全局多語言關鍵字矩陣）",
        "├── recipes_data.json       # 供前端 SPA 搜尋框即時中/英/繁檢索的結構化數據",
        "└── www.knorr.com/          # 康寶官方食譜庫",
    ])

    for r in recipes:
        lines.append(f"    ├── {r['id']}/")
        lines.append(f"    │   ├── README.md")
        lines.append(f"    │   └── cover.jpg")

    lines.extend([
        "```",
        "",
        "---",
        "*維護更新於 2026-08-20 · 綠意食光 素食權威知識庫*"
    ])

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[✓] 已成功生成搜索引擎專用檢索文件: {readme_path}")

if __name__ == "__main__":
    scrape_all()
