# 绿意食光 · 素食与蔬食全球权威菜谱与测评导航

> 🌐 **GitHub Pages 在线访问**：[https://leon7786.github.io/20260818-vegetarianism/](https://leon7786.github.io/20260818-vegetarianism/)

🌿 **Global Vegetarian & Vegan Authority Guide & Recipe Library**

一个浅色清新、植物美学风格的全球权威素食与纯素平台导航及精选菜谱数据库系统。

---

## 🌟 页面与系统特性

- **🌐 GitHub Pages 全球在线可访问**：已配置自动化静态托管与全球 CDN 加速。
- **🔍 三语即时食谱检索引擎**：右上角搜索栏深度集成 `/recipe` 本地食谱库，原生支持**简体中文、繁體中文、English**与食材级精准匹配（如搜 `tofu`、`南瓜`、`soup`、`鲜菇`、`素面`）。
- **🍲 交互式食谱详情弹窗**：点击食谱卡片可直接调出高清成品图、份量耗时、**用料清单勾选备料**、分步烹饪步骤、大厨提鲜要点与官方原站直达。
- **📑 搜索引擎专用索引（SEO Master Index）**：在 [`recipe/README.md`](recipe/README.md) 提供完整的结构化多语言检索矩阵、食材摘要表与本地目录树。
- **🏛️ 39 个全球权威美食平台收录**：
  - 🇨🇳 **中华美食（16个）**：Knorr 康宝素食、观音山蔬食、Just Green Mall、Cookpad台湾、爱料理、豆果美食、下厨房、美食天下、香港佛联会、香哈网、杨桃美食网、VegeAngel、美食杰、100道经典素菜、世界素联、香港01等。
  - 🔬 **科学实测（5个）**：America's Test Kitchen、Serious Eats、Good Housekeeping Institute、Viva! Vegan Recipe Club、鲜味信息中心（Umami）。
  - 🌍 **权威媒体与榜单（10个）**：TasteAtlas 世界素食排名、BBC Good Food、HappyCow、NYT Cooking、Allrecipes、Food Network、EatingWell、Epicurious、The Kitchn、VegNews。
  - 👩‍🍳 **知名名厨与获奖博客（5个）**：101 Cookbooks (Heidi Swanson)、Smitten Kitchen、Cookie and Kate、Love and Lemons、Sharon Palmer。
  - 🛠️ **数据工具与国际倡导（3个）**：Spoonacular API & 数据库、Veganuary 国际纯素一月、Reddit r/vegetarian 精华。
- **⭐ 收藏夹系统**：基于 LocalStorage 本地持久化，随时标记收藏喜爱的平台。
- **🥗 素食流派与营养指南弹窗**：内置纯素（Vegan）、蛋奶素（Ovo-Lacto）、鲜味科学（Umami）与关键营养摄入建议。
- **📱 全设备自适应体验**：深度针对大屏桌面、iPad 平板与手机移动端进行触控反馈优化，支持一键平滑返回顶部。

---

## 📁 目录结构

```text
20260818-vegetarianism/
├── index.html                  # 响应式单页网站（集成多语言检索与菜谱弹窗）
├── .nojekyll                   # GitHub Pages 静态文件直通配置
├── README.md                   # 项目介绍与说明（包含在线 Pages 地址）
├── lists/
│   └── all.md                  # 39 个权威平台网址与分类详单
└── recipe/
    ├── README.md               # 搜索引擎 SEO 多语言检索索引文件
    ├── recipes_data.json       # 前端多语言检索引擎数据源
    ├── build_recipe_database.py # 全自动食谱爬取与多语言索引构建工具
    └── www.knorr.com/          # 康宝官方精选食谱库
        ├── 蕈菇南瓜素麵/       # 独立食谱文件夹（包含 README.md + cover.jpg）
        ├── 鮮菇豆腐煲(素)/
        ├── 三絲豆腐羹(素)/
        ├── 涼拌素什錦(素)/
        ├── 炸海苔腐皮卷 (全素)/
        ├── 鹹酥菇菇 (蛋奶素)/
        ├── 菇菇素米糕/
        ├── 菌菇南瓜湯(素)/
        ├── 如意冬瓜卷/
        └── 金沙豆腐/
```

---

## 🚀 本地预览

通过任意静态 HTTP 服务器运行：

```bash
# 使用 Python 启动本地预览服务：
python3 -m http.server 30818 --directory /root/1CT-Share/20260818-vegetarianism
```

在浏览器打开 `http://127.0.0.1:30818` 即可查看。

---
*Inspired by Huang Huiling | © 2026 All Rights Reserved*
