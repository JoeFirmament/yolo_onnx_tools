#!/usr/bin/env python3
"""
最简单的RK3588 ONNX导出方案
动态替换检测头的forward方法，无需修改源码
"""

import torch
import torch.nn as nn
from ultralytics import YOLO
import types
import argparse
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


def create_rk3588_forward(detect_head):
    """为检测头创建RK3588风格的forward方法"""
    
    # 创建conv1x1层 - 按照yolov8_train_inf.md第120-122行
    conv1x1 = nn.Conv2d(16, 1, 1, bias=False).requires_grad_(False)
    x = torch.arange(16, dtype=torch.float)
    conv1x1.weight.data[:] = nn.Parameter(x.view(1, 16, 1, 1))
    
    # 将conv1x1添加到检测头
    detect_head.conv1x1 = conv1x1
    
    def rk3588_forward(self, x):
        """完全复制yolov8_train_inf.md第125-134行的forward逻辑"""
        y = []
        for i in range(self.nl):
            t1 = self.cv2[i](x[i])  # 回归分支
            t2 = self.cv3[i](x[i])  # 分类分支（保持logits格式，不加sigmoid）
            
            # 完全复制文档第132行的DFL处理逻辑
            dfl_processed = self.conv1x1(
                t1.view(t1.shape[0], 4, 16, -1)  # reshape to [batch, 4, 16, H*W]
                .transpose(2, 1)                  # transpose to [batch, 16, 4, H*W]
                .softmax(1)                      # softmax on 16 distributions
            )  # conv1x1: [batch, 1, 4, H*W]
            
            # RK3588 期望的回归输出布局：保持扁平化 [batch, 1, 4, H*W]
            reg_output = dfl_processed
            
            y.append(reg_output)  # regN
            y.append(t2)         # clsN
        
        return y
    
    return rk3588_forward


def export_rk3588_onnx(model_path, output_path=None):
    """导出RK3588优化的ONNX模型"""
    
    if output_path is None:
        model_stem = Path(model_path).stem
        output_path = f"{model_stem}_rk3588_simple.onnx"
    
    print(f"📦 加载YOLO模型: {model_path}")
    model = YOLO(model_path)
    
    # 设置模型为推理模式
    model.model.eval()
    model.model.float()
    
    # 获取检测头
    detect_head = model.model.model[-1]
    print(f"✓ 检测头类型: {type(detect_head)}")
    print(f"✓ 检测层数: {detect_head.nl}")
    print(f"✓ 类别数: {detect_head.nc}")
    
    # 动态替换forward方法
    print(f"🔄 替换检测头forward方法...")
    new_forward = create_rk3588_forward(detect_head)
    detect_head.forward = types.MethodType(new_forward, detect_head)
    
    # 测试模型
    print(f"🧪 测试修改后的模型...")
    dummy_input = torch.randn(1, 3, 640, 640)
    
    with torch.no_grad():
        try:
            outputs = model.model(dummy_input)
            print(f"✓ 模型测试成功，输出数量: {len(outputs)}")
            for i, out in enumerate(outputs):
                print(f"  输出{i}: {list(out.shape)}")
        except Exception as e:
            print(f"❌ 模型测试失败: {e}")
            return
    
    # 按照yolov8_train_inf.md第192-195行设置输入输出名称
    input_names = ["data"]
    output_names = ["reg1", "cls1", "reg2", "cls2", "reg3", "cls3"]
    
    print(f"🔄 导出ONNX模型到: {output_path}")
    torch.onnx.export(
        model.model,
        dummy_input,
        output_path,
        verbose=False,
        input_names=input_names,
        output_names=output_names,
        opset_version=11,
        do_constant_folding=True,
        # 固定batch=1，与侵入式方法保持完全一致
        dynamic_axes=None
    )
    
    print(f"✅ RK3588 ONNX导出成功: {output_path}")
    
    # 验证ONNX模型
    try:
        import onnxruntime as ort
        print(f"🧪 验证ONNX模型...")
        session = ort.InferenceSession(output_path, providers=['CPUExecutionProvider'])
        
        print("\n📊 ONNX模型信息:")
        print("输入:")
        for inp in session.get_inputs():
            print(f"  {inp.name}: {inp.shape} ({inp.type})")
        
        print("输出:")
        for out in session.get_outputs():
            print(f"  {out.name}: {out.shape} ({out.type})")
        
        # 测试推理对比
        print(f"\n🎯 推理对比测试:")
        input_data = dummy_input.numpy()
        
        # ONNX推理
        onnx_outputs = session.run(None, {input_names[0]: input_data})
        print("ONNX输出:")
        for i, (name, output) in enumerate(zip(output_names, onnx_outputs)):
            print(f"  {name}: {output.shape}, 数值范围: [{output.min():.4f}, {output.max():.4f}]")
        
        # PT推理
        with torch.no_grad():
            pt_outputs = model.model(dummy_input)
        print("PT输出:")
        for i, output in enumerate(pt_outputs):
            output_np = output.numpy()
            name = output_names[i]
            print(f"  {name}: {output_np.shape}, 数值范围: [{output_np.min():.4f}, {output_np.max():.4f}]")
        
    except ImportError:
        print("⚠️ 未安装onnxruntime，跳过验证")
    except Exception as e:
        print(f"⚠️ ONNX验证失败: {e}")


def main():
    parser = argparse.ArgumentParser(description='Simple RK3588 ONNX Export')
    parser.add_argument('model', help='Path to YOLOv8 model (.pt file)')
    parser.add_argument('-o', '--output', help='Output ONNX file path')
    
    args = parser.parse_args()
    
    # 导出RK3588优化的ONNX
    export_rk3588_onnx(args.model, args.output)


if __name__ == "__main__":
    main()