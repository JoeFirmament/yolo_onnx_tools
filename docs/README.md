## 项目简介
本仓库用于 YOLOv8/YOLO11 在 RK3588 上的训练、导出、验证与部署。当前稳定方案以“RKNN logits 规范”为准：
- ONNX 输出为 6 张量：`reg1, cls1, reg2, cls2, reg3, cls3`
- 回归分支 reg：DFL 已完成的四边距离，扁平布局 `[1, 1, 4, HW]`
- 分类分支 cls：logits（未 sigmoid），布局 `[1, C, H, W]`
- 预处理使用 letterbox；stride 顺序固定 `[8, 16, 32]`

## 目录结构与核心文件
- 根目录
  - `simple_rk3588_export.py`：标准导出脚本（PT → ONNX，6 输出，reg 扁平，cls=logits）
  - `modern_dual_comparator.py`：PT ↔ ONNX 实时对比 GUI，可视化 + 后处理（会对 logits 做 sigmoid）
  - `validate_onnx_cls_format.py`：ONNX 检查脚本（输入输出形状、cls 概率/logits 判别）
  - `yolov8_train_inf.md`：原始侵入式导出方法参考（仅参考，不改）
- `ultralytics/`：上游 YOLO 框架（保持原样）
- `datasets/`：数据集
- `runs/`、`weights/`、`images/`：训练、权重与样例图片
- `docs/archive/`（建议后续建立）：存放过时/旧流程文档与脚本

## 环境要求
- Python 3.8+（建议使用 Conda 管理）
- onnxruntime、opencv-python-headless（GUI 需 tkinter、Pillow）
- macOS/Linux/ARM Linux 均可作为工具运行环境；RKNN 转换与部署在 RK3588 设备端完成

## 快速上手
### 1) 导出 ONNX（RK3588 规范）
```bash
python simple_rk3588_export.py best.pt -o best_rk3588_simple.onnx
```
特性：
- 输出 6 张量；`reg=[1,1,4,HW]`（DFL 后距离），`cls=[1,C,H,W]`（logits）
- 固定 batch=1；`opset_version=11`；关闭 dynamic_axes，便于 RKNN 转换

### 2) 检查 ONNX 输出
```bash
python validate_onnx_cls_format.py best_rk3588_simple.onnx --letterbox \
  -i images/20250811_100002_frame_000000.jpg
```
期望：
- `reg1/2/3`: `[1,1,4,6400/1600/400]` 且数值 > 0
- `cls1/2/3`: `[1,2,H,W]` 且判定为 logits（min 多为负）

### 3) 可视化对比（PT ↔ ONNX）
```bash
python modern_dual_comparator.py
```
使用说明：
- 模型：左侧分别加载 `best.pt` 与导出的 `*_rk3588_simple.onnx`
- 预处理：letterbox（GUI 内置）
- 后处理：对 ONNX 的 cls（logits）执行稳定 sigmoid（clip[-50,50] 后 sigmoid）
- 置信度阈值：建议 0.01～0.05（滑块下限 0.01）
- 显示策略：默认“每类保留最高分”（如需多框可切换到 NMS 流程）

## RKNN 侧后处理规范（对齐线上分发）
- 量化模型：int8 → 反量化 → logits → unsigmoid 阈值预筛选 → sigmoid → 概率
- 浮点模型：logits → sigmoid → 概率
- 解码：
  - 以 `cls` 的形状得到 H、W，生成 anchors（中心点为 `(x+0.5, y+0.5)*stride`）
  - `reg[0,0].T → [H*W, 4]`，四个距离 `l,t,r,b` 配合 anchors 与 stride 还原 xyxy
  - letterbox 逆变换（去 padding + 按比例还原到原图）

## 常见错误与排查
- 现象：GUI 没有框
  - 原因1：阈值过高（0.1）。处理：降到 0.01～0.05
  - 原因2：加载的是旧 ONNX（cls 已 sigmoid），GUI 又 sigmoid → 置信度异常。处理：统一使用“cls=logits”的 RK3588 规范 ONNX
- 现象：GUI 打印“最高置信度=1.0000/0.0000”成片
  - 原因：把 logits 当概率直接 clip 到 [0,1]。处理：确认 GUI 确实对 logits 做了 sigmoid（本版本已处理）
- 现象：回归输出形状报“不匹配”或“未知”
  - 原因：reg 不是 `[1,1,4,HW]`。处理：用标准导出脚本重新导出
- 现象：视频线程异常（`cap.isOpened` 报错）
  - 原因：视频句柄未打开或被提前释放。处理：重新选择视频；当前 GUI 已用局部句柄保护
- 现象：RKNN 转换失败或推理出错
  - 检查：batch 是否固定为 1；是否用了 dynamic_axes；opset 版本≥11；输入尺寸固定 640×640

## 最佳实践
- 导出与验证使用统一脚本：`simple_rk3588_export.py` → `validate_onnx_cls_format.py` → `modern_dual_comparator.py`
- 始终使用 letterbox 预处理；stride 固定 `[8,16,32]`
- ONNX 的 `cls` 统一保持 logits；目标设备/GUI 再做 sigmoid
- 在提交给客户的 RKNN 流程中记录版本与导出时间，便于回溯

## FAQ
- Q：为什么不在导出图中对 cls 加 sigmoid？
  - A：RKNN 量化/加速链路可用 unsigmoid 阈值预筛选，能减少 sigmoid 调用，效率更高；统一 logits 更利于上/下游一致
- Q：为什么 reg 采用 `[1,1,4,HW]` 扁平布局？
  - A：IO 更小；CPU 后处理更快；量化后误差更可控；与 RKNN 示例常见实现更一致

## 版本与规范
- 当前稳定规范：6 输出；`reg=[1,1,4,HW]`（DFL 后距离）；`cls=[1,C,H,W]`（logits）；letterbox 预处理；stride `[8,16,32]`
- 参考文档：`yolov8_train_inf.md`（不修改，仅供参考）
- 主要脚本：`simple_rk3588_export.py`、`modern_dual_comparator.py`、`validate_onnx_cls_format.py`