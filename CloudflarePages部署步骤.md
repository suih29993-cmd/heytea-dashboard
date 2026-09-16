# Cloudflare Pages 部署看板（替代 Netlify，免费不限流量）

## 为什么要换

- Netlify 免费版按 **credits** 计量，额度用尽后横幅会提示 *running on operational credits*：**站点仍在线，但生产部署（production deploy）被暂停**——也就是 `git push` 之后线上不再更新，要等下个计费周期或升级付费团队才恢复。
- Cloudflare Pages 免费版：**不限带宽、不限请求**，500 次构建/月，单次部署最多 20,000 个文件、单文件最大 25 MiB。我们的看板是单个约 1 MB 的 HTML，完全够用，也不会再出现"空间满了"。
- 现有 Netlify 站点**不会立刻消失**，可以两个链接并行一段时间，确认新链接没问题后再停用旧的。

## 方式 A：连 GitHub 自动部署（推荐，体验和现在一致）

1. 登录 <https://dash.cloudflare.com> → 左侧 **Workers & Pages** → **Create** → 选 **Pages** → **Connect to Git**。
2. 授权 GitHub，选中仓库 `suih29993-cmd/heytea-dashboard`，生产分支填 `main`。
3. 构建设置：

   | 项 | 值 |
   | --- | --- |
   | Framework preset | `None` |
   | Build command | 见下方代码块（直接整行复制） |
   | Build output directory | `部署_Netlify` |
   | 环境变量（可选） | `PYTHON_VERSION` = `3.11` |

   Build command 一行照抄（`python3` / `python` 哪个存在用哪个，避免构建镜像差异）：

   ```bash
   (python3 -X utf8 generate_html.py || python -X utf8 generate_html.py) && cp dashboard.html 部署_Netlify/index.html
   ```

4. 点 **Save and Deploy**，1~2 分钟后得到固定链接：`https://<项目名>.pages.dev`。
5. 以后更新数据：本地 `python -X utf8 build_data.py` → `git push origin main` → 链接自动更新（和现在 Netlify 一样）。
   **记得把 `data.json` 一起提交**（线上构建只读它，原始 Excel 不入库）。

> 构建日志若报找不到 Python（`python3`、`python` 都不存在），别折腾，直接用方式 B，它不需要任何构建环境。

构建命令需要访问 `data.json`（仓库里）并把产物写到 `部署_Netlify/index.html`（该文件被 `.gitignore` 忽略，构建期生成）。

## 方式 B：网页拖拽直传（最简单，零依赖）

1. Workers & Pages → **Create** → **Pages** → **Upload assets**。
2. 项目名填 `heytea-dashboard`，把 **`部署_Netlify` 文件夹**整个拖进去（里面要有 `index.html`），点 Deploy。
3. 以后更新数据：

   ```bat
   python -X utf8 build_data.py
   python -X utf8 generate_html.py
   copy /y dashboard.html "部署_Netlify\index.html"
   ```

   然后进项目 → **Create new deployment** → 把同一文件夹再拖一次。
   **链接不变**（这点比 Netlify Drop 好，Drop 每次都会换成新链接）。

## 方式 C：Wrangler 命令行（本机暂时用不了）

需要 Node + npm，本机当前**没有 npm**（`where npm` 找不到，只有 Codex 自带的 node），所以这条先跳过。将来装了 Node 后可以：

```bash
npx wrangler pages deploy 部署_Netlify --project-name=heytea-dashboard
```

## 换托管期间怎么发数据

- 老 Netlify 链接仍能打开，只是数据冻结在最后一次成功部署的版本。
- 急着发最新一期数据时，直接发 **`dashboard.html` 单文件**给同事即可：数据全内联，双击浏览器就能看，不依赖任何服务器（约 1 MB，微信/企业微信可直接传）。
- 也可以双击 `启动看板.bat` 用本地服务看（`http://127.0.0.1:8000`）。

## 防爬虫（顺手做掉，Netlify / Cloudflare 通用）

看板链接不该被搜索引擎收录，被爬虫反复抓取也会消耗托管额度。发布目录里已放好：

- `部署_Netlify/robots.txt`：`Disallow: /`
- `部署_Netlify/_headers`：对所有响应加 `X-Robots-Tag: noindex, nofollow`

两个文件 Netlify 和 Cloudflare Pages 都认，不用改配置。

## 排错：部署 12 秒就失败 / `Latest build failed`

现象：Workers & Pages 里项目名 `heytea-dashboard`，构建卡在 **Deploying** 阶段失败，Build settings 显示
`Deploy command = npx wrangler deploy`、`Build command = None`。

原因：这个项目是 **Workers 项目**（Create 时选了 Workers → Import a repository），不是 Pages 项目。
Workers 项目会执行 `npx wrangler deploy`，需要仓库里有 `wrangler.toml` / `wrangler.jsonc`；
本项目是纯静态站点，原先没有该文件，所以必然失败。

两种解法，任选其一：

**解法 1（推荐）：改成 Pages 项目** —— 见上面的「方式 A」。
新建时一定要在 **Pages** 这一栏点 `Connect to Git`（Workers 栏的 `Import a repository` 会再建出一个 Worker 项目）。
建好 Pages 项目后，这个失败的 Worker 项目可以到 Settings → Delete project 删掉；名字若被占用，Pages 项目换个名字（如 `heytea-dashboard-pages`）即可。

**解法 2：保留现有 Worker 项目**（少动一步，链接形如 `https://heytea-dashboard.<你的账号>.workers.dev`）：

1. 仓库根目录已有 `wrangler.jsonc`（把 `部署_Netlify` 作为静态资源目录），**先 `git pull` 拉到最新**。
2. 进入项目 → **Settings → Build**，把 **Build command** 从 `None` 改成：

   ```bash
   (python3 -X utf8 generate_html.py || python -X utf8 generate_html.py) && cp dashboard.html 部署_Netlify/index.html
   ```

   （`Deploy command` 保持 `npx wrangler deploy` 不动；`Root directory` 保持 `/`。）
   注意 `Build command` 不能留空：发布目录里的 `index.html` 不在仓库里，是构建期生成的。
3. 回到 **Deployments** → 右侧 `Retry deployment`（或重新 push 一次）。
4. 构建日志里若报 `Cannot find module 'wrangler'`，把 Deploy command 改成 `npx --yes wrangler deploy`。

> 两条路的产物是同一份 `部署_Netlify` 目录，只是「谁来托管」不同：Pages 走 `*.pages.dev`，Workers 静态资源走 `*.workers.dev`。
> Cloudflare 免费版下两者都不收流量费。

## 常见坑

- **`部署_Netlify` 目录必须存在于仓库里**：`.gitignore` 忽略了 `部署_Netlify/index.html`，但目录里有 `README_上传说明.txt`，所以目录本身在仓库中存在，构建时用 `cp` 生成 `index.html` 没问题。
- **构建出来是旧数据**：说明 `data.json` 没提交。线上只认 `data.json`，原始 Excel 不入库。
- **改了 Excel 但线上没变**：`build_data.py --merge` 不会重新解析 Excel，必须 `--folder <期>` 或全量重建后再提交 `data.json`。
- **首次部署 404**：确认 Build output directory 填的是 `部署_Netlify`（不要写成 `/部署_Netlify` 或仓库根目录）。
