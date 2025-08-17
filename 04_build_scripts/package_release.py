#!/usr/bin/env python3
"""
YOLO Annotation Tool - 发布打包脚本
整理构建产物并创建发布包
"""

import os
import sys
import shutil
import platform
from pathlib import Path
from datetime import datetime

def get_platform_info():
    """获取平台信息"""
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    if system == 'darwin':
        system = 'macos'
    elif system == 'windows':
        system = 'windows'
    elif system == 'linux':
        system = 'linux'
    
    return system, arch

def create_release_package():
    """创建发布包"""
    system, arch = get_platform_info()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 创建发布目录
    release_name = f"YOLO_Annotation_Tool_{system}_{arch}_{timestamp}"
    release_dir = Path("release") / release_name
    release_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 创建发布包: {release_name}")
    
    # 复制可执行文件
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("❌ 错误: dist目录不存在，请先运行构建脚本")
        return False
    
    print("📦 复制可执行文件...")
    for item in dist_dir.iterdir():
        if item.is_file():
            shutil.copy2(item, release_dir)
            print(f"   📄 {item.name}")
        elif item.is_dir():
            shutil.copytree(item, release_dir / item.name, dirs_exist_ok=True)
            print(f"   📁 {item.name}/")
    
    # 复制文档文件
    docs_to_copy = [
        "README_BUILD.md",
        "RELEASE_NOTES.md",
        "requirements.txt"
    ]
    
    print("📚 复制文档文件...")
    for doc in docs_to_copy:
        if Path(doc).exists():
            shutil.copy2(doc, release_dir)
            print(f"   📄 {doc}")
    
    # 创建使用说明
    usage_file = release_dir / "使用说明.txt"
    with open(usage_file, 'w', encoding='utf-8') as f:
        f.write(f"""YOLO Annotation Tool v1.0 - 使用说明
========================================

📋 系统要求:
- 操作系统: {system.title()} ({arch})
- 内存: 8GB+ (推荐16GB+)
- 存储: 5GB可用空间

🚀 快速开始:
""")
        
        if system == 'windows':
            f.write("""
1. 双击 YOLO_Annotation_Tool.exe 启动程序
2. 如果提示缺少运行库，请安装 Visual C++ Redistributable
3. 首次启动可能较慢，请耐心等待

💡 提示:
- 右键点击exe文件 → 属性 → 兼容性 → 以管理员身份运行
- 如果杀毒软件误报，请添加到白名单
""")
        elif system == 'macos':
            f.write("""
1. 双击 "YOLO Annotation Tool.app" 启动程序
2. 如果提示"无法验证开发者"，请按以下步骤：
   - 系统偏好设置 → 安全性与隐私 → 点击"仍要打开"
   - 或在终端运行: xattr -cr "YOLO Annotation Tool.app"

💡 提示:
- 也可以在终端运行: ./YOLO_Annotation_Tool
- 首次启动可能较慢，请耐心等待
""")
        elif system == 'linux':
            f.write("""
1. 运行启动脚本: ./run_yolo_tool.sh (推荐)
2. 或直接运行: ./YOLO_Annotation_Tool

💡 如果遇到依赖问题，请安装:
sudo apt update
sudo apt install python3-tk libgl1-mesa-glx libglib2.0-0

💡 提示:
- 确保文件有执行权限: chmod +x YOLO_Annotation_Tool
- 首次启动可能较慢，请耐心等待
""")
        
        f.write("""
📖 详细使用教程:
请查看 README_BUILD.md 文件获取完整使用指南

🔧 故障排除:
请查看 RELEASE_NOTES.md 文件中的故障排除部分

📞 技术支持:
- 邮箱: bquill@qq.com
- 项目: RK3588深度学习平台

版本信息: v1.0.0
构建时间: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + f"""
构建平台: {system}-{arch}
""")
    
    # 创建版本信息文件
    version_file = release_dir / "version.json"
    import json
    version_info = {
        "version": "1.0.0",
        "build_time": datetime.now().isoformat(),
        "platform": f"{system}-{arch}",
        "python_version": platform.python_version(),
        "build_machine": platform.node()
    }
    
    with open(version_file, 'w', encoding='utf-8') as f:
        json.dump(version_info, f, indent=2, ensure_ascii=False)
    
    # 计算文件大小
    total_size = 0
    file_count = 0
    for item in release_dir.rglob('*'):
        if item.is_file():
            total_size += item.stat().st_size
            file_count += 1
    
    total_size_mb = total_size / (1024 * 1024)
    
    print(f"\n✅ 发布包创建完成!")
    print(f"📁 位置: {release_dir.absolute()}")
    print(f"📊 统计: {file_count} 个文件, 总大小 {total_size_mb:.1f} MB")
    
    # 创建压缩包(可选)
    try:
        import zipfile
        zip_file = release_dir.parent / f"{release_name}.zip"
        
        print(f"\n📦 创建压缩包: {zip_file.name}")
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for item in release_dir.rglob('*'):
                if item.is_file():
                    arcname = item.relative_to(release_dir.parent)
                    zf.write(item, arcname)
        
        zip_size_mb = zip_file.stat().st_size / (1024 * 1024)
        print(f"📦 压缩包大小: {zip_size_mb:.1f} MB")
        
    except Exception as e:
        print(f"⚠️  压缩包创建失败: {e}")
    
    return True

def main():
    """主函数"""
    print("📦 YOLO Annotation Tool - 发布打包工具")
    print("=" * 50)
    
    if not create_release_package():
        return 1
    
    print(f"\n🎉 发布打包完成!")
    print(f"\n💡 后续步骤:")
    print(f"   1. 测试可执行文件是否正常运行")
    print(f"   2. 上传到GitHub Releases或其他分发平台")
    print(f"   3. 更新项目文档和版本标签")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())