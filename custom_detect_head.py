#!/usr/bin/env python3
"""
自定义YOLOv8检测头 - 为RK3588优化
可以作为插件使用，不需要修改原始代码
"""

import torch
import torch.nn as nn
from ultralytics.nn.modules import Conv, DFL, Proto
from ultralytics.utils.tal import dist2bbox, make_anchors
import copy


class RK3588DetectHead(nn.Module):
    """为RK3588优化的检测头 - 继承自YOLOv8 Detect"""
    
    def __init__(self, nc=80, ch=()):
        """初始化RK3588优化的检测头"""
        super().__init__()
        self.nc = nc  # 类别数
        self.nl = len(ch)  # 检测层数
        self.reg_max = 16  # DFL通道数
        self.no = nc + self.reg_max * 4  # 每个anchor的输出数
        self.stride = torch.zeros(self.nl)  # 步长
        self.end2end = False
        
        # 通道配置
        c2, c3 = max((16, ch[0] // 4, self.reg_max * 4)), max(ch[0], min(self.nc, 100))
        
        # 回归分支
        self.cv2 = nn.ModuleList(
            nn.Sequential(Conv(x, c2, 3), Conv(c2, c2, 3), nn.Conv2d(c2, 4 * self.reg_max, 1)) 
            for x in ch
        )
        
        # 分类分支
        self.cv3 = nn.ModuleList(
            nn.Sequential(Conv(x, c3, 3), Conv(c3, c3, 3), nn.Conv2d(c3, self.nc, 1)) 
            for x in ch
        )
        
        # DFL模块
        self.dfl = DFL(self.reg_max) if self.reg_max > 1 else nn.Identity()
        
        # RK3588优化：添加conv1x1用于DFL处理
        self.conv1x1 = nn.Conv2d(16, 1, 1, bias=False)
        self.conv1x1.requires_grad_(False)
        x = torch.arange(16, dtype=torch.float)
        self.conv1x1.weight.data[:] = nn.Parameter(x.view(1, 16, 1, 1))
        
        # 导出模式标志
        self.export_mode = False
        self.export_format = 'rk3588'  # 可以是 'rk3588' 或 'standard'
    
    def forward(self, x):
        """前向传播"""
        if self.export_mode and self.export_format == 'rk3588':
            return self.forward_rk3588(x)
        else:
            return self.forward_standard(x)
    
    def forward_rk3588(self, x):
        """RK3588优化的前向传播 - 导出6个输出"""
        y = []
        for i in range(self.nl):
            # 获取回归和分类特征
            reg_feat = self.cv2[i](x[i])  # [batch, 64, H, W]
            cls_feat = self.cv3[i](x[i])  # [batch, nc, H, W]
            
            # 处理回归输出 - 应用DFL
            batch, _, h, w = reg_feat.shape
            reg_feat = reg_feat.view(batch, 4, 16, -1).transpose(2, 1).softmax(1)
            reg_output = self.conv1x1(reg_feat)  # [batch, 1, 4, H*W]
            
            # 添加到输出
            y.append(reg_output)
            y.append(cls_feat)
        
        return y
    
    def forward_standard(self, x):
        """标准YOLOv8前向传播"""
        for i in range(self.nl):
            x[i] = torch.cat((self.cv2[i](x[i]), self.cv3[i](x[i])), 1)
        
        if self.training:
            return x
        
        # 推理时的处理
        shape = x[0].shape
        x_cat = torch.cat([xi.view(shape[0], self.no, -1) for xi in x], 2)
        
        if self.export_mode:
            return x_cat
        
        # 标准后处理
        box, cls = x_cat.split((self.reg_max * 4, self.nc), 1)
        dbox = self.decode_bboxes(box)
        
        y = torch.cat((dbox, cls.sigmoid()), 1)
        return y, x
    
    def decode_bboxes(self, bboxes):
        """解码边界框"""
        return dist2bbox(self.dfl(bboxes), self.anchors.unsqueeze(0), xywh=True, dim=1) * self.strides
    
    def set_export_mode(self, mode=True, format='rk3588'):
        """设置导出模式"""
        self.export_mode = mode
        self.export_format = format


def replace_detect_head(model, export_format='rk3588'):
    """替换模型的检测头为RK3588优化版本"""
    # 找到Detect层
    detect_layer = None
    detect_index = -1
    
    for i, module in enumerate(model.model):
        if module.__class__.__name__ == 'Detect':
            detect_layer = module
            detect_index = i
            break
    
    if detect_layer is None:
        raise ValueError("No Detect layer found in model")
    
    # 创建新的检测头
    nc = detect_layer.nc
    ch = [detect_layer.cv2[i][0].conv.in_channels for i in range(detect_layer.nl)]
    new_detect = RK3588DetectHead(nc=nc, ch=ch)
    
    # 复制权重
    new_detect.cv2.load_state_dict(detect_layer.cv2.state_dict())
    new_detect.cv3.load_state_dict(detect_layer.cv3.state_dict())
    new_detect.dfl.load_state_dict(detect_layer.dfl.state_dict())
    new_detect.stride = detect_layer.stride
    
    # 设置导出模式
    new_detect.set_export_mode(True, export_format)
    
    # 替换检测头
    model.model[detect_index] = new_detect
    
    return model


# 使用示例
if __name__ == "__main__":
    from ultralytics import YOLO
    
    # 加载模型
    model = YOLO('yolov8n.pt')
    
    # 替换检测头
    model.model = replace_detect_head(model.model, export_format='rk3588')
    
    # 导出ONNX
    dummy_input = torch.randn(1, 3, 640, 640)
    torch.onnx.export(
        model.model,
        dummy_input,
        "yolov8n_rk3588.onnx",
        input_names=["images"],
        output_names=["reg1", "cls1", "reg2", "cls2", "reg3", "cls3"],
        opset_version=11
    )