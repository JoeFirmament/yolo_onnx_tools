@echo off
REM Windows平台打包脚本
echo 🚀 Windows平台 - YOLO Annotation Tool 打包
echo ================================================

echo 📋 安装依赖...
pip install -r requirements.txt

echo 🧹 清理构建目录...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo 🔨 开始构建...
pyinstaller --clean --noconfirm yolo_annotation_tool.spec

echo 📦 创建发布包...
if not exist "release\windows" mkdir "release\windows"
xcopy "dist\*" "release\windows\" /E /I /Y

echo ✅ 构建完成! 
echo 📁 可执行文件位置: release\windows\
echo 💡 双击 YOLO_Annotation_Tool.exe 即可运行

pause