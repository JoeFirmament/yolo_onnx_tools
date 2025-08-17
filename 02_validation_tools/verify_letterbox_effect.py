#!/usr/bin/env python3
"""
验证letterbox预处理对PT-ONNX置信度匹配的影响
证明letterbox预处理是实现完美PT-ONNX匹配的关键
"""

import cv2
import numpy as np
import onnxruntime as ort
from ultralytics import YOLO

def letterbox(image, new_shape=(640, 640), color=(114, 114, 114)):
    """与Ultralytics一致的letterbox预处理"""
    shape = image.shape[:2]  # (h, w)
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
    dw /= 2
    dh /= 2

    if shape[::-1] != new_unpad:
        image = cv2.resize(image, new_unpad, interpolation=cv2.INTER_LINEAR)

    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    image = cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return image, r, (dw, dh)

def test_preprocessing_effect():
    """测试预处理方式对置信度的影响"""
    
    print("🧪 验证letterbox预处理对PT-ONNX置信度匹配的影响")
    print("=" * 70)
    
    # 加载模型
    try:
        pt_model = YOLO("best.pt")
        onnx_session = ort.InferenceSession("best_rk3588_simple.onnx", providers=['CPUExecutionProvider'])
        print("✅ 模型加载成功")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        print("提示：请先运行 python simple_rk3588_export.py best.pt")
        return
    
    # 测试图片
    test_image = "datasets/temp/images/val/20250811_100002_frame_000142.jpg"
    try:
        frame = cv2.imread(test_image)
        if frame is None:
            raise ValueError("无法读取图片")
        print(f"📸 测试图片: {test_image}")
        print(f"原始尺寸: {frame.shape}")
    except Exception as e:
        print(f"❌ 图片加载失败: {e}")
        return
    
    # PT模型推理（内部使用letterbox）
    pt_results = pt_model(test_image, conf=0.1, verbose=False)
    
    print(f"\n🔥 PT模型结果:")
    pt_detections = []
    if pt_results[0].boxes is not None:
        for box in pt_results[0].boxes:
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            class_name = pt_model.names[cls]
            pt_detections.append((class_name, conf))
            print(f"  {class_name}: {conf:.6f}")
    
    # ONNX测试1: 使用简单resize
    print(f"\n⚡ ONNX模型结果 (简单resize):")
    
    # resize预处理
    frame_resized = cv2.resize(frame, (640, 640))
    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
    frame_normalized = frame_rgb.astype(np.float32) / 255.0
    frame_tensor = np.transpose(frame_normalized, (2, 0, 1))
    frame_tensor = np.expand_dims(frame_tensor, axis=0)
    
    # ONNX推理
    input_name = onnx_session.get_inputs()[0].name
    outputs = onnx_session.run(None, {input_name: frame_tensor})
    
    # 简单后处理
    resize_detections = simple_postprocess(outputs, frame.shape[1], frame.shape[0])
    for det in resize_detections:
        print(f"  {det['class_name']}: {det['score']:.6f}")
    
    # ONNX测试2: 使用letterbox
    print(f"\n⚡ ONNX模型结果 (letterbox):")
    
    # letterbox预处理
    frame_letterbox, r, (dw, dh) = letterbox(frame, (640, 640))
    frame_rgb = cv2.cvtColor(frame_letterbox, cv2.COLOR_BGR2RGB)
    frame_normalized = frame_rgb.astype(np.float32) / 255.0
    frame_tensor = np.transpose(frame_normalized, (2, 0, 1))
    frame_tensor = np.expand_dims(frame_tensor, axis=0)
    
    # ONNX推理
    outputs = onnx_session.run(None, {input_name: frame_tensor})
    
    # letterbox后处理
    letterbox_detections = letterbox_postprocess(outputs, frame.shape[1], frame.shape[0], r, dw, dh)
    for det in letterbox_detections:
        print(f"  {det['class_name']}: {det['score']:.6f}")
    
    # 对比分析
    print(f"\n📊 置信度对比分析:")
    print("-" * 50)
    
    # 按类别对比
    pt_dict = {name: conf for name, conf in pt_detections}
    resize_dict = {det['class_name']: det['score'] for det in resize_detections}
    letterbox_dict = {det['class_name']: det['score'] for det in letterbox_detections}
    
    for class_name in ['basketball', 'rim']:
        pt_conf = pt_dict.get(class_name, 0)
        resize_conf = resize_dict.get(class_name, 0)
        letterbox_conf = letterbox_dict.get(class_name, 0)
        
        if pt_conf > 0 or resize_conf > 0 or letterbox_conf > 0:
            print(f"\n{class_name}:")
            print(f"  PT模型:        {pt_conf:.6f}")
            print(f"  ONNX(resize):  {resize_conf:.6f}  (差异: {abs(pt_conf-resize_conf):.6f})")
            print(f"  ONNX(letterbox): {letterbox_conf:.6f}  (差异: {abs(pt_conf-letterbox_conf):.6f})")
            
            if abs(pt_conf - letterbox_conf) < 0.000001:
                print(f"  ✅ letterbox实现完美匹配!")
            elif abs(pt_conf - resize_conf) > abs(pt_conf - letterbox_conf):
                print(f"  🎯 letterbox显著改善了匹配度")
                improvement = abs(pt_conf - resize_conf) / abs(pt_conf - letterbox_conf)
                print(f"  📈 改善倍数: {improvement:.1f}x")
            else:
                print(f"  ⚠️  需要进一步调试")

def simple_postprocess(outputs, original_width, original_height):
    """简单的resize后处理"""
    reg_outputs = [outputs[i] for i in [0, 2, 4]]
    cls_outputs = [outputs[i] for i in [1, 3, 5]]
    strides = [8, 16, 32]
    class_names = ['basketball', 'rim']
    
    all_detections = []
    
    for i, (reg_output, cls_output, stride) in enumerate(zip(reg_outputs, cls_outputs, strides)):
        if reg_output.shape[1] == 1:
            continue
            
        _, _, height, width = cls_output.shape
        
        # 处理分类输出
        cls_pred = cls_output.squeeze(0).transpose(1, 2, 0)
        cls_pred = np.clip(cls_pred.astype(np.float32), -10, 10)
        cls_scores = 1 / (1 + np.exp(-cls_pred))
        
        # 处理回归输出
        if reg_output.shape[1] == 4:
            reg_pred = reg_output.squeeze(0).transpose(1, 2, 0).reshape(-1, 4)
            
            # 创建anchor网格
            yv, xv = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')
            anchors = np.stack([xv + 0.5, yv + 0.5], axis=-1) * stride
            anchors = anchors.reshape(-1, 2)
            
            cls_scores_flat = cls_scores.reshape(-1, 2)
            max_scores = np.max(cls_scores_flat, axis=1)
            class_ids = np.argmax(cls_scores_flat, axis=1)
            
            valid_mask = max_scores > 0.1
            
            if np.any(valid_mask):
                valid_anchors = anchors[valid_mask]
                valid_reg = reg_pred[valid_mask]
                valid_scores = max_scores[valid_mask]
                valid_classes = class_ids[valid_mask]
                
                # 坐标解码
                left, top, right, bottom = valid_reg[:, 0], valid_reg[:, 1], valid_reg[:, 2], valid_reg[:, 3]
                cx, cy = valid_anchors[:, 0], valid_anchors[:, 1]
                
                x1 = cx - left * stride
                y1 = cy - top * stride
                x2 = cx + right * stride
                y2 = cy + bottom * stride
                
                boxes = np.stack([x1, y1, x2, y2], axis=1)
                
                for j in range(len(boxes)):
                    if boxes[j, 2] > boxes[j, 0] and boxes[j, 3] > boxes[j, 1]:
                        all_detections.append({
                            'bbox': boxes[j],
                            'score': valid_scores[j],
                            'class_id': valid_classes[j],
                            'class_name': class_names[valid_classes[j]]
                        })
    
    # 简单缩放
    scale_x = original_width / 640
    scale_y = original_height / 640
    
    for det in all_detections:
        det['bbox'][[0, 2]] *= scale_x
        det['bbox'][[1, 3]] *= scale_y
    
    # 按类别保留最高分
    best_by_class = {}
    for det in all_detections:
        cid = det['class_id']
        if cid not in best_by_class or det['score'] > best_by_class[cid]['score']:
            best_by_class[cid] = det
    
    return list(best_by_class.values())

def letterbox_postprocess(outputs, original_width, original_height, r, dw, dh):
    """letterbox后处理"""
    reg_outputs = [outputs[i] for i in [0, 2, 4]]
    cls_outputs = [outputs[i] for i in [1, 3, 5]]
    strides = [8, 16, 32]
    class_names = ['basketball', 'rim']
    
    all_detections = []
    
    for i, (reg_output, cls_output, stride) in enumerate(zip(reg_outputs, cls_outputs, strides)):
        if reg_output.shape[1] == 1:
            continue
            
        _, _, height, width = cls_output.shape
        
        # 处理分类输出
        cls_pred = cls_output.squeeze(0).transpose(1, 2, 0)
        cls_pred = np.clip(cls_pred.astype(np.float32), -10, 10)
        cls_scores = 1 / (1 + np.exp(-cls_pred))
        
        # 处理回归输出
        if reg_output.shape[1] == 4:
            reg_pred = reg_output.squeeze(0).transpose(1, 2, 0).reshape(-1, 4)
            
            # 创建anchor网格
            yv, xv = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')
            anchors = np.stack([xv + 0.5, yv + 0.5], axis=-1) * stride
            anchors = anchors.reshape(-1, 2)
            
            cls_scores_flat = cls_scores.reshape(-1, 2)
            max_scores = np.max(cls_scores_flat, axis=1)
            class_ids = np.argmax(cls_scores_flat, axis=1)
            
            valid_mask = max_scores > 0.1
            
            if np.any(valid_mask):
                valid_anchors = anchors[valid_mask]
                valid_reg = reg_pred[valid_mask]
                valid_scores = max_scores[valid_mask]
                valid_classes = class_ids[valid_mask]
                
                # 坐标解码
                left, top, right, bottom = valid_reg[:, 0], valid_reg[:, 1], valid_reg[:, 2], valid_reg[:, 3]
                cx, cy = valid_anchors[:, 0], valid_anchors[:, 1]
                
                x1 = cx - left * stride
                y1 = cy - top * stride
                x2 = cx + right * stride
                y2 = cy + bottom * stride
                
                boxes = np.stack([x1, y1, x2, y2], axis=1)
                
                for j in range(len(boxes)):
                    if boxes[j, 2] > boxes[j, 0] and boxes[j, 3] > boxes[j, 1]:
                        all_detections.append({
                            'bbox': boxes[j],
                            'score': valid_scores[j],
                            'class_id': valid_classes[j],
                            'class_name': class_names[valid_classes[j]]
                        })
    
    # letterbox坐标恢复
    for det in all_detections:
        bbox = det['bbox'].astype(np.float32)
        bbox[[0, 2]] -= dw
        bbox[[1, 3]] -= dh
        bbox /= r
        bbox[0] = max(0, min(bbox[0], original_width - 1))
        bbox[1] = max(0, min(bbox[1], original_height - 1))
        bbox[2] = max(0, min(bbox[2], original_width - 1))
        bbox[3] = max(0, min(bbox[3], original_height - 1))
        det['bbox'] = bbox
    
    # 按类别保留最高分
    best_by_class = {}
    for det in all_detections:
        cid = det['class_id']
        if cid not in best_by_class or det['score'] > best_by_class[cid]['score']:
            best_by_class[cid] = det
    
    return list(best_by_class.values())

if __name__ == "__main__":
    test_preprocessing_effect()