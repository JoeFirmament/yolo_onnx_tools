#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import os
from pathlib import Path

import numpy as np
import onnxruntime as ort

try:
    import cv2
except Exception:
    cv2 = None


def letterbox(image, new_shape=(640, 640), color=(114, 114, 114)):
    h0, w0 = image.shape[:2]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)
    r = min(new_shape[0] / h0, new_shape[1] / w0)
    new_unpad = (int(round(w0 * r)), int(round(h0 * r)))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
    dw /= 2
    dh /= 2
    if (w0, h0) != new_unpad:
        image = cv2.resize(image, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    image = cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return image


def preprocess_image(img_bgr, size=640, letterbox_enabled=True):
    if letterbox_enabled:
        img = letterbox(img_bgr, (size, size))
    else:
        img = cv2.resize(img_bgr, (size, size))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    x = (img.astype(np.float32) / 255.0).transpose(2, 0, 1)[None]
    return x


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -250, 250)))


def analyze_outputs(tag, names, outputs):
    print(f"\n[{tag}]")
    cls_kv = {}
    for name, arr in zip(names, outputs):
        a = np.asarray(arr)
        a_min, a_max, a_mean = a.min(), a.max(), a.mean()
        print(f"  {name}: shape={tuple(a.shape)}, min={a_min:.4f}, max={a_max:.4f}, mean={a_mean:.4f}")
        if "cls" in name:
            in01 = (a >= 0.0).mean() * (a <= 1.0).mean()  # 粗略
            # 更稳健判断：范围在[0,1]且均值也在[0,1] → 概率；否则视为logits
            is_prob = (a_min >= -1e-6) and (a_max <= 1.0 + 1e-6)
            kind = "prob(0~1)" if is_prob else "logits"
            # 打印阈上数量参考
            if is_prob:
                above_01 = (a > 0.1).sum()
                above_03 = (a > 0.3).sum()
                above_05 = (a > 0.5).sum()
                print(f"    -> type={kind}, >0.1:{above_01}, >0.3:{above_03}, >0.5:{above_05}")
            else:
                above0 = (a > 0).sum()
                above2 = (a > 2.0).sum()
                print(f"    -> type={kind}, >0:{above0}, >2.0:{above2}")
            cls_kv[name] = (is_prob, a_min, a_max)
    return cls_kv


def main():
    ap = argparse.ArgumentParser(description="Validate ONNX cls outputs (prob vs logits) and IO shapes")
    ap.add_argument("model", type=str, help="Path to ONNX model")
    ap.add_argument("-i", "--image", type=str, default="", help="Optional image for real inference")
    ap.add_argument("--size", type=int, default=640, help="Input size (default: 640)")
    ap.add_argument("--letterbox", action="store_true", help="Use letterbox preprocess (default: False)")
    ap.add_argument("--providers", type=str, default="CPUExecutionProvider",
                    help="Comma-separated ORT providers, default CPUExecutionProvider")
    args = ap.parse_args()

    model_path = Path(args.model)
    assert model_path.exists(), f"Model not found: {model_path}"

    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    sess = ort.InferenceSession(str(model_path), providers=providers)

    print("Inputs:")
    for i in sess.get_inputs():
        print(f"  {i.name}: {i.shape} ({i.type})")
    print("Outputs:")
    out_names = [o.name for o in sess.get_outputs()]
    for o in sess.get_outputs():
        print(f"  {o.name}: {o.shape} ({o.type})")

    # Dummy inference
    inp0 = sess.get_inputs()[0]
    if isinstance(inp0.shape[0], str):
        b, c, h, w = 1, 3, args.size, args.size
    else:
        # 尽量按模型静态形状推测
        b = int(inp0.shape[0]) if isinstance(inp0.shape[0], (int, np.integer)) else 1
        c = int(inp0.shape[1]) if isinstance(inp0.shape[1], (int, np.integer)) else 3
        h = int(inp0.shape[2]) if isinstance(inp0.shape[2], (int, np.integer)) else args.size
        w = int(inp0.shape[3]) if isinstance(inp0.shape[3], (int, np.integer)) else args.size
    x_dummy = np.random.randn(b, c, h, w).astype(np.float32)
    outs_dummy = sess.run(None, {inp0.name: x_dummy})
    analyze_outputs("dummy", out_names, outs_dummy)

    # Real image inference
    if args.image:
        if cv2 is None:
            print("\n[warn] OpenCV not available; cannot run image inference.")
        elif not os.path.exists(args.image):
            print(f"\n[warn] image not found: {args.image}")
        else:
            img = cv2.imread(args.image)
            x_img = preprocess_image(img, size=args.size, letterbox_enabled=args.letterbox)
            outs_img = sess.run(None, {inp0.name: x_img})
            cls_info = analyze_outputs("image", out_names, outs_img)

            # 额外判断：若三个 cls 输出都被判定为 logits，给出提示
            cls_flags = [v[0] for k, v in cls_info.items() if "cls" in k]
            if cls_flags and not any(cls_flags):
                print("\n[hint] cls 似乎是 logits。可在可视化/后处理中对 cls 做一次 sigmoid 再阈值；"
                      "或在导出图中为 cls1/2/3 加 Sigmoid 使其变为 0~1 概率。")
            elif cls_flags and all(cls_flags):
                print("\n[hint] cls 似乎已是概率(0~1)。可直接用概率阈值(如 0.01~0.1)进行过滤。")

    print("\nDone.")


if __name__ == "__main__":
    main()