#!/bin/bash
# macOS平台打包脚本

echo "🚀 macOS平台 - YOLO Annotation Tool 打包"
echo "=============================================="

# 检查Python和pip
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python3 未安装"
    exit 1
fi

echo "📋 安装依赖..."
pip3 install -r requirements.txt

echo "🧹 清理构建目录..."
rm -rf build dist __pycache__

echo "🔨 开始构建..."
pyinstaller --clean --noconfirm yolo_annotation_tool.spec

if [ $? -eq 0 ]; then
    echo "✅ 构建成功!"
    
    echo "📦 创建发布包..."
    mkdir -p release/macos
    cp -R dist/* release/macos/
    
    echo "📁 可执行文件位置: release/macos/"
    echo "💡 双击 'YOLO Annotation Tool.app' 即可运行"
    echo ""
    echo "🔧 如需签名应用(发布到App Store):"
    echo "   codesign --deep --force --verify --verbose --sign 'Developer ID Application: Your Name' 'release/macos/YOLO Annotation Tool.app'"
    echo ""
    echo "📱 创建DMG安装包:"
    echo "   hdiutil create -volname 'YOLO Annotation Tool' -srcfolder 'release/macos' -ov -format UDZO 'YOLO_Annotation_Tool.dmg'"
else
    echo "❌ 构建失败!"
    exit 1
fi