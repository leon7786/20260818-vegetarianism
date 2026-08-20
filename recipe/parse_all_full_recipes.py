import os
import re
import json

RECIPE_DIR = "/root/1CT-Share/20260818-vegetarianism/recipe"
KNORR_DIR = os.path.join(RECIPE_DIR, "www.knorr.com")
GYS_DIR = os.path.join(RECIPE_DIR, "vegan.gys.org.tw")
JGM_DIR = os.path.join(RECIPE_DIR, "www.justgreenmall.com")
DOUGUO_DIR = os.path.join(RECIPE_DIR, "www.douguo.com")
XCF_DIR = os.path.join(RECIPE_DIR, "www.xiachufang.com")

def clean_text(s):
    if not s:
        return ""
    s = s.replace('\u200b', '').replace('\ufeff', '').replace('\u3000', ' ')
    s = re.sub(r'[\r\t]', ' ', s)
    s = re.sub(r' +', ' ', s)
    return s.strip()

def parse_markdown_recipe(platform_prefix, platform_domain, folder_name, md_path, default_cat="家常蔬食"):
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    title_m = re.search(r'^#\s*([^\n(（]+)', text)
    title = clean_text(title_m.group(1)) if title_m else folder_name

    raw_title_m = re.search(r'-\s*\*\*原始標題\*\*[:：]\s*([^\n]+)', text)
    raw_title = clean_text(raw_title_m.group(1)) if raw_title_m else title

    diet_m = re.search(r'-\s*\*\*素食流派 / Diet\*\*[:：]\s*([^\n]+)', text)
    diet = clean_text(diet_m.group(1)) if diet_m else "全素 Vegan"

    category_m = re.search(r'-\s*\*\*料理分類 / Category\*\*[:：]\s*([^\n]+)', text)
    category = clean_text(category_m.group(1)) if category_m else default_cat

    url_m = re.search(r'\[[^\]]+\]\((https?://[^)]+)\)', text)
    source_url = url_m.group(1) if url_m else f"https://{platform_domain}"

    servings = "2-4 人份"
    serv_m = re.search(r'-\s*\*\*份量 / Servings\*\*[:：]\s*([^\n]+)', text)
    if serv_m:
        servings = clean_text(serv_m.group(1))

    # Ingredients
    ingredients = []
    ing_block = re.search(r'## 🌿 食材(?:及佐料清單|清單)? / Ingredients([\s\S]*?)(?=## 🍳|## 🔪|## 💡|## 📖|---|$)', text)
    if ing_block:
        for line in ing_block.group(1).split('\n'):
            line = clean_text(line)
            if line.startswith(('-', '*', '▪', '•')):
                cleaned = clean_text(re.sub(r'^[▪\-*•]\s*', '', line))
                if cleaned and len(cleaned) < 80:
                    ingredients.append(cleaned)

    # Steps
    steps = []
    step_block = re.search(r'## 🍳 烹飪步驟 / Step-by-Step Cooking Steps([\s\S]*?)(?=## 💡|## 📖|---|$)', text)
    if step_block:
        for line in step_block.group(1).split('\n'):
            line = clean_text(line)
            m = re.match(r'^\d+[\.、]\s*(.*)', line)
            if m:
                step_txt = clean_text(m.group(1))
                if step_txt:
                    steps.append(step_txt)

    # Tips
    tip_m = re.search(r'## 💡 大廚美味秘訣 / Chef\'s Tips([\s\S]*?)(?=## 📖|---|$)', text)
    tip = clean_text(tip_m.group(1).replace('-', '')) if tip_m else ""

    img_rel_path = f"recipe/{platform_domain}/{folder_name}/cover.jpg"

    return {
        "id": f"{platform_prefix}_{folder_name}",
        "name": title,
        "name_hans": title,
        "name_en": title,
        "keywords_en": f"{title} {platform_domain} vegetarian vegan recipe chinese food",
        "category": category,
        "diet": diet,
        "servings": servings,
        "prep_time": "10 分鐘",
        "cook_time": "15 分鐘",
        "total_time": "25 分鐘",
        "ingredients": ingredients,
        "steps": steps,
        "desc": tip[:200] if tip else f"{title} · 精選素食家常美味",
        "source_url": source_url,
        "image": img_rel_path,
        "local_dir": f"{platform_domain}/{folder_name}"
    }

def main():
    total_recipes = []

    # 1. Knorr
    with open(os.path.join(RECIPE_DIR, "recipes_data.json"), "r", encoding="utf-8") as f:
        existing = json.load(f)
    knorr_recipes = [r for r in existing if "knorr" in r.get("local_dir", "")]
    total_recipes.extend(knorr_recipes)

    # 2. GYS
    if os.path.exists(GYS_DIR):
        for folder in sorted(os.listdir(GYS_DIR)):
            folder_path = os.path.join(GYS_DIR, folder)
            md_file = os.path.join(folder_path, "README.md")
            if os.path.isdir(folder_path) and os.path.exists(md_file):
                total_recipes.append(parse_markdown_recipe("gys", "vegan.gys.org.tw", folder, md_file, "經典蔬食"))

    # 3. JustGreenMall
    if os.path.exists(JGM_DIR):
        for folder in sorted(os.listdir(JGM_DIR)):
            folder_path = os.path.join(JGM_DIR, folder)
            md_file = os.path.join(folder_path, "README.md")
            if os.path.isdir(folder_path) and os.path.exists(md_file):
                total_recipes.append(parse_markdown_recipe("jgm", "www.justgreenmall.com", folder, md_file, "精緻純素"))

    # 4. Douguo
    if os.path.exists(DOUGUO_DIR):
        for folder in sorted(os.listdir(DOUGUO_DIR)):
            folder_path = os.path.join(DOUGUO_DIR, folder)
            md_file = os.path.join(folder_path, "README.md")
            if os.path.isdir(folder_path) and os.path.exists(md_file):
                total_recipes.append(parse_markdown_recipe("dg", "www.douguo.com", folder, md_file, "家常素食"))

    # 5. Xiachufang
    if os.path.exists(XCF_DIR):
        for folder in sorted(os.listdir(XCF_DIR)):
            folder_path = os.path.join(XCF_DIR, folder)
            md_file = os.path.join(folder_path, "README.md")
            if os.path.isdir(folder_path) and os.path.exists(md_file):
                total_recipes.append(parse_markdown_recipe("xcf", "www.xiachufang.com", folder, md_file, "流行素食"))

    print(f"Total recipes across 5 platforms: {len(total_recipes)}")

    # Clean newlines in fields
    for r in total_recipes:
        if isinstance(r.get('desc'), str):
            r['desc'] = r['desc'].replace('\n', ' ').strip()
        if isinstance(r.get('steps'), list):
            r['steps'] = [s.replace('\n', ' ').strip() for s in r['steps']]
        if isinstance(r.get('ingredients'), list):
            r['ingredients'] = [i.replace('\n', ' ').strip() for i in r['ingredients']]

    # Save to recipes_data.json
    with open(os.path.join(RECIPE_DIR, "recipes_data.json"), "w", encoding="utf-8") as f:
        json.dump(total_recipes, f, ensure_ascii=False, indent=2)

    # Embed in index.html safely without re.sub
    with open("/root/1CT-Share/20260818-vegetarianism/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    pos1 = html.find("const RECIPES_DATA = ")
    pos2 = html.find("const PLATFORMS_DATA = ")
    if pos1 != -1 and pos2 != -1:
        recipes_js = "const RECIPES_DATA = " + json.dumps(total_recipes, ensure_ascii=False) + ";\n\n    "
        new_html = html[:pos1] + recipes_js + html[pos2:]
        with open("/root/1CT-Share/20260818-vegetarianism/index.html", "w", encoding="utf-8") as f:
            f.write(new_html)

    print("[✓] Successfully updated index.html and recipes_data.json!")

if __name__ == "__main__":
    main()
