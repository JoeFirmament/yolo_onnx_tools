#!/usr/bin/env python3
"""
基于YOLOv8的图片自动标注工具
使用现代化Tkinter GUI界面，支持PT模型自动标注
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


class ModernAutoAnnotationTool:
    def __init__(self):
        # 检查依赖
        if not DEPENDENCIES_OK:
            self.show_dependency_error()
            return
            
        self.root = tk.Tk()
        self.root.title("YOLOv8 自动标注工具 - AI图片智能标注")
        self.root.geometry("1100x800")
        self.root.minsize(900, 700)
        self.root.configure(bg='#f8f9fa')
        
        # 设置应用图标和窗口属性
        try:
            if sys.platform == "darwin":  # macOS
                self.root.call('wm', 'iconbitmap', self.root._w, '-default')
        except:
            pass
        
        # 现代化配色方案 - 参考健康仪表板设计
        self.colors = {
            'bg': '#f5f6fa',        # 主背景 - 浅紫灰色
            'card': '#ffffff',      # 卡片背景 - 纯白
            'primary': '#ff4757',   # 主色调 - 红色强调
            'success': '#2ed573',   # 成功绿色
            'danger': '#ff3838',    # 错误红色
            'warning': '#ffa502',   # 警告橙色
            'text': '#2f3542',      # 主文字 - 深灰
            'text_muted': '#57606f', # 次要文字 - 中灰
            'text_light': '#a4b0be', # 辅助文字 - 浅灰
            'border': '#f1f2f6',    # 边框色 - 极浅灰
            'accent': '#ff6b7a'     # 辅助强调色
        }
        
        # 初始化变量
        self.model_path = tk.StringVar()
        self.image_folder = tk.StringVar()
        self.confidence_threshold = tk.DoubleVar(value=0.5)
        self.current_model = None
        self.class_names = []
        self.progress_var = tk.DoubleVar()
        self.is_processing = False
        
        # 统计变量
        self.stats = {
            'total_images': 0,
            'processed_images': 0,
            'skipped_images': 0,
            'detected_objects': 0,
            'processing_time': 0
        }
        
        self.configure_styles()
        self.create_widgets()
    
    def configure_styles(self):
        """配置现代化TTK样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 标题样式
        style.configure('Title.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['text'],
                       font=('SF Pro Display', 24, 'bold'))
        
        style.configure('Subtitle.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['text_muted'],
                       font=('SF Pro Text', 12))
        
        style.configure('CardTitle.TLabel',
                       background=self.colors['card'],
                       foreground=self.colors['text'],
                       font=('SF Pro Display', 16, 'bold'))
        
        style.configure('CardValue.TLabel',
                       background=self.colors['card'],
                       foreground=self.colors['text'],
                       font=('SF Pro Display', 32, 'bold'))
        
        style.configure('CardUnit.TLabel',
                       background=self.colors['card'],
                       foreground=self.colors['text_muted'],
                       font=('SF Pro Text', 14))
        
        style.configure('CardDesc.TLabel',
                       background=self.colors['card'],
                       foreground=self.colors['text_light'],
                       font=('SF Pro Text', 11))
        
        style.configure('Info.TLabel',
                       background=self.colors['card'],
                       foreground=self.colors['text'],
                       font=('SF Pro Text', 11))
        
        style.configure('Muted.TLabel',
                       background=self.colors['card'],
                       foreground=self.colors['text_muted'],
                       font=('SF Pro Text', 10))
        
        # 按钮样式
        style.configure('Primary.TButton',
                       font=('SF Pro Text', 11, 'bold'),
                       foreground='white',
                       background=self.colors['primary'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        
        style.configure('Success.TButton',
                       font=('SF Pro Text', 11, 'bold'),
                       foreground='white',
                       background=self.colors['success'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        
        # 输入框样式
        style.configure('Modern.TEntry',
                       fieldbackground=self.colors['card'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.colors['border'],
                       font=('SF Pro Text', 11))
    
    def create_card(self, parent, title, icon=None):
        """创建现代化卡片容器 - 仿健康仪表板风格"""
        # 卡片主容器 - 添加阴影效果
        card = tk.Frame(parent, bg=self.colors['card'], relief='flat', bd=0)
        card.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        # 创建阴影效果（使用额外的Frame）
        shadow = tk.Frame(parent, bg='#e8e9ed', height=2)
        
        # 卡片标题区 - 仿仪表板的标题样式
        header = tk.Frame(card, bg=self.colors['card'])
        header.pack(fill='x', padx=25, pady=(20, 15))
        
        # 标题行 - 图标+标题
        title_row = tk.Frame(header, bg=self.colors['card'])
        title_row.pack(fill='x')
        
        # 左侧标题
        title_label = ttk.Label(title_row, text=title, style='CardTitle.TLabel')
        title_label.pack(side='left')
        
        # 卡片内容区 - 增加边距
        content = tk.Frame(card, bg=self.colors['card'])
        content.pack(fill='both', expand=True, padx=25, pady=(0, 25))
        
        return card, content
    
    def create_widgets(self):
        """创建主界面"""
        # 主容器 - 仪表板风格布局
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True, padx=25, pady=20)
        
        # 应用标题区
        self.create_header(main_container)
        
        # 第一行：配置卡片（左右布局）
        config_row = tk.Frame(main_container, bg=self.colors['bg'])
        config_row.pack(fill='x', pady=(0, 20))
        
        # 左侧：模型配置
        model_frame = tk.Frame(config_row, bg=self.colors['bg'])
        model_frame.pack(side='left', fill='both', expand=True, padx=(0, 15))
        self.create_model_card(model_frame)
        
        # 右侧：处理配置
        process_frame = tk.Frame(config_row, bg=self.colors['bg'])  
        process_frame.pack(side='right', fill='both', expand=True, padx=(15, 0))
        self.create_processing_card(process_frame)
        
        # 第二行：进度卡片（全宽）
        progress_row = tk.Frame(main_container, bg=self.colors['bg'])
        progress_row.pack(fill='x', pady=(0, 20))
        self.create_progress_card(progress_row)
        
        # 第三行：文件管理 + 统计信息（左右布局）
        bottom_row = tk.Frame(main_container, bg=self.colors['bg'])
        bottom_row.pack(fill='both', expand=True)
        
        # 左侧：文件管理面板
        file_manager_frame = tk.Frame(bottom_row, bg=self.colors['bg'])
        file_manager_frame.pack(side='left', fill='both', expand=True, padx=(0, 15))
        self.create_file_manager_card(file_manager_frame)
        
        # 右侧：统计信息卡片组
        stats_frame = tk.Frame(bottom_row, bg=self.colors['bg'])
        stats_frame.pack(side='right', fill='both', expand=True, padx=(15, 0))
        self.create_stats_card(stats_frame)
        
        # 预览窗口（独立窗口）
        self.preview_window = None
    
    def create_header(self, parent):
        """创建应用标题区"""
        title_frame = tk.Frame(parent, bg=self.colors['bg'])
        title_frame.pack(fill='x', pady=(0, 25))
        
        ttk.Label(title_frame, text="AI自动标注工具", 
                 style='Title.TLabel').pack(anchor='w')
        ttk.Label(title_frame, text="基于YOLOv8的智能图片标注系统，自动生成LabelMe格式JSON文件", 
                 style='Subtitle.TLabel').pack(anchor='w', pady=(5, 0))
    
    def create_model_card(self, parent):
        """创建模型配置卡片"""
        card, content = self.create_card(parent, "模型配置")
        card.pack(fill='x', pady=(0, 15))
        
        # 模型文件选择
        model_frame = tk.Frame(content, bg=self.colors['card'])
        model_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(model_frame, text="YOLOv8 模型文件 (.pt)", style='Info.TLabel').pack(anchor='w', pady=(0, 5))
        
        model_row = tk.Frame(model_frame, bg=self.colors['card'])
        model_row.pack(fill='x')
        
        self.model_entry = ttk.Entry(model_row, textvariable=self.model_path, style='Modern.TEntry')
        self.model_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        ttk.Button(model_row, text="浏览", command=self.browse_model, 
                  style='Primary.TButton').pack(side='right')
        
        # 模型状态显示
        self.model_status = ttk.Label(content, text="[待选择] 请选择YOLOv8模型文件", style='Muted.TLabel')
        self.model_status.pack(anchor='w')
    
    def create_processing_card(self, parent):
        """创建处理配置卡片"""
        card, content = self.create_card(parent, "处理配置")
        card.pack(fill='x', pady=(0, 15))
        
        # 图片文件夹选择
        folder_frame = tk.Frame(content, bg=self.colors['card'])
        folder_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(folder_frame, text="图片文件夹", style='Info.TLabel').pack(anchor='w', pady=(0, 5))
        
        folder_row = tk.Frame(folder_frame, bg=self.colors['card'])
        folder_row.pack(fill='x')
        
        self.folder_entry = ttk.Entry(folder_row, textvariable=self.image_folder, style='Modern.TEntry')
        self.folder_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        ttk.Button(folder_row, text="浏览", command=self.browse_folder, 
                  style='Primary.TButton').pack(side='right')
        
        # 置信度阈值
        conf_frame = tk.Frame(content, bg=self.colors['card'])
        conf_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(conf_frame, text="置信度阈值", style='Info.TLabel').pack(anchor='w', pady=(0, 5))
        
        conf_row = tk.Frame(conf_frame, bg=self.colors['card'])
        conf_row.pack(fill='x')
        
        self.conf_scale = tk.Scale(conf_row, from_=0.1, to=0.9, resolution=0.05, 
                                  orient='horizontal', variable=self.confidence_threshold,
                                  bg=self.colors['card'], fg=self.colors['text'],
                                  highlightthickness=0, troughcolor=self.colors['border'])
        self.conf_scale.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        self.conf_label = ttk.Label(conf_row, text=f"{self.confidence_threshold.get():.2f}", style='Info.TLabel')
        self.conf_label.pack(side='right')
        
        # 绑定置信度变化事件
        self.conf_scale.config(command=self.update_confidence_label)
        
        # 开始处理按钮
        button_frame = tk.Frame(content, bg=self.colors['card'])
        button_frame.pack(fill='x', pady=(10, 0))
        
        self.process_btn = ttk.Button(button_frame, text="开始自动标注", 
                                     command=self.start_processing, style='Success.TButton')
        self.process_btn.pack(side='right')
        
        self.stop_btn = ttk.Button(button_frame, text="停止处理", 
                                  command=self.stop_processing, style='Primary.TButton', state='disabled')
        self.stop_btn.pack(side='right', padx=(0, 10))
        
        # 预览按钮
        self.preview_btn = ttk.Button(button_frame, text="预览标注", 
                                     command=self.open_preview_window, style='Primary.TButton')
        self.preview_btn.pack(side='right', padx=(0, 10))
    
    def create_progress_card(self, parent):
        """创建进度显示卡片"""
        card, content = self.create_card(parent, "处理进度")
        card.pack(fill='x', pady=(0, 15))
        
        # 进度条
        self.progress_bar = ttk.Progressbar(content, variable=self.progress_var, 
                                           length=500, mode='determinate')
        self.progress_bar.pack(fill='x', pady=(0, 10))
        
        # 状态文字
        self.status_label = ttk.Label(content, text="[就绪] 准备开始处理", style='Info.TLabel')
        self.status_label.pack(anchor='w')
        
        # 当前处理文件
        self.current_file_label = ttk.Label(content, text="", style='Muted.TLabel')
        self.current_file_label.pack(anchor='w', pady=(5, 0))
    
    def create_stats_card(self, parent):
        """创建统计信息卡片 - 仪表板风格"""
        # 创建两行布局
        stats_row1 = tk.Frame(parent, bg=self.colors['bg'])
        stats_row1.pack(fill='x', pady=(0, 15))
        
        stats_row2 = tk.Frame(parent, bg=self.colors['bg'])
        stats_row2.pack(fill='both', expand=True)
        
        # 第一行：三个小卡片
        self.create_file_stats_card(stats_row1)
        self.create_detection_stats_card(stats_row1)
        self.create_progress_stats_card(stats_row1)
        
        # 第二行：详细日志卡片
        self.create_log_card(stats_row2)
    
    def create_file_stats_card(self, parent):
        """文件统计卡片"""
        card, content = self.create_card(parent, "文件统计")
        card.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # 主要数值
        value_frame = tk.Frame(content, bg=self.colors['card'])
        value_frame.pack(fill='x', pady=(10, 15))
        
        self.total_files_label = ttk.Label(value_frame, text="0", style='CardValue.TLabel')
        self.total_files_label.pack()
        
        unit_label = ttk.Label(value_frame, text="总图片", style='CardUnit.TLabel')
        unit_label.pack()
        
        # 详细信息
        details_frame = tk.Frame(content, bg=self.colors['card'])
        details_frame.pack(fill='x')
        
        self.processed_label = ttk.Label(details_frame, text="已处理: 0", style='CardDesc.TLabel')
        self.processed_label.pack(anchor='w')
        
        self.pending_label = ttk.Label(details_frame, text="待处理: 0", style='CardDesc.TLabel')
        self.pending_label.pack(anchor='w')
    
    def create_detection_stats_card(self, parent):
        """检测统计卡片"""
        card, content = self.create_card(parent, "检测统计")
        card.pack(side='left', fill='both', expand=True, padx=(5, 5))
        
        # 主要数值
        value_frame = tk.Frame(content, bg=self.colors['card'])
        value_frame.pack(fill='x', pady=(10, 15))
        
        self.total_detections_label = ttk.Label(value_frame, text="0", style='CardValue.TLabel')
        self.total_detections_label.pack()
        
        unit_label = ttk.Label(value_frame, text="检测对象", style='CardUnit.TLabel')
        unit_label.pack()
        
        # 详细信息
        details_frame = tk.Frame(content, bg=self.colors['card'])
        details_frame.pack(fill='x')
        
        self.avg_per_image_label = ttk.Label(details_frame, text="平均/图: 0", style='CardDesc.TLabel')
        self.avg_per_image_label.pack(anchor='w')
    
    def create_progress_stats_card(self, parent):
        """进度统计卡片"""
        card, content = self.create_card(parent, "处理时间")
        card.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # 主要数值
        value_frame = tk.Frame(content, bg=self.colors['card'])
        value_frame.pack(fill='x', pady=(10, 15))
        
        self.processing_time_label = ttk.Label(value_frame, text="0.0", style='CardValue.TLabel')
        self.processing_time_label.pack()
        
        unit_label = ttk.Label(value_frame, text="秒", style='CardUnit.TLabel')
        unit_label.pack()
        
        # 状态信息
        self.status_desc_label = ttk.Label(content, text="等待开始", style='CardDesc.TLabel')
        self.status_desc_label.pack()
    
    def create_log_card(self, parent):
        """日志详情卡片"""
        card, content = self.create_card(parent, "处理日志")
        card.pack(fill='both', expand=True)
        
        # 日志文本区域
        self.stats_text = tk.Text(content, height=6, bg=self.colors['card'], 
                                 fg=self.colors['text'], font=('SF Mono', 10),
                                 relief='flat', wrap='word', bd=0)
        self.stats_text.pack(fill='both', expand=True)
        
        # 初始化日志
        self.update_stats_display()
    
    def create_file_manager_card(self, parent):
        """创建文件管理卡片"""
        card, content = self.create_card(parent, "文件管理")
        card.pack(fill='both', expand=True)
        
        # 工具栏
        toolbar = tk.Frame(content, bg=self.colors['card'])
        toolbar.pack(fill='x', pady=(0, 15))
        
        # 刷新按钮
        ttk.Button(toolbar, text="刷新列表", command=self.refresh_file_list, 
                  style='Primary.TButton').pack(side='left', padx=(0, 10))
        
        # 全选/取消按钮
        ttk.Button(toolbar, text="全选", command=self.select_all_files, 
                  style='Primary.TButton').pack(side='left', padx=(0, 10))
        
        ttk.Button(toolbar, text="取消选择", command=self.deselect_all_files, 
                  style='Primary.TButton').pack(side='left', padx=(0, 10))
        
        # 批量操作按钮
        ttk.Button(toolbar, text="删除选中标注", command=self.delete_selected_annotations, 
                  style='Primary.TButton').pack(side='right')
        
        # 文件列表区域
        list_frame = tk.Frame(content, bg=self.colors['card'])
        list_frame.pack(fill='both', expand=True)
        
        # 创建Treeview用于显示文件列表
        columns = ('文件名', '状态', '标注数', '最后修改')
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        # 设置列标题
        self.file_tree.heading('文件名', text='文件名')
        self.file_tree.heading('状态', text='标注状态')
        self.file_tree.heading('标注数', text='标注数量')
        self.file_tree.heading('最后修改', text='最后修改')
        
        # 设置列宽
        self.file_tree.column('文件名', width=200)
        self.file_tree.column('状态', width=80)
        self.file_tree.column('标注数', width=60)
        self.file_tree.column('最后修改', width=120)
        
        # 滚动条
        file_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=file_scrollbar.set)
        
        # 布局
        self.file_tree.pack(side='left', fill='both', expand=True)
        file_scrollbar.pack(side='right', fill='y')
        
        # 右键菜单
        self.create_context_menu()
        
        # 绑定事件
        self.file_tree.bind('<Double-1>', self.on_file_double_click)
        self.file_tree.bind('<Button-2>', self.show_context_menu)  # 右键
        self.file_tree.bind('<Button-3>', self.show_context_menu)  # 右键（Windows）
        
        # 初始化空列表
        self.file_list_data = []
    
    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="查看标注", command=self.view_annotation)
        self.context_menu.add_command(label="编辑标注", command=self.edit_annotation)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除标注", command=self.delete_annotation)
        self.context_menu.add_command(label="重新标注", command=self.re_annotate_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="在文件管理器中显示", command=self.show_in_finder)
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        # 选择点击的项目
        item = self.file_tree.identify_row(event.y)
        if item:
            self.file_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
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
        
        # 按文件名排序
        image_files.sort()
        
        for img_file in image_files:
            json_file = img_file.with_suffix('.json')
            
            # 获取标注状态和数量
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        annotations = json_data.get('shapes', [])
                        status = "已标注"
                        count = len(annotations)
                        # 获取文件修改时间
                        mod_time = json_file.stat().st_mtime
                        mod_time_str = datetime.fromtimestamp(mod_time).strftime("%m-%d %H:%M")
                except:
                    status = "损坏"
                    count = 0
                    mod_time_str = "-"
            else:
                status = "未标注"
                count = 0
                mod_time_str = "-"
            
            # 添加到列表
            item_id = self.file_tree.insert('', 'end', values=(
                img_file.name, status, count, mod_time_str
            ))
            
            # 根据状态设置颜色
            if status == "已标注":
                self.file_tree.set(item_id, '状态', status)
            elif status == "损坏":
                self.file_tree.set(item_id, '状态', status)
            
            # 存储文件路径信息
            self.file_list_data.append({
                'item_id': item_id,
                'image_path': img_file,
                'json_path': json_file,
                'status': status,
                'count': count
            })
    
    def on_file_double_click(self, event):
        """双击文件事件"""
        selection = self.file_tree.selection()
        if selection:
            self.view_annotation()
    
    def view_annotation(self):
        """查看标注"""
        selection = self.file_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        file_info = next((f for f in self.file_list_data if f['item_id'] == item_id), None)
        
        if file_info:
            # 打开预览窗口并定位到该文件
            if self.preview_window is None:
                self.open_preview_window()
            
            # 在预览窗口中定位到该文件
            if self.preview_window and hasattr(self.preview_window, 'locate_file'):
                self.preview_window.locate_file(file_info['image_path'].name)
    
    def edit_annotation(self):
        """编辑标注"""
        selection = self.file_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        file_info = next((f for f in self.file_list_data if f['item_id'] == item_id), None)
        
        if file_info and file_info['json_path'].exists():
            self.open_annotation_editor(file_info['image_path'], file_info['json_path'])
    
    def delete_annotation(self):
        """删除单个标注"""
        selection = self.file_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        file_info = next((f for f in self.file_list_data if f['item_id'] == item_id), None)
        
        if file_info and file_info['json_path'].exists():
            result = messagebox.askyesno("确认删除", 
                                       f"确定要删除 {file_info['image_path'].name} 的标注文件吗？")
            if result:
                try:
                    file_info['json_path'].unlink()
                    messagebox.showinfo("删除成功", "标注文件已删除")
                    self.refresh_file_list()
                    self.scan_images()  # 更新统计
                except Exception as e:
                    messagebox.showerror("删除失败", f"删除标注文件失败:\n{str(e)}")
    
    def re_annotate_file(self):
        """重新标注单个文件"""
        selection = self.file_tree.selection()
        if not selection:
            return
        
        if not self.current_model:
            messagebox.showwarning("警告", "请先加载模型")
            return
        
        item_id = selection[0]
        file_info = next((f for f in self.file_list_data if f['item_id'] == item_id), None)
        
        if file_info:
            try:
                # 删除现有标注（如果存在）
                if file_info['json_path'].exists():
                    file_info['json_path'].unlink()
                
                # 重新标注
                detections = self.process_single_image(file_info['image_path'])
                
                messagebox.showinfo("标注完成", 
                                  f"重新标注完成\n检测到 {len(detections)} 个对象")
                
                self.refresh_file_list()
                self.scan_images()  # 更新统计
            except Exception as e:
                messagebox.showerror("标注失败", f"重新标注失败:\n{str(e)}")
    
    def show_in_finder(self):
        """在文件管理器中显示"""
        selection = self.file_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        file_info = next((f for f in self.file_list_data if f['item_id'] == item_id), None)
        
        if file_info:
            import subprocess
            import sys
            
            if sys.platform == "darwin":  # macOS
                subprocess.call(["open", "-R", str(file_info['image_path'])])
            elif sys.platform == "win32":  # Windows
                subprocess.call(["explorer", "/select,", str(file_info['image_path'])])
            else:  # Linux
                subprocess.call(["xdg-open", str(file_info['image_path'].parent)])
    
    def select_all_files(self):
        """全选文件"""
        for item in self.file_tree.get_children():
            self.file_tree.selection_add(item)
    
    def deselect_all_files(self):
        """取消全选"""
        self.file_tree.selection_remove(self.file_tree.selection())
    
    def delete_selected_annotations(self):
        """删除选中的标注文件"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除标注的文件")
            return
        
        file_infos = [next((f for f in self.file_list_data if f['item_id'] == item_id), None) 
                     for item_id in selection]
        file_infos = [f for f in file_infos if f and f['json_path'].exists()]
        
        if not file_infos:
            messagebox.showwarning("警告", "选中的文件中没有标注文件")
            return
        
        result = messagebox.askyesno("确认批量删除", 
                                   f"确定要删除 {len(file_infos)} 个标注文件吗？")
        if result:
            deleted_count = 0
            for file_info in file_infos:
                try:
                    file_info['json_path'].unlink()
                    deleted_count += 1
                except:
                    pass
            
            messagebox.showinfo("删除完成", f"成功删除 {deleted_count} 个标注文件")
            self.refresh_file_list()
            self.scan_images()  # 更新统计
    
    def open_annotation_editor(self, image_path, json_path):
        """打开标注编辑器"""
        # 创建简单的标注编辑窗口
        editor_window = AnnotationEditor(self, image_path, json_path, self.colors)
    
    def update_confidence_label(self, value):
        """更新置信度标签"""
        self.conf_label.config(text=f"{float(value):.2f}")
    
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
            # 刷新文件列表
            if hasattr(self, 'file_tree'):
                self.refresh_file_list()
    
    def load_model(self):
        """加载YOLO模型"""
        model_file = self.model_path.get()
        if not model_file or not os.path.exists(model_file):
            self.model_status.config(text="[错误] 模型文件不存在")
            return
        
        self.model_status.config(text="[处理中] 正在加载模型...")
        self.root.update_idletasks()
        
        try:
            # 处理PyTorch 2.6+的weights_only安全限制
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
            
            # 获取类别名称
            self.class_names = list(self.current_model.names.values())
            
            # 测试推理以确保模型完全可用
            import numpy as np
            dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
            test_results = self.current_model(dummy_img, verbose=False)
            
            self.model_status.config(text=f"[成功] 模型加载成功 - 支持{len(self.class_names)}个类别: {', '.join(self.class_names[:3])}{'...' if len(self.class_names) > 3 else ''}")
            
        except Exception as e:
            error_msg = str(e)
            if "weights_only" in error_msg or "WeightsUnpickler" in error_msg:
                # PyTorch版本兼容性问题
                detailed_msg = f"""模型加载失败 - PyTorch版本兼容性问题

错误信息: {error_msg}

可能的解决方案:
1. 使用较旧版本的PyTorch (如2.0-2.5)
2. 重新训练模型并保存
3. 使用权重字典文件(.dict.pt)而不是完整模型

建议: 尝试使用 ultralytics/weights/yolov8.dict.pt 文件"""
                
                self.model_status.config(text="[错误] 模型版本不兼容")
                messagebox.showerror("模型兼容性问题", detailed_msg)
            else:
                self.model_status.config(text=f"[错误] 模型加载失败: {error_msg}")
                messagebox.showerror("模型加载错误", f"模型加载失败:\n{error_msg}")
    
    def scan_images(self):
        """扫描图片文件夹"""
        folder = self.image_folder.get()
        if not folder or not os.path.exists(folder):
            return
        
        # 获取所有jpg文件
        image_files = list(Path(folder).glob("*.jpg")) + list(Path(folder).glob("*.JPG"))
        existing_json = list(Path(folder).glob("*.json"))
        
        # 计算需要处理的文件
        needs_annotation = []
        for img_file in image_files:
            json_file = img_file.with_suffix('.json')
            if not json_file.exists():
                needs_annotation.append(img_file)
        
        self.stats['total_images'] = len(image_files)
        self.stats['processed_images'] = len(existing_json)
        self.stats['skipped_images'] = len(image_files) - len(needs_annotation)
        
        self.update_stats_display()
    
    def update_stats_display(self):
        """更新统计信息显示 - 仪表板风格"""
        # 更新卡片数值
        total = self.stats['total_images']
        processed = self.stats['processed_images'] 
        pending = total - processed - self.stats['skipped_images']
        detections = self.stats['detected_objects']
        processing_time = self.stats['processing_time']
        
        # 更新文件统计卡片
        self.total_files_label.config(text=str(total))
        self.processed_label.config(text=f"已处理: {processed}")
        self.pending_label.config(text=f"待处理: {pending}")
        
        # 更新检测统计卡片
        self.total_detections_label.config(text=str(detections))
        avg_per_image = f"{detections/max(processed, 1):.1f}" if processed > 0 else "0"
        self.avg_per_image_label.config(text=f"平均/图: {avg_per_image}")
        
        # 更新时间统计卡片
        self.processing_time_label.config(text=f"{processing_time:.1f}")
        status_text = "处理中..." if self.is_processing else "等待开始"
        self.status_desc_label.config(text=status_text)
        
        # 更新详细日志
        log_text = f"""处理概览:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[文件处理]
总计: {total} 个图片文件
完成: {processed} 个 ({(processed/max(total,1)*100):.1f}%)
跳过: {self.stats['skipped_images']} 个 (已有标注)
等待: {pending} 个

[检测结果] 
对象总数: {detections} 个
平均密度: {avg_per_image} 对象/图片
处理效率: {(processed/max(processing_time,0.001)*60):.1f} 图片/分钟

[系统状态]
状态: {status_text}
用时: {processing_time:.2f} 秒
"""
        
        if hasattr(self, 'stats_text'):
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, log_text)
    
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
        self.status_label.config(text="[取消] 用户取消处理")
    
    def validate_inputs(self):
        """验证输入"""
        if not self.current_model:
            messagebox.showerror("错误", "请先选择并加载模型文件")
            return False
        
        if not self.image_folder.get() or not os.path.exists(self.image_folder.get()):
            messagebox.showerror("错误", "请选择有效的图片文件夹")
            return False
        
        return True
    
    def process_images(self):
        """处理图片的主函数"""
        import time
        start_time = time.time()
        
        folder = Path(self.image_folder.get())
        image_files = list(folder.glob("*.jpg")) + list(folder.glob("*.JPG"))
        
        # 过滤已有JSON的图片
        to_process = []
        for img_file in image_files:
            json_file = img_file.with_suffix('.json')
            if not json_file.exists():
                to_process.append(img_file)
        
        if not to_process:
            self.root.after(0, lambda: self.status_label.config(text="[完成] 所有图片都已有标注文件"))
            self.is_processing = False
            self.root.after(0, lambda: self.process_btn.config(state='normal'))
            self.root.after(0, lambda: self.stop_btn.config(state='disabled'))
            return
        
        total_detections = 0
        processed_count = 0
        
        for i, img_file in enumerate(to_process):
            if not self.is_processing:
                break
            
            # 更新进度
            progress = (i / len(to_process)) * 100
            self.root.after(0, lambda p=progress: self.progress_var.set(p))
            self.root.after(0, lambda f=img_file.name: self.current_file_label.config(text=f"正在处理: {f}"))
            self.root.after(0, lambda i=i+1, t=len(to_process): self.status_label.config(text=f"[处理中] 正在处理 {i}/{t}..."))
            
            try:
                detections = self.process_single_image(img_file)
                total_detections += len(detections)
                processed_count += 1
                
                # 更新统计
                self.stats['detected_objects'] = total_detections
                self.stats['processed_images'] = len([f for f in folder.glob("*.json")])
                self.root.after(0, self.update_stats_display)
                
            except Exception as e:
                print(f"处理文件 {img_file} 时出错: {e}")
        
        # 处理完成
        end_time = time.time()
        self.stats['processing_time'] = end_time - start_time
        
        self.root.after(0, lambda: self.progress_var.set(100))
        self.root.after(0, lambda: self.status_label.config(text=f"[完成] 处理完成！共处理 {processed_count} 个文件，检测到 {total_detections} 个对象"))
        self.root.after(0, lambda: self.current_file_label.config(text=""))
        self.root.after(0, lambda: self.process_btn.config(state='normal'))
        self.root.after(0, lambda: self.stop_btn.config(state='disabled'))
        self.root.after(0, self.update_stats_display)
        
        self.is_processing = False
    
    def process_single_image(self, img_file):
        """处理单张图片"""
        # 运行YOLOv8检测
        results = self.current_model(str(img_file), conf=self.confidence_threshold.get())
        
        # 获取图片尺寸
        image = cv2.imread(str(img_file))
        height, width = image.shape[:2]
        
        # 解析检测结果
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # 获取边界框坐标 (xyxy格式)
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = self.class_names[class_id]
                    
                    # 创建检测对象
                    detection = {
                        "label": class_name,
                        "text": "",
                        "points": [[float(x1), float(y1)], [float(x2), float(y2)]],
                        "group_id": None,
                        "shape_type": "rectangle",
                        "flags": {}
                    }
                    detections.append(detection)
        
        # 生成LabelMe格式JSON
        json_data = {
            "version": "0.4.30",
            "flags": {},
            "shapes": detections,
            "imagePath": img_file.name,
            "imageData": None,
            "imageHeight": height,
            "imageWidth": width
        }
        
        # 保存JSON文件
        json_file = img_file.with_suffix('.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        return detections
    
    def open_preview_window(self):
        """打开图片预览窗口"""
        if self.preview_window is not None:
            try:
                self.preview_window.lift()  # 将窗口置顶
                self.preview_window.focus_force()
                return
            except:
                self.preview_window = None
        
        folder = self.image_folder.get()
        if not folder or not os.path.exists(folder):
            messagebox.showwarning("警告", "请先选择图片文件夹")
            return
        
        self.preview_window = ImagePreviewWindow(self, folder, self.colors)
    
    def show_dependency_error(self):
        """显示依赖错误对话框"""
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
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
    print("正在启动YOLOv8自动标注工具...")
    
    if not DEPENDENCIES_OK:
        print(f"[错误] 依赖库缺失: {MISSING_DEPS}")
        print("请运行以下命令安装依赖:")
        print("pip install ultralytics opencv-python pillow torch torchvision")
        return
    
    print("[成功] 依赖检查通过")
    print("正在初始化GUI界面...")
    
    try:
        app = ModernAutoAnnotationTool()
        app.run()
    except Exception as e:
        print(f"[错误] 应用启动失败: {e}")
        messagebox.showerror("启动错误", f"应用启动失败:\n{str(e)}")


class ImagePreviewWindow:
    """图片预览和标注查看窗口"""
    
    def __init__(self, parent_app, folder_path, colors):
        self.parent_app = parent_app
        self.folder_path = Path(folder_path)
        self.colors = colors
        
        # 扫描图片文件
        self.image_files = self.scan_image_files()
        self.current_index = 0
        
        # 创建窗口
        self.window = tk.Toplevel(parent_app.root)
        self.window.title("图片标注预览")
        self.window.geometry("1200x800")
        self.window.minsize(800, 600)
        self.window.configure(bg=colors['bg'])
        
        # 窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_ui()
        
        if self.image_files:
            self.load_current_image()
        else:
            self.show_no_images_message()
    
    def scan_image_files(self):
        """扫描图片文件"""
        image_files = []
        for ext in ['*.jpg', '*.JPG', '*.jpeg', '*.JPEG', '*.png', '*.PNG']:
            image_files.extend(self.folder_path.glob(ext))
        
        # 按文件名排序
        return sorted(image_files)
    
    def setup_ui(self):
        """设置UI界面"""
        # 主容器
        main_frame = tk.Frame(self.window, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # 顶部控制区
        self.create_control_panel(main_frame)
        
        # 中间图片显示区
        self.create_image_display(main_frame)
        
        # 底部信息区
        self.create_info_panel(main_frame)
    
    def create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = tk.Frame(parent, bg=self.colors['card'], relief='flat', bd=1)
        control_frame.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        control_frame.pack(fill='x', pady=(0, 15))
        
        # 内部容器
        inner_frame = tk.Frame(control_frame, bg=self.colors['card'])
        inner_frame.pack(fill='x', padx=20, pady=15)
        
        # 左侧：导航按钮
        nav_frame = tk.Frame(inner_frame, bg=self.colors['card'])
        nav_frame.pack(side='left')
        
        self.prev_btn = ttk.Button(nav_frame, text="< 上一张", command=self.prev_image, 
                                  style='Primary.TButton')
        self.prev_btn.pack(side='left', padx=(0, 10))
        
        self.next_btn = ttk.Button(nav_frame, text="下一张 >", command=self.next_image, 
                                  style='Primary.TButton')
        self.next_btn.pack(side='left')
        
        # 中间：图片选择下拉框
        select_frame = tk.Frame(inner_frame, bg=self.colors['card'])
        select_frame.pack(side='left', padx=(30, 0))
        
        ttk.Label(select_frame, text="选择图片:", 
                 background=self.colors['card'], foreground=self.colors['text'],
                 font=('SF Pro Text', 11)).pack(side='left', padx=(0, 10))
        
        self.image_var = tk.StringVar()
        self.image_combo = ttk.Combobox(select_frame, textvariable=self.image_var,
                                       width=30, state='readonly')
        self.image_combo.pack(side='left')
        self.image_combo.bind('<<ComboboxSelected>>', self.on_image_selected)
        
        # 填充下拉框
        if self.image_files:
            image_names = [f.name for f in self.image_files]
            self.image_combo['values'] = image_names
            self.image_combo.set(image_names[0] if image_names else "")
        
        # 右侧：显示控制
        display_frame = tk.Frame(inner_frame, bg=self.colors['card'])
        display_frame.pack(side='right')
        
        self.show_annotations = tk.BooleanVar(value=True)
        self.annotation_check = ttk.Checkbutton(display_frame, text="显示标注框",
                                               variable=self.show_annotations,
                                               command=self.refresh_image)
        self.annotation_check.pack(side='right')
    
    def create_image_display(self, parent):
        """创建图片显示区域"""
        # 图片显示卡片
        image_card = tk.Frame(parent, bg=self.colors['card'], relief='flat', bd=1)
        image_card.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        image_card.pack(fill='both', expand=True, pady=(0, 15))
        
        # 图片显示区域（带滚动条）
        self.canvas = tk.Canvas(image_card, bg=self.colors['card'], highlightthickness=0)
        
        # 滚动条
        v_scrollbar = ttk.Scrollbar(image_card, orient='vertical', command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(image_card, orient='horizontal', command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 布局
        self.canvas.pack(side='left', fill='both', expand=True, padx=20, pady=20)
        v_scrollbar.pack(side='right', fill='y', pady=20)
        h_scrollbar.pack(side='bottom', fill='x', padx=20)
        
        # 鼠标滚轮支持
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)
        self.canvas.bind("<Button-5>", self.on_mousewheel)
    
    def create_info_panel(self, parent):
        """创建信息面板"""
        info_card = tk.Frame(parent, bg=self.colors['card'], relief='flat', bd=1)
        info_card.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        info_card.pack(fill='x')
        
        # 信息内容
        info_content = tk.Frame(info_card, bg=self.colors['card'])
        info_content.pack(fill='x', padx=20, pady=15)
        
        # 左侧：图片信息
        left_info = tk.Frame(info_content, bg=self.colors['card'])
        left_info.pack(side='left', fill='both', expand=True)
        
        self.image_info_label = ttk.Label(left_info, text="图片信息：未加载",
                                         background=self.colors['card'], 
                                         foreground=self.colors['text'],
                                         font=('SF Pro Text', 10))
        self.image_info_label.pack(anchor='w')
        
        # 右侧：标注信息
        right_info = tk.Frame(info_content, bg=self.colors['card'])
        right_info.pack(side='right')
        
        self.annotation_info_label = ttk.Label(right_info, text="标注信息：未检测到标注文件",
                                              background=self.colors['card'],
                                              foreground=self.colors['text_muted'],
                                              font=('SF Pro Text', 10))
        self.annotation_info_label.pack(anchor='e')
    
    def load_current_image(self):
        """加载当前图片"""
        if not self.image_files or self.current_index >= len(self.image_files):
            return
        
        image_file = self.image_files[self.current_index]
        json_file = image_file.with_suffix('.json')
        
        try:
            # 加载图片
            pil_image = Image.open(image_file)
            original_size = pil_image.size
            
            # 加载标注（如果存在）
            annotations = []
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    annotations = json_data.get('shapes', [])
            
            # 绘制标注框
            if self.show_annotations.get() and annotations:
                pil_image = self.draw_annotations(pil_image, annotations)
            
            # 调整图片尺寸以适应显示区域
            display_image = self.resize_image_for_display(pil_image)
            
            # 转换为PhotoImage
            self.current_photo = ImageTk.PhotoImage(display_image)
            
            # 显示图片
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor='nw', image=self.current_photo)
            
            # 更新滚动区域
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # 更新信息显示
            self.update_info_display(image_file, original_size, annotations)
            
            # 更新下拉框选择
            self.image_combo.set(image_file.name)
            
            # 更新按钮状态
            self.update_button_states()
            
        except Exception as e:
            messagebox.showerror("错误", f"加载图片失败:\n{str(e)}")
    
    def draw_annotations(self, image, annotations):
        """在图片上绘制标注框"""
        draw_image = image.copy()
        draw = ImageDraw.Draw(draw_image)
        
        # 定义颜色
        colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF']
        
        for i, shape in enumerate(annotations):
            if shape.get('shape_type') == 'rectangle' and len(shape.get('points', [])) == 2:
                points = shape['points']
                x1, y1 = points[0]
                x2, y2 = points[1]
                
                # 确保坐标顺序正确
                x1, x2 = min(x1, x2), max(x1, x2)
                y1, y2 = min(y1, y2), max(y1, y2)
                
                # 选择颜色
                color = colors[i % len(colors)]
                
                # 绘制矩形框
                draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                
                # 绘制标签
                label = shape.get('label', 'Unknown')
                if label:
                    # 尝试获取字体
                    try:
                        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
                    except:
                        font = ImageFont.load_default()
                    
                    # 计算文字位置和背景
                    bbox = draw.textbbox((0, 0), label, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    
                    # 绘制文字背景
                    draw.rectangle([x1, y1-text_height-4, x1+text_width+8, y1], fill=color)
                    
                    # 绘制文字
                    draw.text((x1+4, y1-text_height-2), label, fill='white', font=font)
        
        return draw_image
    
    def resize_image_for_display(self, image, max_width=800, max_height=600):
        """调整图片尺寸以适应显示"""
        width, height = image.size
        
        # 计算缩放比例
        scale_x = max_width / width
        scale_y = max_height / height
        scale = min(scale_x, scale_y, 1.0)  # 不放大，只缩小
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return image
    
    def update_info_display(self, image_file, original_size, annotations):
        """更新信息显示"""
        # 图片信息
        width, height = original_size
        file_size = image_file.stat().st_size
        info_text = f"文件: {image_file.name} | 尺寸: {width}x{height} | 大小: {file_size:,} bytes | 进度: {self.current_index + 1}/{len(self.image_files)}"
        self.image_info_label.config(text=info_text)
        
        # 标注信息
        if annotations:
            labels = [shape.get('label', 'Unknown') for shape in annotations]
            label_counts = {}
            for label in labels:
                label_counts[label] = label_counts.get(label, 0) + 1
            
            label_info = ', '.join([f"{label}×{count}" for label, count in label_counts.items()])
            annotation_text = f"检测到 {len(annotations)} 个标注: {label_info}"
            self.annotation_info_label.config(text=annotation_text, foreground=self.colors['success'])
        else:
            json_file = image_file.with_suffix('.json')
            if json_file.exists():
                annotation_text = "标注文件存在但无有效标注"
                self.annotation_info_label.config(text=annotation_text, foreground=self.colors['warning'])
            else:
                annotation_text = "未找到标注文件"
                self.annotation_info_label.config(text=annotation_text, foreground=self.colors['text_muted'])
    
    def update_button_states(self):
        """更新按钮状态"""
        self.prev_btn.config(state='normal' if self.current_index > 0 else 'disabled')
        self.next_btn.config(state='normal' if self.current_index < len(self.image_files) - 1 else 'disabled')
    
    def show_no_images_message(self):
        """显示无图片消息"""
        self.canvas.delete("all")
        self.canvas.create_text(400, 300, text="未找到图片文件\n\n支持格式: JPG, JPEG, PNG",
                               font=('SF Pro Text', 16), fill=self.colors['text_muted'], justify='center')
    
    def prev_image(self):
        """上一张图片"""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()
    
    def next_image(self):
        """下一张图片"""
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.load_current_image()
    
    def on_image_selected(self, event=None):
        """下拉框选择图片事件"""
        selected_name = self.image_var.get()
        for i, img_file in enumerate(self.image_files):
            if img_file.name == selected_name:
                self.current_index = i
                self.load_current_image()
                break
    
    def refresh_image(self):
        """刷新图片显示"""
        self.load_current_image()
    
    def on_mousewheel(self, event):
        """鼠标滚轮事件"""
        if event.delta:
            delta = event.delta
        else:
            delta = -1 * event.num if event.num == 5 else 1 * event.num
        
        self.canvas.yview_scroll(int(-1 * (delta / 120)), "units")
    
    def on_closing(self):
        """窗口关闭事件"""
        self.parent_app.preview_window = None
        self.window.destroy()
    
    def lift(self):
        """将窗口置顶"""
        self.window.lift()
        
    def focus_force(self):
        """强制获取焦点"""
        self.window.focus_force()
    
    def locate_file(self, filename):
        """定位到指定文件"""
        for i, img_file in enumerate(self.image_files):
            if img_file.name == filename:
                self.current_index = i
                self.load_current_image()
                break


class AnnotationEditor:
    """简单的标注编辑器"""
    
    def __init__(self, parent_app, image_path, json_path, colors):
        self.parent_app = parent_app
        self.image_path = image_path
        self.json_path = json_path
        self.colors = colors
        
        # 加载标注数据
        self.load_annotations()
        
        # 创建编辑窗口
        self.window = tk.Toplevel(parent_app.root)
        self.window.title(f"编辑标注 - {image_path.name}")
        self.window.geometry("800x600")
        self.window.configure(bg=colors['bg'])
        
        self.setup_ui()
        
    def load_annotations(self):
        """加载标注数据"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.json_data = json.load(f)
                self.annotations = self.json_data.get('shapes', [])
        except:
            self.annotations = []
            self.json_data = {
                "version": "0.4.30",
                "flags": {},
                "shapes": [],
                "imagePath": self.image_path.name,
                "imageData": None,
                "imageHeight": 0,
                "imageWidth": 0
            }
    
    def setup_ui(self):
        """设置界面"""
        # 主容器
        main_frame = tk.Frame(self.window, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # 工具栏
        toolbar = tk.Frame(main_frame, bg=self.colors['card'], relief='flat', bd=1)
        toolbar.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        toolbar.pack(fill='x', pady=(0, 15))
        
        toolbar_content = tk.Frame(toolbar, bg=self.colors['card'])
        toolbar_content.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(toolbar_content, text="保存", command=self.save_annotations, 
                  style='Success.TButton').pack(side='left', padx=(0, 10))
        ttk.Button(toolbar_content, text="取消", command=self.close_editor, 
                  style='Primary.TButton').pack(side='left', padx=(0, 10))
        ttk.Button(toolbar_content, text="删除选中", command=self.delete_selected, 
                  style='Primary.TButton').pack(side='left', padx=(0, 10))
        
        # 标注列表
        list_card = tk.Frame(main_frame, bg=self.colors['card'], relief='flat', bd=1)
        list_card.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        list_card.pack(fill='both', expand=True)
        
        # 标题
        header = tk.Frame(list_card, bg=self.colors['card'])
        header.pack(fill='x', padx=20, pady=(15, 10))
        ttk.Label(header, text="标注列表", style='CardTitle.TLabel').pack(anchor='w')
        
        # 列表内容
        content = tk.Frame(list_card, bg=self.colors['card'])
        content.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # 创建Treeview
        columns = ('类别', 'X1', 'Y1', 'X2', 'Y2', '宽度', '高度')
        self.annotation_tree = ttk.Treeview(content, columns=columns, show='headings', height=10)
        
        # 设置列标题
        for col in columns:
            self.annotation_tree.heading(col, text=col)
            self.annotation_tree.column(col, width=80)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(content, orient='vertical', command=self.annotation_tree.yview)
        self.annotation_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.annotation_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 加载数据
        self.refresh_annotation_list()
    
    def refresh_annotation_list(self):
        """刷新标注列表"""
        # 清空现有项目
        for item in self.annotation_tree.get_children():
            self.annotation_tree.delete(item)
        
        # 添加标注项目
        for i, annotation in enumerate(self.annotations):
            if annotation.get('shape_type') == 'rectangle' and len(annotation.get('points', [])) == 2:
                label = annotation.get('label', 'Unknown')
                points = annotation['points']
                x1, y1 = points[0]
                x2, y2 = points[1]
                
                # 确保坐标顺序正确
                x1, x2 = min(x1, x2), max(x1, x2)
                y1, y2 = min(y1, y2), max(y1, y2)
                
                width = x2 - x1
                height = y2 - y1
                
                self.annotation_tree.insert('', 'end', values=(
                    label, f"{x1:.1f}", f"{y1:.1f}", f"{x2:.1f}", f"{y2:.1f}",
                    f"{width:.1f}", f"{height:.1f}"
                ))
    
    def delete_selected(self):
        """删除选中的标注"""
        selection = self.annotation_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的标注")
            return
        
        # 获取选中项目的索引
        indices = []
        for item in selection:
            index = self.annotation_tree.index(item)
            indices.append(index)
        
        # 按索引倒序删除（避免索引变化问题）
        for index in sorted(indices, reverse=True):
            if 0 <= index < len(self.annotations):
                del self.annotations[index]
        
        # 刷新列表
        self.refresh_annotation_list()
    
    def save_annotations(self):
        """保存标注"""
        try:
            # 更新JSON数据
            self.json_data['shapes'] = self.annotations
            
            # 获取图片尺寸（如果没有的话）
            if self.json_data.get('imageHeight', 0) == 0:
                try:
                    with Image.open(self.image_path) as img:
                        self.json_data['imageWidth'] = img.width
                        self.json_data['imageHeight'] = img.height
                except:
                    pass
            
            # 保存到文件
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.json_data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("保存成功", "标注已保存")
            
            # 刷新父窗口的文件列表
            if hasattr(self.parent_app, 'refresh_file_list'):
                self.parent_app.refresh_file_list()
            
            # 关闭编辑器
            self.close_editor()
            
        except Exception as e:
            messagebox.showerror("保存失败", f"保存标注失败:\n{str(e)}")
    
    def close_editor(self):
        """关闭编辑器"""
        self.window.destroy()


if __name__ == "__main__":
    main()