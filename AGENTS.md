# AGENTS.md · 喜茶华南战区数据看板

面向在本目录工作的 AI 代理与协作者。**动手前先读完本文**，尤其是下面「已知特例」——那些是踩过坑之后刻意写成这样的，不要当成 bug 去"修好"。

---

## 1. 项目是什么

纯前端单文件看板，数据全内联，双击 HTML 即可离线打开。

```
Excel（评分数据） --build_data.py--> data.json --generate_html.py--> dashboard.html
```

三个视图：**区域周报总览** / **门店全景排名** / **督导视图**。
注意：这里的"周"指周期，数据文件夹叫「双周基础数据」只是命名习惯，实际是周维度数据。

### 工作区约束

- 路径含中文，PowerShell 下写文件请用 `Out-File -Encoding utf8` / `Set-Content -Encoding UTF8`，不要用默认编码。
- 跑 Python 建议加 `-X utf8`，否则中文 print 可能乱码。
- git 的写操作（add/commit/push）需要沙箱外权限，`.git` 目录对代理是只读的。
- `openpyxl` 读这些表会刷 `UserWarning: Unknown extension` / `Conditional Formatting extension`，无害，可 `2>$null` 屏蔽。

---

## 2. 常用命令

```bash
python -X utf8 build_data.py                                  # 全量重建所有期 -> data.json（慢）
python -X utf8 build_data.py --folder 双周基础数据0824-0830   # 只重建这一期，写入 _data_cache/
python -X utf8 build_data.py --merge                          # 只合并现有缓存 -> data.json，不解析 Excel
python -X utf8 generate_html.py                               # data.json -> dashboard.html
python -X utf8 server.py [--port 8080] [--no-open]            # 本地实时服务（默认 8000）
```

- `server.py` 每 **2 秒**轮询：期文件夹的 `(文件名, mtime_ns, size)` 签名变了才重建**那一期**；`build_data.py` / `generate_html.py` 自身变了会**全量**重建。页面通过版本号长轮询自动刷新，无需手动刷新。
- 双击 `启动看板.bat` 即可：它用 `--no-open` 起服务，3 秒后再打开 `http://127.0.0.1:8000`。
- 改了同一期文件夹里的 Excel 之后，`--merge` **不会**重新解析，必须 `--folder <期>` 或全量构建。

---

## 3. 数据源

```
双周基础数据MMDD-MMDD/                  # 文件夹名决定周期；正则 ^双周基础数据(\d{2})(\d{2})-(\d{2})(\d{2})$
├── 评分数据/                           # ★ 唯一的数据来源
│   ├── 全国评分数据8月-美团.xlsx
│   ├── 全国评分数据8月-闪购.xlsx
│   └── 有公式/                         # 自动跳过（只扫一层，不进子目录）
└── 基础数据/<期>.xlsx                  # 可选，只用来补 门店ID / 门店类型
```

- 文件名含「美团」/「闪购」即被识别；`~$` 开头的 Excel 锁文件自动跳过。
- 基础数据底表读 `门店基础数据底表` sheet（门店名第 5 列、类型第 4 列、ID 第 6 列，从第 4 行起）。
- **`PERIOD_YEAR = 2026` 硬编码在 `build_data.py`**，跨年要改。
- 门店一律按**门店名字符串**匹配；名字对不上就当两家店。

### 取数口径（列号均为 0 基，与 Excel 字母对应已注明）

| Sheet | 键列 | 起始行 | 说明 |
| --- | --- | --- | --- |
| `华南门店维度` | 门店名 = 5（F） | 6 | 美团评分 G/H，复购率 P/Q；二级指标只有本期 |
| `华南汇总` | 城市名 = 3（D） | 5 | **指标列比门店维度左移 1**（美团评分 = F/G）；`战区` 为战区行，`影响分数` 行跳过 |
| `督导维度`（美团）/ `督导`（闪购） | 督导名 = 1（B） | 3 | 本期/上期/变化**三元组**，起始列 2、5、8、11、14、17、20 |

### 指标清单（16 项，美团 8 + 闪购 8）

- 美团：`mt_score` 美团评分、`mt_repeat` 复购率、`mt_goods_sat` 商品满意度、`mt_pack_sat` 包装满意度、`mt_repeat_score` 复购率指标得分、`mt_food_safe` 食品安全负反馈率、`mt_reply_score` 消息回复率得分、`mt_service_fb` 服务负反馈率
- 闪购：`sg_score` 闪购评分、`sg_cancel` 商责取消率、`sg_taste_sat` 口味满意度、`sg_pack_sat` 包装满意度、`sg_repeat_score` 复购率指标得分、`sg_food_safe` 食品安全负反馈率、`sg_reply_score` 消息回复率、`sg_service_fb` 服务负反馈率

指标定义分散在三处，**改口径要同时改**：
`build_data.py` 的 `STORE_COLS` / `SUMMARY_COLS` / `SUP_COLS`，`generate_html.py` 的 `METRICS`（名称/单位/方向）与 `METRIC_HELP`（问号提示文案）。

### 督导视图派生指标（`build_data.py` 的 `COMPOSITE`）

| 指标 | 公式 |
| --- | --- |
| `mt_quality` / `sg_quality` 商品质量分 | （满意度×30% + 包装满意度×10% + 复购率指标得分×20% + 食品安全负反馈率×20%）÷ **80%** |
| `mt_service` / `sg_service` 服务体验分 | （消息回复率×10% + 服务负反馈率×10%）÷ **20%** |

- 闪购的「满意度」取 `sg_taste_sat` 口味满意度；美团取 `mt_goods_sat`。
- **必须除以权重合计**（80% / 20%）归一化到 0–5 分，这样 `评分 = 商品质量分×80% + 服务体验分×20%` 才成立；直接加权求和得到的是 0–4 / 0–1，是错的。
- 由 `_apply_composites()` 在 `build_period()` 与 `merge()` 两处统一补齐，覆盖门店/督导/城市/区域四级；任一分项缺失则该派生指标为 `None`（显示 `—`）。
- 只调 `COMPOSITE` 时不需要重新解析 Excel，`python -X utf8 build_data.py --merge` 即可刷新 `data.json`。

### 前端用到的指标分组

| 常量 | 内容 |
| --- | --- |
| `REGION_METRICS` | 美团评分、复购率、闪购评分、商责取消率（区域总览 4 张 KPI 卡） |
| `BOTTOM_METRICS` | 同上 4 项，Bottom 5 表 |
| `V3_MT_ORDER` / `V3_SG_ORDER` | 督导视图（督导表现表 + 门店明细，两张表列一致）：美团 = 评分 + 商品质量分 + 服务体验分；闪购 = 评分 + 商品质量分 + 服务体验分 + 商责取消率 |
| `SUB_MT` / `SUB_SG` | 门店明细里点击展开的二级指标 |

---

## 4. 已知特例（刻意如此，勿"修复"）

1. **闪购督导表最后一组列（20–22）被跳过**：它是比率，不是 0–5 分，与门店级口径不一致。因此闪购督导的「服务负反馈率」改由旗下门店聚合。
2. **闪购督导表没有商责取消率** → 由该督导旗下门店聚合（`_agg`）。
3. **闪购 `华南汇总` 战区行没有商责取消率** → 按城市**门店数加权**平均补齐（`_wavg`）。
4. **闪购目前整表无上期数据** → 闪购指标环比显示 `—`。环比 UI 必须保留，下一期文件补齐后自动生效。
5. **闪购消息回复率取 N 列「消息回复率（10%）」得分**，**不是** P/Q 列的「本期/上期消息回复率」百分比。闪购 `华南汇总` 同理。
6. **复购率取美团 P 列「本期复购率」/ Q 列「上期复购率」**。
7. **门店类型在评分数据里没有** → 取不到就记 `'未知'`（前端不使用该字段，不要因此报错或丢门店）。
8. **只在评分数据里出现、基础数据底表找不到的门店要保留**，不回退、不丢弃。
9. `华南分类型` sheet 当前未使用。
10. **异常阈值沿用旧值**：评分 `< 4.5`、商责取消率 `> 0.003`。命中时**只给该单元格**上浅红底，不做整行/整列/整卡染色。

---

## 5. 改代码的约定

- **只改视觉，不动数据与功能**——这是本项目反复出现的需求边界。改 CSS 时不要顺手改计算逻辑。
- 配色/字号等集中在 `generate_html.py` 的 `:root`，改主题只动这里：

  | 变量 | 值 | 用途 |
  | --- | --- | --- |
  | `--bg` | `#F9F8F6` | 暖白页面底 |
  | `--card` | `#FFFFFF` | 卡片/表格底 |
  | `--ink` | `#1A1A1A` | 主文字 |
  | `--sub` | `#6E6B66` | 辅助文字 |
  | `--line` | `#E8E6E1` | 分割线 |
  | `--accent` | `#45684A` | 品牌茶绿（仅 Tab / 当前导航 / 少量强调 / 正向变化） |
  | `--good` / `--bad` / `--neu` | `#5E7E5A` / `#BE554B` / `#A3A09A` | 改善 / 恶化 / 无变化 |
  | `--warn-bg` / `--th-bg` | `#F9EFEC` / `#F1F0EC` | 异常单元格 / 表头 |

- 字体：正文 `Noto Sans SC`，数字 `Inter`，品牌标题 `Noto Serif SC`（`--font-sans` / `--font-num`）。
- 设计原则：暖白 + 白 + 墨黑 + 低饱和茶绿；**不加渐变、插画、复杂阴影、装饰性图标**；表头不要用绿色。
- `generate_html.py` 是往内联 `<script>` 里塞 JS 的，改完**必须验证内联 JS 语法**：

```python
import io, re, subprocess
s = io.open('dashboard.html', encoding='utf-8').read()
js = max(re.findall(r'<script[^>]*>(.*?)</script>', s, re.S), key=len)
io.open('_chk.js', 'w', encoding='utf-8').write(js)
print(subprocess.run(['node', '--check', '_chk.js'], capture_output=True, text=True).returncode)  # 0 = OK
```

---

## 6. 上线流程

`push` 到 `main` → Netlify 自动构建并更新固定链接。

```bash
python -X utf8 build_data.py
python -X utf8 generate_html.py
copy /y dashboard.html "部署_Netlify\index.html"
git add -A && git commit -m "..." && git push origin main
```

**关键**：`.gitignore` 排除了 `dashboard.html`、`部署_Netlify/index.html`、`双周基础数据*/`、`_data_cache/`，所以线上构建只认 `data.json`——**更新数据时必须把 `data.json` 一起提交**，否则 Netlify 重建出来的还是旧数据。

`推送更新.bat` 只 `git add data.json`，**不会**提交代码改动；改了代码请手动 `git add -A`。

其他部署方式见 `README.md`；腾讯云 COS 见 `腾讯云COS部署步骤.md`。

---

## 7. 临时文件

调试脚本用完请删掉。`_data_cache/` 是构建缓存（可删，删了下次全量重建）。`.gitignore` 已忽略 `_pw_*.js`、`_shot_*.png` 等临时产物，但别让它们留在仓库里。
