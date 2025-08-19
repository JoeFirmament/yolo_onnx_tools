#!/usr/bin/env python3
"""
台球自动标注工具 - 现代化版本
基于Roboflow API，采用现代化GUI设计
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import json
import cv2
import os
import sys
from pathlib import Path
import threading
from datetime import datetime
import warnings

# 抑制系统警告
warnings.filterwarnings("ignore", category=UserWarning)
if sys.platform == "darwin":
    os.environ['TK_SILENCE_DEPRECATION'] = '1'


class ModernBilliardAnnotationTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Billiard Auto Annotation Tool")
        self.root.geometry("1100x800")
        self.root.minsize(900, 650)
        
        # 专业低饱和度配色方案 - 遵循终极指南标准
        self.colors = {
            'bg': '#f8f9fa',        # 主背景：极浅灰白（清洁专业）
            'card': '#ffffff',      # 卡片背景：纯白（突出内容）
            'primary': '#6c757d',   # 主色调：中性灰（专业稳重）
            'success': '#6c9b7f',   # 成功色：柔和绿（清淡有效）
            'danger': '#a0727d',    # 危险色：暗红灰（温和警告）
            'warning': '#b8860b',   # 警告色：暗金色（低调提醒）
            'text': '#212529',      # 主文字：深灰黑（最高可读性）
            'text_muted': '#6c757d', # 次要文字：中性灰（清晰层次）
            'text_light': '#adb5bd', # 辅助文字：浅灰（不干扰）
            'border': '#e9ecef',    # 边框色：浅灰（微妙分割）
            'accent': '#6c9b7f',    # 辅助强调色：柔和绿
            # 保持兼容性的旧属性名
            'text_secondary': '#6c757d',
            'success_text': '#6c9b7f',
            'error_text': '#a0727d',
            'warning_text': '#b8860b',
            'info': '#f1f3f4',
            'info_text': '#5a7a8a',
        }
        
        # 设置字体
        self.fonts = {
            'mono': ('SF Mono', 'Consolas', 'Monaco', 'Courier New'),
            'sans': ('SF Pro Text', 'Helvetica Neue', 'Arial'),
        }
        
        # 设置ttk样式
        self.setup_styles()
        
        self.root.configure(bg=self.colors['bg'])
        
        # API配置
        self.api_key = "Vw6OHkkjkqToMYHdReav"
        self.api_url = "https://detect.roboflow.com/billiards-y0wwp/3"
        
        # 状态变量
        self.image_folder = tk.StringVar()
        self.confidence_threshold = tk.DoubleVar(value=0.5)
        self.is_processing = False
        self.progress_var = tk.DoubleVar()
        
        # 台球类别映射
        self.ball_classes = {
            0: "1", 1: "2", 2: "3", 3: "4", 4: "5", 5: "6", 6: "7", 7: "8",
            8: "9", 9: "10", 10: "11", 11: "12", 12: "13", 13: "14", 14: "15", 15: "cue"
        }
        
        # 统计数据
        self.stats = {
            'total_images': 0,
            'processed_images': 0,
            'detected_balls': 0,
            'skipped_images': 0
        }
        
        self.setup_ui()
    
    def setup_styles(self):
        """设置ttk样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 按钮样式 - 参考auto_annotation_tool_classify.py的成功实现
        style.configure('Primary.TButton',
                       font=('SF Pro Text', 11, 'bold'),
                       foreground='white',
                       background='#ff4757',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        
        style.configure('Success.TButton',
                       font=('SF Pro Text', 11, 'bold'),
                       foreground='white',
                       background='#2ed573',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        
        style.configure('Stop.TButton',
                       font=('SF Pro Text', 11, 'bold'),
                       foreground='white',
                       background='#ff3838',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        
        style.configure('Secondary.TButton',
                       font=('SF Pro Text', 10),
                       foreground='#2f3542',
                       background='#f1f2f6',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(10, 6))
        
        # ✅ 输入框样式 - 完整的光标设置
        style.configure('Modern.TEntry',
                       fieldbackground=self.colors['card'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.colors['border'],
                       insertcolor=self.colors['text'],  # 🔑 光标颜色
                       insertwidth=2,  # 🔑 光标宽度
                       font=('SF Pro Text', 11))
        
    def setup_ui(self):
        """设置用户界面"""
        # 创建主容器
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 标题区域
        self.create_header(main_container)
        
        # 主内容区域
        content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        content_frame.pack(fill='both', expand=True, pady=(20, 0))
        
        # 左侧配置面板
        left_panel = self.create_card(content_frame)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # 右侧信息面板
        right_panel = self.create_card(content_frame)
        right_panel.pack(side='right', fill='both', padx=(10, 0))
        right_panel.configure(width=350)
        
        # 填充面板内容
        self.setup_left_panel(left_panel)
        self.setup_right_panel(right_panel)
        
        # 底部状态栏
        self.setup_status_bar(main_container)
        
    def create_header(self, parent):
        """创建标题区域"""
        header_frame = tk.Frame(parent, bg=self.colors['bg'])
        header_frame.pack(fill='x')
        
        # 主标题
        title_label = tk.Label(
            header_frame,
            text="Billiard Auto Annotation Tool",
            font=(self.fonts['sans'][0], 24, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['bg']
        )
        title_label.pack(anchor='w')
        
        # 副标题
        subtitle_label = tk.Label(
            header_frame,
            text="基于Roboflow API的智能台球检测与标注系统",
            font=(self.fonts['sans'][0], 12),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg']
        )
        subtitle_label.pack(anchor='w', pady=(5, 0))
        
        # 分割线
        separator = tk.Frame(header_frame, height=1, bg=self.colors['border'])
        separator.pack(fill='x', pady=(15, 0))
    
    def create_card(self, parent):
        """创建卡片容器"""
        card_frame = tk.Frame(parent, bg=self.colors['card'], relief='solid', bd=1)
        card_frame.configure(highlightbackground=self.colors['border'], highlightthickness=0)
        return card_frame
    
    def setup_left_panel(self, parent):
        """设置左侧配置面板"""
        content = tk.Frame(parent, bg=self.colors['card'])
        content.pack(fill='both', expand=True, padx=30, pady=30)
        
        # 文件夹选择区域
        self.create_section_title(content, "图片文件夹")
        folder_frame = self.create_input_group(content)
        
        tk.Label(
            folder_frame,
            text="选择包含台球图片的文件夹:",
            font=(self.fonts['sans'][0], 11),
            fg=self.colors['text'],
            bg=self.colors['card']
        ).pack(anchor='w')
        
        path_frame = tk.Frame(folder_frame, bg=self.colors['card'])
        path_frame.pack(fill='x', pady=(5, 0))
        
        self.folder_entry = ttk.Entry(
            path_frame,
            textvariable=self.image_folder,
            style='Modern.TEntry'
        )
        self.folder_entry.pack(side='left', fill='x', expand=True)
        
        browse_btn = ttk.Button(
            path_frame,
            text="浏览",
            command=self.browse_folder,
            style='Primary.TButton'
        )
        browse_btn.pack(side='right', padx=(10, 0))
        
        # 检测设置区域
        self.create_section_title(content, "检测设置", pady_top=25)
        settings_frame = self.create_input_group(content)
        
        # 置信度设置
        conf_label = tk.Label(
            settings_frame,
            text="置信度阈值:",
            font=(self.fonts['sans'][0], 11),
            fg=self.colors['text'],
            bg=self.colors['card']
        )
        conf_label.pack(anchor='w')
        
        conf_control_frame = tk.Frame(settings_frame, bg=self.colors['card'])
        conf_control_frame.pack(fill='x', pady=(5, 0))
        
        self.conf_scale = tk.Scale(
            conf_control_frame,
            from_=0.1, to=0.9,
            resolution=0.05,
            orient='horizontal',
            variable=self.confidence_threshold,
            font=(self.fonts['mono'][0], 9),
            bg=self.colors['card'],
            fg=self.colors['text'],
            highlightthickness=0,
            relief='flat'
        )
        self.conf_scale.pack(side='left', fill='x', expand=True)
        
        self.conf_label = tk.Label(
            conf_control_frame,
            text="0.50",
            font=(self.fonts['mono'][0], 10, 'bold'),
            fg='#666666',
            bg=self.colors['card'],
            width=6
        )
        self.conf_label.pack(side='right', padx=(10, 0))
        
        self.conf_scale.config(command=self.update_conf_label)
        
        # 检测类别信息
        self.create_section_title(content, "检测类别", pady_top=25)
        classes_frame = self.create_input_group(content)
        
        classes_info = tk.Text(
            classes_frame,
            height=4,
            font=(self.fonts['mono'][0], 9),
            bg=self.colors['info'],
            fg=self.colors['info_text'],
            relief='solid',
            bd=1,
            wrap='word'
        )
        classes_info.pack(fill='x')
        
        classes_text = """支持检测台球类别:
• 1-15号彩球 (1, 2, 3, ..., 15)
• 母球 (cue)
• 自动生成LabelMe格式标注"""
        
        classes_info.insert('1.0', classes_text)
        classes_info.configure(state='disabled')
        
        # 处理控制
        self.create_section_title(content, "处理控制", pady_top=25)
        control_frame = self.create_input_group(content)
        
        button_frame = tk.Frame(control_frame, bg=self.colors['card'])
        button_frame.pack(fill='x')
        
        self.start_btn = ttk.Button(
            button_frame,
            text="开始标注",
            command=self.start_annotation,
            style='Success.TButton'
        )
        self.start_btn.pack(side='left')
        
        self.stop_btn = ttk.Button(
            button_frame,
            text="停止",
            command=self.stop_annotation,
            style='Stop.TButton',
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=(15, 0))
        
        # 进度显示
        progress_frame = tk.Frame(control_frame, bg=self.colors['card'])
        progress_frame.pack(fill='x', pady=(20, 0))
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            mode='determinate',
            length=400
        )
        
        self.progress_label = tk.Label(
            progress_frame,
            text="",
            font=(self.fonts['sans'][0], 10),
            fg=self.colors['text_secondary'],
            bg=self.colors['card']
        )
        
    def setup_right_panel(self, parent):
        """设置右侧信息面板"""
        content = tk.Frame(parent, bg=self.colors['card'])
        content.pack(fill='both', expand=True, padx=20, pady=30)
        
        # 统计信息
        self.create_section_title(content, "处理统计", size=14)
        
        stats_frame = tk.Frame(content, bg=self.colors['card'])
        stats_frame.pack(fill='x', pady=(10, 0))
        
        # 创建统计显示
        self.stats_labels = {}
        
        stats_items = [
            ("总图片数", "total_images"),
            ("已处理", "processed_images"),
            ("检测台球", "detected_balls"),
            ("跳过图片", "skipped_images")
        ]
        
        for i, (label, key) in enumerate(stats_items):
            row = tk.Frame(stats_frame, bg=self.colors['card'])
            row.pack(fill='x', pady=2)
            
            tk.Label(
                row,
                text=f"{label}:",
                font=(self.fonts['sans'][0], 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['card']
            ).pack(side='left')
            
            value_label = tk.Label(
                row,
                text="0",
                font=(self.fonts['mono'][0], 10, 'bold'),
                fg='#666666',
                bg=self.colors['card']
            )
            value_label.pack(side='right')
            
            self.stats_labels[key] = value_label
        
        # 处理日志
        self.create_section_title(content, "处理日志", size=14, pady_top=25)
        
        log_frame = tk.Frame(content, bg=self.colors['card'])
        log_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        # 创建文本框和滚动条
        text_frame = tk.Frame(log_frame, bg=self.colors['card'])
        text_frame.pack(fill='both', expand=True)
        
        self.log_text = tk.Text(
            text_frame,
            font=(self.fonts['mono'][0], 9),
            bg='white',
            fg=self.colors['text'],
            relief='solid',
            bd=1,
            wrap='word'
        )
        
        log_scrollbar = tk.Scrollbar(
            text_frame,
            orient='vertical',
            command=self.log_text.yview
        )
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        log_scrollbar.pack(side='right', fill='y')
        
        # 日志控制按钮
        log_control_frame = tk.Frame(content, bg=self.colors['card'])
        log_control_frame.pack(fill='x', pady=(10, 0))
        
        clear_log_btn = ttk.Button(
            log_control_frame,
            text="清空日志",
            command=self.clear_log,
            style='Secondary.TButton'
        )
        clear_log_btn.pack(side='right')
        
        # 联系方式
        self.create_section_title(content, "联系方式", size=12, pady_top=25)
        
        contact_label = tk.Label(
            content,
            text="bquill@qq.com",
            font=(self.fonts['mono'][0], 10),
            fg='#666666',
            bg=self.colors['card'],
            cursor='hand2'
        )
        contact_label.pack(anchor='w')
        contact_label.bind("<Button-1>", lambda e: self.copy_to_clipboard("bquill@qq.com"))
        
    def create_section_title(self, parent, text, size=12, pady_top=0):
        """创建区域标题"""
        title_label = tk.Label(
            parent,
            text=text,
            font=(self.fonts['sans'][0], size, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['card']
        )
        title_label.pack(anchor='w', pady=(pady_top, 10))
    
    def create_input_group(self, parent):
        """创建输入组容器"""
        group_frame = tk.Frame(parent, bg=self.colors['card'])
        group_frame.pack(fill='x', pady=(0, 20))
        return group_frame
    
    def setup_status_bar(self, parent):
        """设置底部状态栏"""
        status_frame = tk.Frame(parent, bg=self.colors['border'], height=1)
        status_frame.pack(fill='x', pady=(20, 0))
        
        self.status_label = tk.Label(
            parent,
            text="就绪 - 请选择图片文件夹开始处理",
            font=(self.fonts['sans'][0], 10),
            fg=self.colors['text_light'],
            bg=self.colors['bg']
        )
        self.status_label.pack(anchor='w', pady=(10, 0))
    
    def copy_to_clipboard(self, text):
        """复制到剪贴板"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.update_status("已复制到剪贴板: " + text)
    
    def update_status(self, message, msg_type="info"):
        """更新状态信息"""
        color_map = {
            "info": self.colors['text_light'],
            "success": self.colors['success_text'],
            "error": self.colors['error_text'],
            "warning": self.colors['warning_text']
        }
        
        self.status_label.configure(
            text=message,
            fg=color_map.get(msg_type, self.colors['text_light'])
        )
        self.root.update()
    
    def update_conf_label(self, value):
        """更新置信度标签"""
        self.conf_label.config(text=f"{float(value):.2f}")
    
    def update_stats(self):
        """更新统计显示"""
        for key, label in self.stats_labels.items():
            label.config(text=str(self.stats[key]))
    
    def log(self, message, msg_type="info"):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 根据消息类型设置简单标记
        type_marks = {
            "info": "·",
            "success": "+",
            "error": "!",
            "warning": "?",
            "processing": ">"
        }
        
        mark = type_marks.get(msg_type, "·")
        log_message = f"[{timestamp}] {mark} {message}\n"
        
        self.log_text.insert('end', log_message)
        self.log_text.see('end')
        self.root.update_idletasks()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete('1.0', 'end')
        self.log("日志已清空", "info")
    
    def browse_folder(self):
        """选择图片文件夹"""
        folder = filedialog.askdirectory(
            title="选择包含台球图片的文件夹"
        )
        if folder:
            self.image_folder.set(folder)
            self.log(f"选择文件夹: {folder}", "info")
            self.scan_images()
    
    def scan_images(self):
        """扫描图片文件"""
        folder = self.image_folder.get()
        if not folder:
            return
        
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
            image_files.extend(Path(folder).glob(ext))
        
        annotated = sum(1 for img in image_files if img.with_suffix('.json').exists())
        to_process = len(image_files) - annotated
        
        self.stats['total_images'] = len(image_files)
        self.stats['processed_images'] = 0
        self.stats['detected_balls'] = 0
        self.stats['skipped_images'] = annotated
        
        self.update_stats()
        
        self.log(f"扫描完成: 找到 {len(image_files)} 张图片", "success")
        self.log(f"已标注: {annotated} 张，待处理: {to_process} 张", "info")
        
        if to_process == 0:
            self.log("所有图片都已标注完成！", "success")
        
        self.update_status(f"扫描完成 - {to_process} 张图片待处理")
    
    def start_annotation(self):
        """开始标注"""
        if not self.image_folder.get():
            messagebox.showerror("错误", "请先选择图片文件夹")
            return
        
        if not os.path.exists(self.image_folder.get()):
            messagebox.showerror("错误", "选择的文件夹不存在")
            return
        
        self.is_processing = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        # 显示进度条
        self.progress_bar.pack(fill='x', pady=(0, 5))
        self.progress_label.pack()
        
        # 在新线程中处理
        thread = threading.Thread(target=self.process_images, daemon=True)
        thread.start()
    
    def stop_annotation(self):
        """停止标注"""
        self.is_processing = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        
        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()
        
        self.update_status("处理已停止")
        self.log("用户停止处理", "warning")
    
    def process_images(self):
        """处理图片"""
        folder = Path(self.image_folder.get())
        
        # 获取所有图片文件
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
            image_files.extend(folder.glob(ext))
        
        # 过滤掉已标注的图片
        to_process = [img for img in image_files if not img.with_suffix('.json').exists()]
        
        if not to_process:
            self.root.after(0, lambda: self.log("所有图片都已标注完成", "success"))
            self.root.after(0, self.stop_annotation)
            return
        
        self.root.after(0, lambda: self.log(f"开始处理 {len(to_process)} 张图片", "processing"))
        
        processed = 0
        detected_total = 0
        
        for i, img_file in enumerate(to_process):
            if not self.is_processing:
                break
            
            # 更新进度
            progress = (i + 1) / len(to_process) * 100
            self.root.after(0, lambda p=progress: self.progress_var.set(p))
            self.root.after(0, lambda f=img_file.name: self.progress_label.config(text=f"处理中: {f}"))
            
            self.root.after(0, lambda i=i, total=len(to_process), name=img_file.name: 
                          self.log(f"({i+1}/{total}) 处理: {name}", "processing"))
            
            try:
                # 使用API检测
                detections = self.detect_with_api(str(img_file))
                
                if detections:
                    # 保存标注
                    self.save_annotations(img_file, detections)
                    processed += 1
                    detected_total += len(detections)
                    
                    self.root.after(0, lambda count=len(detections): 
                                  self.log(f"   检测到 {count} 个台球，已保存标注", "success"))
                else:
                    self.root.after(0, lambda: self.log("   未检测到台球", "warning"))
                
                # 更新统计
                self.stats['processed_images'] = processed
                self.stats['detected_balls'] = detected_total
                self.root.after(0, self.update_stats)
                
            except Exception as e:
                self.root.after(0, lambda err=str(e): self.log(f"   处理失败: {err}", "error"))
        
        # 完成处理
        self.root.after(0, lambda: self.progress_var.set(100))
        self.root.after(0, lambda: self.log(f"处理完成! 成功标注 {processed} 张图片，共检测到 {detected_total} 个台球", "success"))
        self.root.after(0, self.stop_annotation)
    
    def detect_with_api(self, image_path):
        """使用API检测台球"""
        try:
            with open(image_path, 'rb') as f:
                files = {'file': f}
                params = {'api_key': self.api_key}
                response = requests.post(self.api_url, files=files, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                predictions = result.get('predictions', [])
                
                # 过滤低置信度检测
                conf_threshold = self.confidence_threshold.get()
                filtered = [p for p in predictions if p.get('confidence', 0) >= conf_threshold]
                
                return filtered
            else:
                self.root.after(0, lambda code=response.status_code: 
                              self.log(f"   API错误: HTTP {code}", "error"))
                return []
                
        except Exception as e:
            self.root.after(0, lambda err=str(e): self.log(f"   API异常: {err}", "error"))
            return []
    
    def save_annotations(self, image_path, detections):
        """保存LabelMe格式的标注"""
        # 获取图片尺寸
        image = cv2.imread(str(image_path))
        height, width = image.shape[:2]
        
        # 创建LabelMe格式的标注
        shapes = []
        for detection in detections:
            x = detection.get('x', 0)
            y = detection.get('y', 0)
            w = detection.get('width', 0)
            h = detection.get('height', 0)
            confidence = detection.get('confidence', 0)
            class_name = detection.get('class', 'unknown')
            
            # 转换为矩形坐标
            x1 = x - w/2
            y1 = y - h/2
            x2 = x + w/2
            y2 = y + h/2
            
            shape = {
                "label": f"ball_{class_name}",
                "text": "",
                "points": [[float(x1), float(y1)], [float(x2), float(y2)]],
                "group_id": None,
                "shape_type": "rectangle",
                "flags": {}
            }
            shapes.append(shape)
        
        # 创建LabelMe JSON
        annotation = {
            "version": "0.4.30",
            "flags": {},
            "shapes": shapes,
            "imagePath": image_path.name,
            "imageData": None,
            "imageHeight": height,
            "imageWidth": width
        }
        
        # 保存JSON文件
        json_path = image_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(annotation, f, indent=2, ensure_ascii=False)
    
    def run(self):
        """运行GUI"""
        # 设置窗口图标（如果有的话）
        try:
            icon_path = Path(__file__).parent.parent / "04_build_scripts" / "bquill.png"
            if icon_path.exists():
                # 在macOS上可能需要转换为适当格式
                pass
        except:
            pass
        
        self.root.mainloop()


def main():
    """主函数"""
    print("启动现代化台球自动标注工具...")
    
    app = ModernBilliardAnnotationTool()
    app.run()


if __name__ == "__main__":
    main()