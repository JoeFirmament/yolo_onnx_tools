#!/bin/bash
# Linux平台打包脚本

echo "🚀 Linux平台 - YOLO Annotation Tool 打包"
echo "============================================"

# 检查Python和pip
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python3 未安装"
    echo "请运行: sudo apt update && sudo apt install python3 python3-pip python3-tk"
    exit 1
fi

# 检查tkinter
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "❌ 错误: tkinter 未安装"
    echo "请运行: sudo apt install python3-tk"
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
    mkdir -p release/linux
    cp -R dist/* release/linux/
    
    # 创建启动脚本
    cat > release/linux/run_yolo_tool.sh << 'EOF'
#!/bin/bash
# YOLO Annotation Tool 启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 启动 YOLO Annotation Tool..."
./YOLO_Annotation_Tool

if [ $? -ne 0 ]; then
    echo "❌ 启动失败，请检查依赖是否安装完整"
    echo "可能需要安装: sudo apt install python3-tk libgl1-mesa-glx"
    read -p "按回车键退出..."
fi
EOF
    
    chmod +x release/linux/run_yolo_tool.sh
    chmod +x release/linux/YOLO_Annotation_Tool
    
    echo "📁 可执行文件位置: release/linux/"
    echo "💡 运行方式:"
    echo "   方法1: ./YOLO_Annotation_Tool"
    echo "   方法2: ./run_yolo_tool.sh (推荐)"
    echo ""
    echo "📦 创建AppImage包 (可选):"
    echo "   1. 下载 appimagetool: wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    echo "   2. chmod +x appimagetool-x86_64.AppImage"
    echo "   3. 创建AppDir结构并打包"
else
    echo "❌ 构建失败!"
    exit 1
fi