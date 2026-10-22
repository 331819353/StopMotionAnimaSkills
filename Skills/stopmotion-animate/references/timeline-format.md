# 镜头时间轴 v1 与基础合成

## 运行方式

需要 Python 3.9+ 和 Pillow。先找到实际可用的运行时。下面的 `python` 指该运行时，脚本路径从本 skill 目录解析，镜头 JSON 保存在影片项目中。

```sh
python /path/to/stopmotion-animate/scripts/compose_frames.py check /path/to/project/shots/SH_001.json
python /path/to/stopmotion-animate/scripts/compose_frames.py render /path/to/project/shots/SH_001.json --out /path/to/project/shots/SH_001_v01_frames
```

`check` 验证 JSON、全部引用图片、尺寸、alpha、整数帧区间和状态字段。`render` 内部也先执行全部检查，再渲染。错误返回非零退出码，不写半成品输出目录。输出目录必须不存在，避免覆盖已有成果。

成功输出：`frames/frame_000000.png` 起的完整连续帧、`contact_sheet.png`（最多 12 张均匀取样＋状态切换前后关键帧）、`render.json`（参数、输入文件摘要与实际输出）。拼图用于初查，不是可播放预览；仍需编码并观看、按镜头选择放大检查。基础脚本不包含声音与视频编码。

## JSON 结构

下面是结构示例，不自带影片图片。使用前必须将 paths 和尺寸替换为真实素材数据。除所列字段外不接收其他字段，避免默默忽略用户想要的效果。

```json
{
  "schema_version": 1,
  "canvas": {"width": 640, "height": 360, "background": [242, 235, 222, 255]},
  "fps": 24,
  "frame_count": 24,
  "assets": {
    "AST_001_P01": {
      "path": "../../assets/AST_001_P01.png",
      "expected_size": [160, 200],
      "pivot": [80, 190],
      "alpha_required": true
    },
    "AST_001_P02": {
      "path": "../../assets/AST_001_P02.png",
      "expected_size": [160, 200],
      "pivot": [80, 190],
      "alpha_required": true
    }
  },
  "tracks": [
    {
      "id": "character",
      "z": 10,
      "gap_policy": "invisible",
      "states": [
        {"start": 0, "end": 12, "asset": "AST_001_P01", "x": 200, "y": 320, "scale": 1, "rotation": 0, "opacity": 1},
        {"start": 12, "end": 24, "asset": "AST_001_P02", "x": 240, "y": 320, "scale": 1, "rotation": 0, "opacity": 1}
      ]
    }
  ]
}
```

## 字段与坐标

- schema_version 固定 1；整数 fps、frame_count 必须为正数。当前基础实现不支持分数 fps；需要时选择实际支持的外部合成工具并保持全片一致。
- canvas width/height 是正整数，background 是四个 0–255 整数 RGBA。透明背景可用 `[0,0,0,0]`。
- assets 是非空对象，键即真实资产／姿态 ID。path 仅支持本地 PNG，绝对路径或相对 JSON 所在目录的路径；不接受网络 URL。
- expected_size 是真实源图宽高；pivot 是源图像素坐标，允许在图外定义支点。alpha_required=true 时，实际 PNG 必须有透明通道且至少一个像素非完全不透明，不接受画在白底／棋盘格上的假透明。背景可为 false。
- tracks 是非空数组；id 唯一，z 为整数，按 z 从小到大合成；相同 z 按数组顺序后者盖前者。需要中途变层可拆为不同 z 的轨道，用互斥时间段避免重复。
- gap_policy 必须显式为 invisible：轨道无状态覆盖的帧不可见。初次出现／离开时间因此可被明确设计。不要忘写区间而期待自动保持。
- states 非空，每项均完整填写 start/end/asset/x/y/scale/rotation/opacity，不继承上一状态。按 start 递增，区间不可重叠，允许相邻和显式空隙。
- 帧从 0 开始，区间 `[start,end)`，即包含 start 不含 end，且 `0 ≤ start < end ≤ frame_count`。每状态在整个区间保持不变，没有任何自动插值。
- x/y 表示源图 pivot 摆放到画布的像素位置，画布左上为 (0,0)，x 向右、y 向下。坐标可为小数，取样到像素时需检查细微跳动；优先按视觉效果选择整数步长。
- scale 为正数，保持宽高比；rotation 单位为度、绕 pivot 逆时针为正。opacity 为 0–1。平面旋转不创造新视角。

## 实现边界与错误处理

渲染采用最近邻取样，不生成新姿态、不变形、不补帧。每个状态的图层只在状态改变时重算，状态保持期间复用。透明度乘原始 alpha，不改变源文件。

自动校验无法判断脚底是否正确、物体是否滑动、角色身份是否漂移、知识是否成立。坐标在画布外也可能是有意出入场，因此不强制报错；必须看预览核查。

不支持音频、文字排版、相机、动态 z、蒙版、3D、混合模式、自动接触绑定、分数帧率和影片编码。需要时先将精确文本／遮挡预处理成 PNG，或换实际可用的合成工具，不向 JSON 塞未知字段。

脚本读所有图片完成验证后才开始输出，先写同级临时目录，成功后改名为目标目录。异常清理临时结果，输入文件不变；故意中断或系统退出遗留的临时目录可以核实后清理。不要覆盖正式成果。

## 整画面模式的现有字段写法

无需新增脚本字段：每张完整PNG是一个asset，expected_size为真实完整画布，pivot=[0,0]，alpha_required=false（不透明场景）。仅设一个full_frame轨道，各状态使用对应整幅asset，x=y=0、scale=1、rotation=0、opacity=1，在整数帧区间切换。输出画布与源图一致，不单独变换人物／道具。统一交付尺寸转换按项目规范另记，不用于掩盖局部比例漂移。

这些参数只保证整图按帧替换，不会检查画面中的比例、数量、接触、未授权变化或背景闪烁；仍需视觉验收。
