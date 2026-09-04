# heytea-dashboard · 喜茶华南战区运营数据看板

> 每周追踪华南一区 / 华南二区门店基础数据与排名，支撑运营动作。
> 纯前端 HTML 交互看板，数据全内联，双击即可离线打开；支持多周期切换与自动更新。

---

## 功能亮点

- **区域周报总览**：华南一区 / 二区基础数据 + 各区 **Bottom3** 门店
- **门店全景排名**：分区域、分城市的门店基础数据 + **Top3 / Bottom10**，支持按指标独立排名
- **督导视图**：按督导查看下属门店明细，含“督导表现”与“门店明细”两个表格
- **多周期切换**：右上角“数据周期”下拉，可在不同数据期之间切换
- **多层级多选筛选**：区域、城市（省份-城市树形多选）、督导、平台均可多选
- **指标口径注释**：美团新增指标（综合体验分、商品质量分、服务体验分、商品满意度、包装满意度）带问号说明
- **实时更新**：本地服务自动检测新增数据文件夹，只重建对应期，页面无需手动刷新
- **轻量品牌化**：喜茶图形 logo 内嵌 favicon 与顶栏，单文件即可分发

### 核心指标（12 个，按渠道）

| 渠道 | 指标 |
| --- | --- |
| 美团（7） | 商家评分、在线联系回复率、综合体验分、商品质量分、服务体验分、商品满意度、包装满意度 |
| 闪购（5） | 商家评分、消息回复率、差评回复率、商责取消率（外卖评分 / 近 7 日差评回复率可扩展） |

---

## 技术栈

- 纯 **HTML + CSS + JavaScript**，无前端框架，无需后端依赖
- 数据：`data.json`（构建期由 Excel 汇总，页面内联）
- 字体：正文 `Noto Sans SC`，数字 `Inter`，品牌标题 `Noto Serif SC`
- 配色：暖白 `#F9F8F6` + 白 `#FFFFFF` + 墨黑 `#1A1A1A` + 低饱和茶绿 `#45684A`，改善 `#5E7E5A` / 恶化 `#BE554B`
- 部署：Git + Netlify 自动构建

---

## 项目结构

| 文件 | 作用 |
| --- | --- |
| `build_data.py` | 扫描数据文件夹 → 解析 Excel → 输出 `data.json` |
| `generate_html.py` | 读取 `data.json` → 生成自包含 `dashboard.html` |
| `server.py` | 本地实时服务，监听数据变动并增量重建 |
| `启动看板.bat` | 一键启动本地服务并打开浏览器 |
| `推送更新.bat` | 重建数据 → 生成页面 → 提交并推送 GitHub |
| `发布_Netlify.bat` | 重建数据 → 生成页面 → 发布到 Netlify |
| `netlify.toml` | Netlify 自动构建配置 |
| `data.json` | 已合并的多期数据（用于部署构建） |
| `logo.png` | 喜茶图形 logo（favicon + 顶栏内嵌源图） |

---

## 数据源

按周期新建文件夹，命名格式固定：

```text
双周基础数据MMDD-MMDD/
├── 双周基础数据MMDD-MMDD.xlsx        # 主文件：汇总 + 门店基础数据
└── 有公式/
    └── 1双周基础数据MMDD-MMDD.xlsx   # 美团评价日明细（5 个新增指标来源）
```

例如：`双周基础数据0810-0816`、`双周基础数据0824-0830`。

> 文件夹名里的日期决定周期，页面右上角“数据周期”会自动列出所有期。

---

## 本地使用

### 一键启动

双击 `启动看板.bat`。首次启动会重建数据（约半分钟），随后自动打开：

```text
http://127.0.0.1:8000
```

### 手动启动服务

```bash
python server.py               # 默认端口 8000，自动打开浏览器
python server.py --port 8080   # 改端口
python server.py --no-open     # 不自动打开浏览器
```

### 更新数据

把新的 `双周基础数据MMDD-MMDD` 文件夹放进本目录，服务会自动检测：

- 只重建**变动的那一期**（增量构建，更快）
- 无需手动刷新，页面自动更新
- 首次出现的新文件夹会自动构建，并加入“数据周期”下拉

---

## 部署

### 方式一：Git + Netlify（推荐，链接固定）

仓库已通过网络钩子接入 Netlify，`push` 到 `main` 即自动构建：

```bash
git add -A
git commit -m "更新看板"
git push origin main
```

Netlify 会执行 `python generate_html.py` 生成 `dashboard.html`，再复制到 `部署_Netlify/index.html` 作为发布目录。

也可以双击 `推送更新.bat` 一键完成“重建 + 提交 + 推送”。

### 方式二：Netlify CLI / 拖拽

双击 `发布_Netlify.bat`：重建数据并复制 `dashboard.html` 到 `部署_Netlify/`，然后：

- 已安装 Netlify CLI：自动执行 `netlify deploy --prod`
- 未安装：手动把 `部署_Netlify` 拖到 [app.netlify.com/drop](https://app.netlify.com/drop)

> 注意：Drop 每次上传会生成**新链接**；要覆盖旧链接请使用 CLI 或 Git 自动部署。

### 方式三：腾讯云 COS / 阿里云 OSS

1. 运行 `build_data.py` 与 `generate_html.py` 生成 `dashboard.html`
2. 在 COS / OSS 创建存储桶，开启**静态网站托管**
3. 上传 `dashboard.html`，设置 `Content-Type: text/html; charset=utf-8`
4. 若仍被浏览器下载，确认响应头**不含** `Content-Disposition` / `x-cos-force-download`

---

## 常用命令

```bash
python build_data.py      # 解析 Excel → data.json
python generate_html.py   # data.json → dashboard.html
python server.py          # 本地实时预览
```

---

## 版权说明

内部运营工具，数据与设计版权归喜茶所有。
