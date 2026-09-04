@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 更新看板并推送到 GitHub
echo 正在重建数据...
python build_data.py
if errorlevel 1 ( echo 数据构建失败& pause & exit /b 1 )
python generate_html.py
if errorlevel 1 ( echo 页面生成失败& pause & exit /b 1 )
echo 正在提交并推送...
git add data.json
git commit -m "update dashboard data"
git push
echo 完成。Netlify 会自动重新构建并更新链接。
pause
