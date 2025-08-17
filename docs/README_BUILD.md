# YOLO Annotation Tool

一个专为YOLOv8设计的自动标注工具，支持图像自动检测标注、预览管理和标注编辑功能。

## ✨ 主要特性

- 🤖 **智能自动标注** - 基于YOLOv8模型进行图像目标检测
- 🏷️ **类别自定义** - 支持重命名检测类别，满足不同项目需求  
- 👁️ **实时预览** - 单窗口预览模式，支持双击快速切换
- 🗑️ **标注管理** - 支持删除标注，自动同步状态更新
- 📊 **进度统计** - 实时显示处理进度和检测统计
- 🎯 **选择性标注** - 可选择需要标注的特定类别
- 💻 **跨平台支持** - Windows、macOS、Linux全平台支持

## 📋 系统要求

### 最低要求
- **操作系统**: Windows 10+ / macOS 10.12+ / Ubuntu 18.04+
- **内存**: 8GB RAM (推荐16GB+)
- **存储**: 5GB可用空间
- **显卡**: 支持CUDA的GPU (可选，CPU也可运行)

### Python环境 (仅开发者)
- Python 3.8+
- CUDA 11.8+ (GPU加速，可选)

## 🚀 快速开始

### 方式一：直接运行 (推荐)

1. **下载可执行文件**
   - [Windows版本](https://github.com/yourrepo/releases) - `YOLO_Annotation_Tool.exe`
   - [macOS版本](https://github.com/yourrepo/releases) - `YOLO Annotation Tool.app`  
   - [Linux版本](https://github.com/yourrepo/releases) - `YOLO_Annotation_Tool`

2. **运行程序**
   - **Windows**: 双击 `YOLO_Annotation_Tool.exe`
   - **macOS**: 双击 `YOLO Annotation Tool.app`
   - **Linux**: 运行 `./YOLO_Annotation_Tool` 或 `./run_yolo_tool.sh`

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/yourrepo/yolo-annotation-tool.git
cd yolo-annotation-tool

# 安装依赖
pip install -r requirements.txt

# 运行程序
python auto_annotation_tool_minimal.py
```

## 📖 使用指南

### 1. 加载模型
- 点击 **Browse** 选择YOLOv8模型文件 (`.pt` 格式)
- 支持官方预训练模型和自定义训练模型
- 模型加载后会显示支持的类别列表

### 2. 选择类别
- 在类别列表中勾选需要标注的目标类别
- 支持 **全选/全不选** 快速操作
- 可以重命名类别名称以适应项目需求

### 3. 选择图片文件夹
- 点击 **Browse** 选择包含图片的文件夹
- 支持格式: JPG, JPEG, PNG
- 自动扫描并显示文件统计信息

### 4. 开始自动标注
- 设置置信度阈值 (推荐0.5)
- 点击 **START PROCESSING** 开始自动标注
- 实时查看处理进度和统计信息

### 5. 预览和管理
- **双击文件** 快速预览图片和标注
- **右键菜单** 访问预览和删除功能
- **删除标注** 自动同步更新文件状态

## 🛠️ 开发者指南

### 构建可执行文件

```bash
# 安装打包依赖
pip install pyinstaller

# 跨平台自动构建
python build.py

# 或使用平台特定脚本
# Windows:
build_windows.bat

# macOS:
./build_macos.sh

# Linux:
./build_linux.sh
```

### 项目结构
```
yolo-annotation-tool/
├── auto_annotation_tool_minimal.py    # 主程序
├── yolo_annotation_tool.spec          # PyInstaller配置
├── requirements.txt                    # Python依赖
├── build.py                           # 跨平台构建脚本
├── build_windows.bat                  # Windows构建脚本
├── build_macos.sh                     # macOS构建脚本
├── build_linux.sh                     # Linux构建脚本
└── README.md                          # 项目说明
```

## 📝 输出格式

生成的标注文件采用 **LabelMe JSON** 格式，兼容多种标注工具：

```json
{
  "version": "0.4.30",
  "flags": {},
  "shapes": [
    {
      "label": "person",
      "points": [[x1, y1], [x2, y2]],
      "shape_type": "rectangle",
      "flags": {}
    }
  ],
  "imagePath": "image.jpg",
  "imageHeight": 640,
  "imageWidth": 480
}
```

## 🔧 常见问题

### Q: 程序启动很慢？
A: 首次启动需要加载PyTorch模型，请耐心等待。后续启动会更快。

### Q: 显存不足错误？
A: 降低置信度阈值或关闭其他占用GPU的程序。程序会自动使用CPU运行。

### Q: macOS提示"无法验证开发者"？
A: 系统偏好设置 → 安全性与隐私 → 点击"仍要打开"

### Q: Linux下缺少依赖？
A: 运行 `sudo apt install python3-tk libgl1-mesa-glx`

### Q: 标注结果不准确？
A: 调整置信度阈值，或使用更适合的YOLOv8模型

## 🤝 贡献

欢迎提交问题报告和功能请求！

1. Fork本仓库
2. 创建功能分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'Add amazing feature'`
4. 推送分支: `git push origin feature/amazing-feature`
5. 创建Pull Request

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

## 🙏 致谢

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) - 核心检测模型
- [PyInstaller](https://github.com/pyinstaller/pyinstaller) - 跨平台打包工具
- [OpenCV](https://opencv.org/) - 图像处理库
- [PIL/Pillow](https://python-pillow.org/) - 图像处理库

---

**⭐ 如果这个工具对你有帮助，请给个Star支持一下！**