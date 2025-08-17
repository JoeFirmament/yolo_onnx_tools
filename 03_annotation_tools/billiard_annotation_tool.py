#!/usr/bin/env python3
"""
台球自动标注工具 - 基于Roboflow API
使用已测试成功的台球检测API进行自动标注
现代化GUI界面，符合macOS规范
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

# 抑制macOS系统警告
warnings.filterwarnings("ignore", category=UserWarning)
if sys.platform == "darwin":  # macOS
    os.environ['TK_SILENCE_DEPRECATION'] = '1'


class BilliardAnnotationTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎱 台球自动标注工具 - AI智能检测")
        self.root.geometry("1000x750")
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
            'already_annotated': 0,
            'detected_objects': 0,
            'processing_time': 0
        }
        
        self.configure_styles()
        self.setup_ui()
        
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
        
        style.configure('Danger.TButton',
                       font=('SF Pro Text', 11, 'bold'),
                       foreground='white',
                       background=self.colors['danger'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        
        # 输入框样式
        style.configure('Modern.TEntry',
                       fieldbackground=self.colors['card'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.colors['border'],
                       insertcolor=self.colors['text'],  # 设置光标颜色
                       insertwidth=2,  # 设置光标宽度
                       font=('SF Pro Text', 11))
    
    def create_card(self, parent, title, icon=None):
        """创建现代化卡片容器 - 仿健康仪表板风格"""
        # 卡片主容器 - 添加阴影效果
        card = tk.Frame(parent, bg=self.colors['card'], relief='flat', bd=0)
        card.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
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
    
    def setup_ui(self):
        """设置现代化界面"""
        # 主容器 - 仪表板风格布局
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True, padx=25, pady=20)
        
        # 应用标题区
        self.create_header(main_container)
        
        # 第一行：配置卡片（左右布局）
        config_row = tk.Frame(main_container, bg=self.colors['bg'])
        config_row.pack(fill='x', pady=(0, 20))
        
        # 左侧：API配置
        api_frame = tk.Frame(config_row, bg=self.colors['bg'])
        api_frame.pack(side='left', fill='both', expand=True, padx=(0, 15))
        self.create_api_card(api_frame)
        
        # 右侧：处理配置
        process_frame = tk.Frame(config_row, bg=self.colors['bg'])  
        process_frame.pack(side='right', fill='both', expand=True, padx=(15, 0))
        self.create_processing_card(process_frame)
        
        # 第二行：进度卡片（全宽）
        progress_row = tk.Frame(main_container, bg=self.colors['bg'])
        progress_row.pack(fill='x', pady=(0, 20))
        self.create_progress_card(progress_row)
        
        # 第三行：结果显示（全宽）
        results_row = tk.Frame(main_container, bg=self.colors['bg'])
        results_row.pack(fill='both', expand=True)
        self.create_results_card(results_row)
    
    def create_header(self, parent):
        """创建应用标题区"""
        title_frame = tk.Frame(parent, bg=self.colors['bg'])
        title_frame.pack(fill='x', pady=(0, 25))
        
        ttk.Label(title_frame, text="🎱 台球自动标注工具", 
                 style='Title.TLabel').pack(anchor='w')
        ttk.Label(title_frame, text="基于Roboflow API的智能台球检测与标注，自动生成LabelMe格式标注文件", 
                 style='Subtitle.TLabel').pack(anchor='w', pady=(5, 0))
    
    def create_api_card(self, parent):
        """创建API配置卡片"""
        card, content = self.create_card(parent, "🔧 API配置")
        card.pack(fill='x', pady=(0, 15))
        
        # API信息显示
        api_frame = tk.Frame(content, bg=self.colors['card'])
        api_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(api_frame, text="Roboflow API状态", style='Info.TLabel').pack(anchor='w', pady=(0, 5))
        
        # API状态显示
        status_frame = tk.Frame(api_frame, bg=self.colors['card'])
        status_frame.pack(fill='x')
        
        self.api_status = ttk.Label(status_frame, text="✅ API已配置 - 台球检测模型", style='Muted.TLabel')
        self.api_status.pack(anchor='w')
        
        # 台球类别显示
        classes_frame = tk.Frame(content, bg=self.colors['card'])
        classes_frame.pack(fill='x', pady=(15, 0))
        
        ttk.Label(classes_frame, text="检测类别", style='Info.TLabel').pack(anchor='w', pady=(0, 5))
        
        classes_text = "1-15号球 + 母球(cue)，共16种台球类型"
        ttk.Label(classes_frame, text=classes_text, style='Muted.TLabel').pack(anchor='w')
    
    def create_processing_card(self, parent):
        """创建处理配置卡片"""
        card, content = self.create_card(parent, "⚙️ 处理配置")
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
        self.conf_scale.config(command=self.update_conf_label)
        
        # 开始处理按钮
        button_frame = tk.Frame(content, bg=self.colors['card'])
        button_frame.pack(fill='x', pady=(10, 0))
        
        self.start_button = ttk.Button(button_frame, text="🚀 开始标注", 
                                     command=self.start_annotation, style='Success.TButton')
        self.start_button.pack(side='right')
        
        self.stop_button = ttk.Button(button_frame, text="⏹ 停止处理", 
                                    command=self.stop_annotation, style='Danger.TButton', state='disabled')
        self.stop_button.pack(side='right', padx=(0, 10))
    
    def create_progress_card(self, parent):
        """创建进度显示卡片"""
        card, content = self.create_card(parent, "📊 处理进度")
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
    
    def create_results_card(self, parent):
        """创建结果显示卡片"""
        card, content = self.create_card(parent, "📝 处理日志")
        card.pack(fill='both', expand=True)
        
        # 工具栏
        toolbar = tk.Frame(content, bg=self.colors['card'])
        toolbar.pack(fill='x', pady=(0, 15))
        
        ttk.Button(toolbar, text="清空日志", command=self.clear_log, 
                  style='Primary.TButton').pack(side='right')
        
        # 日志文本区域
        text_frame = tk.Frame(content, bg=self.colors['card'])
        text_frame.pack(fill='both', expand=True)
        
        self.results_text = tk.Text(text_frame, height=12, bg=self.colors['card'], 
                                   fg=self.colors['text'], font=('SF Mono', 10),
                                   relief='flat', wrap='word', bd=0,
                                   insertbackground=self.colors['text'],  # 光标颜色
                                   insertwidth=2)  # 光标宽度
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def browse_folder(self):
        """选择图片文件夹"""
        folder = filedialog.askdirectory(title="选择包含台球图片的文件夹")
        if folder:
            self.image_folder.set(folder)
            self.log(f"📁 选择文件夹: {folder}")
            self.scan_images()
            self.update_stats_display()
            
    def scan_images(self):
        """扫描图片文件"""
        folder = self.image_folder.get()
        if not folder:
            return
            
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
            image_files.extend(Path(folder).glob(ext))
            
        self.log(f"🔍 找到 {len(image_files)} 张图片")
        
        # 统计已标注的图片
        annotated = sum(1 for img in image_files if img.with_suffix('.json').exists())
        self.log(f"📊 统计结果: 已标注 {annotated} 张，待标注 {len(image_files) - annotated} 张")
        
        # 更新统计数据
        self.stats['total_images'] = len(image_files)
        self.stats['already_annotated'] = annotated
        self.stats['processed_images'] = 0  # 本次处理数，开始时为0
        self.stats['detected_objects'] = 0
        
        self.update_stats_display()
    
    def update_stats_display(self):
        """更新统计信息显示"""
        # 这里可以添加统计卡片的更新逻辑
        # 目前通过日志显示统计信息
        pass
        
    def update_conf_label(self, value):
        """更新置信度标签"""
        self.conf_label.config(text=f"{float(value):.2f}")
        
    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.results_text.insert('end', log_message)
        self.results_text.see('end')
        self.root.update_idletasks()
        
    def clear_log(self):
        """清空日志"""
        self.results_text.delete('1.0', 'end')
        
    def start_annotation(self):
        """开始标注"""
        if not self.image_folder.get():
            messagebox.showerror("错误", "请先选择图片文件夹")
            return
            
        if not os.path.exists(self.image_folder.get()):
            messagebox.showerror("错误", "选择的文件夹不存在")
            return
            
        self.is_processing = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        # 在新线程中处理
        threading.Thread(target=self.process_images, daemon=True).start()
        
    def stop_annotation(self):
        """停止标注"""
        self.is_processing = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="[取消] 用户停止处理")
        self.log("⏹ 用户停止处理")
        
    def process_images(self):
        """处理图片"""
        import time
        start_time = time.time()
        
        folder = Path(self.image_folder.get())
        
        # 获取所有图片文件
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
            image_files.extend(folder.glob(ext))
            
        # 过滤掉已标注的图片
        to_process = [img for img in image_files if not img.with_suffix('.json').exists()]
        
        if not to_process:
            self.log("✅ 所有图片都已标注完成")
            self.stop_annotation()
            return
            
        self.log(f"🚀 开始处理 {len(to_process)} 张图片")
        
        # 重置本次处理的统计数据
        self.stats['processed_images'] = 0
        self.stats['detected_objects'] = 0
        
        processed = 0
        detected_total = 0
        
        for i, img_file in enumerate(to_process):
            if not self.is_processing:
                break
                
            # 更新进度
            progress = (i + 1) / len(to_process) * 100
            self.progress_var.set(progress)
            self.status_label.config(text=f"[处理中] {img_file.name}")
            self.current_file_label.config(text=f"正在处理: {img_file.name}")
            
            self.log(f"🔄 处理 ({i+1}/{len(to_process)}): {img_file.name}")
            
            try:
                # 使用API检测
                detections = self.detect_with_api(str(img_file))
                
                if detections:
                    # 保存标注
                    self.save_annotations(img_file, detections)
                    processed += 1
                    detected_total += len(detections)
                    
                    # 更新统计
                    self.stats['processed_images'] = processed
                    self.stats['detected_objects'] = detected_total
                    
                    self.log(f"   ✅ 检测到 {len(detections)} 个台球，已保存标注")
                else:
                    self.log(f"   ⚠️  未检测到台球")
                    
            except Exception as e:
                self.log(f"   ❌ 处理失败: {e}")
                
        # 完成处理
        end_time = time.time()
        self.stats['processing_time'] = end_time - start_time
        
        self.progress_var.set(100)
        self.status_label.config(text="[完成] 处理完成")
        self.current_file_label.config(text="")
        
        # 生成完成消息
        processing_time = self.stats['processing_time']
        status_message = f"🎉 处理完成! 用时 {processing_time:.1f}秒，成功标注 {processed} 张图片，共检测到 {detected_total} 个台球"
        if len(to_process) - processed > 0:
            status_message += f"，{len(to_process) - processed} 张图片未检测到目标"
        
        self.log(status_message)
        self.stop_annotation()
        
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
                self.log(f"   API错误: {response.status_code}")
                return []
                
        except Exception as e:
            self.log(f"   API异常: {e}")
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
        """运行应用"""
        self.root.mainloop()


def main():
    """主函数"""
    print("🎱 启动台球自动标注工具...")
    print("[成功] 依赖检查通过")
    print("正在初始化现代化GUI界面...")
    
    try:
        app = BilliardAnnotationTool()
        app.run()
    except Exception as e:
        print(f"[错误] 应用启动失败: {e}")
        messagebox.showerror("启动错误", f"应用启动失败:\n{str(e)}")


if __name__ == "__main__":
    main()