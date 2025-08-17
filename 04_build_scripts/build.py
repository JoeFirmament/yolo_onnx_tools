#!/usr/bin/env python3
"""
YOLO Annotation Tool - 跨平台打包脚本
支持Windows、macOS、Linux平台的可执行文件生成
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

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

def check_dependencies():
    """检查必要的依赖"""
    required_packages = [
        'pyinstaller',
        'torch',
        'ultralytics',
        'opencv-python',
        'Pillow'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

def clean_build():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"清理目录: {dir_name}")

def build_executable():
    """构建可执行文件"""
    system, arch = get_platform_info()
    
    print(f"🔨 开始构建 {system}-{arch} 平台可执行文件...")
    
    # PyInstaller 命令
    cmd = [
        'pyinstaller',
        '--clean',
        '--noconfirm',
        'yolo_annotation_tool.spec'
    ]
    
    try:
        # 运行PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 构建成功!")
        
        # 显示输出文件信息
        dist_dir = Path('dist')
        if dist_dir.exists():
            print(f"\n📦 输出文件位置: {dist_dir.absolute()}")
            for item in dist_dir.iterdir():
                if item.is_file():
                    size_mb = item.stat().st_size / (1024 * 1024)
                    print(f"   📄 {item.name} ({size_mb:.1f} MB)")
                elif item.is_dir():
                    print(f"   📁 {item.name}/")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败!")
        print(f"错误: {e}")
        if e.stdout:
            print(f"标准输出: {e.stdout}")
        if e.stderr:
            print(f"错误输出: {e.stderr}")
        return False

def create_release_package():
    """创建发布包"""
    system, arch = get_platform_info()
    
    # 创建发布目录
    release_dir = Path(f'release/{system}-{arch}')
    release_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制可执行文件
    dist_dir = Path('dist')
    if dist_dir.exists():
        for item in dist_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, release_dir)
                print(f"复制: {item.name} -> {release_dir}")
            elif item.is_dir() and system == 'macos' and item.suffix == '.app':
                shutil.copytree(item, release_dir / item.name, dirs_exist_ok=True)
                print(f"复制: {item.name} -> {release_dir}")
    
    # 复制说明文件
    docs_to_copy = ['README.md', 'requirements.txt']
    for doc in docs_to_copy:
        if Path(doc).exists():
            shutil.copy2(doc, release_dir)
            print(f"复制: {doc} -> {release_dir}")
    
    print(f"\n📦 发布包已创建: {release_dir.absolute()}")

def main():
    """主函数"""
    print("🚀 YOLO Annotation Tool - 跨平台打包工具")
    print("=" * 50)
    
    # 获取平台信息
    system, arch = get_platform_info()
    print(f"📋 检测到平台: {system}-{arch}")
    
    # 检查依赖
    print(f"\n📋 检查依赖包...")
    if not check_dependencies():
        return 1
    
    # 清理构建目录
    print(f"\n🧹 清理构建目录...")
    clean_build()
    
    # 构建可执行文件
    print(f"\n🔨 开始构建...")
    if not build_executable():
        return 1
    
    # 创建发布包
    print(f"\n📦 创建发布包...")
    create_release_package()
    
    print(f"\n✅ 构建完成!")
    print(f"\n💡 使用说明:")
    print(f"   1. 在 release/{system}-{arch}/ 目录中找到可执行文件")
    print(f"   2. 分发时需要确保目标机器安装了必要的运行库")
    print(f"   3. 首次运行可能需要较长时间加载PyTorch模型")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())