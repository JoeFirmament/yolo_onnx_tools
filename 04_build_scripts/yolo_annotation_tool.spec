# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 自动检测隐藏导入
hidden_imports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'cv2',
    'numpy',
    'torch',
    'torchvision',
    'ultralytics',
    'ultralytics.models',
    'ultralytics.nn',
    'ultralytics.utils',
    'ultralytics.engine',
    'pathlib',
    'json',
    'threading',
    'datetime',
    'warnings',
    're'
]

# 收集ultralytics的所有子模块
ultralytics_imports = collect_submodules('ultralytics')
hidden_imports.extend(ultralytics_imports)

# 收集数据文件
datas = []
datas += collect_data_files('ultralytics')

block_cipher = None

a = Analysis(
    ['auto_annotation_tool_minimal.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'jupyter',
        'notebook',
        'IPython'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YOLO_Annotation_Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设为False隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='bquill.icns'  # 使用自定义图标
)

# macOS 特定配置
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='YOLO Annotation Tool.app',
        icon='bquill.icns',
        bundle_identifier='com.yourcompany.yolo-annotation-tool',
        info_plist={
            'CFBundleName': 'YOLO Annotation Tool',
            'CFBundleDisplayName': 'YOLO Annotation Tool',
            'CFBundleIdentifier': 'com.yourcompany.yolo-annotation-tool',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleInfoDictionaryVersion': '6.0',
            'LSMinimumSystemVersion': '10.12.0',
        },
    )