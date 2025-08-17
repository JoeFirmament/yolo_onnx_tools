# YOLO Annotation Tool - 发布说明

## 📦 可执行文件打包指南

本项目支持生成Windows、macOS、Linux三个平台的可执行文件，方便最终用户直接运行。

### 🛠️ 构建环境要求

#### 通用要求
- Python 3.8+
- 足够的内存空间 (推荐16GB+)
- 网络连接 (用于下载依赖)

#### 平台特定要求
- **Windows**: Windows 10+ / Visual Studio Build Tools
- **macOS**: macOS 10.12+ / Xcode Command Line Tools  
- **Linux**: Ubuntu 18.04+ / 必要的系统库

### 🚀 快速构建

#### 1. 环境准备
```bash
# 激活包含PyTorch和Ultralytics的conda环境
conda activate your_env_name

# 安装打包依赖
pip install pyinstaller opencv-python Pillow
```

#### 2. 构建可执行文件
```bash
# 方法1: 跨平台自动构建
python build.py

# 方法2: 使用平台特定脚本
# Windows:
build_windows.bat

# macOS:
./build_macos.sh

# Linux:
./build_linux.sh

# 方法3: 直接使用PyInstaller
pyinstaller --clean --noconfirm yolo_annotation_tool.spec
```

### 📁 输出文件说明

构建完成后，在 `dist/` 目录中会生成：

#### Windows 平台
```
dist/
├── YOLO_Annotation_Tool.exe    # 单文件可执行程序
└── [依赖库文件]                 # 运行时库
```

#### macOS 平台
```
dist/
├── YOLO_Annotation_Tool        # 命令行可执行文件
└── YOLO Annotation Tool.app/   # macOS应用包
    ├── Contents/
    │   ├── Info.plist
    │   ├── MacOS/
    │   ├── Resources/
    │   └── Frameworks/
    └── [代码签名信息]
```

#### Linux 平台
```
dist/
├── YOLO_Annotation_Tool        # 可执行文件
└── run_yolo_tool.sh            # 启动脚本(推荐使用)
```

### 📊 文件大小参考

| 平台 | 文件大小 | 说明 |
|------|----------|------|
| Windows | ~150MB | 包含完整的PyTorch运行时 |
| macOS | ~140MB | Universal2 二进制文件 |
| Linux | ~160MB | 包含系统兼容层 |

### 🎯 发布流程

#### 1. 准备发布
```bash
# 创建版本标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 构建所有平台(需要相应平台环境)
python build.py

# 创建发布包
mkdir -p release/v1.0.0
cp -r dist/* release/v1.0.0/
```

#### 2. 测试验证
- [ ] 在目标平台上测试可执行文件
- [ ] 验证模型加载功能
- [ ] 测试图片处理流程
- [ ] 验证预览和删除功能

#### 3. 发布检查清单
- [ ] 所有平台可执行文件正常运行
- [ ] README文档更新
- [ ] 版本号更新
- [ ] 发布说明编写完成
- [ ] 测试用例通过

### 🔧 故障排除

#### 构建时常见问题

**Q: 构建失败，提示缺少依赖？**
```bash
# 确保在正确的conda环境中
conda activate your_env_name

# 检查必要依赖
python -c "import torch, ultralytics, cv2, PIL; print('依赖检查通过')"

# 重新安装打包工具
pip install --upgrade pyinstaller
```

**Q: macOS提示无法验证开发者？**
```bash
# 移除扩展属性
xattr -cr "dist/YOLO Annotation Tool.app"

# 或者为app签名(需要开发者证书)
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name" \
  "dist/YOLO Annotation Tool.app"
```

**Q: Linux运行时缺少库？**
```bash
# 安装必要的系统库
sudo apt update
sudo apt install python3-tk libgl1-mesa-glx libglib2.0-0
```

**Q: Windows运行时出现DLL错误？**
- 确保目标机器安装了 Visual C++ Redistributable
- 使用 `--collect-all` 选项重新构建

#### 运行时常见问题

**Q: 程序启动很慢？**
- 正常现象，首次加载PyTorch需要时间
- 后续启动会有缓存，速度会提升

**Q: 显存不足？**
- 程序会自动降级到CPU运行
- 可以关闭其他占用GPU的程序

**Q: 无法加载模型？**
- 检查模型文件格式是否为 `.pt`
- 确保模型是用兼容版本的PyTorch训练的

### 📈 性能优化

#### 减小文件大小
```bash
# 使用UPX压缩(可选)
pyinstaller --upx-dir=/path/to/upx yolo_annotation_tool.spec

# 排除不必要的模块
# 在.spec文件的excludes中添加不需要的包
```

#### 提升启动速度
- 使用 `--onedir` 模式替代 `--onefile`
- 预编译Python字节码
- 使用较小的PyTorch版本

### 🔄 自动化构建

#### GitHub Actions示例
```yaml
name: Build Executables
on: [push, release]

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Build executable
      run: python build.py
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: yolo-tool-${{ matrix.os }}
        path: dist/
```

### 📝 版本历史

#### v1.0.0 (2024-08-16)
- ✨ 初始发布版本
- 🤖 支持YOLOv8自动标注
- 👁️ 实时预览功能
- 🗑️ 标注删除管理
- 💻 跨平台支持(Windows/macOS/Linux)

### 📞 技术支持

如果在构建或使用过程中遇到问题：

1. 查看 [常见问题](#故障排除) 部分
2. 发送邮件至 bquill@qq.com 获取技术支持
3. 请在邮件中详细描述问题和环境信息

---

**📦 成功构建后，可执行文件可以独立运行，无需Python环境！**