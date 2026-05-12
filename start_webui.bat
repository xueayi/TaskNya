@echo off
setlocal

set PORT=%1
if "%PORT%"=="" set PORT=9870

echo 正在启动TaskNya Web界面...
echo.
echo   访问地址: http://localhost:%PORT%
echo.
python webui.py --port %PORT%
pause
