#!/usr/bin/env python3
"""
YOLOv8自动标注工具 - 现代化界面版本
采用更清晰的布局和现代化的视觉设计
生成与LabelMe兼容的JSON格式标注文件
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
import math

# 抑制macOS系统警告
warnings.filterwarnings("ignore", category=UserWarning)
if sys.platform == "darwin":  # macOS
    os.environ['TK_SILENCE_DEPRECATION'] = '1'

try:
    import torch
    from ultralytics import YOLO
    DEPENDENCIES_OK = True
except ImportError as e:
    DEPENDENCIES_OK = False
    MISSING_DEPS = str(e)


class ModernAnnotationTool:
    def __init__(self):
        # 检查依赖
        if not DEPENDENCIES_OK:
            self.show_dependency_error()
            return
            
        self.root = tk.Tk()
        self.root.title("YOLO智能标注助手")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # 设置应用图标和窗口属性
        try:
            if sys.platform == "darwin":  # macOS
                self.root.call('wm', 'iconbitmap', self.root._w, '-default')
        except:
            pass
        
        # 现代化配色方案 - 基于参考图的设计
        self.colors = {
            'bg': '#f8f9fa',           # 主背景 - 浅灰白
            'sidebar': '#ffffff',       # 侧边栏背景
            'card': '#ffffff',          # 卡片背景
            'primary': '#ff4757',       # 主色调 - 活力红
            'primary_dark': '#ee3e4f',  # 主色深色
            'success': '#00d68f',       # 成功绿
            'warning': '#ffaa00',       # 警告橙
            'danger': '#ff3d71',        # 危险红
            'info': '#0095ff',          # 信息蓝
            'text': '#192038',          # 主文字 - 深蓝黑
            'text_secondary': '#6e84a3', # 次要文字
            'text_light': '#9ca9b9',    # 辅助文字
            'border': '#e3e8ef',        # 边框色
            'shadow': '#d1dbe6',        # 阴影色
            'hover': '#f5f7fa',         # 悬停背景
            'track': '#f1f3f7',         # 进度条轨道
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
        
        # 文件列表排序状态
        self.sort_column = '文件名'
        self.sort_reverse = False
        
        # 统计变量 - 改进的数据结构
        self.stats = {
            'total_images': 0,
            'processed_images': 0,
            'already_annotated': 0,
            'no_detection_images': 0,
            'detected_objects': 0,
            'processing_time': 0,
            'success_rate': 0,
            'avg_objects_per_image': 0
        }
        
        self.configure_styles()
        self.create_main_layout()
        
    def configure_styles(self):
        """配置现代化TTK样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置颜色和字体
        style.configure('Title.TLabel',
                       background=self.colors['card'],
                       foreground=self.colors['text'],
                       font=('SF Pro Display', 20, 'bold'))
        
        style.configure('Heading.TLabel',
                       background=self.colors['card'],
                       foreground=self.colors['text'],
                       font=('SF Pro Display', 14, 'bold'))
        
        style.configure('Body.TLabel',
                       background=self.colors['card'],
                       foreground=self.colors['text_secondary'],
                       font=('SF Pro Text', 11))
        
        style.configure('Small.TLabel',
                       background=self.colors['card'],
                       foreground=self.colors['text_light'],
                       font=('SF Pro Text', 9))
        
        # 按钮样式
        style.configure('Primary.TButton',
                       font=('SF Pro Text', 11, 'bold'),
                       foreground='white',
                       background=self.colors['primary'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        
        style.map('Primary.TButton',
                 background=[('active', self.colors['primary_dark'])])
        
        style.configure('Secondary.TButton',
                       font=('SF Pro Text', 11),
                       foreground=self.colors['text'],
                       background=self.colors['hover'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        
        style.configure('Success.TButton',
                       font=('SF Pro Text', 11, 'bold'),
                       foreground='white',
                       background=self.colors['success'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        
        # 进度条样式
        style.configure('Custom.Horizontal.TProgressbar',
                       troughcolor=self.colors['track'],
                       background=self.colors['primary'],
                       borderwidth=0,
                       lightcolor=self.colors['primary'],
                       darkcolor=self.colors['primary'])
        
        # ✅ 输入框样式 - 完整的光标设置
        style.configure('Modern.TEntry',
                       fieldbackground=self.colors['card'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.colors['border'],
                       insertcolor=self.colors['text'],  # 🔑 光标颜色
                       insertwidth=2,  # 🔑 光标宽度
                       font=('SF Pro Text', 11))
    
    def create_main_layout(self):
        """创建主布局 - 左侧边栏 + 右主内容区"""
        # 主容器
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True)
        
        # 左侧边栏（固定宽度）
        self.sidebar = tk.Frame(main_container, bg=self.colors['sidebar'], width=320)
        self.sidebar.pack(side='left', fill='y', padx=(0, 1))
        self.sidebar.pack_propagate(False)
        
        # 右侧主内容区
        self.content_area = tk.Frame(main_container, bg=self.colors['bg'])
        self.content_area.pack(side='left', fill='both', expand=True)
        
        # 创建各部分
        self.create_sidebar()
        self.create_content_area()
    
    def create_sidebar(self):
        """创建侧边栏"""
        # Logo区域
        logo_frame = tk.Frame(self.sidebar, bg=self.colors['sidebar'], height=80)
        logo_frame.pack(fill='x', padx=20, pady=(20, 0))
        logo_frame.pack_propagate(False)
        
        # 标题
        title_label = tk.Label(logo_frame, text="🤖 YOLO标注助手",
                              font=('SF Pro Display', 18, 'bold'),
                              bg=self.colors['sidebar'],
                              fg=self.colors['text'])
        title_label.pack(anchor='w', pady=(15, 5))
        
        subtitle_label = tk.Label(logo_frame, text="智能图像标注工具",
                                 font=('SF Pro Text', 11),
                                 bg=self.colors['sidebar'],
                                 fg=self.colors['text_secondary'])
        subtitle_label.pack(anchor='w')
        
        # 分隔线
        self.create_separator(self.sidebar)
        
        # 模型配置区
        self.create_model_section()
        
        # 处理配置区
        self.create_process_section()
        
        # 操作按钮区（固定在底部）
        self.create_action_buttons()
    
    def create_separator(self, parent, height=1):
        """创建分隔线"""
        sep = tk.Frame(parent, bg=self.colors['border'], height=height)
        sep.pack(fill='x', padx=20, pady=15)
        return sep
    
    def create_model_section(self):
        """创建模型配置区"""
        section = tk.Frame(self.sidebar, bg=self.colors['sidebar'])
        section.pack(fill='x', padx=20, pady=(0, 10))
        
        # 区域标题
        tk.Label(section, text="📦 模型配置",
                font=('SF Pro Display', 13, 'bold'),
                bg=self.colors['sidebar'],
                fg=self.colors['text']).pack(anchor='w', pady=(0, 10))
        
        # 模型选择
        tk.Label(section, text="选择模型文件",
                font=('SF Pro Text', 10),
                bg=self.colors['sidebar'],
                fg=self.colors['text_secondary']).pack(anchor='w', pady=(0, 5))
        
        model_frame = tk.Frame(section, bg=self.colors['sidebar'])
        model_frame.pack(fill='x', pady=(0, 10))
        
        self.model_entry = ttk.Entry(model_frame,
                                    textvariable=self.model_path,
                                    style='Modern.TEntry')
        self.model_entry.pack(side='left', fill='x', expand=True)
        
        tk.Button(model_frame, text="浏览",
                 command=self.browse_model,
                 bg=self.colors['primary'],
                 fg='white',
                 relief='flat',
                 font=('SF Pro Text', 10, 'bold'),
                 padx=15,
                 cursor='hand2').pack(side='right', padx=(5, 0))
        
        # 模型状态
        self.model_status = tk.Label(section,
                                    text="⚪ 未加载模型",
                                    font=('SF Pro Text', 10),
                                    bg=self.colors['sidebar'],
                                    fg=self.colors['text_light'])
        self.model_status.pack(anchor='w')
        
        # 图片文件夹选择
        tk.Label(section, text="选择图片文件夹",
                font=('SF Pro Text', 10),
                bg=self.colors['sidebar'],
                fg=self.colors['text_secondary']).pack(anchor='w', pady=(15, 5))
        
        folder_frame = tk.Frame(section, bg=self.colors['sidebar'])
        folder_frame.pack(fill='x', pady=(0, 10))
        
        self.folder_entry = ttk.Entry(folder_frame,
                                     textvariable=self.image_folder,
                                     style='Modern.TEntry')
        self.folder_entry.pack(side='left', fill='x', expand=True)
        
        tk.Button(folder_frame, text="浏览",
                 command=self.browse_folder,
                 bg=self.colors['primary'],
                 fg='white',
                 relief='flat',
                 font=('SF Pro Text', 10, 'bold'),
                 padx=15,
                 cursor='hand2').pack(side='right', padx=(5, 0))
    
    def create_process_section(self):
        """创建处理配置区"""
        section = tk.Frame(self.sidebar, bg=self.colors['sidebar'])
        section.pack(fill='x', padx=20, pady=(0, 10))
        
        # 置信度阈值
        tk.Label(section, text="🎯 检测设置",
                font=('SF Pro Display', 13, 'bold'),
                bg=self.colors['sidebar'],
                fg=self.colors['text']).pack(anchor='w', pady=(0, 10))
        
        tk.Label(section, text="置信度阈值",
                font=('SF Pro Text', 10),
                bg=self.colors['sidebar'],
                fg=self.colors['text_secondary']).pack(anchor='w', pady=(0, 5))
        
        # 置信度滑块框架
        conf_frame = tk.Frame(section, bg=self.colors['sidebar'])
        conf_frame.pack(fill='x', pady=(0, 10))
        
        self.conf_scale = tk.Scale(conf_frame,
                                  from_=0.1, to=0.9,
                                  resolution=0.05,
                                  orient='horizontal',
                                  variable=self.confidence_threshold,
                                  bg=self.colors['sidebar'],
                                  fg=self.colors['text'],
                                  highlightthickness=0,
                                  troughcolor=self.colors['track'],
                                  activebackground=self.colors['primary'],
                                  showvalue=False)
        self.conf_scale.pack(side='left', fill='x', expand=True)
        
        self.conf_label = tk.Label(conf_frame,
                                  text=f"{self.confidence_threshold.get():.2f}",
                                  font=('SF Pro Text', 11, 'bold'),
                                  bg=self.colors['sidebar'],
                                  fg=self.colors['primary'])
        self.conf_label.pack(side='right', padx=(10, 0))
        
        self.conf_scale.config(command=self.update_confidence_label)
        
        # 类别选择区域（动态创建）
        self.class_frame = tk.Frame(section, bg=self.colors['sidebar'])
        self.class_frame.pack(fill='x', pady=(10, 0))
    
    def create_action_buttons(self):
        """创建操作按钮区"""
        # 底部固定区域
        bottom_frame = tk.Frame(self.sidebar, bg=self.colors['sidebar'])
        bottom_frame.pack(side='bottom', fill='x', padx=20, pady=20)
        
        # 开始处理按钮
        self.process_btn = tk.Button(bottom_frame,
                                    text="🚀 开始标注",
                                    command=self.start_processing,
                                    bg=self.colors['success'],
                                    fg='white',
                                    relief='flat',
                                    font=('SF Pro Text', 12, 'bold'),
                                    padx=20,
                                    pady=12,
                                    cursor='hand2')
        self.process_btn.pack(fill='x', pady=(0, 10))
        
        # 停止按钮
        self.stop_btn = tk.Button(bottom_frame,
                                 text="⏹ 停止处理",
                                 command=self.stop_processing,
                                 bg=self.colors['danger'],
                                 fg='white',
                                 relief='flat',
                                 font=('SF Pro Text', 12, 'bold'),
                                 padx=20,
                                 pady=12,
                                 cursor='hand2',
                                 state='disabled')
        self.stop_btn.pack(fill='x')
    
    def create_content_area(self):
        """创建右侧主内容区"""
        # 顶部统计卡片
        self.create_stats_cards()
        
        # 中间进度区域
        self.create_progress_section()
        
        # 底部文件列表
        self.create_file_list_section()
    
    def create_stats_cards(self):
        """创建统计卡片区"""
        cards_frame = tk.Frame(self.content_area, bg=self.colors['bg'])
        cards_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        # 创建4个统计卡片
        cards_data = [
            ("📁", "总文件数", "total_images", self.colors['info']),
            ("✅", "已完成", "processed_images", self.colors['success']),
            ("🎯", "检测目标", "detected_objects", self.colors['warning']),
            ("⏱", "处理时间", "processing_time", self.colors['primary'])
        ]
        
        self.stat_labels = {}
        
        for icon, title, key, color in cards_data:
            card = self.create_stat_card(cards_frame, icon, title, key, color)
            card.pack(side='left', fill='both', expand=True, padx=(0, 10))
    
    def create_stat_card(self, parent, icon, title, key, color):
        """创建单个统计卡片"""
        card = tk.Frame(parent, bg=self.colors['card'], relief='flat')
        card.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        # 内容容器
        content = tk.Frame(card, bg=self.colors['card'])
        content.pack(fill='both', expand=True, padx=20, pady=15)
        
        # 图标和标题行
        header = tk.Frame(content, bg=self.colors['card'])
        header.pack(fill='x')
        
        tk.Label(header, text=icon, font=('', 20), bg=self.colors['card']).pack(side='left')
        tk.Label(header, text=title, font=('SF Pro Text', 11),
                bg=self.colors['card'], fg=self.colors['text_secondary']).pack(side='left', padx=(8, 0))
        
        # 数值
        value_text = "0" if key != "processing_time" else "0.0s"
        value_label = tk.Label(content, text=value_text,
                              font=('SF Pro Display', 28, 'bold'),
                              bg=self.colors['card'], fg=color)
        value_label.pack(anchor='w', pady=(8, 0))
        
        # 保存标签引用
        self.stat_labels[key] = value_label
        
        # 附加信息
        if key == "processed_images":
            self.progress_text = tk.Label(content, text="进度: 0%",
                                         font=('SF Pro Text', 10),
                                         bg=self.colors['card'],
                                         fg=self.colors['text_light'])
            self.progress_text.pack(anchor='w')
        elif key == "detected_objects":
            self.avg_text = tk.Label(content, text="平均: 0/图",
                                    font=('SF Pro Text', 10),
                                    bg=self.colors['card'],
                                    fg=self.colors['text_light'])
            self.avg_text.pack(anchor='w')
        
        return card
    
    def create_progress_section(self):
        """创建进度显示区"""
        progress_frame = tk.Frame(self.content_area, bg=self.colors['card'])
        progress_frame.pack(fill='x', padx=20, pady=(10, 10))
        progress_frame.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        content = tk.Frame(progress_frame, bg=self.colors['card'])
        content.pack(fill='x', padx=20, pady=15)
        
        # 标题行
        header = tk.Frame(content, bg=self.colors['card'])
        header.pack(fill='x', pady=(0, 10))
        
        tk.Label(header, text="处理进度",
                font=('SF Pro Display', 14, 'bold'),
                bg=self.colors['card'],
                fg=self.colors['text']).pack(side='left')
        
        self.status_label = tk.Label(header, text="就绪",
                                    font=('SF Pro Text', 11),
                                    bg=self.colors['card'],
                                    fg=self.colors['text_secondary'])
        self.status_label.pack(side='right')
        
        # 进度条
        self.progress_bar = ttk.Progressbar(content,
                                           variable=self.progress_var,
                                           mode='determinate',
                                           style='Custom.Horizontal.TProgressbar')
        self.progress_bar.pack(fill='x', pady=(0, 10))
        
        # 当前文件
        self.current_file_label = tk.Label(content, text="",
                                          font=('SF Pro Text', 10),
                                          bg=self.colors['card'],
                                          fg=self.colors['text_light'])
        self.current_file_label.pack(anchor='w')
    
    def create_file_list_section(self):
        """创建文件列表区"""
        list_frame = tk.Frame(self.content_area, bg=self.colors['card'])
        list_frame.pack(fill='both', expand=True, padx=20, pady=(10, 20))
        list_frame.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        # 标题栏
        header = tk.Frame(list_frame, bg=self.colors['card'])
        header.pack(fill='x', padx=20, pady=15)
        
        tk.Label(header, text="文件管理",
                font=('SF Pro Display', 14, 'bold'),
                bg=self.colors['card'],
                fg=self.colors['text']).pack(side='left')
        
        # 操作按钮
        btn_frame = tk.Frame(header, bg=self.colors['card'])
        btn_frame.pack(side='right')
        
        tk.Button(btn_frame, text="刷新",
                 command=self.refresh_file_list,
                 bg=self.colors['hover'],
                 fg=self.colors['text'],
                 relief='flat',
                 font=('SF Pro Text', 10),
                 padx=12,
                 cursor='hand2').pack(side='left', padx=(0, 5))
        
        tk.Button(btn_frame, text="预览",
                 command=self.open_preview,
                 bg=self.colors['hover'],
                 fg=self.colors['text'],
                 relief='flat',
                 font=('SF Pro Text', 10),
                 padx=12,
                 cursor='hand2').pack(side='left')
        
        # 文件列表
        list_container = tk.Frame(list_frame, bg=self.colors['card'])
        list_container.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # 创建Treeview
        columns = ('文件名', '状态', '标注数', '修改时间')
        self.file_tree = ttk.Treeview(list_container, columns=columns, show='headings', height=15)
        
        # 设置列
        for col in columns:
            self.file_tree.heading(col, text=col, command=lambda c=col: self.sort_file_list(c))
            self.file_tree.column(col, width=150)
        
        self.file_tree.column('文件名', width=300)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_container, orient='vertical', command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.file_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 绑定事件
        self.file_tree.bind('<Double-1>', self.on_file_double_click)
        
        self.file_list_data = []
    
    def create_class_selection_ui(self):
        """创建类别选择界面"""
        # 清空现有内容
        for widget in self.class_frame.winfo_children():
            widget.destroy()
        
        if not self.class_names:
            return
        
        # 标题和操作按钮
        header = tk.Frame(self.class_frame, bg=self.colors['sidebar'])
        header.pack(fill='x', pady=(0, 10))
        
        tk.Label(header, text="选择标注类别",
                font=('SF Pro Text', 10),
                bg=self.colors['sidebar'],
                fg=self.colors['text_secondary']).pack(side='left')
        
        tk.Button(header, text="全选",
                 command=self.select_all_classes,
                 bg=self.colors['hover'],
                 fg=self.colors['text'],
                 relief='flat',
                 font=('SF Pro Text', 9),
                 padx=8,
                 cursor='hand2').pack(side='right', padx=(5, 0))
        
        tk.Button(header, text="清空",
                 command=self.select_none_classes,
                 bg=self.colors['hover'],
                 fg=self.colors['text'],
                 relief='flat',
                 font=('SF Pro Text', 9),
                 padx=8,
                 cursor='hand2').pack(side='right')
        
        # 类别列表容器（可滚动）
        list_frame = tk.Frame(self.class_frame, bg=self.colors['hover'], height=200)
        list_frame.pack(fill='both', expand=True)
        list_frame.pack_propagate(False)
        
        # 创建Canvas和滚动条
        canvas = tk.Canvas(list_frame, bg=self.colors['hover'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['hover'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 创建类别复选框
        self.class_vars = {}
        self.selected_classes = {}
        
        for i, class_name in enumerate(self.class_names):
            var = tk.BooleanVar(value=False)
            self.class_vars[i] = var
            self.selected_classes[i] = False
            
            # 创建复选框行
            row = tk.Frame(scrollable_frame, bg=self.colors['hover'])
            row.pack(fill='x', padx=10, pady=2)
            
            cb = tk.Checkbutton(row, text=class_name,
                               variable=var,
                               bg=self.colors['hover'],
                               fg=self.colors['text'],
                               selectcolor=self.colors['hover'],
                               activebackground=self.colors['hover'],
                               font=('SF Pro Text', 10),
                               command=lambda idx=i: self.on_class_selection_change(idx))
            cb.pack(anchor='w')
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 更新状态
        self.update_class_selection_status()
    
    def update_stats_display(self):
        """更新统计显示"""
        # 更新统计卡片
        if hasattr(self, 'stat_labels'):
            self.stat_labels['total_images'].config(text=str(self.stats['total_images']))
            self.stat_labels['processed_images'].config(text=str(self.stats['processed_images']))
            self.stat_labels['detected_objects'].config(text=str(self.stats['detected_objects']))
            
            # 处理时间
            time_text = f"{self.stats['processing_time']:.1f}s"
            self.stat_labels['processing_time'].config(text=time_text)
            
            # 进度百分比
            if self.stats['total_images'] > 0:
                progress = (self.stats['processed_images'] / self.stats['total_images']) * 100
                self.progress_text.config(text=f"进度: {progress:.1f}%")
            
            # 平均检测数
            if self.stats['processed_images'] > 0:
                avg = self.stats['detected_objects'] / self.stats['processed_images']
                self.avg_text.config(text=f"平均: {avg:.1f}/图")
    
    def update_processing_time(self):
        """实时更新处理时间"""
        if self.is_processing and hasattr(self, 'process_start_time'):
            import time
            current_time = time.time()
            self.stats['processing_time'] = current_time - self.process_start_time
            self.update_stats_display()
            # 每500毫秒更新一次
            self.root.after(500, self.update_processing_time)
    
    def browse_model(self):
        """浏览模型文件"""
        filename = filedialog.askopenfilename(
            title="选择YOLOv8模型文件",
            filetypes=[("PyTorch模型", "*.pt"), ("所有文件", "*.*")]
        )
        if filename:
            self.model_path.set(filename)
            self.load_model()
    
    def browse_folder(self):
        """浏览图片文件夹"""
        folder = filedialog.askdirectory(title="选择图片文件夹")
        if folder:
            self.image_folder.set(folder)
            self.scan_images()
            self.refresh_file_list()
    
    def load_model(self):
        """加载YOLO模型"""
        model_file = self.model_path.get()
        if not model_file or not os.path.exists(model_file):
            self.model_status.config(text="❌ 模型文件不存在", fg=self.colors['danger'])
            return
        
        self.model_status.config(text="⏳ 正在加载模型...", fg=self.colors['warning'])
        self.root.update_idletasks()
        
        try:
            # 处理PyTorch安全限制
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
            
            # 创建类别选择界面
            self.create_class_selection_ui()
            
            self.model_status.config(text=f"✅ 已加载 ({len(self.class_names)}个类别)",
                                   fg=self.colors['success'])
            
        except Exception as e:
            self.model_status.config(text="❌ 加载失败", fg=self.colors['danger'])
            messagebox.showerror("模型加载错误", f"无法加载模型:\n{str(e)}")
    
    def scan_images(self):
        """扫描图片文件夹"""
        folder = self.image_folder.get()
        if not folder or not os.path.exists(folder):
            return
        
        # 获取所有图片文件
        image_files = []
        for ext in ['*.jpg', '*.JPG', '*.jpeg', '*.JPEG', '*.png', '*.PNG']:
            image_files.extend(Path(folder).glob(ext))
        
        # 统计已有标注
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
        
        # 清空现有列表
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        self.file_list_data = []
        folder = Path(self.image_folder.get())
        
        if not folder.exists():
            return
        
        # 扫描图片文件
        image_files = []
        for ext in ['*.jpg', '*.JPG', '*.jpeg', '*.JPEG', '*.png', '*.PNG']:
            image_files.extend(folder.glob(ext))
        
        image_files.sort()
        
        for img_file in image_files:
            json_file = img_file.with_suffix('.json')
            
            # 获取状态
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        annotations = json_data.get('shapes', [])
                        status = "✅ 已标注"
                        count = len(annotations)
                        mod_time = datetime.fromtimestamp(json_file.stat().st_mtime).strftime("%m-%d %H:%M")
                except:
                    status = "⚠️ 损坏"
                    count = 0
                    mod_time = "-"
            else:
                status = "⭕ 未标注"
                count = 0
                mod_time = "-"
            
            # 添加到列表
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
    
    def sort_file_list(self, column):
        """排序文件列表"""
        # 实现排序逻辑（简化版）
        pass
    
    def on_file_double_click(self, event):
        """双击文件事件"""
        selection = self.file_tree.selection()
        if selection:
            # 可以打开预览窗口
            pass
    
    def on_class_selection_change(self, class_id):
        """类别选择变化"""
        self.selected_classes[class_id] = self.class_vars[class_id].get()
        self.update_class_selection_status()
    
    def update_class_selection_status(self):
        """更新类别选择状态"""
        selected_count = sum(1 for selected in self.selected_classes.values() if selected)
        total_count = len(self.selected_classes)
        
        if selected_count == 0:
            status = "⚪ 请选择标注类别"
            color = self.colors['text_light']
        else:
            status = f"🟢 已选择 {selected_count}/{total_count} 个类别"
            color = self.colors['success']
        
        if hasattr(self, 'model_status') and self.current_model:
            self.model_status.config(text=status, fg=color)
    
    def select_all_classes(self):
        """全选类别"""
        for var in self.class_vars.values():
            var.set(True)
        for class_id in self.selected_classes:
            self.selected_classes[class_id] = True
        self.update_class_selection_status()
    
    def select_none_classes(self):
        """清空类别选择"""
        for var in self.class_vars.values():
            var.set(False)
        for class_id in self.selected_classes:
            self.selected_classes[class_id] = False
        self.update_class_selection_status()
    
    def update_confidence_label(self, value):
        """更新置信度标签"""
        self.conf_label.config(text=f"{float(value):.2f}")
    
    def validate_inputs(self):
        """验证输入"""
        if not self.current_model:
            messagebox.showerror("错误", "请先加载模型")
            return False
        
        if not self.image_folder.get() or not os.path.exists(self.image_folder.get()):
            messagebox.showerror("错误", "请选择有效的图片文件夹")
            return False
        
        if not any(self.selected_classes.values()):
            messagebox.showerror("错误", "请至少选择一个标注类别")
            return False
        
        return True
    
    def start_processing(self):
        """开始处理"""
        if not self.validate_inputs():
            return
        
        self.is_processing = True
        self.process_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        # 在新线程中处理
        self.processing_thread = threading.Thread(target=self.process_images, daemon=True)
        self.processing_thread.start()
    
    def stop_processing(self):
        """停止处理"""
        self.is_processing = False
        self.process_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_label.config(text="已停止")
    
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
            self.root.after(0, lambda: self.status_label.config(text="所有图片已标注"))
            self.is_processing = False
            self.root.after(0, lambda: self.process_btn.config(state='normal'))
            self.root.after(0, lambda: self.stop_btn.config(state='disabled'))
            return
        
        # 重置统计
        self.stats['processed_images'] = 0
        self.stats['detected_objects'] = 0
        
        # 启动实时更新
        self.update_processing_time()
        
        # 处理每张图片
        for i, img_file in enumerate(to_process):
            if not self.is_processing:
                break
            
            # 更新进度
            progress = ((i + 1) / len(to_process)) * 100
            self.root.after(0, lambda p=progress: self.progress_var.set(p))
            self.root.after(0, lambda f=img_file.name: self.current_file_label.config(text=f"处理: {f}"))
            self.root.after(0, lambda: self.status_label.config(text="处理中..."))
            
            try:
                # 运行检测
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
                                detection = {
                                    "label": self.class_names[class_id],
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
                
                # 更新统计
                self.stats['processed_images'] += 1
                self.stats['detected_objects'] += len(detections)
                
            except Exception as e:
                print(f"处理 {img_file} 时出错: {e}")
        
        # 处理完成
        self.is_processing = False
        
        self.root.after(0, lambda: self.progress_var.set(100))
        self.root.after(0, lambda: self.status_label.config(text="处理完成"))
        self.root.after(0, lambda: self.current_file_label.config(text=""))
        self.root.after(0, lambda: self.process_btn.config(state='normal'))
        self.root.after(0, lambda: self.stop_btn.config(state='disabled'))
        self.root.after(0, self.update_stats_display)
        self.root.after(0, self.refresh_file_list)
    
    def open_preview(self):
        """打开预览窗口"""
        # 可以实现预览功能
        messagebox.showinfo("预览", "预览功能开发中...")
    
    def show_dependency_error(self):
        """显示依赖错误"""
        root = tk.Tk()
        root.withdraw()
        
        error_msg = f"""依赖库缺失！

缺失的依赖: {MISSING_DEPS}

请安装以下依赖包:
• pip install ultralytics
• pip install opencv-python
• pip install pillow
• pip install torch torchvision

安装完成后重新运行程序。"""
        
        messagebox.showerror("依赖错误", error_msg)
        root.destroy()
    
    def run(self):
        """运行应用"""
        if not DEPENDENCIES_OK:
            return
        self.root.mainloop()


def main():
    """主函数"""
    print("正在启动YOLO智能标注助手...")
    
    if not DEPENDENCIES_OK:
        print(f"[错误] 依赖库缺失: {MISSING_DEPS}")
        print("请运行以下命令安装依赖:")
        print("pip install ultralytics opencv-python pillow torch torchvision")
        return
    
    print("[成功] 依赖检查通过")
    print("正在初始化界面...")
    
    try:
        app = ModernAnnotationTool()
        app.run()
    except Exception as e:
        print(f"[错误] 应用启动失败: {e}")
        messagebox.showerror("启动错误", f"应用启动失败:\n{str(e)}")


if __name__ == "__main__":
    main()