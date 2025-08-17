#!/usr/bin/env python3
"""
项目文件整理脚本
核心功能：PT转ONNX (针对RK3588)
"""

import os
import shutil
from pathlib import Path

def organize_files():
    """按功能整理项目文件"""
    
    print("🗂️ 开始整理RK3588项目文件...")
    print("核心功能：PT → ONNX → RKNN")
    print("=" * 50)
    
    # 创建目录结构
    directories = {
        "01_core_conversion": "核心转换工具 (PT→ONNX→RKNN)",
        "02_validation_tools": "验证和测试工具",
        "03_annotation_tools": "标注工具集",
        "04_build_scripts": "打包构建脚本",
        "models": "模型文件存储",
        "docs": "文档",
        "datasets": "数据集",
        "temp": "临时文件"
    }
    
    for dir_name, description in directories.items():
        Path(dir_name).mkdir(exist_ok=True)
        print(f"📁 创建: {dir_name}/ - {description}")
    
    # 文件分类映射
    file_mappings = {
        # 核心转换工具
        "01_core_conversion": [
            "simple_rk3588_export.py",  # ⭐ 核心：RK3588专用导出脚本
            "rk3588_export_gui.py",     # ⭐ GUI版本导出工具
            "custom_detect_head.py",     # 自定义检测头
        ],
        
        # 验证工具
        "02_validation_tools": [
            "validate_onnx_cls_format.py",    # ONNX格式验证
            "verify_letterbox_effect.py",     # letterbox效果验证
            "modern_dual_comparator.py",      # PT vs ONNX对比工具
        ],
        
        # 标注工具
        "03_annotation_tools": [
            "auto_annotation_tool_minimal.py",  # 极简版标注工具
            "auto_annotation_tool_classify.py",  # 分类版标注工具
            "auto_annotation_tool_modern.py",    # 现代版标注工具
            "billiard_annotation_tool.py",       # 台球标注工具
        ],
        
        # 构建脚本
        "04_build_scripts": [
            "build.py",
            "build_windows.bat",
            "build_macos.sh", 
            "build_linux.sh",
            "package_release.py",
            "yolo_annotation_tool.spec",
            "bquill.png",
            "bquill.icns",
        ],
        
        # 模型文件
        "models": [
            "best.pt",
            "Q_rim_basketball_20250813.pt",
            "Play_Basketball_2025_5.pt",
            "*.onnx",
            "*.rknn",
        ],
        
        # 文档
        "docs": [
            "README.md",
            "CLAUDE.md",
            "*.md",
        ]
    }
    
    # 执行文件移动
    for target_dir, file_patterns in file_mappings.items():
        for pattern in file_patterns:
            if '*' in pattern:
                # 处理通配符
                for file in Path('.').glob(pattern):
                    if file.is_file() and not str(file).startswith(tuple(directories.keys())):
                        try:
                            shutil.move(str(file), target_dir)
                            print(f"  ✓ {file} → {target_dir}/")
                        except:
                            pass
            else:
                # 处理具体文件
                if Path(pattern).exists() and Path(pattern).is_file():
                    try:
                        shutil.move(pattern, target_dir)
                        print(f"  ✓ {pattern} → {target_dir}/")
                    except:
                        pass
    
    # 创建主README
    create_main_readme()
    
    print("\n✅ 整理完成！")

def create_main_readme():
    """创建主README文件"""
    readme_content = """# RK3588 YOLOv8 部署工具集

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
"""
    
    with open("README_PROJECT.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("📄 创建主README: README_PROJECT.md")

if __name__ == "__main__":
    organize_files()