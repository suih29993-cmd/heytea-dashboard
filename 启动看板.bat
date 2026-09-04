@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 喜茶数据看板 - 实时版
echo 正在启动喜茶华南区数据看板（实时版）...
echo 首次启动会重新构建数据，约需半分钟；完成后会自动打开浏览器。
echo.
where python >nul 2>nul
if %errorlevel%==0 (set PY=python) else (set PY=py)
start "喜茶数据看板-服务" cmd /k "%PY% server.py --no-open"
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8000"
echo 已在浏览器中打开看板：http://127.0.0.1:8000
echo 关闭“喜茶数据看板-服务”那个黑色窗口即可停止服务。
exit
