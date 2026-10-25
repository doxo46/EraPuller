@echo off
chcp 65001 >nul
title EraPuller 跨时代的拉取器 - 构建脚本
echo.
echo  [EraPuller] 正在安装依赖...
python -m pip install -r requirements.txt || goto :err
echo.
echo  [EraPuller] 正在打包 EXE...
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name "EraPuller" ^
  --icon "icon.ico" ^
  --exclude-module PySide6.QtWebEngineCore ^
  --exclude-module PySide6.QtWebEngineWidgets ^
  --exclude-module PySide6.QtWebEngineQuick ^
  --exclude-module PySide6.QtWebChannel ^
  --exclude-module PySide6.QtQml ^
  --exclude-module PySide6.QtQuick ^
  --exclude-module PySide6.QtMultimedia ^
  --exclude-module PySide6.Qt3DCore ^
  main.py || goto :err
echo.
echo  [EraPuller] 完成！EXE 位于 dist\EraPuller.exe
pause
exit /b 0
:err
echo.
echo  [EraPuller] 构建失败，请检查上方错误信息。
pause
exit /b 1
