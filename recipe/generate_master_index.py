import os
import json

RECIPE_ROOT = "/root/1CT-Share/20260818-vegetarianism/recipe"

with open(os.path.join(RECIPE_ROOT, "recipes_data.json"), "r", encoding="utf-8") as f:
    recipes = json.load(f)

knorr_recipes = [r for r in recipes if "knorr" in r.get("local_dir", "")]
gys_recipes = [r for r in recipes if "gys" in r.get("local_dir", "") or "gys" in r.get("id", "")]
jgm_recipes = [r for r in recipes if "justgreenmall" in r.get("local_dir", "") or "jgm" in r.get("id", "")]

lines = [
    "# 🌱 全球蔬食與素食精選食譜庫檢索索引 (Vegetarian & Vegan Recipe Master Index)",
    "",
    "> **說明**：本目錄為 Antigravity 素食導航項目的本地食譜庫，提供結構化 Markdown、高清成品圖與多語言（簡體 / 繁體 / 英文）檢索支援，方便搜尋引擎快速抓取索引與使用者本地查詢。",
    "",
    f"**當前已歸檔食譜總數**：`{len(recipes)}` 道精選素食料理（觀音山蔬食館：`{len(gys_recipes)}` 道 ｜ 康寶官方：`{len(knorr_recipes)}` 道 ｜ 植境 JustGreen Mall：`{len(jgm_recipes)}` 道）",
    "",
    "---",
    "",
    f"## 📚 1. 植境 JustGreen Mall 官方素食博客食譜 ({len(jgm_recipes)} 道)",
    "",
    "| 序號 | 食譜名稱 (繁/簡/英) | 分類 / 流派 | 耗時 | 食材精選摘要 | 食譜詳情與圖文 |",
    "| :--- | :--- | :--- | :--- | :--- | :--- |"
]

for idx, r in enumerate(jgm_recipes, 1):
    ing_summary = "、".join([i.split(" ")[0] for i in r["ingredients"][:4]])
    link_md = f"[{r['name']}]({r['local_dir']}/README.md)"
    lines.append(
        f"| {idx} | **{r['name']}**<br>*{r['name_hans']}*<br>`{r['name_en']}` | {r['category']}<br><span style='color:#15803d;'>{r['diet']}</span> | {r['total_time']} | {ing_summary}... | {link_md} |"
    )

lines.extend([
    "",
    "---",
    "",
    f"## 📚 2. 康寶 (Knorr) 台灣官方素食料理系列 ({len(knorr_recipes)} 道)",
    "",
    "| 序號 | 食譜名稱 (繁/簡/英) | 分類 / 流派 | 耗時 | 食譜詳情與圖文 |",
    "| :--- | :--- | :--- | :--- | :--- |"
])

for idx, r in enumerate(knorr_recipes, 1):
    time_display = f"備料{r['prep_time']} / 烹飪{r['cook_time']}"
    link_md = f"[{r['name']}]({r['local_dir']}/README.md)"
    lines.append(
        f"| {idx} | **{r['name']}**<br>*{r['name_hans']}*<br>`{r['name_en']}` | {r['category']}<br><span style='color:#15803d;'>{r['diet']}</span> | {time_display} | {link_md} |"
    )

lines.extend([
    "",
    "---",
    "",
    f"## 📚 3. 觀音山 · 素食料理簡單做 — 7大專區純淨食譜系列 ({len(gys_recipes)} 道)",
    "",
    "| 序號 | 食譜名稱 | 飲食流派 | 分類 | 食材精選摘要 | 食譜詳情與圖文 |",
    "| :--- | :--- | :--- | :--- | :--- | :--- |"
])

for idx, r in enumerate(gys_recipes, 1):
    ing_summary = "、".join([i.split(" ")[0] for i in r["ingredients"][:3]])
    link_md = f"[{r['name']}]({r['local_dir']}/README.md)"
    lines.append(
        f"| {idx} | **{r['name']}** | <span style='color:#15803d;'>{r['diet']}</span> | {r['category']} | {ing_summary}... | {link_md} |"
    )

lines.extend([
    "",
    "---",
    "",
    "## 📂 資料夾目錄結構 (Repository Structure)",
    "",
    "```text",
    "recipe/",
    "├── README.md               # 本檢索索引文件（提供搜索引擎爬蟲與全局關鍵字矩陣）",
    f"├── recipes_data.json       # 供前端 SPA 搜尋框即時檢索的結構化數據 ({len(recipes)} 道)",
    f"├── www.justgreenmall.com/  # 植境 JustGreen Mall 素食食譜庫 ({len(jgm_recipes)} 道)",
    f"├── www.knorr.com/          # 康寶官方素食食譜庫 ({len(knorr_recipes)} 道)",
    f"└── vegan.gys.org.tw/       # 觀音山蔬食館食譜庫 ({len(gys_recipes)} 道)",
    "```",
    "",
    "---",
    "*維護更新於 2026-08-20 · 綠意食光 素食權威知識庫*"
])

with open(os.path.join(RECIPE_ROOT, "README.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Master README.md regenerated successfully with {len(recipes)} recipes across 3 platforms!")
