import os
import re
import json
import urllib.parse
from curl_cffi import requests
from bs4 import BeautifulSoup

TARGET_BASE = "/root/1CT-Share/20260818-vegetarianism/recipe/www.justgreenmall.com"
RECIPE_ROOT = "/root/1CT-Share/20260818-vegetarianism/recipe"

RECIPES_META = [
    {
        "url": "https://www.justgreenmall.com/blog/posts/vegan-dongpo-pork-recipe",
        "title": "紅燒素東坡寶",
        "title_hans": "红烧素东坡宝",
        "title_en": "Braised Vegan Dongpo Pork",
        "keywords_en": "braised vegan dongpo pork belly soy protein plant-based banquet chinese",
        "category": "中式料理 / 精緻熱菜",
        "diet": "全素 Vegan",
        "servings": "3-4 人份",
        "prep_time": "10 分鐘",
        "cook_time": "20 分鐘",
        "total_time": "30 分鐘",
        "image_url": "https://img.shoplineapp.com/media/image_clips/66cbf0a2708b7be8cf049b66/original.png?1724641442"
    },
    {
        "url": "https://www.justgreenmall.com/blog/posts/vegan-curry-snow-peas-rice-1",
        "title": "素咖喱北海雪片燴飯",
        "title_hans": "素咖喱北海雪片烩饭",
        "title_en": "Vegan Curry Snow Peas Rice with Plant Fish Flakes",
        "keywords_en": "vegan curry snow peas rice stewed curry plant fish flakes japanese curry",
        "category": "異國料理 / 咖喱燴飯",
        "diet": "全素 Vegan",
        "servings": "2 人份",
        "prep_time": "5 分鐘",
        "cook_time": "15 分鐘",
        "total_time": "20 分鐘",
        "image_url": "https://img.shoplineapp.com/media/image_clips/66c40ec28365a9001f5b607f/original.png?1724124865"
    },
    {
        "url": "https://www.justgreenmall.com/blog/posts/" + urllib.parse.quote("【素食食譜】金黃脆香猴頭菇素煎餃-美味製作指南😍"),
        "title": "金黃脆香猴頭菇素煎餃",
        "title_hans": "金黄脆香猴头菇素煎饺",
        "title_en": "Golden Crispy Lion's Mane Mushroom Vegan Potstickers",
        "keywords_en": "golden crispy lion mane mushroom vegan dumpling potstickers dim sum",
        "category": "點心料理 / 煎餃鍋貼",
        "diet": "全素 Vegan",
        "servings": "4-6 人份",
        "prep_time": "5 分鐘",
        "cook_time": "10 分鐘",
        "total_time": "15 分鐘",
        "image_url": "https://img.shoplineapp.com/media/image_clips/66d965885c57d500225c09c4/original.PNG?1725523335"
    },
    {
        "url": "https://www.justgreenmall.com/blog/posts/vege-soup-recipe-healthy-soy-lionhead",
        "title": "鮮香素獅子頭煲",
        "title_hans": "鲜香素狮子头煲",
        "title_en": "Braised Vegan Lion's Head Claypot Casserole",
        "keywords_en": "braised vegan lion head stew claypot soup casserole chinese vegetarian banquet",
        "category": "煲仔料理 / 經典煲湯",
        "diet": "全素 Vegan",
        "servings": "3-4 人份",
        "prep_time": "10 分鐘",
        "cook_time": "15 分鐘",
        "total_time": "25 分鐘",
        "image_url": "https://img.shoplineapp.com/media/image_clips/66cbec98b029030019d5d8c0/original.png?1724640407"
    }
]

def clean_text(s):
    if not s:
        return ""
    s = s.replace('\u200b', '').replace('\ufeff', '').replace('\u3000', ' ')
    s = re.sub(r'[\r\t]', ' ', s)
    s = re.sub(r' +', ' ', s)
    return s.strip()

def scrape_justgreenmall():
    os.makedirs(TARGET_BASE, exist_ok=True)
    results = []

    for item in RECIPES_META:
        title = item["title"]
        url = item["url"]
        print(f"[*] 正在抓取 JustGreen Mall: {title} ({url})")

        recipe_dir = os.path.join(TARGET_BASE, title)
        os.makedirs(recipe_dir, exist_ok=True)

        # 下載高清原圖
        cover_path = os.path.join(recipe_dir, "cover.jpg")
        img_url = item["image_url"]
        try:
            r_img = requests.get(img_url, impersonate="chrome120", timeout=15)
            if r_img.status_code == 200:
                with open(cover_path, "wb") as f:
                    f.write(r_img.content)
                print(f"[✓] 封面圖已下載: {os.path.getsize(cover_path)} bytes")
        except Exception as e:
            print(f"[!] 下載封面圖失敗: {e}")

        # 抓取網頁內容
        r = requests.get(url, impersonate="chrome120", timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        post_body = soup.find('div', class_=re.compile(r'blog-post-content|post-content|fr-view|custom-page-content', re.I))
        if not post_body:
            post_body = soup.find('article') or soup.find('main')
        
        raw_text = post_body.get_text("\n", strip=True) if post_body else ""

        # 根據具體菜譜解析食材與步驟
        ingredients = []
        steps = []
        tips = ""

        if title == "紅燒素東坡寶":
            ingredients = [
                "素東坡肉丁 300克",
                "青江菜 200克",
                "薑片 3片",
                "八角 2個",
                "桂皮 1小塊",
                "冰糖 30克",
                "生抽 2湯匙",
                "老抽 1湯匙",
                "素蠔油 1湯匙",
                "麻油 1茶匙",
                "水 500毫升",
                "植物油 適量"
            ]
            steps = [
                "【備料】將素東坡肉丁用水輕輕沖洗，瀝乾水分；青江菜洗淨汆燙擺盤備用。",
                "【煎香】熱鑊下少量植物油，將素東坡肉丁煎至表面微黃定型出香。",
                "【爆香香料】鑊中留底油，加入薑片、八角和桂皮小火炒出濃郁香氣。",
                "【炒糖色與燜煮】加入冰糖慢火炒融，倒入生抽、老抽、素蠔油與500毫升水煮沸，放入素東坡肉丁轉小火慢燉15分鐘入味。",
                "【大火收汁】轉大火將湯汁收至濃稠紅亮，淋上少許麻油提亮，盛入鋪有青江菜的盤中即可享用。"
            ]
            tips = "素東坡肉丁以大豆植物蛋白製成，口感醇厚吸汁，青江菜可依當季喜好替換為小白菜或西蘭花。"

        elif title == "素咖喱北海雪片燴飯":
            ingredients = [
                "素北海雪片 200克",
                "工研咖喱 1塊",
                "熱白米飯 1碗",
                "四季豆/豆角 1條 (切丁)",
                "紅辣椒 1條 (切丁)",
                "老薑絲 15克",
                "芝麻油 1湯匙",
                "生抽 1茶匙",
                "海鹽 1/2茶匙",
                "糖 1/2茶匙",
                "白胡椒粉 少許",
                "清水 1碗"
            ]
            steps = [
                "【備料】素北海雪片解凍切塊，豆角切小丁，紅辣椒切碎，生薑切細絲。",
                "【熱鍋爆香】熱鑊倒入芝麻油，加入薑絲與辣椒丁爆香。",
                "【煎炒主料】加入素北海雪片與豆角丁，翻炒2-3分鐘至微金黃。",
                "【調配咖喱】倒入1碗清水煮沸，加入工研咖喱塊與生抽、糖調味，小火攪拌至咖喱完全融化濃稠。",
                "【燴飯盛盤】將濃郁的咖喱雪片淋在熱騰騰的白米飯上即可享用。"
            ]
            tips = "素北海雪片植物蛋白富含纖維，類似白身魚肉口感，搭配工研咖喱濃醇香辣，非常開胃。"

        elif title == "金黃脆香猴頭菇素煎餃":
            ingredients = [
                "猴頭菇手工純素水餃 20-24個",
                "植物油 2-3湯匙",
                "清水 100-150毫升",
                "太白粉水 1湯匙 (勾冰花薄脆)",
                "經典沾醬：純釀黑醋、生抽、薑絲、辣油"
            ]
            steps = [
                "【熱鍋排餃】平底不沾鍋倒入2湯匙植物油，中火加熱均勻，將猴頭菇水餃整齊排入鍋中。",
                "【煎出脆底】中火煎約2分鐘，底部呈現微金黃色澤。",
                "【加水燜煮】倒入約100-150毫升清水（或稀薄太白粉水），立即蓋上鍋蓋，轉中小火燜煎6-8分鐘蒸熟內餡。",
                "【開蓋收脆】開蓋轉中大火，讓水分完全蒸發，煎至底部形成金黃酥脆的冰花脆皮即可起鍋。"
            ]
            tips = "純植物配方猴頭菇水餃鮮嫩多汁，煎餃時加蓋水煎能鎖住菇菌鮮香，出鍋趁熱蘸薑醋食用風味最佳。"

        elif title == "鮮香素獅子頭煲":
            ingredients = [
                "紅燒素獅子頭 8個",
                "新鮮生菜/結球萵苣 1棵",
                "鮮冬菇 200克",
                "蔬菜清湯 800毫升",
                "老薑片 3片",
                "植物油 2湯匙",
                "素蠔油 1湯匙",
                "老抽 1/2茶匙",
                "白胡椒粉 1/4茶匙",
                "麻油 1/2茶匙",
                "生粉水 1湯匙"
            ]
            steps = [
                "【備料】生菜洗淨撕大片鋪於砂鍋底；鮮冬菇去蒂表面刻花；生薑切片備用。",
                "【爆香煎菇】熱鍋下油，中小火爆香薑片與冬菇，煎出蕈菇香氣。",
                "【砂鍋慢煨】注入800ml蔬菜清湯與素獅子頭，加入素蠔油、老抽、白胡椒粉調味，大火煮沸後轉小火煨煮10分鐘入味。",
                "【勾芡淋油】淋入薄生粉水輕推勾薄芡，滴入麻油，倒入鋪有鮮生菜的砂鍋中即可熱騰騰上桌。"
            ]
            tips = "素獅子頭飽滿扎實，吸飽冬菇清湯與素蠔油精華，底部的生菜脆甜解膩，是全家人暖心滋補的經典煲湯。"

        # 生成 Markdown 文檔
        md_lines = [
            f"# {title} ({item['title_en']})",
            "",
            f"![{title}](cover.jpg)",
            "",
            "## 📋 基本資訊 / Recipe Overview",
            f"- **料理名稱 (繁體)**：{title}",
            f"- **料理名称 (简体)**：{item['title_hans']}",
            f"- **English Title**：{item['title_en']}",
            f"- **素食流派 / Diet**：{item['diet']}",
            f"- **料理分類 / Category**：{item['category']}",
            f"- **份量 / Servings**：{item['servings']}",
            f"- **準備時間 / Prep Time**：{item['prep_time']}",
            f"- **烹飪時間 / Cook Time**：{item['cook_time']}",
            f"- **總計耗時 / Total Time**：{item['total_time']}",
            f"- **來源平台 / Source**：[植境 JustGreen Mall]({url})",
            "",
            "## 🌿 食材清單 / Ingredients",
        ]
        for ing in ingredients:
            md_lines.append(f"- {ing}")

        md_lines.extend([
            "",
            "## 🍳 烹飪步驟 / Step-by-Step Cooking Steps",
        ])
        for idx, step in enumerate(steps, 1):
            md_lines.append(f"{idx}. {step}")

        md_lines.extend([
            "",
            "## 💡 大廚美味秘訣 / Chef's Tips",
            f"- {tips}",
            "",
            "## 📖 官方博客圖文原著詳情",
            "",
            raw_text,
            "",
            "---",
            f"*食譜歸檔時間：2026-08-20 · 來源：植境 JustGreen Mall (www.justgreenmall.com)*"
        ])

        md_path = os.path.join(recipe_dir, "README.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        record = {
            "id": f"jgm_{title}",
            "name": title,
            "name_hans": item["title_hans"],
            "name_en": item["title_en"],
            "keywords_en": item["keywords_en"],
            "category": item["category"],
            "diet": item["diet"],
            "servings": item["servings"],
            "prep_time": item["prep_time"],
            "cook_time": item["cook_time"],
            "total_time": item["total_time"],
            "ingredients": ingredients,
            "steps": steps,
            "desc": tips,
            "source_url": url,
            "image": f"recipe/www.justgreenmall.com/{title}/cover.jpg",
            "local_dir": f"www.justgreenmall.com/{title}"
        }
        results.append(record)
        print(f"[✓] 已成功歸檔 JustGreenMall 食譜: {title}")

    return results

if __name__ == "__main__":
    scrape_justgreenmall()
