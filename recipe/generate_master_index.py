import os
import json

RECIPE_ROOT = "/root/1CT-Share/20260818-vegetarianism/recipe"

with open(os.path.join(RECIPE_ROOT, "recipes_data.json"), "r", encoding="utf-8") as f:
    recipes = json.load(f)

knorr_recipes = [r for r in recipes if "knorr" in r.get("local_dir", "")]
gys_recipes = [r for r in recipes if "gys" in r.get("local_dir", "") or "gys" in r.get("id", "")]
jgm_recipes = [r for r in recipes if "justgreenmall" in r.get("local_dir", "") or "jgm" in r.get("id", "")]
dg_recipes = [r for r in recipes if "douguo" in r.get("local_dir", "") or "dg" in r.get("id", "")]
xcf_recipes = [r for r in recipes if "xiachufang" in r.get("local_dir", "") or "xcf" in r.get("id", "")]

lines = [
    "# 🌱 全球蔬食與素食精選食譜庫檢索索引 (Vegetarian & Vegan Recipe Master Index)",
    "",
    "> **說明**：本目錄為 Antigravity 素食導航項目的本地食譜庫，提供結構化 Markdown、高清成品圖與多語言（簡體 / 繁體 / 英文）檢索支援，方便搜尋引擎快速抓取索引與使用者本地查詢。",
    "",
    f"**當前已歸檔食譜總數**：`{len(recipes)}` 道精選素食料理",
    f"- 🥢 **下廚房 (Xiachufang)**：`{len(xcf_recipes)}` 道",
    f"- 🍲 **豆果美食 (Douguo)**：`{len(dg_recipes)}` 道",
    f"- 🌿 **觀音山蔬食館 (Guanyinshan)**：`{len(gys_recipes)}` 道",
    f"- 🥗 **康寶官方 (Knorr Taiwan)**：`{len(knorr_recipes)}` 道",
    f"- 🥑 **植境 JustGreen Mall**：`{len(jgm_recipes)}` 道",
    "",
    "---",
    "",
    f"## 📚 1. 下廚房 · 素食主義專區熱門菜譜 ({len(xcf_recipes)} 道)",
    "",
    "| 序號 | 食譜名稱 | 飲食流派 | 分類 | 食材精選摘要 | 食譜詳情 |",
    "| :--- | :--- | :--- | :--- | :--- | :--- |"
]

for idx, r in enumerate(xcf_recipes, 1):
    ing_summary = "、".join([i.split(" ")[0] for i in r["ingredients"][:3]])
    link_md = f"[{r['name']}]({r['local_dir']}/README.md)"
    lines.append(f"| {idx} | **{r['name']}** | <span style='color:#15803d;'>{r['diet']}</span> | {r['category']} | {ing_summary}... | {link_md} |")

lines.extend([
    "",
    "---",
    "",
    f"## 📚 2. 豆果美食 · 素食專區家常菜譜 ({len(dg_recipes)} 道)",
    "",
    "| 序號 | 食譜名稱 | 飲食流派 | 分類 | 食材精選摘要 | 食譜詳情 |",
    "| :--- | :--- | :--- | :--- | :--- | :--- |"
])

for idx, r in enumerate(dg_recipes, 1):
    ing_summary = "、".join([i.split(" ")[0] for i in r["ingredients"][:3]])
    link_md = f"[{r['name']}]({r['local_dir']}/README.md)"
    lines.append(f"| {idx} | **{r['name']}** | <span style='color:#15803d;'>{r['diet']}</span> | {r['category']} | {ing_summary}... | {link_md} |")

lines.extend([
    "",
    "---",
    "",
    f"## 📚 3. 觀音山 · 素食料理簡單做 ({len(gys_recipes)} 道)",
    "",
    "| 序號 | 食譜名稱 | 飲食流派 | 分類 | 食材精選摘要 | 食譜詳情 |",
    "| :--- | :--- | :--- | :--- | :--- | :--- |"
])

for idx, r in enumerate(gys_recipes, 1):
    ing_summary = "、".join([i.split(" ")[0] for i in r["ingredients"][:3]])
    link_md = f"[{r['name']}]({r['local_dir']}/README.md)"
    lines.append(f"| {idx} | **{r['name']}** | <span style='color:#15803d;'>{r['diet']}</span> | {r['category']} | {ing_summary}... | {link_md} |")

lines.extend([
    "",
    "---",
    "",
    f"## 📚 4. 康寶 (Knorr) 台灣官方素食料理 ({len(knorr_recipes)} 道)",
    "",
    "| 序號 | 食譜名稱 | 飲食流派 | 分類 | 耗時 | 食譜詳情 |",
    "| :--- | :--- | :--- | :--- | :--- | :--- |"
])

for idx, r in enumerate(knorr_recipes, 1):
    time_display = f"備料{r['prep_time']} / 烹飪{r['cook_time']}"
    link_md = f"[{r['name']}]({r['local_dir']}/README.md)"
    lines.append(f"| {idx} | **{r['name']}** | <span style='color:#15803d;'>{r['diet']}</span> | {r['category']} | {time_display} | {link_md} |")

lines.extend([
    "",
    "---",
    "",
    f"## 📚 5. 植境 JustGreen Mall 官方博客食譜 ({len(jgm_recipes)} 道)",
    "",
    "| 序號 | 食譜名稱 | 飲食流派 | 分類 | 耗時 | 食譜詳情 |",
    "| :--- | :--- | :--- | :--- | :--- | :--- |"
])

for idx, r in enumerate(jgm_recipes, 1):
    link_md = f"[{r['name']}]({r['local_dir']}/README.md)"
    lines.append(f"| {idx} | **{r['name']}** | <span style='color:#15803d;'>{r['diet']}</span> | {r['category']} | {r['total_time']} | {link_md} |")

lines.extend([
    "",
    "---",
    "",
    "## 📂 資料夾目錄結構 (Repository Structure)",
    "",
    "```text",
    "recipe/",
    "├── README.md               # 全局搜尋引擎檢索索引文件",
    f"├── recipes_data.json       # 前端 SPA 搜尋框即時檢索結構化數據 ({len(recipes)} 道)",
    f"├── www.xiachufang.com/     # 下廚房熱門素食食譜庫 ({len(xcf_recipes)} 道)",
    f"├── www.douguo.com/         # 豆果美食素食食譜庫 ({len(dg_recipes)} 道)",
    f"├── vegan.gys.org.tw/       # 觀音山蔬食館食譜庫 ({len(gys_recipes)} 道)",
    f"├── www.knorr.com/          # 康寶官方素食食譜庫 ({len(knorr_recipes)} 道)",
    f"└── www.justgreenmall.com/  # 植境 JustGreen Mall 素食食譜庫 ({len(jgm_recipes)} 道)",
    "```",
    "",
    "---",
    "*維護更新於 2026-08-20 · 綠意食光 素食權威知識庫*"
])

with open(os.path.join(RECIPE_ROOT, "README.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Master README.md regenerated successfully with {len(recipes)} recipes across 5 platforms!")
