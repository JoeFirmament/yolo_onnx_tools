# RK3588 YOLOv8 部署工具集

## 🎯 核心功能：PT → ONNX → RKNN

本项目专注于将PyTorch训练的YOLOv8模型优化部署到瑞芯微RK3588平台。

## 📁 目录结构

```
rk3588_Tutorial/
├── 01_core_conversion/          # ⭐ 核心转换工具
│   ├── simple_rk3588_export.py        # RK3588专用ONNX导出
│   ├── rk3588_export_gui.py           # ONNX导出GUI
│   └── custom_detect_head.py          # 定制检测头
│
├── 02_validation_tools/         # 验证测试工具
│   ├── modern_dual_comparator.py      # PT vs ONNX可视化对比
│   ├── validate_onnx_cls_format.py    # ONNX格式验证
│   └── verify_letterbox_effect.py     # 预处理效果验证
│
├── 03_annotation_tools/         # 📋 标注工具集
│   ├── auto_annotation_tool_classify.py   # 智能分类标注
│   ├── auto_annotation_tool_modern.py     # 全功能标注
│   ├── auto_annotation_tool_minimal.py    # 极简标注
│   ├── billiard_annotation_tool_modern.py # 台球检测标注
│   └── test_gui_buttons.py              # GUI按钮测试
│
├── 04_build_scripts/            # 🔧 打包构建工具
│   ├── build.py               # 跨平台构建主脚本
│   ├── package_release.py     # 发布包生成
│   ├── build_linux.sh         # Linux构建
│   ├── build_macos.sh         # macOS构建
│   ├── build_windows.bat      # Windows构建
│   └── *.spec                 # PyInstaller配置
│
├── 05_ref_data/               # 参考数据
├── 06_models/                 # 🎯 模型文件存放
│   ├── best.pt               # 训练好的PT模型
│   ├── *.onnx                # 导出的ONNX模型
│   └── *.rknn               # RKNN模型
│
├── datasets/                  # 数据集
├── Billiards/                 # 台球检测数据
├── docs/                      # 📋 完整文档
│   ├── tkinter_gui_ultimate_guide.md    # 🎨 GUI开发规范
│   ├── tkinter_gui_archive_*.tar.gz     # 历史归档
│   └── yolov8_*_guide.md                # 技术指南系列
│
├── build/                     # 构建输出目录
├── dist/                      # 分发文件
├── label_sample/              # 标注示例
├── requirements.txt           # 依赖配置
└── README.md                  # 本文件
```

⚠️ **注意**：GUI工具实际已分版本提供，
- 命令行版本：在对应工具目录下
- 可视化版本：主要以GUI形式提供，配套文件迁移

## 🚀 快速开始

### 1. PT转ONNX（命令行版）
```bash
cd 01_core_conversion
python simple_rk3588_export.py ../models/best.pt
```

### 2. PT转ONNX（可视化GUI版）
```bash
python 04_gui_applications/rk3588_export_gui.py
```

### 3. 验证转换结果
```bash
# 命令行验证
python 01_core_conversion/modern_dual_comparator.py

# 可视化验证
python 04_gui_applications/modern_dual_comparator.py
```

### 4. 数据标注工具
```bash
# 智能分类标注（推荐）
python 03_annotation_tools/auto_annotation_tool_classify.py

# 极简标注
python 03_annotation_tools/auto_annotation_tool_minimal.py
```

### 5. 转换为RKNN
```bash
# GUI版本（推荐）
python 01_core_conversion/rk3588_export_gui.py

# 命令行版本（高级用户）
rknn-toolkit2 convert --onnx ../06_models/best.onnx --target rk3588
```

## 🎨 GUI开发指南

项目已实现现代化的Tkinter GUI系统：[📋 tkinter_gui_ultimate_guide.md](docs/tkinter_gui_ultimate_guide.md)

### 核心特性
- **跨平台兼容** - macOS/Windows/Linux 完美运行
- **卡片式界面** - 清晰的功能分区  
- **实时反馈** - 进度条和状态提示
- **统一风格** - 专业级视觉效果

## 📧 联系方式
- Email: bquill@qq.com
- Project: RK3588深度学习平台
