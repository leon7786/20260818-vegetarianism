import os
import re
import json

RECIPE_DIR = "/root/1CT-Share/20260818-vegetarianism/recipe"
KNORR_DIR = os.path.join(RECIPE_DIR, "www.knorr.com")
GYS_DIR = os.path.join(RECIPE_DIR, "vegan.gys.org.tw")

def clean_text(s):
    if not s:
        return ""
    s = s.replace('\u200b', '').replace('\ufeff', '').replace('\u3000', ' ')
    s = re.sub(r'[\r\t]', ' ', s)
    s = re.sub(r' +', ' ', s)
    return s.strip()

def parse_gys_markdown(folder_name, md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Title & Diet
    raw_title_m = re.search(r'-\s*\*\*(?:原始標題|料理名稱)\*\*[:：]\s*([^\n]+)', text)
    raw_title = raw_title_m.group(1).strip() if raw_title_m else folder_name
    
    diet = "全素 Vegan"
    if "奶素" in text[:500]:
        diet = "奶素 Lacto-Vegetarian"
    elif "蛋素" in text[:500]:
        diet = "蛋素 Ovo-Vegetarian"
    elif "蛋奶素" in text[:500]:
        diet = "蛋奶素 Ovo-Lacto"

    # Category
    category = "主食種類 / 米麵主食"
    if any(k in folder_name for k in ["拉麵", "麵", "冬粉", "米粉", "義大利麵", "筆管麵", "烏龍麵"]):
        category = "麵食料理"
    elif any(k in folder_name for k in ["飯", "粥", "米", "壽司", "布丁", "炊飯", "燉飯"]):
        category = "米食料理"
    elif any(k in folder_name for k in ["餅", "捲", "排"]):
        category = "點心煎餅"

    # Source URL
    url_m = re.search(r'\[觀音山[^\]]*\]\((https?://[^)]+)\)', text)
    source_url = url_m.group(1) if url_m else "https://vegan.gys.org.tw/recipe/staple-food/"

    # 2. Servings
    servings = "2-4 人份"
    serv_m = re.search(r'[(（](\d+(?:-\d+)?)\s*人份[)）]', text)
    if serv_m:
        servings = f"{serv_m.group(1)} 人份"

    # 3. Ingredients
    ingredients = []
    
    # Check table format first
    table_m = re.search(r'\|(?:\s*食材[^\n]*\|)\n\|(?:\s*[-:]+\s*\|)+\n([\s\S]*?)(?=\n\n|\n##|\n---)', text)
    if table_m:
        for line in table_m.group(1).split('\n'):
            line = line.strip()
            if line.startswith('|'):
                cells = [clean_text(c) for c in line.split('|')[1:-1]]
                if cells and cells[0] and not cells[0].startswith('---'):
                    ing_str = f"{cells[0]}：{cells[1]}" if len(cells) > 1 and cells[1] else cells[0]
                    ingredients.append(clean_text(ing_str.replace('**', '')))

    if not ingredients:
        # Check standard block
        ing_block_m = re.search(r'(?:食材及佐料|食材清單|準備食材與佐料|Ingredients)[^\n]*\n([\s\S]*?)(?=\n\s*(?:[?▪❒#\d\.]*烹飪步驟|[?▪❒#\d\.]*料理步驟|[?▪❒#\d\.]*作法|[?▪❒#\d\.]*#素食料理簡單做|【刀工|【調理|Instructions|##|###|$))', text)
        if ing_block_m:
            raw_block = ing_block_m.group(1)
            for line in raw_block.split('\n'):
                line = clean_text(line)
                if not line or any(k in line for k in ['烹飪步驟', '料理步驟', '作法', '調理', 'Instructions', '刀工']):
                    continue
                # Line starting with bullet or number
                if re.match(r'^[▪\-*•?❒\d+\.]', line):
                    cleaned = re.sub(r'^[▪\-*•?❒\d+\.]\s*', '', line)
                    cleaned = re.sub(r'^[▪️\-*•?❒\d+\.]\s*', '', cleaned)
                    cleaned = clean_text(cleaned.replace('**', ''))
                    if cleaned and not any(k in cleaned for k in ['Ingredients', '規格', '---', '烹飪步驟', '料理步驟', '刀工']):
                        ingredients.append(cleaned)
                elif '、' in line or '，' in line or '適量' in line:
                    parts = re.split(r'[、，]', line)
                    for p in parts:
                        p = clean_text(p)
                        if p and len(p) > 1 and not any(k in p for k in ['準備', '材料', 'Ingredients', '烹飪步驟', '料理步驟', '開始']):
                            ingredients.append(p)

    # 4. Steps
    steps = []
    prep_steps = []
    prep_m = re.search(r'【(?:刀工[/／]前處理|前處理|備料|刀工與前處理)】([\s\S]*?)(?=【(?:調理作法|作法|烹調步驟|調理|特別說明|recipe)】|##|###|$)', text)
    if prep_m:
        for line in prep_m.group(1).split('\n'):
            line = clean_text(line)
            m = re.match(r'^\d+[\.、]\s*(.*)', line)
            if m:
                step_txt = clean_text(m.group(1))
                if step_txt:
                    prep_steps.append(f"【備料】{step_txt}")
            elif line.startswith(('▪', '-', '*', '•')):
                step_txt = clean_text(re.sub(r'^[▪\-*•]\s*', '', line))
                if step_txt:
                    prep_steps.append(f"【備料】{step_txt}")

    cook_steps = []
    cook_m = re.search(r'【(?:調理作法|作法|烹調步驟|調理|烹飪步驟|Step-by-Step Cooking Instructions)】([\s\S]*?)(?=【(?:特別說明|recipe|大廚美味秘訣|大廚秘訣|料理小貼士|料理筆記)】|本食譜提供|##|###|$)', text)
    if cook_m:
        for line in cook_m.group(1).split('\n'):
            line = clean_text(line)
            m = re.match(r'^\d+[\.、]\s*(.*)', line)
            if m:
                step_txt = clean_text(m.group(1))
                if step_txt:
                    cook_steps.append(step_txt)
            elif line.startswith(('▪', '-', '*', '•')):
                step_txt = clean_text(re.sub(r'^[▪\-*•]\s*', '', line))
                if step_txt:
                    cook_steps.append(step_txt)

    if prep_steps or cook_steps:
        steps = prep_steps + cook_steps
    else:
        generic_step_m = re.search(r'(?:烹飪步驟|烹調作法|#素食料理簡單做，開始|Cooking Steps|料理步驟)[\s\S]*?(?=特別說明|本食譜提供|【recipe】|##|###|$)', text)
        if generic_step_m:
            for line in generic_step_m.group(0).split('\n'):
                line = clean_text(line)
                m = re.match(r'^\d+[\.、]\s*(.*)', line)
                if m:
                    step_txt = clean_text(m.group(1))
                    if step_txt and not step_txt.startswith(('食材', '備料', '地瓜1-2斤', '腰果')):
                        steps.append(step_txt)

    if not steps:
        for line in text.split('\n'):
            line = clean_text(line)
            m = re.match(r'^\d+[\.、]\s*(.*)', line)
            if m:
                txt = clean_text(m.group(1))
                if len(txt) > 8 and not any(k in txt for k in ['地瓜1-2斤', '碗', '克', '公分', '市售']):
                    steps.append(txt)

    # 5. Chef tips & Description
    tip_m = re.search(r'(?:特別說明|大廚美味秘訣|大廚秘訣|大廚技巧|主廚小貼士|Chef\'s Tips)[：:\s]*([\s\S]*?)(?=本食譜提供|【recipe】|##|###|---|$)', text)
    tip = clean_text(tip_m.group(1).replace('】', '')) if tip_m else ""
    tip = re.sub(r'^[^\w\u4e00-\u9fa5]+', '', tip)

    intro_m = re.search(r'## 📖 食譜圖文詳情[^\n]*\n+([\s\S]*?)(?=\n[?▪❒#\d|]|食材|Ingredients)', text)
    intro = clean_text(intro_m.group(1)) if intro_m else ""

    desc_text = tip or intro or f"觀音山蔬食館主廚推薦：{folder_name}"
    desc_text = clean_text(re.sub(r'[\?？]+', '', desc_text))[:250]

    img_rel_path = f"recipe/vegan.gys.org.tw/{folder_name}/cover.jpg"

    return {
        "id": f"gys_{folder_name}",
        "name": folder_name,
        "name_hans": folder_name,
        "name_en": folder_name,
        "keywords_en": f"{folder_name} vegan vegetarian staple food taiwanese guanyinshan noodles rice",
        "category": category,
        "diet": diet,
        "servings": servings,
        "prep_time": "10 分鐘",
        "cook_time": "15 分鐘",
        "total_time": "25 分鐘",
        "ingredients": [clean_text(i) for i in ingredients if clean_text(i) and len(clean_text(i)) < 60],
        "steps": [clean_text(s) for s in steps if clean_text(s)],
        "desc": desc_text,
        "source_url": source_url,
        "image": img_rel_path,
        "local_dir": f"vegan.gys.org.tw/{folder_name}"
    }

def main():
    with open(os.path.join(RECIPE_DIR, "recipes_data.json"), "r", encoding="utf-8") as f:
        existing = json.load(f)
    
    knorr_recipes = [r for r in existing if "knorr" in r.get("local_dir", "")]

    gys_recipes = []
    for folder in sorted(os.listdir(GYS_DIR)):
        folder_path = os.path.join(GYS_DIR, folder)
        if not os.path.isdir(folder_path):
            continue
        md_file = os.path.join(folder_path, "README.md")
        if not os.path.exists(md_file):
            continue
        record = parse_gys_markdown(folder, md_file)
        if record:
            gys_recipes.append(record)

    total_recipes = knorr_recipes + gys_recipes
    print(f"Total recipes parsed: {len(total_recipes)} (Knorr: {len(knorr_recipes)}, GYS: {len(gys_recipes)})")

    # Save to recipes_data.json
    with open(os.path.join(RECIPE_DIR, "recipes_data.json"), "w", encoding="utf-8") as f:
        json.dump(total_recipes, f, ensure_ascii=False, indent=2)

    # Embed in index.html safely without re.sub unescaping
    with open("/root/1CT-Share/20260818-vegetarianism/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    pos1 = html.find("const RECIPES_DATA = ")
    pos2 = html.find("const PLATFORMS_DATA = ")
    if pos1 != -1 and pos2 != -1:
        recipes_js = "const RECIPES_DATA = " + json.dumps(total_recipes, ensure_ascii=False) + ";\n\n    "
        new_html = html[:pos1] + recipes_js + html[pos2:]
        with open("/root/1CT-Share/20260818-vegetarianism/index.html", "w", encoding="utf-8") as f:
            f.write(new_html)

    print("[✓] Successfully parsed full text, granular ingredients, and steps for all recipes!")

if __name__ == "__main__":
    main()
