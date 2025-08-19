# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

这是一个基于RK3588硬件平台的YOLOv8深度学习项目教程，专注于瑞芯微(RockChip)平台上的目标检测模型训练、导出、量化和部署。该项目包含了完整的Ultralytics YOLO框架代码，用于篮球篮筐检测任务。

主要技术栈：
- YOLOv8/YOLO11 目标检测框架
- PyTorch 深度学习框架  
- ONNX 模型导出格式
- RK3588 嵌入式AI芯片部署

## Common Development Commands

### 模型训练
```bash
# 使用Docker环境训练模型
docker run -it --gpus "device=0" --name pytorch24.08 -v ~/train:/softs nvcr.io/nvidia/pytorch:24.08-py3 /bin/bash

# 安装依赖
pip install ultralytics -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install "opencv-python-headless<4.3"
```

### 测试和验证
```bash
# ✅ 主要验证工具
python modern_dual_comparator.py       # PT vs ONNX实时对比GUI工具
python verify_letterbox_effect.py      # letterbox预处理效果验证

# PT模型推理测试
yolo predict model=best.pt source='datasets/temp/images/val/20250811_100002_frame_000142.jpg'

# ultralytics框架测试（可选）
cd ultralytics && pytest tests/         # 运行基础测试
```

### 模型导出
```bash
# ✅ 推荐：RK3588专用导出脚本（非侵入式，完美匹配yolov8_train_inf.md效果）
python simple_rk3588_export.py best.pt

# 标准ONNX导出（用于对比验证）
yolo export model=best.pt format=onnx

# PT vs ONNX实时对比验证
python modern_dual_comparator.py
```

### GUI开发
```bash
# 现代化Tkinter GUI开发 - 参考完整指南
# 详细教程: docs/tkinter_gui_ultimate_guide.md

# 快速启动模板（直接可运行）：
python -c "
import tkinter as tk
from tkinter import ttk
import sys, os, warnings

warnings.filterwarnings('ignore', category=UserWarning)
if sys.platform == 'darwin': os.environ['TK_SILENCE_DEPRECATION'] = '1'

class QuickGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('现代化GUI')
        self.root.geometry('800x600')
        self.colors = {'bg': '#f5f6fa', 'card': '#ffffff', 'primary': '#ff4757'}
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Primary.TButton', background=self.colors['primary'], 
                       foreground='white', borderwidth=0, focuscolor='none', padding=(20,10))
        
        self.root.configure(bg=self.colors['bg'])
        
        main = tk.Frame(self.root, bg=self.colors['bg'])
        main.pack(fill='both', expand=True, padx=20, pady=20)
        
        card = tk.Frame(main, bg=self.colors['card'], highlightbackground='#f1f2f6', highlightthickness=1)
        card.pack(fill='x', pady=10)
        
        content = tk.Frame(card, bg=self.colors['card'])
        content.pack(fill='x', padx=25, pady=25)
        
        ttk.Label(content, text='现代化GUI演示', background=self.colors['card'], 
                 font=('SF Pro Display', 16, 'bold')).pack(anchor='w', pady=(0,10))
        ttk.Button(content, text='点击测试', style='Primary.TButton').pack()
        
        self.root.mainloop()

QuickGUI()
"
```

### 代码质量检查
基于pyproject.toml配置：
```bash
# 代码格式化
ruff format .
yapf --recursive --in-place ultralytics/

# 代码检查
ruff check .

# 类型检查
mypy ultralytics/
```

## Project Architecture

### Core Components

1. **ultralytics/** - 核心YOLO框架
   - `models/yolo/` - YOLO模型定义和实现
   - `engine/` - 训练、验证、预测引擎
   - `nn/` - 神经网络组件和模块
   - `utils/` - 工具函数和辅助模块
   - `cfg/` - 配置文件和数据集定义

2. **weights/** - 模型权重文件存储
   - `yolov8.dict.pt` - 模型状态字典
   - `Rim_Basketball_724_teacher.onnx` - 导出的ONNX模型

3. **datasets/** - 训练数据组织结构
   ```
   datasets/cx/
   ├── images/
   │   ├── train/    # 训练图片
   │   └── val/      # 验证图片
   └── labels/
       ├── train/    # 训练标注
       └── val/      # 验证标注
   ```

### Model Workflow

1. **训练流程**: 使用`ultralytics.YOLO`类加载模型配置，在自定义数据集上训练
2. **导出流程**: 使用`simple_rk3588_export.py`实现RK3588优化的ONNX导出（无需修改源码）
3. **量化部署**: 使用toolkit2工具进行模型量化，适配RK3588硬件

### RK3588平台优化

项目包含针对瑞芯微RK3588平台的特殊优化：

1. **✅ 最终方案**: `simple_rk3588_export.py` - 非侵入式RK3588 ONNX导出
   - 完全复制`yolov8_train_inf.md`侵入式修改的效果
   - 保持ultralytics源码不变
   - 输出格式：6个独立张量 `reg1,cls1,reg2,cls2,reg3,cls3`
   - PT-ONNX完美数值匹配

2. **验证工具**: `modern_dual_comparator.py` - PT vs ONNX实时对比
   - letterbox预处理确保完美匹配
   - 零置信度差异
   - 可视化对比界面

3. **参考文档**: `yolov8_train_inf.md` - 原始侵入式修改方法（仅作参考）

## Dataset Configuration

使用YAML格式定义数据集：
```yaml
path: /path/to/dataset
train: images/train
val: images/val
nc: 2  # 类别数量
names:
  0: target_class_1
  1: target_class_2
```

## 开发注意事项

- ✅ **推荐导出方法**: 使用`simple_rk3588_export.py`进行RK3588模型导出
- 🚫 **不要修改ultralytics源码**: 保持系统干净，便于升级维护
- 🐳 **训练环境**: 建议使用Docker确保依赖一致性
- 🧪 **验证工具**: 使用`modern_dual_comparator.py`验证PT-ONNX一致性
- 📁 **文件组织**: 核心功能在根目录，`ultralytics/`保持原始状态
- 🎯 **面向用户**: 专为中国开发者和RK3588平台用户设计

## Key Files and Scripts

### 核心脚本 (根目录)
- `simple_rk3588_export.py` - **✅ RK3588 ONNX导出脚本** (推荐使用)
- `modern_dual_comparator.py` - **✅ PT vs ONNX实时对比工具**
- `verify_letterbox_effect.py` - letterbox预处理效果验证
- `yolov8_train_inf.md` - 原始侵入式修改方法参考文档

### 模型文件
- `best.pt` - 主要的训练模型权重
- `Q_rim_basketball_20250813.pt` - 备用模型权重
- `ultralytics/rim_basketball.yaml` - 篮球检测任务配置
- `*_rk3588_simple.onnx` - 导出的RK3588优化ONNX模型