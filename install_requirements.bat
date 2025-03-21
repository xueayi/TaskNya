@echo off
echo 正在安装依赖项...
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo 安装失败，请检查错误信息。
) else (
    echo 所有依赖项已成功安装。
)

pause