#!/usr/bin/env python3
"""
GUI按钮显示测试脚本
用于验证修复后的按钮在macOS上是否正常显示
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

def test_button_styles():
    """测试按钮样式"""
    root = tk.Tk()
    root.title("按钮显示测试 - macOS修复验证")
    root.geometry("600x400")
    root.configure(bg='#f5f6fa')
    
    # 配置样式
    style = ttk.Style()
    style.theme_use('clam')
    
    # 参考auto_annotation_tool_classify.py的成功实现
    style.configure('Primary.TButton',
                   font=('SF Pro Text', 11, 'bold'),
                   foreground='white',
                   background='#ff4757',
                   borderwidth=0,
                   focuscolor='none',
                   padding=(20, 10))
    
    style.configure('Success.TButton',
                   font=('SF Pro Text', 11, 'bold'),
                   foreground='white',
                   background='#2ed573',
                   borderwidth=0,
                   focuscolor='none',
                   padding=(20, 10))
    
    style.configure('Danger.TButton',
                   font=('SF Pro Text', 11, 'bold'),
                   foreground='white',
                   background='#ff3838',
                   borderwidth=0,
                   focuscolor='none',
                   padding=(20, 10))
    
    # 创建测试界面
    main_frame = tk.Frame(root, bg='#f5f6fa')
    main_frame.pack(fill='both', expand=True, padx=30, pady=30)
    
    title_label = tk.Label(
        main_frame,
        text="GUI按钮修复测试",
        font=('SF Pro Display', 20, 'bold'),
        fg='#2f3542',
        bg='#f5f6fa'
    )
    title_label.pack(pady=(0, 30))
    
    # 测试按钮
    button_frame = tk.Frame(main_frame, bg='#f5f6fa')
    button_frame.pack(pady=20)
    
    ttk.Button(
        button_frame,
        text="Primary按钮测试",
        style='Primary.TButton'
    ).pack(side='left', padx=10)
    
    ttk.Button(
        button_frame,
        text="Success按钮测试",
        style='Success.TButton'
    ).pack(side='left', padx=10)
    
    ttk.Button(
        button_frame,
        text="Danger按钮测试",
        style='Danger.TButton'
    ).pack(side='left', padx=10)
    
    # 状态信息
    status_label = tk.Label(
        main_frame,
        text=f"平台: {sys.platform}\n如果你能看到彩色按钮且文字清晰，说明修复成功！",
        font=('SF Pro Text', 12),
        fg='#57606f',
        bg='#f5f6fa',
        justify='center'
    )
    status_label.pack(pady=30)
    
    # 关闭按钮
    close_btn = ttk.Button(
        main_frame,
        text="关闭测试",
        command=root.destroy,
        style='Primary.TButton'
    )
    close_btn.pack(pady=20)
    
    root.mainloop()

if __name__ == "__main__":
    print("🧪 开始GUI按钮显示测试...")
    print(f"🖥️  平台: {sys.platform}")
    
    if sys.platform == "darwin":
        print("🍎 检测到macOS，正在测试修复效果...")
    
    test_button_styles()
    print("✅ 测试完成！")