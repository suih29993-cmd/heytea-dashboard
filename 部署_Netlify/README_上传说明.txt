【如何把看板发成链接】

方式一：Netlify Drop（免代码，最快，但每次是“新链接”）
1. 打开 https://app.netlify.com/drop
2. 把整个「部署_Netlify」文件夹拖进网页（或只拖 index.html）。
3. 几秒后会得到链接，例如 https://xxxx.netlify.app/
4. 把该链接发给别人即可。
注意：Drop 每次上传都会生成一个【新】网址，且不会自动覆盖旧网址。所以每次更新数据后，旧链接不会变，需要重新拖一次并把新链接再发一次。

方式二：固定同一个链接（推荐）
要让“同一个链接”自动更新，不要把网站当成一次性上传，而要绑定成一个可更新的站点。两种做法：

（A）Git 自动部署（真正自动：改完数据 → git push → 链接自动更新）
1. 把这个文件夹做成 Git 仓库，并推到 GitHub/Gitee。
2. 在 Netlify 新建站点时选“导入现有 Git 仓库”，绑定该仓库。
3. Netlify 会读取根目录的 netlify.toml：自动执行 generate_html.py（读取已提交的 data.json），
   并把「部署_Netlify」作为发布目录。之后每次本地更新数据并 git push，链接自动更新，无需手动上传。
   （注意：data.json 必须一起提交；新增/更新的“双周基础数据MMDD-MMDD”文件夹可不提交。）

（B）命令行一键发布（免 Git：更新数据后双击一次「发布_Netlify.bat」）
1. 首次：安装 Netlify CLI（npm i -g netlify-cli），执行 netlify login 登录，
   再在项目目录执行 netlify link 绑定一个站点（或 netlify init 创建新站点）。
2. 之后每次更新数据，双击「发布_Netlify.bat」：
   自动重建数据 → 生成 index.html → 发布到【同一个】站点链接。

说明：
- index.html 已包含全部数据/样式/Logo，是自包含网页，无需后端。
- 在线时加载 Google Fonts（Noto Sans SC / Inter），离线/加载失败会自动用系统中文字体，不影响数据。
- 若收件人主要在中国大陆，Netlify/Vercel 有时访问不稳定；可改用公司内网或腾讯云 COS / 阿里云 OSS 静态托管。
