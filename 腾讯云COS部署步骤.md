# 腾讯云 COS 部署看板（发链接）

把 `部署_Netlify/index.html` 上传到腾讯云对象存储 COS，开启静态网站托管，即可得到一个可公开访问的链接。

## 前置条件
- 有腾讯云账号并完成**实名认证**。
- 已开通「对象存储 COS」（免费额度足够放一个 html）。

## 步骤

### 1. 创建存储桶
1. 登录腾讯云控制台 → 搜索「对象存储 COS」→ 进入 COS 控制台。
2. 点「创建存储桶」：
   - 名称：如 `heyttea-dashboard`（全局唯一，小写字母/数字/中划线）。
   - 地域：选国内就近，如「华南-广州」「华东-上海」「华北-北京」（给大陆用户访问）。
   - 访问权限：选 **公有读私有写**（别人能看，只有你能改）。
3. 创建完成后进入该存储桶。

### 2. 开启静态网站托管
1. 存储桶 →「基础配置」→「静态网站」。
2. 开启静态网站：
   - 索引文档：`index.html`
   - 错误文档：`index.html`（可选）
3. 保存后记录**静态网站访问域名**，形如：
   `https://<bucket>.cos-website.<region>.myqcloud.com`
   （用这个域名访问，根路径直接打开看板，不需要在地址后加 `/index.html`。）

### 3. 上传 index.html
1. 存储桶 →「文件列表」→「上传文件」。
2. 把 `部署_Netlify/index.html` 拖进去上传（建议只传 index.html，别把说明文档一起传）。
3. 确认对象的 **Content-Type = text/html; charset=utf-8**（COS 一般按 `.html` 自动识别；若显示成 `application/octet-stream` 或打开变成下载，就在对象「基本信息」里把 Content-Type 改成 text/html; charset=utf-8）。

### 4. 获取链接发出去
- 用第 2 步记录的静态网站域名：`https://<bucket>.cos-website.<region>.myqcloud.com`
- 浏览器打开该地址应直接看到看板，把这个链接发给别人即可。

## 常见坑
- **打开变成下载**：Content-Type 不是 `text/html`，按第 3 步修改。
- **别人访问 403**：存储桶权限不是「公有读」，改成公有读私有写。
- **默认域名（cos.***.myqcloud.com）打不开首页**：默认域名不带静态托管逻辑，要用 `cos-website.***.myqcloud.com` 的静态网站域名。
- **要不要备案**：用 COS 自带的 `cos-website` 域名**不需要备案**；只有绑定自己的自定义域名才需要 ICP 备案。

## 后续更新数据
- 用 `build_data.py` + `generate_html.py` 重新生成 `dashboard.html` 后，覆盖到 `部署_Netlify/index.html`。
- 再到 COS 文件列表里「上传/覆盖」同一个 `index.html` 即可。
- 想保留历史版本可在存储桶开启「版本控制」。

## 可选：绑定 CDN / 自定义域名（更正式、更快）
- COS「域名管理」绑定已备案的自定义域名，添加 CNAME 解析到 COS 的默认域名。
- 或开通 CDN 加速，国内访问更稳；CDN 源站填 COS。
