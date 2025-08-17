#!/usr/bin/env python3
"""
YOLOv8自动标注工具 - 极简主义版本
简洁、高效、专注于功能
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path
import threading
from datetime import datetime
from PIL import Image, ImageTk, ImageDraw, ImageFont
import warnings

# 抑制系统警告
warnings.filterwarnings("ignore", category=UserWarning)
if sys.platform == "darwin":
    os.environ['TK_SILENCE_DEPRECATION'] = '1'

try:
    import torch
    from ultralytics import YOLO
    DEPENDENCIES_OK = True
except ImportError as e:
    DEPENDENCIES_OK = False
    MISSING_DEPS = str(e)


class MinimalAnnotationTool:
    def __init__(self):
        if not DEPENDENCIES_OK:
            self.show_dependency_error()
            return
            
        self.root = tk.Tk()
        self.root.title("YOLO Auto Annotation")
        self.root.geometry("1300x850")
        self.root.minsize(1100, 700)
        
        # 极简配色 - 低饱和度状态色
        self.colors = {
            'bg': '#fafafa',           # 背景
            'sidebar': '#ffffff',       # 侧边栏
            'card': '#ffffff',          # 卡片
            'text': '#1a1a1a',          # 主文字 - 更清晰
            'text_secondary': '#4a4a4a', # 次要文字 - 加深  
            'text_light': '#7a7a7a',    # 辅助文字 - 加深
            'border': '#f0f0f0',        # 边框 - 更浅
            'hover': '#f8f8f8',         # 悬停
            'accent': '#2a2a2a',        # 强调色
            # 低饱和度状态色
            'success': '#e8f5e9',       # 成功 - 淡绿背景
            'success_text': '#2e7d32',  # 成功 - 绿色文字
            'error': '#ffebee',         # 错误 - 淡红背景
            'error_text': '#c62828',    # 错误 - 红色文字
            'warning': '#fff3e0',       # 警告 - 淡橙背景
            'warning_text': '#ef6c00',  # 警告 - 橙色文字
            'info': '#e3f2fd',          # 信息 - 淡蓝背景
            'info_text': '#1565c0',     # 信息 - 蓝色文字
        }
        
        # 设置默认字体
        self.fonts = {
            'mono': ('SF Mono', 'Consolas', 'Monaco', 'Courier New'),  # 等宽字体
            'sans': ('SF Pro Text', 'Helvetica Neue', 'Arial'),        # 无衬线字体
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # 初始化变量
        self.model_path = tk.StringVar()
        self.image_folder = tk.StringVar()
        self.confidence_threshold = tk.DoubleVar(value=0.5)
        self.current_model = None
        self.class_names = []
        self.selected_classes = {}
        self.custom_class_names = {}
        self.progress_var = tk.DoubleVar()
        self.is_processing = False
        
        # 排序状态
        self.sort_column = 'Filename'
        self.sort_reverse = False
        
        # 预览窗口管理
        self.preview_window = None
        self.current_preview_path = None
        
        # 统计数据
        self.stats = {
            'total_images': 0,
            'processed_images': 0,
            'already_annotated': 0,
            'no_detection_images': 0,
            'detected_objects': 0,
            'processing_time': 0
        }
        
        self.setup_styles()
        self.create_layout()
        
    def setup_styles(self):
        """设置极简样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 极简按钮 - 极细边框
        style.configure('Minimal.TButton',
                       background=self.colors['card'],
                       foreground=self.colors['text_secondary'],
                       borderwidth=0,
                       focuscolor='none',  # 🔑 关键修复：防止按钮显示异常
                       relief='flat',
                       font=(self.fonts['mono'], 10, 'normal'),
                       padding=(10, 6))
        
        style.map('Minimal.TButton',
                 background=[('active', self.colors['hover'])],
                 foreground=[('active', self.colors['text'])])
        
        # 主要按钮 - 淡色背景
        style.configure('Primary.TButton',
                       background=self.colors['success'],
                       foreground=self.colors['success_text'],
                       borderwidth=0,
                       focuscolor='none',  # 🔑 关键修复：防止按钮显示异常
                       font=(self.fonts['mono'], 10, 'normal'),
                       padding=(10, 8))
        
        style.map('Primary.TButton',
                 background=[('active', '#d4edda')],
                 foreground=[('active', self.colors['success_text'])])
        
        # 进度条
        style.configure('Minimal.Horizontal.TProgressbar',
                       background=self.colors['info_text'],
                       troughcolor=self.colors['info'],
                       borderwidth=0,
                       lightcolor=self.colors['info_text'],
                       darkcolor=self.colors['info_text'])
        
        # ✅ 输入框样式 - 添加完整的光标设置
        style.configure('Modern.TEntry',
                       fieldbackground=self.colors['card'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.colors['border'],
                       insertcolor=self.colors['text'],  # 🔑 光标颜色
                       insertwidth=2,  # 🔑 光标宽度
                       font=(self.fonts['mono'], 9))
    
    def create_layout(self):
        """创建布局"""
        # 主容器
        main = tk.Frame(self.root, bg=self.colors['bg'])
        main.pack(fill='both', expand=True)
        
        # 左侧栏（300px固定宽度）
        self.sidebar = tk.Frame(main, bg=self.colors['sidebar'], width=300)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        
        # 分隔线
        sep = tk.Frame(main, bg=self.colors['border'], width=1)
        sep.pack(side='left', fill='y')
        
        # 右侧内容区
        self.content = tk.Frame(main, bg=self.colors['bg'])
        self.content.pack(side='left', fill='both', expand=True)
        
        self.create_sidebar_content()
        self.create_content_area()
    
    def create_sidebar_content(self):
        """创建侧边栏内容"""
        # 标题
        header = tk.Frame(self.sidebar, bg=self.colors['sidebar'], height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="YOLO Annotation",
                font=(self.fonts['mono'], 15, 'normal'),
                bg=self.colors['sidebar'],
                fg=self.colors['text']).pack(pady=20)
        
        # 内容容器（带内边距）
        container = tk.Frame(self.sidebar, bg=self.colors['sidebar'])
        container.pack(fill='both', expand=True, padx=20)
        
        # 模型部分
        self.create_section_title(container, "Model")
        
        # 模型路径输入
        model_frame = tk.Frame(container, bg=self.colors['sidebar'])
        model_frame.pack(fill='x', pady=(5, 15))
        
        self.model_entry = ttk.Entry(model_frame,
                                    textvariable=self.model_path,
                                    style='Modern.TEntry')
        self.model_entry.pack(side='left', fill='x', expand=True)
        
        ttk.Button(model_frame, text="Browse",
                  command=self.browse_model,
                  style='Minimal.TButton').pack(side='right', padx=(5, 0))
        
        self.model_status = tk.Label(container,
                                    text="No model loaded",
                                    font=(self.fonts['mono'], 9),
                                    bg=self.colors['sidebar'],
                                    fg=self.colors['text_light'],
                                    anchor='w')
        self.model_status.pack(fill='x', pady=(0, 20))
        
        # 图片文件夹部分
        self.create_section_title(container, "Images")
        
        folder_frame = tk.Frame(container, bg=self.colors['sidebar'])
        folder_frame.pack(fill='x', pady=(5, 20))
        
        self.folder_entry = ttk.Entry(folder_frame,
                                     textvariable=self.image_folder,
                                     style='Modern.TEntry')
        self.folder_entry.pack(side='left', fill='x', expand=True)
        
        ttk.Button(folder_frame, text="Browse",
                  command=self.browse_folder,
                  style='Minimal.TButton').pack(side='right', padx=(5, 0))
        
        # 设置部分
        self.create_section_title(container, "Settings")
        
        # 置信度
        tk.Label(container, text="Confidence Threshold",
                font=('Helvetica', 9),
                bg=self.colors['sidebar'],
                fg=self.colors['text_secondary'],
                anchor='w').pack(fill='x', pady=(5, 5))
        
        conf_frame = tk.Frame(container, bg=self.colors['sidebar'])
        conf_frame.pack(fill='x', pady=(0, 20))
        
        self.conf_scale = tk.Scale(conf_frame,
                                  from_=0.1, to=0.9,
                                  resolution=0.05,
                                  orient='horizontal',
                                  variable=self.confidence_threshold,
                                  bg=self.colors['sidebar'],
                                  fg=self.colors['text'],
                                  highlightthickness=0,
                                  troughcolor=self.colors['border'],
                                  activebackground=self.colors['text'],
                                  showvalue=False,
                                  bd=0)
        self.conf_scale.pack(side='left', fill='x', expand=True)
        
        self.conf_label = tk.Label(conf_frame,
                                  text=f"{self.confidence_threshold.get():.2f}",
                                  font=(self.fonts['mono'], 10, 'normal'),
                                  bg=self.colors['sidebar'],
                                  fg=self.colors['text'])
        self.conf_label.pack(side='right', padx=(10, 0))
        
        self.conf_scale.config(command=self.update_confidence_label)
        
        # 类别选择区域
        self.class_container = tk.Frame(container, bg=self.colors['sidebar'])
        self.class_container.pack(fill='both', expand=True, pady=(0, 20))
        
        # 底部按钮
        bottom = tk.Frame(self.sidebar, bg=self.colors['sidebar'])
        bottom.pack(side='bottom', fill='x', padx=20, pady=20)
        
        self.process_btn = tk.Button(bottom,
                                    text="START PROCESSING",
                                    command=self.start_processing,
                                    bg=self.colors['success'],
                                    fg=self.colors['success_text'],
                                    relief='flat',
                                    bd=0,
                                    highlightbackground=self.colors['success_text'],
                                    highlightthickness=1,
                                    font=(self.fonts['mono'], 10, 'normal'),
                                    padx=20,
                                    pady=10,
                                    cursor='hand2')
        self.process_btn.pack(fill='x', pady=(0, 10))
        self.process_btn.bind('<Enter>', lambda e: self.process_btn.config(bg='#d4edda'))
        self.process_btn.bind('<Leave>', lambda e: self.process_btn.config(bg=self.colors['success']))
        
        self.stop_btn = tk.Button(bottom,
                                 text="STOP",
                                 command=self.stop_processing,
                                 bg=self.colors['card'],
                                 fg=self.colors['text_light'],
                                 relief='flat',
                                 bd=0,
                                 highlightbackground=self.colors['border'],
                                 highlightthickness=1,
                                 font=(self.fonts['mono'], 10, 'normal'),
                                 padx=20,
                                 pady=8,
                                 cursor='hand2',
                                 state='disabled')
        self.stop_btn.pack(fill='x')
        self.stop_btn.bind('<Enter>', lambda e: self.stop_btn.config(bg=self.colors['error'], fg=self.colors['error_text']) if self.stop_btn['state'] == 'normal' else None)
        self.stop_btn.bind('<Leave>', lambda e: self.stop_btn.config(bg=self.colors['card'], fg=self.colors['text_secondary']) if self.stop_btn['state'] == 'normal' else None)
        
        # 底部联系信息
        contact_frame = tk.Frame(self.sidebar, bg=self.colors['sidebar'])
        contact_frame.pack(side='bottom', fill='x', padx=20, pady=(0, 10))
        
        # 分隔线
        separator = tk.Frame(contact_frame, bg=self.colors['border'], height=1)
        separator.pack(fill='x', pady=(0, 8))
        
        # 版本信息
        version_label = tk.Label(contact_frame,
                                text="YOLO Annotation Tool v1.0",
                                font=(self.fonts['mono'], 8),
                                bg=self.colors['sidebar'],
                                fg=self.colors['text_light'])
        version_label.pack(anchor='w')
        
        # 联系方式
        contact_label = tk.Label(contact_frame,
                                text="📧 Contact: bquill@qq.com",
                                font=(self.fonts['mono'], 8),
                                bg=self.colors['sidebar'],
                                fg=self.colors['text_light'],
                                cursor='hand2')
        contact_label.pack(anchor='w', pady=(2, 0))
        
        # 关于按钮
        about_label = tk.Label(contact_frame,
                              text="ℹ️ About",
                              font=(self.fonts['mono'], 8),
                              bg=self.colors['sidebar'],
                              fg=self.colors['text_light'],
                              cursor='hand2')
        about_label.pack(anchor='w', pady=(2, 0))
        
        # 绑定点击事件
        contact_label.bind('<Button-1>', lambda e: self.open_email_client())
        contact_label.bind('<Enter>', lambda e: contact_label.config(fg=self.colors['info_text']))
        contact_label.bind('<Leave>', lambda e: contact_label.config(fg=self.colors['text_light']))
        
        about_label.bind('<Button-1>', lambda e: self.show_about_dialog())
        about_label.bind('<Enter>', lambda e: about_label.config(fg=self.colors['info_text']))
        about_label.bind('<Leave>', lambda e: about_label.config(fg=self.colors['text_light']))
    
    def open_email_client(self):
        """打开邮箱客户端"""
        import webbrowser
        try:
            webbrowser.open('mailto:bquill@qq.com?subject=YOLO Annotation Tool - Feedback')
        except Exception as e:
            # 如果无法打开邮箱客户端，显示邮箱地址
            messagebox.showinfo("Contact Information", 
                               "Email: bquill@qq.com\n\n"
                               "Subject: YOLO Annotation Tool - Feedback")
    
    def show_about_dialog(self):
        """显示关于对话框"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About YOLO Annotation Tool")
        about_window.geometry("500x400")
        about_window.configure(bg=self.colors['bg'])
        about_window.resizable(False, False)
        
        # 使窗口居中
        about_window.transient(self.root)
        about_window.grab_set()
        
        # 主框架
        main_frame = tk.Frame(about_window, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 标题
        title_label = tk.Label(main_frame,
                              text="YOLO Annotation Tool",
                              font=(self.fonts['mono'], 18, 'bold'),
                              bg=self.colors['bg'],
                              fg=self.colors['text'])
        title_label.pack(pady=(0, 10))
        
        # 版本信息
        version_label = tk.Label(main_frame,
                                text="Version 1.0.0",
                                font=(self.fonts['mono'], 12),
                                bg=self.colors['bg'],
                                fg=self.colors['text_secondary'])
        version_label.pack(pady=(0, 20))
        
        # 描述文本
        description = """基于YOLOv8的智能图像标注工具
        
🎯 主要功能:
• 自动目标检测与标注
• 可选择性类别过滤
• 自定义类别重命名
• 实时预览与管理
• 批量处理支持

🛠️ 技术栈:
• YOLOv8 深度学习框架
• PyTorch 推理引擎
• OpenCV 图像处理
• Tkinter GUI界面

📋 适用场景:
• 机器学习数据准备
• 计算机视觉标注
• 目标检测数据集制作"""
        
        desc_label = tk.Label(main_frame,
                             text=description,
                             font=(self.fonts['mono'], 10),
                             bg=self.colors['bg'],
                             fg=self.colors['text'],
                             justify='left',
                             anchor='w')
        desc_label.pack(fill='x', pady=(0, 20))
        
        # 联系信息框架
        contact_frame = tk.Frame(main_frame, bg=self.colors['card'], relief='solid', bd=1)
        contact_frame.pack(fill='x', pady=(0, 20))
        
        contact_inner = tk.Frame(contact_frame, bg=self.colors['card'])
        contact_inner.pack(padx=15, pady=15)
        
        # 联系信息标题
        tk.Label(contact_inner,
                text="📞 联系信息",
                font=(self.fonts['mono'], 12, 'bold'),
                bg=self.colors['card'],
                fg=self.colors['text']).pack(anchor='w', pady=(0, 10))
        
        # 邮箱
        email_frame = tk.Frame(contact_inner, bg=self.colors['card'])
        email_frame.pack(fill='x', pady=2)
        
        tk.Label(email_frame,
                text="📧 邮箱:",
                font=(self.fonts['mono'], 10),
                bg=self.colors['card'],
                fg=self.colors['text_secondary']).pack(side='left')
        
        email_link = tk.Label(email_frame,
                             text="bquill@qq.com",
                             font=(self.fonts['mono'], 10, 'underline'),
                             bg=self.colors['card'],
                             fg=self.colors['info_text'],
                             cursor='hand2')
        email_link.pack(side='left', padx=(10, 0))
        email_link.bind('<Button-1>', lambda e: self.open_email_client())
        
        # 项目信息
        tk.Label(contact_inner,
                text="🚀 项目: RK3588深度学习平台",
                font=(self.fonts['mono'], 10),
                bg=self.colors['card'],
                fg=self.colors['text_secondary']).pack(anchor='w', pady=2)
        
        tk.Label(contact_inner,
                text="🔧 技术支持: 瑞芯微AI部署优化",
                font=(self.fonts['mono'], 10),
                bg=self.colors['card'],
                fg=self.colors['text_secondary']).pack(anchor='w', pady=2)
        
        # 按钮框架
        button_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        button_frame.pack(side='bottom')
        
        # 关闭按钮
        close_btn = tk.Button(button_frame,
                             text="关闭",
                             command=about_window.destroy,
                             bg=self.colors['success'],
                             fg=self.colors['success_text'],
                             relief='flat',
                             bd=0,
                             font=(self.fonts['mono'], 10),
                             padx=30,
                             pady=8,
                             cursor='hand2')
        close_btn.pack()
        
        # 焦点设置
        about_window.focus_set()
    
    def create_section_title(self, parent, text):
        """创建分区标题"""
        tk.Label(parent, text=text.upper(),
                font=('Helvetica', 9, 'bold'),
                bg=self.colors['sidebar'],
                fg=self.colors['text_secondary'],
                anchor='w').pack(fill='x', pady=(0, 5))
    
    def create_content_area(self):
        """创建内容区"""
        # 顶部统计
        stats_frame = tk.Frame(self.content, bg=self.colors['bg'])
        stats_frame.pack(fill='x', padx=20, pady=20)
        
        # 4个统计指标
        stats_data = [
            ("Total Files", 'total_images', self.colors['text']),
            ("Processed", 'processed_images', self.colors['success_text']),
            ("Detections", 'detected_objects', self.colors['warning_text']),
            ("Time", 'processing_time', self.colors['text_secondary'])
        ]
        
        self.stat_labels = {}
        for title, key, color in stats_data:
            stat = self.create_stat_widget(stats_frame, title, key, color)
            stat.pack(side='left', fill='both', expand=True, padx=(0, 15))
        
        # 进度条区域
        progress_frame = tk.Frame(self.content, bg=self.colors['card'])
        progress_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # 进度条容器
        prog_container = tk.Frame(progress_frame, bg=self.colors['card'])
        prog_container.pack(fill='x', padx=20, pady=20)
        
        # 状态文字
        status_row = tk.Frame(prog_container, bg=self.colors['card'])
        status_row.pack(fill='x', pady=(0, 10))
        
        tk.Label(status_row, text="Progress",
                font=('Helvetica', 11, 'bold'),
                bg=self.colors['card'],
                fg=self.colors['text']).pack(side='left')
        
        self.status_label = tk.Label(status_row,
                                    text="Ready",
                                    font=(self.fonts['mono'], 9),
                                    bg=self.colors['card'],
                                    fg=self.colors['text_secondary'])
        self.status_label.pack(side='right')
        
        # 进度条
        self.progress_bar = ttk.Progressbar(prog_container,
                                           variable=self.progress_var,
                                           style='Minimal.Horizontal.TProgressbar')
        self.progress_bar.pack(fill='x', pady=(0, 5))
        
        # 当前文件
        self.current_file_label = tk.Label(prog_container,
                                          text="",
                                          font=(self.fonts['mono'], 9),
                                          bg=self.colors['card'],
                                          fg=self.colors['text_light'])
        self.current_file_label.pack(anchor='w')
        
        # 文件列表
        self.create_file_list()
    
    def create_stat_widget(self, parent, title, key, color):
        """创建统计组件"""
        frame = tk.Frame(parent, bg=self.colors['card'])
        frame.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        inner = tk.Frame(frame, bg=self.colors['card'])
        inner.pack(padx=15, pady=12)
        
        # 标题
        tk.Label(inner, text=title,
                font=('Helvetica', 9),
                bg=self.colors['card'],
                fg=self.colors['text_secondary']).pack(anchor='w')
        
        # 数值
        value_text = "0" if key != "processing_time" else "0.0s"
        value_label = tk.Label(inner, text=value_text,
                              font=(self.fonts['mono'], 20, 'normal'),
                              bg=self.colors['card'],
                              fg=color)
        value_label.pack(anchor='w')
        
        self.stat_labels[key] = value_label
        
        # 附加信息
        if key == 'processed_images':
            self.progress_text = tk.Label(inner, text="0%",
                                         font=(self.fonts['mono'], 9),
                                         bg=self.colors['card'],
                                         fg=self.colors['text_light'])
            self.progress_text.pack(anchor='w')
        elif key == 'detected_objects':
            self.avg_text = tk.Label(inner, text="avg: 0",
                                    font=(self.fonts['mono'], 9),
                                    bg=self.colors['card'],
                                    fg=self.colors['text_light'])
            self.avg_text.pack(anchor='w')
        
        return frame
    
    def create_file_list(self):
        """创建文件列表"""
        list_frame = tk.Frame(self.content, bg=self.colors['card'])
        list_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        list_frame.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        # 标题栏
        header = tk.Frame(list_frame, bg=self.colors['card'])
        header.pack(fill='x', padx=20, pady=15)
        
        tk.Label(header, text="File List",
                font=('Helvetica', 11, 'bold'),
                bg=self.colors['card'],
                fg=self.colors['text']).pack(side='left')
        
        # 操作按钮
        ttk.Button(header, text="Refresh",
                  command=self.refresh_file_list,
                  style='Minimal.TButton').pack(side='right', padx=(5, 0))
        
        ttk.Button(header, text="Preview",
                  command=self.open_preview,
                  style='Minimal.TButton').pack(side='right')
        
        # 列表容器
        list_container = tk.Frame(list_frame, bg=self.colors['card'])
        list_container.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Treeview
        columns = ('Filename', 'Status', 'Objects', 'Modified')
        self.file_tree = ttk.Treeview(list_container, columns=columns, show='headings')
        
        # 配置列
        for col in columns:
            self.file_tree.heading(col, text=col, 
                                  command=lambda c=col: self.sort_file_list(c))
            self.file_tree.column(col, width=120)
        
        self.file_tree.column('Filename', width=350)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_container, orient='vertical', 
                                 command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.file_tree.bind('<Double-1>', self.on_file_double_click)
        self.file_tree.bind('<Button-2>', self.on_file_right_click)  # 右键菜单
        self.file_tree.bind('<Button-3>', self.on_file_right_click)  # 右键菜单（Windows）
        
        self.file_list_data = []
    
    def create_class_selection(self):
        """创建类别选择界面"""
        # 清空容器
        for widget in self.class_container.winfo_children():
            widget.destroy()
        
        if not self.class_names:
            return
        
        # 标题行
        header = tk.Frame(self.class_container, bg=self.colors['sidebar'])
        header.pack(fill='x', pady=(0, 10))
        
        tk.Label(header, text="CLASSES",
                font=('Helvetica', 9, 'bold'),
                bg=self.colors['sidebar'],
                fg=self.colors['text_secondary']).pack(side='left')
        
        # 操作按钮
        btn_frame = tk.Frame(header, bg=self.colors['sidebar'])
        btn_frame.pack(side='right')
        
        tk.Label(btn_frame, text="All",
                font=('Helvetica', 9, 'underline'),
                bg=self.colors['sidebar'],
                fg=self.colors['text'],
                cursor='hand2').pack(side='left', padx=(0, 10))
        tk.Label(btn_frame, text="None",
                font=('Helvetica', 9, 'underline'),
                bg=self.colors['sidebar'],
                fg=self.colors['text'],
                cursor='hand2').pack(side='left')
        
        # 绑定点击事件
        btn_frame.winfo_children()[0].bind('<Button-1>', lambda e: self.select_all_classes())
        btn_frame.winfo_children()[1].bind('<Button-1>', lambda e: self.select_none_classes())
        
        # 类别列表框架
        list_frame = tk.Frame(self.class_container, bg=self.colors['card'], 
                             relief='solid', bd=1)
        list_frame.pack(fill='both', expand=True)
        
        # Canvas和滚动条
        canvas = tk.Canvas(list_frame, bg=self.colors['card'], 
                          highlightthickness=0, height=150)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.colors['card'])
        
        scrollable.bind("<Configure>", 
                       lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 创建复选框
        self.class_vars = {}
        self.selected_classes = {}
        self.custom_name_entries = {}
        
        for i, class_name in enumerate(self.class_names):
            var = tk.BooleanVar(value=True)  # 默认选中所有类别
            self.class_vars[i] = var
            self.selected_classes[i] = True
            
            row = tk.Frame(scrollable, bg=self.colors['card'])
            row.pack(fill='x', padx=10, pady=3)
            
            # 复选框
            cb = tk.Checkbutton(row, text="", variable=var,
                               bg=self.colors['card'],
                               activebackground=self.colors['card'],
                               highlightthickness=0,
                               selectcolor=self.colors['card'],
                               command=lambda idx=i: self.on_class_change(idx))
            cb.pack(side='left')
            
            # 类别名（可编辑）
            name_entry = tk.Entry(row, 
                                 bg=self.colors['card'],
                                 fg=self.colors['text'],
                                 relief='flat',
                                 font=(self.fonts['mono'], 9),
                                 highlightthickness=1,
                                 highlightbackground=self.colors['border'],
                                 highlightcolor=self.colors['info_text'],
                                 insertbackground=self.colors['text'],  # 🔑 光标颜色
                                 insertwidth=2,  # 🔑 光标宽度
                                 bd=0)
            name_entry.insert(0, class_name)
            name_entry.pack(side='left', fill='x', expand=True, padx=(5, 0))
            
            self.custom_name_entries[i] = name_entry
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.update_class_status()
    
    def browse_model(self):
        """选择模型文件"""
        filename = filedialog.askopenfilename(
            title="Select YOLO Model",
            filetypes=[("PyTorch Model", "*.pt"), ("All Files", "*.*")]
        )
        if filename:
            self.model_path.set(filename)
            self.load_model()
    
    def browse_folder(self):
        """选择图片文件夹"""
        folder = filedialog.askdirectory(title="Select Image Folder")
        if folder:
            self.image_folder.set(folder)
            self.scan_images()
            self.refresh_file_list()
    
    def load_model(self):
        """加载模型"""
        model_file = self.model_path.get()
        if not model_file or not os.path.exists(model_file):
            self.model_status.config(text="Invalid model file", fg=self.colors['error'])
            return
        
        self.model_status.config(text="Loading model...", fg=self.colors['text_secondary'])
        self.root.update_idletasks()
        
        try:
            # PyTorch安全配置
            import torch.serialization
            torch.serialization.add_safe_globals([
                'ultralytics.nn.tasks.DetectionModel',
                'ultralytics.nn.modules.head.Detect',
                'ultralytics.nn.modules.block.C2f',
                'ultralytics.nn.modules.conv.Conv',
                'ultralytics.nn.modules.conv.DWConv',
                'ultralytics.nn.modules.block.SPPF',
                'torch.nn.modules.upsampling.Upsample',
                'torch.nn.modules.container.Sequential',
                'torch.nn.modules.activation.SiLU'
            ])
            
            self.current_model = YOLO(model_file)
            self.class_names = list(self.current_model.names.values())
            
            # 测试推理
            dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
            test_results = self.current_model(dummy_img, verbose=False)
            
            # 创建类别选择
            self.create_class_selection()
            
            self.model_status.config(text=f"Model loaded ({len(self.class_names)} classes)",
                                   fg=self.colors['success'])
            
        except Exception as e:
            self.model_status.config(text="Failed to load model", fg=self.colors['error'])
            messagebox.showerror("Error", f"Failed to load model:\n{str(e)}")
    
    def scan_images(self):
        """扫描图片文件夹"""
        folder = self.image_folder.get()
        if not folder or not os.path.exists(folder):
            return
        
        image_files = []
        for ext in ['*.jpg', '*.JPG', '*.jpeg', '*.JPEG', '*.png', '*.PNG']:
            image_files.extend(Path(folder).glob(ext))
        
        already_annotated = sum(1 for img in image_files if img.with_suffix('.json').exists())
        
        self.stats['total_images'] = len(image_files)
        self.stats['already_annotated'] = already_annotated
        self.stats['processed_images'] = 0
        self.stats['detected_objects'] = 0
        self.stats['processing_time'] = 0
        
        self.update_stats_display()
    
    def refresh_file_list(self):
        """刷新文件列表"""
        if not self.image_folder.get():
            return
        
        # 清空列表
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        self.file_list_data = []
        folder = Path(self.image_folder.get())
        
        if not folder.exists():
            return
        
        # 扫描文件
        image_files = []
        for ext in ['*.jpg', '*.JPG', '*.jpeg', '*.JPEG', '*.png', '*.PNG']:
            image_files.extend(folder.glob(ext))
        
        image_files.sort()
        
        for img_file in image_files:
            json_file = img_file.with_suffix('.json')
            
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        annotations = json_data.get('shapes', [])
                        status = "Annotated"
                        count = len(annotations)
                        mod_time = datetime.fromtimestamp(json_file.stat().st_mtime).strftime("%m-%d %H:%M")
                except:
                    status = "Error"
                    count = 0
                    mod_time = "-"
            else:
                status = "Pending"
                count = 0
                mod_time = "-"
            
            item_id = self.file_tree.insert('', 'end', values=(
                img_file.name, status, count, mod_time
            ))
            
            self.file_list_data.append({
                'item_id': item_id,
                'image_path': img_file,
                'json_path': json_file,
                'status': status,
                'count': count
            })
        
        # 应用排序
        if hasattr(self, 'sort_column'):
            self.sort_file_list(self.sort_column)
    
    def sort_file_list(self, column):
        """排序文件列表"""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
        data = []
        for item in self.file_tree.get_children():
            values = self.file_tree.item(item)['values']
            data.append((item, values))
        
        # 排序
        col_index = {'Filename': 0, 'Status': 1, 'Objects': 2, 'Modified': 3}
        idx = col_index.get(column, 0)
        
        if column == 'Objects':
            data.sort(key=lambda x: int(x[1][idx]) if str(x[1][idx]).isdigit() else 0,
                     reverse=self.sort_reverse)
        else:
            data.sort(key=lambda x: x[1][idx], reverse=self.sort_reverse)
        
        # 重新排列
        for index, (item, values) in enumerate(data):
            self.file_tree.move(item, '', index)
    
    def on_file_double_click(self, event):
        """双击文件打开预览"""
        selection = self.file_tree.selection()
        if selection:
            # 获取选中文件信息
            item_values = self.file_tree.item(selection[0])['values']
            filename = item_values[0]
            
            # 找到对应的文件路径
            folder = Path(self.image_folder.get())
            image_path = folder / filename
            json_path = image_path.with_suffix('.json')
            
            if image_path.exists():
                # 显示预览窗口（复用现有窗口或创建新窗口）
                self.show_preview(image_path, json_path)
            else:
                messagebox.showerror("Error", f"Image file not found: {filename}")
    
    def on_file_right_click(self, event):
        """右键点击文件显示菜单"""
        # 选择被点击的项目
        item = self.file_tree.identify_row(event.y)
        if item:
            self.file_tree.selection_set(item)
            
            # 获取文件信息
            item_values = self.file_tree.item(item)['values']
            filename = item_values[0]
            status = item_values[1]
            
            # 创建右键菜单
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="Preview", command=lambda: self.open_preview_for_selected())
            
            # 只有已标注的文件才显示删除选项
            if status == "Annotated":
                context_menu.add_separator()
                context_menu.add_command(label="Delete Annotations", 
                                       command=lambda: self.delete_annotations_for_selected())
            
            # 显示菜单
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
    
    def open_preview_for_selected(self):
        """为选中的文件打开预览"""
        selection = self.file_tree.selection()
        if selection:
            # 模拟双击事件
            self.on_file_double_click(None)
    
    def delete_annotations_for_selected(self):
        """删除选中文件的标注"""
        selection = self.file_tree.selection()
        if not selection:
            return
            
        item_values = self.file_tree.item(selection[0])['values']
        filename = item_values[0]
        
        folder = Path(self.image_folder.get())
        image_path = folder / filename
        json_path = image_path.with_suffix('.json')
        
        if json_path.exists():
            self.delete_annotations(image_path, json_path, None)  # 没有预览窗口要关闭
        else:
            messagebox.showwarning("Warning", "No annotations found for this file")
    
    def on_class_change(self, class_id):
        """类别选择变化"""
        self.selected_classes[class_id] = self.class_vars[class_id].get()
        self.update_class_status()
    
    def update_class_status(self):
        """更新类别选择状态"""
        selected = sum(1 for s in self.selected_classes.values() if s)
        total = len(self.selected_classes)
        
        if selected == 0:
            status = "No classes selected"
            color = self.colors['text_light']
        else:
            status = f"{selected}/{total} classes selected"
            color = self.colors['text']
        
        if hasattr(self, 'model_status') and self.current_model:
            self.model_status.config(text=status, fg=color)
    
    def select_all_classes(self):
        """全选"""
        for var in self.class_vars.values():
            var.set(True)
        for class_id in self.selected_classes:
            self.selected_classes[class_id] = True
        self.update_class_status()
    
    def select_none_classes(self):
        """全不选"""
        for var in self.class_vars.values():
            var.set(False)
        for class_id in self.selected_classes:
            self.selected_classes[class_id] = False
        self.update_class_status()
    
    def update_confidence_label(self, value):
        """更新置信度标签"""
        self.conf_label.config(text=f"{float(value):.2f}")
    
    def update_stats_display(self):
        """更新统计显示"""
        if hasattr(self, 'stat_labels'):
            self.stat_labels['total_images'].config(text=str(self.stats['total_images']))
            self.stat_labels['processed_images'].config(text=str(self.stats['processed_images']))
            self.stat_labels['detected_objects'].config(text=str(self.stats['detected_objects']))
            
            time_text = f"{self.stats['processing_time']:.1f}s"
            self.stat_labels['processing_time'].config(text=time_text)
            
            # 进度
            if self.stats['total_images'] > 0:
                progress = (self.stats['processed_images'] / self.stats['total_images']) * 100
                if hasattr(self, 'progress_text'):
                    self.progress_text.config(text=f"{progress:.0f}%")
            
            # 平均
            if self.stats['processed_images'] > 0:
                avg = self.stats['detected_objects'] / self.stats['processed_images']
                if hasattr(self, 'avg_text'):
                    self.avg_text.config(text=f"avg: {avg:.1f}")
    
    def update_processing_time(self):
        """实时更新处理时间"""
        if self.is_processing and hasattr(self, 'process_start_time'):
            import time
            current_time = time.time()
            self.stats['processing_time'] = current_time - self.process_start_time
            self.update_stats_display()
            self.root.after(500, self.update_processing_time)
    
    def validate_inputs(self):
        """验证输入"""
        if not self.current_model:
            messagebox.showerror("Error", "Please load a model first")
            return False
        
        if not self.image_folder.get() or not os.path.exists(self.image_folder.get()):
            messagebox.showerror("Error", "Please select a valid image folder")
            return False
        
        if not any(self.selected_classes.values()):
            messagebox.showerror("Error", "Please select at least one class")
            return False
        
        return True
    
    def start_processing(self):
        """开始处理"""
        if not self.validate_inputs():
            return
        
        # 检查是否有文件需要处理
        folder = Path(self.image_folder.get())
        image_files = []
        for ext in ['*.jpg', '*.JPG', '*.jpeg', '*.JPEG', '*.png', '*.PNG']:
            image_files.extend(folder.glob(ext))
        
        to_process = [img for img in image_files if not img.with_suffix('.json').exists()]
        
        if not to_process:
            messagebox.showinfo("Info", "All images are already annotated")
            return
        
        # 确认开始处理
        result = messagebox.askyesno("Confirm", 
                                   f"Process {len(to_process)} unannotated images?\n"
                                   f"Selected classes: {sum(self.selected_classes.values())}/{len(self.selected_classes)}")
        if not result:
            return
        
        self.is_processing = True
        self.process_btn.config(state='disabled', text="PROCESSING...")
        self.stop_btn.config(state='normal', bg=self.colors['error'], fg=self.colors['error_text'])
        
        self.processing_thread = threading.Thread(target=self.process_images, daemon=True)
        self.processing_thread.start()
    
    def stop_processing(self):
        """停止处理"""
        self.is_processing = False
        self.process_btn.config(state='normal', text="START PROCESSING")
        self.stop_btn.config(state='disabled', bg=self.colors['card'], fg=self.colors['text_light'])
        self.status_label.config(text="Stopped by user")
    
    def process_images(self):
        """处理图片"""
        import time
        self.process_start_time = time.time()
        
        folder = Path(self.image_folder.get())
        
        # 获取需要处理的图片
        image_files = []
        for ext in ['*.jpg', '*.JPG', '*.jpeg', '*.JPEG', '*.png', '*.PNG']:
            image_files.extend(folder.glob(ext))
        
        to_process = [img for img in image_files if not img.with_suffix('.json').exists()]
        
        if not to_process:
            self.root.after(0, lambda: self.status_label.config(text="All files already annotated"))
            self.is_processing = False
            self.root.after(0, lambda: self.process_btn.config(state='normal', text="START PROCESSING"))
            self.root.after(0, lambda: self.stop_btn.config(state='disabled', bg=self.colors['card'], fg=self.colors['text_light']))
            return
        
        # 重置统计
        self.stats['processed_images'] = 0
        self.stats['detected_objects'] = 0
        self.stats['no_detection_images'] = 0
        
        # 启动时间更新
        self.update_processing_time()
        
        # 处理每张图片
        for i, img_file in enumerate(to_process):
            if not self.is_processing:
                break
            
            # 更新进度
            progress = ((i + 1) / len(to_process)) * 100
            self.root.after(0, lambda p=progress: self.progress_var.set(p))
            self.root.after(0, lambda f=img_file.name: self.current_file_label.config(text=f))
            self.root.after(0, lambda: self.status_label.config(text="Processing..."))
            
            try:
                # 检测
                results = self.current_model(str(img_file), conf=self.confidence_threshold.get())
                
                # 获取图片尺寸
                image = cv2.imread(str(img_file))
                height, width = image.shape[:2]
                
                # 解析结果
                detections = []
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            class_id = int(box.cls[0].cpu().numpy())
                            
                            # 只保留选中的类别
                            if class_id in self.selected_classes and self.selected_classes[class_id]:
                                # 获取自定义名称
                                if class_id in self.custom_name_entries:
                                    label = self.custom_name_entries[class_id].get().strip()
                                    if not label:
                                        label = self.class_names[class_id]
                                else:
                                    label = self.class_names[class_id]
                                
                                detection = {
                                    "label": label,
                                    "points": [[float(x1), float(y1)], [float(x2), float(y2)]],
                                    "shape_type": "rectangle",
                                    "flags": {}
                                }
                                detections.append(detection)
                
                # 保存标注
                if detections:
                    json_data = {
                        "version": "0.4.30",
                        "flags": {},
                        "shapes": detections,
                        "imagePath": img_file.name,
                        "imageData": None,
                        "imageHeight": height,
                        "imageWidth": width
                    }
                    
                    json_file = img_file.with_suffix('.json')
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                else:
                    self.stats['no_detection_images'] += 1
                
                # 更新统计
                self.stats['processed_images'] += 1
                self.stats['detected_objects'] += len(detections)
                
            except Exception as e:
                print(f"Error processing {img_file}: {e}")
        
        # 完成
        self.is_processing = False
        
        if hasattr(self, 'process_start_time'):
            self.stats['processing_time'] = time.time() - self.process_start_time
        
        self.root.after(0, lambda: self.progress_var.set(100))
        
        # 生成完成消息
        processed = self.stats['processed_images']
        detected = self.stats['detected_objects']
        skipped = self.stats.get('no_detection_images', 0)
        
        complete_msg = f"Complete! Processed {processed} files, {detected} objects detected"
        if skipped > 0:
            complete_msg += f", {skipped} files had no detections"
        
        self.root.after(0, lambda: self.status_label.config(text=complete_msg))
        self.root.after(0, lambda: self.current_file_label.config(text=""))
        self.root.after(0, lambda: self.process_btn.config(state='normal', text="START PROCESSING"))
        self.root.after(0, lambda: self.stop_btn.config(state='disabled', bg=self.colors['card'], fg=self.colors['text_light']))
        self.root.after(0, self.update_stats_display)
        self.root.after(0, self.refresh_file_list)
    
    def open_preview(self):
        """打开预览"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file to preview")
            return
        
        # 获取选中文件信息
        item_values = self.file_tree.item(selection[0])['values']
        filename = item_values[0]
        
        # 找到对应的文件路径
        folder = Path(self.image_folder.get())
        image_path = folder / filename
        json_path = image_path.with_suffix('.json')
        
        if not image_path.exists():
            messagebox.showerror("Error", f"Image file not found: {filename}")
            return
        
        # 创建预览窗口
        self.show_preview(image_path, json_path)
    
    def show_preview(self, image_path, json_path):
        """显示预览窗口（复用现有窗口或创建新窗口）"""
        # 检查是否已有预览窗口且仍然存在
        window_exists = False
        if self.preview_window:
            try:
                window_exists = self.preview_window.winfo_exists()
            except tk.TclError:
                # 窗口已被销毁
                self.preview_window = None
                window_exists = False
        
        if window_exists:
            # 更新现有窗口内容
            self.update_preview_content(image_path, json_path)
            # 将窗口置于前台
            self.preview_window.lift()
            self.preview_window.focus_force()
        else:
            # 创建新的预览窗口
            self.create_preview_window(image_path, json_path)
    
    def create_preview_window(self, image_path, json_path):
        """创建预览窗口"""
        self.preview_window = tk.Toplevel(self.root)
        self.preview_window.title(f"Preview - {image_path.name}")
        self.preview_window.geometry("800x600")
        self.preview_window.configure(bg=self.colors['bg'])
        self.current_preview_path = image_path
        
        # 设置窗口关闭时的清理回调
        self.preview_window.protocol("WM_DELETE_WINDOW", self.on_preview_window_close)
        
        # 主框架
        self.preview_main_frame = tk.Frame(self.preview_window, bg=self.colors['bg'])
        self.preview_main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 创建预览内容
        self.create_preview_content(image_path, json_path)
    
    def on_preview_window_close(self):
        """预览窗口关闭时的清理"""
        self.preview_window.destroy()
        self.preview_window = None
        self.current_preview_path = None
    
    def update_preview_content(self, image_path, json_path):
        """更新预览窗口内容"""
        if not self.preview_window:
            return
            
        # 更新窗口标题
        self.preview_window.title(f"Preview - {image_path.name}")
        self.current_preview_path = image_path
        
        # 清空现有内容
        for widget in self.preview_main_frame.winfo_children():
            widget.destroy()
        
        # 重新创建内容
        self.create_preview_content(image_path, json_path)
    
    def create_preview_content(self, image_path, json_path):
        """创建预览窗口的内容"""
        # 图片显示区域
        image_frame = tk.Frame(self.preview_main_frame, bg=self.colors['card'], relief='solid', bd=1)
        image_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Canvas和滚动条
        canvas = tk.Canvas(image_frame, bg=self.colors['card'])
        v_scrollbar = ttk.Scrollbar(image_frame, orient='vertical', command=canvas.yview)
        h_scrollbar = ttk.Scrollbar(image_frame, orient='horizontal', command=canvas.xview)
        
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 信息栏
        info_frame = tk.Frame(self.preview_main_frame, bg=self.colors['card'], relief='solid', bd=1)
        info_frame.pack(fill='x', pady=(0, 10))
        
        info_container = tk.Frame(info_frame, bg=self.colors['card'])
        info_container.pack(padx=15, pady=10)
        
        try:
            # 加载并显示图片
            pil_image = Image.open(image_path)
            original_size = pil_image.size
            
            # 加载标注
            annotations = []
            if json_path.exists():
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        annotations = json_data.get('shapes', [])
                except:
                    pass
            
            # 绘制标注框
            if annotations:
                draw_image = pil_image.copy()
                draw = ImageDraw.Draw(draw_image)
                
                for ann in annotations:
                    if ann.get('shape_type') == 'rectangle' and 'points' in ann:
                        points = ann['points']
                        if len(points) >= 2:
                            x1, y1 = points[0]
                            x2, y2 = points[1]
                            
                            # 绘制矩形框
                            draw.rectangle([x1, y1, x2, y2], outline='red', width=2)
                            
                            # 绘制标签
                            label = ann.get('label', 'Unknown')
                            try:
                                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
                            except:
                                font = ImageFont.load_default()
                            
                            # 计算文本尺寸
                            text_bbox = draw.textbbox((0, 0), label, font=font)
                            text_width = text_bbox[2] - text_bbox[0]
                            text_height = text_bbox[3] - text_bbox[1]
                            
                            # 绘制标签背景
                            draw.rectangle([x1, y1-text_height-4, x1+text_width+8, y1], fill='red')
                            # 绘制标签文字
                            draw.text((x1+4, y1-text_height-2), label, fill='white', font=font)
                
                display_image = draw_image
            else:
                display_image = pil_image
            
            # 缩放图片以适应窗口
            max_width, max_height = 760, 500
            if display_image.size[0] > max_width or display_image.size[1] > max_height:
                display_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # 转换为PhotoImage
            photo = ImageTk.PhotoImage(display_image)
            
            # 在Canvas中显示图片
            canvas.create_image(0, 0, anchor='nw', image=photo)
            canvas.configure(scrollregion=canvas.bbox("all"))
            
            # 保持引用
            canvas.image = photo
            
            # 显示信息
            tk.Label(info_container, text=f"File: {image_path.name}",
                    font=(self.fonts['mono'], 10), bg=self.colors['card'], 
                    fg=self.colors['text']).pack(anchor='w')
            
            tk.Label(info_container, text=f"Size: {original_size[0]} × {original_size[1]}",
                    font=(self.fonts['mono'], 10), bg=self.colors['card'], 
                    fg=self.colors['text_secondary']).pack(anchor='w')
            
            if annotations:
                tk.Label(info_container, text=f"Annotations: {len(annotations)} objects",
                        font=(self.fonts['mono'], 10), bg=self.colors['card'], 
                        fg=self.colors['success_text']).pack(anchor='w')
                
                # 显示类别列表
                labels = [ann.get('label', 'Unknown') for ann in annotations]
                label_counts = {}
                for label in labels:
                    label_counts[label] = label_counts.get(label, 0) + 1
                
                label_text = ", ".join([f"{label}({count})" for label, count in label_counts.items()])
                tk.Label(info_container, text=f"Classes: {label_text}",
                        font=(self.fonts['mono'], 9), bg=self.colors['card'], 
                        fg=self.colors['text_light']).pack(anchor='w')
            else:
                tk.Label(info_container, text="No annotations",
                        font=(self.fonts['mono'], 10), bg=self.colors['card'], 
                        fg=self.colors['text_light']).pack(anchor='w')
            
        except Exception as e:
            tk.Label(info_container, text=f"Error loading image: {str(e)}",
                    font=(self.fonts['mono'], 10), bg=self.colors['card'], 
                    fg=self.colors['error_text']).pack(anchor='w')
        
        # 布局Canvas和滚动条
        canvas.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        
        # 按钮框架
        button_frame = tk.Frame(self.preview_main_frame, bg=self.colors['bg'])
        button_frame.pack(pady=5)
        
        # 删除标注按钮（只在有标注时显示）
        if json_path.exists() and annotations:
            delete_btn = tk.Button(button_frame, text="Delete Annotations", 
                                  command=lambda: self.delete_annotations(image_path, json_path, self.preview_window),
                                  bg=self.colors['error'], fg=self.colors['error_text'],
                                  relief='flat', bd=1, padx=20, pady=5,
                                  cursor='hand2')
            delete_btn.pack(side='left', padx=(0, 10))
        elif not json_path.exists():
            # 为未标注的文件提供提示
            no_annotation_label = tk.Label(button_frame, 
                                          text="No annotations • Will be processed during next run",
                                          font=(self.fonts['mono'], 9),
                                          bg=self.colors['bg'], 
                                          fg=self.colors['text_light'])
            no_annotation_label.pack(side='left', padx=(0, 10))
        
        # 关闭按钮
        close_btn = tk.Button(button_frame, text="Close", 
                             command=self.on_preview_window_close,
                             bg=self.colors['card'], fg=self.colors['text'],
                             relief='flat', bd=1, padx=20, pady=5)
        close_btn.pack(side='right')
    
    def delete_annotations(self, image_path, json_path, preview_window):
        """删除标注文件"""
        # 确认删除
        result = messagebox.askyesno("Confirm Delete", 
                                   f"Are you sure you want to delete annotations for:\n{image_path.name}?\n\n"
                                   "This action cannot be undone.")
        if not result:
            return
        
        try:
            # 删除JSON文件
            if json_path.exists():
                json_path.unlink()
                
                # 关闭预览窗口（如果存在）
                if preview_window:
                    preview_window.destroy()
                
                # 同步更新主界面
                self.sync_after_deletion()
                
                # 如果删除的是当前预览的文件，更新预览窗口
                if (self.preview_window and self.preview_window.winfo_exists() and 
                    self.current_preview_path == image_path):
                    self.update_preview_content(image_path, json_path)
                
                # 显示成功消息
                messagebox.showinfo("Success", f"Annotations deleted for {image_path.name}")
            else:
                messagebox.showwarning("Warning", "Annotation file not found")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete annotations:\n{str(e)}")
    
    def sync_after_deletion(self):
        """删除标注后同步更新界面"""
        # 重新扫描图片文件夹，更新统计信息
        self.scan_images()
        
        # 刷新文件列表
        self.refresh_file_list()
        
        # 更新统计显示
        self.update_stats_display()
    
    def show_dependency_error(self):
        """显示依赖错误"""
        root = tk.Tk()
        root.withdraw()
        
        error_msg = f"""Missing dependencies!

{MISSING_DEPS}

Please install:
• pip install ultralytics
• pip install opencv-python
• pip install pillow
• pip install torch torchvision"""
        
        messagebox.showerror("Dependency Error", error_msg)
        root.destroy()
    
    def run(self):
        """运行应用"""
        if not DEPENDENCIES_OK:
            return
        self.root.mainloop()


def main():
    """主函数"""
    print("Starting YOLO Auto Annotation Tool...")
    
    if not DEPENDENCIES_OK:
        print(f"[ERROR] Missing dependencies: {MISSING_DEPS}")
        return
    
    print("[OK] Dependencies checked")
    print("Initializing GUI...")
    print("(Note: macOS system warnings can be ignored)")
    
    try:
        app = MinimalAnnotationTool()
        app.run()
    except Exception as e:
        print(f"[ERROR] Failed to start: {e}")
        messagebox.showerror("Error", f"Failed to start:\n{str(e)}")


if __name__ == "__main__":
    main()