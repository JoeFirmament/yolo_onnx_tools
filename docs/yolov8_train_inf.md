# yolov8训练、导出、推理、推流、加速
## 1、yolov8训练
### 1.1、环境安装
```bash
# 进入home目录
cd ~
# 创建目录
mkdir train
# 下载docker镜像文件
# 更多镜像文件可以访问：https://catalog.ngc.nvidia.com/orgs/nvidia/containers/pytorch/tags获取
docker pull nvcr.io/nvidia/pytorch:24.08-py3
# 安装镜像
docker run -it --gpus "device=0" --name pytorch24.08 -v ~/train:/softs nvcr.io/nvidia/pytorch:24.08-py3 /bin/bash
# 使用vscode进入镜像
# 视频操作演示
# 下载yolov8项目
git clone https://github.com/ultralytics/ultralytics
# 安装yolov8依赖
pip install ultralytics -i https://pypi.tuna.tsinghua.edu.cn/simple
# 安装headless
pip install "opencv-python-headless<4.3"
# 测试推理
yolo predict model=yolov8n.pt source='ultralytics/assets/bus.jpg' device=0
```
### 1.2、熟悉yolov8项目目录
详见视频

### 1.3、训练数据组织
在datasets目录中组织好训练数据，目录结构如下
```bash
# cx是训练数据集的名字，自己定义
# images/train存放训练图片
datasets/cx/images/train
# images/val存放验证图片
datasets/cx/images/val
# labels/train存放训练标注数据
datasets/cx/labels/train
# labels/val存放验证标注数据
datasets/cx/labels/val
```
编写数据说明yaml文件
```yaml
# Train/val/test sets as 1) dir: path/to/imgs, 2) file: path/to/imgs.txt, or 3) list: [path/to/imgs1, path/to/imgs2, ..]
path: /app/docs/yolov8/ultralytics/datasets/bz_formal  # dataset root dir
train: images/train  # train images (relative to 'path') 4 images
val: images/val  # val images (relative to 'path') 4 images
test:  # test images (optional)

# Classes (80 COCO classes)
names:
  0: plant
  1: empty
  2: camber
```

### 1.4、训练
```python
from ultralytics import YOLO

# 加载模型
# model = YOLO('weights/yolov8s.pt')

model = YOLO('ultralytics/cfg/models/v8/yolov8n.yaml')
# model = YOLO('yolov8s.yaml')

results = model.train(data='datasets/bz_formal/bz_formal.yaml', epochs=200, imgsz=640, workers=0, batch=48, name='bz-n-200-formal', project='yolov8_bz' )
```

### 1.5、加速
加速方式是瑞芯微推荐的修改激活函数，可以大幅增加推理速度，但是会降低推理速度此方法在map低于90%时候不建议使用。
找到ultralytics/nn/modules/conv.py大概40行左右，修改激活函数为ReLU，重新训练，训练只可以直接应用yaml模型描述文件不要引用模型。
```python
class Conv(nn.Module):
    """Standard convolution with args(ch_in, ch_out, kernel, stride, padding, groups, dilation, activation)."""

    # default_act = nn.SiLU()  # default activation
    default_act = nn.ReLU()

    def __init__(self, c1, c2, k=1, s=1, p=None, g=1, d=1, act=True):
        """Initialize Conv layer with given arguments including activation."""
        super().__init__()
        self.conv = nn.Conv2d(c1, c2, k, s, autopad(k, p, d), groups=g, dilation=d, bias=False)
        self.bn = nn.BatchNorm2d(c2)
        self.act = self.default_act if act is True else act if isinstance(act, nn.Module) else nn.Identity()

    def forward(self, x):
        """Apply convolution, batch normalization and activation to input tensor."""
        return self.act(self.bn(self.conv(x)))

    def forward_fuse(self, x):
        """Perform transposed convolution of 2D data."""
        return self.act(self.conv(x))
```


## 2、修改模型导出onnx
### 2.1、修改文件
修改ultralytics/nn/modules/head.py30行位置找到__init__添加下面两段
```python
def __init__(self, nc=80, ch=()):
        """Initializes the YOLOv8 detection layer with specified number of classes and channels."""
        super().__init__()
        self.nc = nc  # number of classes
        self.nl = len(ch)  # number of detection layers
        self.reg_max = 16  # DFL channels (ch[0] // 16 to scale 4/8/12/16/20 for n/s/m/l/x)
        self.no = nc + self.reg_max * 4  # number of outputs per anchor
        self.stride = torch.zeros(self.nl)  # strides computed during build
        c2, c3 = max((16, ch[0] // 4, self.reg_max * 4)), max(ch[0], min(self.nc, 100))  # channels
        self.cv2 = nn.ModuleList(
            nn.Sequential(Conv(x, c2, 3), Conv(c2, c2, 3), nn.Conv2d(c2, 4 * self.reg_max, 1)) for x in ch
        )
        self.cv3 = nn.ModuleList(nn.Sequential(Conv(x, c3, 3), Conv(c3, c3, 3), nn.Conv2d(c3, self.nc, 1)) for x in ch)
        self.dfl = DFL(self.reg_max) if self.reg_max > 1 else nn.Identity()

        if self.end2end:
            self.one2one_cv2 = copy.deepcopy(self.cv2)
            self.one2one_cv3 = copy.deepcopy(self.cv3)
        # >>>>>>>>>>>>>>>>>>>>>添加的内容<<<<<<<<<<<<<<<<<<<<
        # 导出 onnx 增加
        self.conv1x1 = nn.Conv2d(16, 1, 1, bias=False).requires_grad_(False)
        x = torch.arange(16, dtype=torch.float)
        self.conv1x1.weight.data[:] = nn.Parameter(x.view(1, 16, 1, 1))
        # >>>>>>>>>>>>>>>>>>>>>添加的内容<<<<<<<<<<<<<<<<<<<<

    def forward(self, x):
        # >>>>>>>>>>>>>>>>>>>>>添加的内容<<<<<<<<<<<<<<<<<<<<
        # 导出 onnx 增加
        y = []
        for i in range(self.nl):
            t1 = self.cv2[i](x[i])
            t2 = self.cv3[i](x[i])
            y.append(self.conv1x1(t1.view(t1.shape[0], 4, 16, -1).transpose(2,1).softmax(1)))
            y.append(t2)
        return y
        # >>>>>>>>>>>>>>>>>>>>>添加的内容<<<<<<<<<<<<<<<<<<<<
        
        """Concatenates and returns predicted bounding boxes and class probabilities."""
        if self.end2end:
            return self.forward_end2end(x)

        for i in range(self.nl):
            x[i] = torch.cat((self.cv2[i](x[i]), self.cv3[i](x[i])), 1)
        if self.training:  # Training path
            return x
        y = self._inference(x)
        return y if self.export else (y, x)
```
修改ultralytics/engine/model.py 237行左右 def _new(self, cfg: str, task=None, model=None, verbose=False) -> None方法下面添加
```python
def _new(self, cfg: str, task=None, model=None, verbose=False) -> None:
        """
        Initializes a new model and infers the task type from the model definitions.

        This method creates a new model instance based on the provided configuration file. It loads the model
        configuration, infers the task type if not specified, and initializes the model using the appropriate
        class from the task map.

        Args:
            cfg (str): Path to the model configuration file in YAML format.
            task (str | None): The specific task for the model. If None, it will be inferred from the config.
            model (torch.nn.Module | None): A custom model instance. If provided, it will be used instead of creating
                a new one.
            verbose (bool): If True, displays model information during loading.

        Raises:
            ValueError: If the configuration file is invalid or the task cannot be inferred.
            ImportError: If the required dependencies for the specified task are not installed.

        Examples:
            >>> model = Model()
            >>> model._new("yolov8n.yaml", task="detect", verbose=True)
        """
        cfg_dict = yaml_model_load(cfg)
        self.cfg = cfg
        self.task = task or guess_model_task(cfg_dict)
        self.model = (model or self._smart_load("model"))(cfg_dict, verbose=verbose and RANK == -1)  # build model
        self.overrides["model"] = self.cfg
        self.overrides["task"] = self.task

        # Below added to allow export from YAMLs
        self.model.args = {**DEFAULT_CFG_DICT, **self.overrides}  # combine default and model args (prefer model args)
        self.model.task = self.task
        self.model_name = cfg
        # >>>>>>>>>>>>>>>>>>>>>添加的内容<<<<<<<<<<<<<<<<<<<<
        print("===========  onnx =========== ")
        import torch
        self.model.fuse() 
        self.model.eval()
        self.model.load_state_dict(torch.load('weights/yolov8.dict.pt', map_location='cpu'), strict=False)

        dummy_input = torch.randn(1, 3, 640, 640)
        input_names = ["data"]
        output_names = ["reg1", "cls1", "reg2", "cls2", "reg3", "cls3"]
        torch.onnx.export(self.model, dummy_input, "weights/yolov8.onnx",
                          verbose=False, input_names=input_names, output_names=output_names, opset_version=11)
        print("======================== convert onnx Finished! .... ")
        # >>>>>>>>>>>>>>>>>>>>>添加的内容<<<<<<<<<<<<<<<<<<<<

    def _load(self, weights: str, task=None) -> None:
        """
        Loads a model from a checkpoint file or initializes it from a weights file.

        This method handles loading models from either .pt checkpoint files or other weight file formats. It sets
        up the model, task, and related attributes based on the loaded weights.

        Args:
            weights (str): Path to the model weights file to be loaded.
            task (str | None): The task associated with the model. If None, it will be inferred from the model.

        Raises:
            FileNotFoundError: If the specified weights file does not exist or is inaccessible.
            ValueError: If the weights file format is unsupported or invalid.

        Examples:
            >>> model = Model()
            >>> model._load("yolov8n.pt")
            >>> model._load("path/to/weights.pth", task="detect")
        """
        if weights.lower().startswith(("https://", "http://", "rtsp://", "rtmp://", "tcp://")):
            weights = checks.check_file(weights, download_dir=SETTINGS["weights_dir"])  # download and return local file
        weights = checks.check_model_file_from_stem(weights)  # add suffix, i.e. yolov8n -> yolov8n.pt

        if Path(weights).suffix == ".pt":
            self.model, self.ckpt = attempt_load_one_weight(weights)
            self.task = self.model.args["task"]
            self.overrides = self.model.args = self._reset_ckpt_args(self.model.args)
            self.ckpt_path = self.model.pt_path
        else:
            weights = checks.check_file(weights)  # runs in all cases, not redundant with above call
            self.model, self.ckpt = weights, None
            self.task = task or guess_model_task(weights)
            self.ckpt_path = weights
        self.overrides["model"] = weights
        self.overrides["task"] = self.task
        self.model_name = weights
        
        # >>>>>>>>>>>>>>>>>>>>>添加的内容<<<<<<<<<<<<<<<<<<<<
        print("===========  Save dict  =========== ")
        import torch
        self.model.fuse()
        self.model.eval()
        torch.save(self.model.state_dict(), 'weights/yolov8.dict.pt')
        print("======================== Save dict Finished! .... ")
        # >>>>>>>>>>>>>>>>>>>>>添加的内容<<<<<<<<<<<<<<<<<<<<
```

### 2.2、导出onnx
在项目根目录下面创建export_onnx.py
```python
>>>>>>>>>>>>>>>>>>>>>修改后导出模型代码<<<<<<<<<<<<<<<<<<<<
from ultralytics import YOLO

# # 加载模型
model = YOLO('weights/yolov8n.pt')
# # 加载模型配置文件，注意需要匹配
model = YOLO('ultralytics/cfg/models/v8/yolov8n.yaml')

>>>>>>>>>>>>>>>>>>>>>原始模型导出代码<<<<<<<<<<<<<<<<<<<<
# from ultralytics import YOLO

# # Load the YOLOv8 model
# model = YOLO("yolov8s.pt")

# # Export the model to ONNX format
# model.export(format="onnx")
```

### 2.3、修改导致的输出格式变化详解

⚠️ **重要说明**: 经过上述修改后，导出的ONNX模型输出格式发生了重大变化，请仔细阅读以下内容。

#### 原始YOLO输出格式 vs 修改后输出格式

**原始YOLO输出**:
- 3个检测层输出
- 每层输出形状: `[batch, (classes + 4 + 16*4), height, width]`
- 输出是合并的tensor，包含分类和回归信息

**修改后输出格式**:
- **6个独立输出**: `reg1, cls1, reg2, cls2, reg3, cls3`
- **分离了回归和分类输出**
- **已完成DFL(Distribution Focal Loss)处理**

#### 具体输出说明

对于输入尺寸 `[1, 3, 640, 640]`，篮球篮筐检测模型(2个类别)的输出：

**回归输出 (reg1, reg2, reg3)**:
- `reg1`: 形状 `[1, 1, 80, 80]` - P3层边界框坐标 (已处理)
- `reg2`: 形状 `[1, 1, 40, 40]` - P4层边界框坐标 (已处理) 
- `reg3`: 形状 `[1, 1, 20, 20]` - P5层边界框坐标 (已处理)

**分类输出 (cls1, cls2, cls3)**:
- `cls1`: 形状 `[1, 2, 80, 80]` - P3层分类概率 (篮球、篮筐)
- `cls2`: 形状 `[1, 2, 40, 40]` - P4层分类概率 (篮球、篮筐)
- `cls3`: 形状 `[1, 2, 20, 20]` - P5层分类概率 (篮球、篮筐)

#### DFL处理说明

修改后的模型在forward中执行了以下DFL处理：
```python
# 对回归分支t1进行DFL处理
t1_processed = self.conv1x1(
    t1.view(t1.shape[0], 4, 16, -1)    # 重塑为 [batch, 4, 16, H*W]
    .transpose(2,1)                     # 转置为 [batch, 16, 4, H*W]  
    .softmax(1)                        # 在16个分布上做softmax
)
```

这意味着：
- ✅ **输出已经是处理后的边界框坐标**，不需要再进行DFL解码
- ✅ **后处理更简单**，直接使用回归输出作为坐标
- ⚠️ **与标准YOLO不同**，需要适配新的后处理流程

#### 后处理注意事项

1. **坐标解码**: 回归输出已经过DFL处理，但仍需要：
   - 乘以对应的stride (8, 16, 32)
   - 加上anchor点坐标偏移

2. **分类处理**: 
   - 对cls输出应用sigmoid激活
   - 类别0: 篮球, 类别1: 篮筐

3. **NMS处理**: 
   - 需要将6个输出重新组合
   - 应用置信度阈值和NMS

#### 测试建议

导出ONNX模型后，建议：
1. 使用ONNXRuntime加载模型验证输出形状
2. 用示例图片测试推理，检查输出数值范围
3. 实现相应的后处理代码
4. 与原始PyTorch模型对比精度

## 3、量化
### 3.1、组织脚本
查看提供的资料，将转换文件复制到toolkit2环境下面

### 3.2、执行量化
查看视频操作方式

## 4、部署使用
代码详解看视频