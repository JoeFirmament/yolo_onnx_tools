#!/usr/bin/env python3
"""
RK3588 ONNX导出工具 - GUI版本
现代化界面，专注于PT→ONNX转换的核心功能
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import threading
from pathlib import Path
from datetime import datetime
import warnings

# 抑制系统警告
warnings.filterwarnings("ignore", category=UserWarning)
if sys.platform == "darwin":
    os.environ['TK_SILENCE_DEPRECATION'] = '1'

try:
    import torch
    import torch.nn as nn
    from ultralytics import YOLO
    import types
    DEPENDENCIES_OK = True
except ImportError as e:
    DEPENDENCIES_OK = False
    MISSING_DEPS = str(e)


class RK3588ExportGUI:
    def __init__(self):
        if not DEPENDENCIES_OK:
            self.show_dependency_error()
            return
            
        self.root = tk.Tk()
        self.root.title("RK3588 ONNX Export Tool")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
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
        
        
        self.root.configure(bg=self.colors['bg'])
        
        # 初始化变量
        self.model_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.is_processing = False
        self.progress_var = tk.DoubleVar()
        
        # 导出配置
        self.batch_size = tk.IntVar(value=1)
        self.img_size = tk.IntVar(value=640)
        self.opset_version = tk.IntVar(value=11)
        
        self.setup_styles()
        self.setup_ui()
    
    def setup_styles(self):
        """设置ttk样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 按钮样式 - 专业低饱和度配色
        style.configure('Primary.TButton',
                       font=('SF Pro Text', 11, 'bold'),
                       foreground='white',
                       background='#6c757d',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        
        style.configure('Success.TButton',
                       font=('SF Pro Text', 11, 'bold'),
                       foreground='white',
                       background='#6c9b7f',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        
        # ✅ 输入框样式 - 完整的光标设置
        style.configure('Modern.TEntry',
                       fieldbackground='white',
                       borderwidth=1,
                       relief='solid',
                       bordercolor='#ddd',
                       insertcolor='#212529',  # 🔑 光标颜色
                       insertwidth=2,  # 🔑 光标宽度
                       font=('SF Pro Text', 11))
        
    def show_dependency_error(self):
        """显示依赖错误"""
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "依赖错误",
            f"缺少必要依赖:\n{MISSING_DEPS}\n\n请安装:\npip install torch ultralytics"
        )
        root.destroy()
    
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
        right_panel.pack(side='right', fill='y', padx=(10, 0))
        right_panel.configure(width=300)
        
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
            text="RK3588 ONNX Export Tool",
            font=(self.fonts['sans'][0], 24, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['bg']
        )
        title_label.pack(anchor='w')
        
        # 副标题
        subtitle_label = tk.Label(
            header_frame,
            text="将PyTorch模型转换为RK3588优化的ONNX格式",
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
        # 内容容器
        content = tk.Frame(parent, bg=self.colors['card'])
        content.pack(fill='both', expand=True, padx=30, pady=30)
        
        # 模型选择区域
        self.create_section_title(content, "模型选择")
        model_frame = self.create_input_group(content)
        
        tk.Label(
            model_frame,
            text="PT模型路径:",
            font=(self.fonts['sans'][0], 11),
            fg=self.colors['text'],
            bg=self.colors['card']
        ).pack(anchor='w')
        
        path_frame = tk.Frame(model_frame, bg=self.colors['card'])
        path_frame.pack(fill='x', pady=(5, 0))
        
        model_entry = ttk.Entry(
            path_frame,
            textvariable=self.model_path,
            style='Modern.TEntry'
        )
        model_entry.pack(side='left', fill='x', expand=True)
        
        browse_btn = ttk.Button(
            path_frame,
            text="浏览",
            command=self.browse_model,
            style='Primary.TButton'
        )
        browse_btn.pack(side='right', padx=(10, 0))
        
        # 输出路径区域
        self.create_section_title(content, "输出设置", pady_top=25)
        output_frame = self.create_input_group(content)
        
        tk.Label(
            output_frame,
            text="输出路径:",
            font=(self.fonts['sans'][0], 11),
            fg=self.colors['text'],
            bg=self.colors['card']
        ).pack(anchor='w')
        
        output_path_frame = tk.Frame(output_frame, bg=self.colors['card'])
        output_path_frame.pack(fill='x', pady=(5, 0))
        
        output_entry = ttk.Entry(
            output_path_frame,
            textvariable=self.output_path,
            style='Modern.TEntry'
        )
        output_entry.pack(side='left', fill='x', expand=True)
        
        output_browse_btn = ttk.Button(
            output_path_frame,
            text="选择",
            command=self.browse_output,
            style='Primary.TButton'
        )
        output_browse_btn.pack(side='right', padx=(10, 0))
        
        # 参数配置区域
        self.create_section_title(content, "导出参数", pady_top=25)
        params_frame = self.create_input_group(content)
        
        # 创建参数网格
        params_grid = tk.Frame(params_frame, bg=self.colors['card'])
        params_grid.pack(fill='x')
        
        # 第一行：Batch Size 和 Image Size
        row1 = tk.Frame(params_grid, bg=self.colors['card'])
        row1.pack(fill='x', pady=(0, 10))
        
        # Batch Size
        batch_frame = tk.Frame(row1, bg=self.colors['card'])
        batch_frame.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        tk.Label(
            batch_frame,
            text="Batch Size:",
            font=(self.fonts['sans'][0], 10),
            fg=self.colors['text'],
            bg=self.colors['card']
        ).pack(anchor='w')
        
        batch_spinbox = tk.Spinbox(
            batch_frame,
            from_=1, to=16,
            textvariable=self.batch_size,
            font=(self.fonts['mono'][0], 10),
            width=10,
            relief='solid',
            bd=1
        )
        batch_spinbox.pack(anchor='w', pady=(2, 0))
        
        # Image Size
        size_frame = tk.Frame(row1, bg=self.colors['card'])
        size_frame.pack(side='right', fill='x', expand=True, padx=(10, 0))
        
        tk.Label(
            size_frame,
            text="Image Size:",
            font=(self.fonts['sans'][0], 10),
            fg=self.colors['text'],
            bg=self.colors['card']
        ).pack(anchor='w')
        
        size_spinbox = tk.Spinbox(
            size_frame,
            from_=320, to=1280, increment=32,
            textvariable=self.img_size,
            font=(self.fonts['mono'][0], 10),
            width=10,
            relief='solid',
            bd=1
        )
        size_spinbox.pack(anchor='w', pady=(2, 0))
        
        # OPSET版本
        opset_frame = tk.Frame(params_grid, bg=self.colors['card'])
        opset_frame.pack(fill='x')
        
        tk.Label(
            opset_frame,
            text="OPSET版本:",
            font=(self.fonts['sans'][0], 10),
            fg=self.colors['text'],
            bg=self.colors['card']
        ).pack(anchor='w')
        
        opset_spinbox = tk.Spinbox(
            opset_frame,
            from_=9, to=17,
            textvariable=self.opset_version,
            font=(self.fonts['mono'][0], 10),
            width=10,
            relief='solid',
            bd=1
        )
        opset_spinbox.pack(anchor='w', pady=(2, 0))
        
        # 导出按钮
        button_frame = tk.Frame(content, bg=self.colors['card'])
        button_frame.pack(fill='x', pady=(30, 0))
        
        self.export_btn = ttk.Button(
            button_frame,
            text="开始导出",
            command=self.start_export,
            style='Success.TButton'
        )
        self.export_btn.pack()
        
        # 进度条
        self.progress_frame = tk.Frame(content, bg=self.colors['card'])
        self.progress_frame.pack(fill='x', pady=(20, 0))
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            length=400
        )
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=(self.fonts['sans'][0], 10),
            fg=self.colors['text_secondary'],
            bg=self.colors['card']
        )
    
    def setup_right_panel(self, parent):
        """设置右侧信息面板"""
        content = tk.Frame(parent, bg=self.colors['card'])
        content.pack(fill='both', expand=True, padx=20, pady=30)
        
        # 功能特点
        self.create_section_title(content, "功能特点", size=14)
        
        features = [
            "• RK3588专用优化",
            "• 6个独立输出张量",
            "• 完美PT-ONNX数值匹配",
            "• 非侵入式转换",
            "• 支持批量处理",
            "• 实时进度显示"
        ]
        
        for feature in features:
            feature_label = tk.Label(
                content,
                text=feature,
                font=(self.fonts['sans'][0], 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['card'],
                anchor='w'
            )
            feature_label.pack(fill='x', pady=(5, 0))
        
        # 输出格式说明
        self.create_section_title(content, "输出格式", size=14, pady_top=25)
        
        format_info = tk.Text(
            content,
            height=8,
            font=(self.fonts['mono'][0], 9),
            bg=self.colors['info'],
            fg=self.colors['info_text'],
            relief='solid',
            bd=1,
            wrap='word'
        )
        format_info.pack(fill='x', pady=(10, 0))
        
        format_text = """输出张量格式:
reg1: [B, 1, 4, H1*W1]
cls1: [B, NC, H1, W1]
reg2: [B, 1, 4, H2*W2]
cls2: [B, NC, H2, W2]
reg3: [B, 1, 4, H3*W3]
cls3: [B, NC, H3, W3]

完美适配RK3588平台"""
        
        format_info.insert('1.0', format_text)
        format_info.configure(state='disabled')
        
        # 联系方式
        self.create_section_title(content, "联系方式", size=14, pady_top=25)
        
        contact_label = tk.Label(
            content,
            text="bquill@qq.com",
            font=(self.fonts['mono'][0], 10),
            fg='#666666',
            bg=self.colors['card'],
            cursor='hand2'
        )
        contact_label.pack(anchor='w')
        
        # 添加点击复制功能
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
            text="就绪",
            font=(self.fonts['sans'][0], 10),
            fg=self.colors['text_light'],
            bg=self.colors['bg']
        )
        self.status_label.pack(anchor='w', pady=(10, 0))
    
    def browse_model(self):
        """浏览模型文件"""
        filename = filedialog.askopenfilename(
            title="选择PT模型文件",
            filetypes=[("PyTorch模型", "*.pt"), ("所有文件", "*.*")]
        )
        if filename:
            self.model_path.set(filename)
            # 自动设置输出路径
            model_path = Path(filename)
            output_name = model_path.stem + "_rk3588_gui.onnx"
            self.output_path.set(str(model_path.parent / output_name))
    
    def browse_output(self):
        """选择输出路径"""
        filename = filedialog.asksaveasfilename(
            title="保存ONNX文件",
            defaultextension=".onnx",
            filetypes=[("ONNX模型", "*.onnx"), ("所有文件", "*.*")]
        )
        if filename:
            self.output_path.set(filename)
    
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
    
    def start_export(self):
        """开始导出过程"""
        if self.is_processing:
            return
            
        if not self.model_path.get():
            messagebox.showerror("错误", "请选择PT模型文件")
            return
            
        if not self.output_path.get():
            messagebox.showerror("错误", "请设置输出路径")
            return
        
        # 开始处理
        self.is_processing = True
        self.export_btn.configure(state='disabled', text="导出中...")
        self.progress_bar.pack(fill='x', pady=(10, 0))
        self.progress_label.pack(pady=(5, 0))
        self.progress_bar.start()
        
        # 在新线程中执行导出
        thread = threading.Thread(target=self.export_model)
        thread.daemon = True
        thread.start()
    
    def export_model(self):
        """实际执行模型导出"""
        try:
            self.update_status("正在加载模型...", "info")
            
            # 导入核心转换函数
            from simple_rk3588_export import create_rk3588_forward
            
            # 加载模型
            model = YOLO(self.model_path.get())
            
            self.update_status("正在应用RK3588优化...", "info")
            
            # 应用RK3588优化
            detect_head = model.model.model[-1]
            rk3588_forward = create_rk3588_forward(detect_head)
            # 统一导出为6输出：对可能的4头模型再加一层保险，仅返回前3头(6张量)
            def forward_6only(self, x):
                out = rk3588_forward(self, x)
                if isinstance(out, (list, tuple)):
                    return list(out)[:6]
                return out
            detect_head.forward = types.MethodType(forward_6only, detect_head)
            
            self.update_status("正在导出ONNX模型...", "info")
            
            # 导出ONNX
            dummy_input = torch.randn(
                self.batch_size.get(),
                3,
                self.img_size.get(),
                self.img_size.get()
            )
            
            torch.onnx.export(
                model.model,
                dummy_input,
                self.output_path.get(),
                input_names=['images'],
                output_names=['reg1', 'cls1', 'reg2', 'cls2', 'reg3', 'cls3'],
                dynamic_axes=None,
                opset_version=self.opset_version.get(),
                verbose=False
            )
            
            # 成功完成
            self.root.after(0, self.export_complete_success)
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.export_complete_error(error_msg))
    
    def export_complete_success(self):
        """导出成功完成"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()
        
        self.is_processing = False
        self.export_btn.configure(state='normal', text="开始导出")
        
        self.update_status("导出完成！", "success")
        
        messagebox.showinfo(
            "导出成功",
            f"RK3588优化的ONNX模型已保存到:\n{self.output_path.get()}\n\n"
            "输出格式: 6个独立张量 (reg1,cls1,reg2,cls2,reg3,cls3)"
        )
    
    def export_complete_error(self, error_msg):
        """导出失败处理"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()
        
        self.is_processing = False
        self.export_btn.configure(state='normal', text="开始导出")
        
        self.update_status("导出失败", "error")
        
        messagebox.showerror(
            "导出失败",
            f"导出过程中发生错误:\n{error_msg}"
        )
    
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
    if not DEPENDENCIES_OK:
        print(f"错误: 缺少必要依赖\n{MISSING_DEPS}")
        print("\n请安装依赖:\npip install torch ultralytics")
        return
    
    app = RK3588ExportGUI()
    app.run()


if __name__ == "__main__":
    main()