# RK3588 YOLOv8 部署工具集

## 🎯 核心功能：PT → ONNX → RKNN

本项目专注于将PyTorch训练的YOLOv8模型优化部署到瑞芯微RK3588平台。

## 📁 目录结构

```
├── 01_core_conversion/     # ⭐ 核心转换工具
│   ├── simple_rk3588_export.py      # RK3588专用ONNX导出（主程序）
│   ├── validate_onnx_cls_format.py  # ONNX格式验证
│   ├── verify_letterbox_effect.py   # 预处理效果验证
│   └── modern_dual_comparator.py    # PT vs ONNX实时对比
│
├── 02_validation_tools/    # 验证测试工具
│
├── 03_annotation_tools/    # 标注工具集
│   ├── auto_annotation_tool_minimal.py  # 极简版（推荐）
│   └── billiard_annotation_tool.py      # 台球检测标注
│
├── 04_build_scripts/       # 打包构建脚本
│   ├── build.py            # 跨平台构建脚本
│   └── package_release.py  # 发布包生成
│
├── models/                 # 模型文件
│   ├── best.pt            # 训练好的PT模型
│   └── *.onnx             # 导出的ONNX模型
│
└── docs/                   # 文档
```

## 🚀 快速开始

### 1. PT转ONNX（针对RK3588优化）
```bash
cd 01_core_conversion
python simple_rk3588_export.py ../models/best.pt
```

### 2. 验证转换结果
```bash
python modern_dual_comparator.py
```

### 3. 转换为RKNN
```bash
# 使用toolkit2进行量化
rknn-toolkit2 ...
```

## 📧 联系方式
- Email: bquill@qq.com
- Project: RK3588深度学习平台
