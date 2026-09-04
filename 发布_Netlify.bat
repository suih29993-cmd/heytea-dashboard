@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 发布看板到 Netlify
echo 正在重建数据...
python build_data.py
if errorlevel 1 ( echo 数据构建失败& pause & exit /b 1 )
python generate_html.py
if errorlevel 1 ( echo 页面生成失败& pause & exit /b 1 )
copy /y dashboard.html "部署_Netlify\index.html" >nul
echo 已更新：部署_Netlify\index.html
where netlify >nul 2>nul
if %errorlevel%==0 (
  echo 正在发布到 Netlify（已连接的站点）...
  netlify deploy --prod --dir="部署_Netlify"
) else (
  echo.
  echo [提示] 未检测到 Netlify CLI。两种方式任选：
  echo   1) 安装 CLI 后重跑本脚本，即可发布到【同一个】链接；
  echo   2) 手动把「部署_Netlify」文件夹重新拖到 https://app.netlify.com/drop
  echo      注意：Drop 每次会上传成【新】链接，不会自动覆盖旧链接。
)
pause
