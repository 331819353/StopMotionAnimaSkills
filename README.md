# 定格动画技能集

一套面向 Codex 的中文数字定格动画技能，覆盖剧本、知识核实、分镜、AI 素材生成、逐帧合成和成片检查。适合故事短片、机制科普和故事化科普。

通过完整画面或完整角色姿态的离散替换、摆放和停格表现动作。纸偶、黏土、毛毡、积木、微缩模型等都可作为视觉材质。核心动作保留定格节奏，不使用视频生成、光流插帧或连续骨骼变形代替。

## 技能组成

| 技能 | 用途 |
| --- | --- |
| [stopmotion-production](Skills/stopmotion-production/SKILL.md) | 总入口：建立简报、选择制作模式、衔接阶段与管理返工 |
| [stopmotion-story](Skills/stopmotion-story/SKILL.md) | 故事剧本、实体道具笑点、反转铺垫与人物因果 |
| [stopmotion-explainer](Skills/stopmotion-explainer/SKILL.md) | 核实知识与来源、拆解机制、明确模型简化与适用边界 |
| [stopmotion-storyboard](Skills/stopmotion-storyboard/SKILL.md) | 分镜、动作阶段、整数帧节拍与动态分镜 |
| [stopmotion-assets](Skills/stopmotion-assets/SKILL.md) | 场景／阶段母版、整画面动作帧、完整角色与交互素材 |
| [stopmotion-animate](Skills/stopmotion-animate/SKILL.md) | 离散帧时间轴、PNG 帧合成、镜头播放检查 |
| [stopmotion-finish](Skills/stopmotion-finish/SKILL.md) | 剪辑、声音、精确字幕、连续性检查与交付 |

这些技能通过相对路径互相引用，建议将全部七个 `stopmotion-*` 文件夹安装在同一父目录下，保留各自的 `references/`、`scripts/` 和 `agents/`。

## 安装

### 通过 Codex 安装

在 Codex 中发送：

```text
$skill-installer
请从 GitHub 仓库 331819353/StopMotionAnimaSkills 的 dev 分支安装
Skills/ 下的全部七个技能：stopmotion-production、stopmotion-story、
stopmotion-explainer、stopmotion-storyboard、stopmotion-assets、
stopmotion-animate、stopmotion-finish。保留完整目录，并安装到同一父目录。
若已有同名技能，请先说明差异，不要直接覆盖。
```

### 手动安装（macOS / Linux）

克隆仓库并进入目录：

```sh
git clone --branch dev https://github.com/331819353/StopMotionAnimaSkills.git
cd StopMotionAnimaSkills
```

在仓库根目录执行以下命令，将七个技能复制到个人技能目录；若发现同名目录或链接，会停止，避免覆盖已有安装：

```sh
(
  skills_dest="$HOME/.agents/skills"
  for skill in Skills/stopmotion-*; do
    skill_name="${skill##*/}"
    if [ -e "$skills_dest/$skill_name" ] || [ -L "$skills_dest/$skill_name" ]; then
      printf '%s\n' "已存在：${skills_dest}/${skill_name}；请先比较并处理已有版本。" >&2
      exit 1
    fi
  done
  mkdir -p "$skills_dest"
  cp -R Skills/stopmotion-* "$skills_dest/"
)
```

仅在某个项目使用时，可把命令中的 `skills_dest` 改为该项目的 `.agents/skills` 绝对路径。仓库中的 `Skills/` 是源码目录，本身不等于已安装。

上述个人／项目目录、自动发现及显式调用方式见 [OpenAI 官方技能文档](https://learn.chatgpt.com/docs/build-skills)。已有安装使用其他路径时，以当前 Codex 的技能列表和安装器实际目标为准，避免重复安装同名技能。安装后检查技能列表；未出现时重启 Codex。CLI / IDE 中可用 `$stopmotion-production` 显式调用，也可描述任务让 Codex 匹配技能。

### 工具与依赖

- 编写剧本、简报与分镜主要依赖技能指令；科普内容还需可核查的资料和检索能力。
- 生成实际图像需要当前环境可用的生图／编辑工具。这套仓库不自带模型、服务额度或图像素材。
- 自带合成脚本需要 Python 3.9+ 和 Pillow，仅在运行该脚本时需要。建议在影片项目的虚拟环境中安装：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install Pillow
```

对白与旁白使用下述 Fish Audio MCP。音乐、音效和 MP4 等视频编码另需可用工具。基础脚本只输出无音频 PNG 帧序列、检查拼图和渲染记录。

### 配音：Fish Audio MCP

在终端添加服务并完成浏览器登录授权：

```sh
codex mcp add fish-audio --url https://api.fish.audio/mcp
# 添加时若未完成登录，再执行：
codex mcp login fish-audio
codex mcp get fish-audio
```

已有配置先核对，无需重复添加。连接方式见 [Fish Audio 官方 MCP 文档](https://docs.fish.audio/overview/mcp)；配音调用以当前 MCP 暴露的工具和参数为准。配置成功、已登录、当前聊天能调用工具是不同状态，需要分别检查。

音色只从 [指定候选表](Skills/stopmotion-finish/references/fish-audio-voices.json) 选择，按男／女及儿童、初高中、青年、中年、老年分组。分组来自用户，使用前核实服务端可用性、语言及样音；同一角色全片固定音色，旁白单独选声。原始 ID 不擅自补齐或修改，不可用时按配音规范处理，不自动回退到服务默认音色。

实际配音先用少量代表台词检查听感和时长，再按说话人／语义段生成与保存到项目 `audio/`。生成会消耗 Fish Audio 额度，先检查余额、当前费用与项目预算；本次无需配音的策划任务不调用生成。用真实音频校准整数帧、动作和字幕，不凭字数估时声称已同步。具体选声、落盘与检查要求见 [配音规范](Skills/stopmotion-finish/references/fish-audio.md)。

## 使用流程

1. **建立简报**：说明受众、主题、故事／科普／混合模式、时长、画幅、语言、材质、预算与交付范围。未指定的信息记录合理假设。
2. **剧本与事实边界**：故事先建立人物动机、因果与铺垫；科普先核实来源和机制；混合模式让故事建立在已核实的知识边界内。
3. **视觉小样**：选择代表镜头，验证母版、尺度、接触关系与姿态替换，再确定整画面或分层方式。
4. **分镜与动态分镜**：规划人物视线、相机、遮挡、必要中间动作、声音和整数帧节拍，试播确认信息来得及读懂。
5. **正式素材**：从已验收母版派生，保持实体几何、身份与状态连续；静止停格复用已有图像，不把输出帧数当作生图次数。
6. **逐镜合成**：按整数帧换图和保持，检查正常播放及关键帧；发现动作或朝向错误时回到相关分镜／素材修正。
7. **成片交付**：完成剪辑、声音与精确文字，检查事实和连续性，交付实际生成的文件与验证范围。

制作支持两种方式：

- **整画面替换**：每个动作状态是一张完整镜头画面，保留布景，通过整幅换图表现动作。
- **完整角色分层**：使用完整角色姿态或角色与道具的交互组合，独立管理环境与遮挡；角色身体、附肢和表情不拆件拼装。科普模型可按机制需要分件。

可以只调用某一阶段；全流程从总入口开始。用户指定的制作方式在后续阶段保持一致。

### 调用示例

完整制作：

```text
$stopmotion-production
制作一部面向小学生的 45 秒故事化科普定格短片，主题是种子发芽。
16:9、中文、黏土微缩风格，采用整画面替换。
请先核实发芽条件，再完成剧本、分镜、小样、素材、合成和成片检查。
把产物保存在 Projs/seed-growth/，记录实际工具、素材成本与未验证项。
```

只做策划：

```text
$stopmotion-storyboard
根据已有剧本制作 30 秒定格分镜和帧表，只交付策划。
人物阅读纸张时，请按人物视线和机位确定纸张正反面，
需要观众读到内容时使用指向纸张的放大框或画面左侧的文字说明。
```

运行基础合成脚本（从仓库根目录执行，路径替换为实际影片项目）：

```sh
.venv/bin/python Skills/stopmotion-animate/scripts/compose_frames.py check /path/to/project/shots/SH_001.json
.venv/bin/python Skills/stopmotion-animate/scripts/compose_frames.py render /path/to/project/shots/SH_001.json --out /path/to/project/shots/SH_001_v01_frames
```

镜头 JSON、真实 PNG 与输出规则见 [时间轴格式](Skills/stopmotion-animate/references/timeline-format.md)。输出目录必须尚不存在。脚本通过只代表文件与时间轴格式可用，画面中的动作、物理关系和知识仍需视觉检查。

## 知识点的图文说明

关键知识点优先采用**图片／机制示意／状态对比＋简短文字**。画面展示结构、过程或差异，短句与标签指出“看哪里、发生什么、在什么条件下成立”，并通过指示线、箭头或邻近排版关联到具体对象。按理解顺序逐步显露，保留图文对照和阅读的停格。

知识说明需要有实际解释作用的画面，不能只浮现一段文字，或用装饰图片配长段旁白。字幕负责转录配音，图内标注负责解释关键关系，两者按需要配合，避免遮挡和堆字。纸张放大框、画面左侧的说明区也可组合相关图像与短文字。

图像辅助理解，事实证据仍需可靠来源。真实照片／观测、数据绘图和机制示意应明确区分，AI 生成示意不能冒充实拍或实验结果。具体要求见 [科普技能](Skills/stopmotion-explainer/SKILL.md)。

## 现实规律与画面表达

动作和空间关系应符合已建立世界的规则。现实场景需要检查尺度、重心与支撑、操作能力、接触与遮挡、物件状态，以及人物和相机分别能看到的表面。幻想或夸张设定要先建立，科普中的简化要说明边界。

例如人物在读单面不透明纸张：有内容的一面应朝向人物，并符合其阅读方向。**从人物对面拍摄时，镜头通常看到纸背**，不能为了让观众读字，就把正文印在朝向镜头的背面。过肩或人物主观镜头可按合法视线展示正文；纸张翻面则应有对应动作，不能换帧时自动换面。

观众需要知道正文时，可保留纸张的真实朝向，使用以下表达：

- 从纸张引出指示线与放大框，展示与该纸张当前状态一致的内容。若正文在原镜头不可见，明确这是内容示意，不假称直接放大了纸背像素。
- 在画面左侧等留白区域浮现正文或摘要，作为画外说明，明确关联到纸张。
- 切换为能看到正文的过肩、主观或插入特写，并保持纸张状态和空间关系连续。

放大框和浮现文字属于给观众看的说明层，不是场景中凭空出现的第二张纸，也不自动表示角色看到了说明层。精确文字用确定性排版制作，再按分镜合成；整画面模式也可叠加此类说明，而不拆改人物或道具。

规则在分镜、提示词、素材和成片验收中共同执行，详见 [连续性与物理规范](Skills/stopmotion-production/references/continuity-and-physics.md)。

## 项目文件与完成状态

影片产物放在独立项目目录，例如 `Projs/<project-name>/`，不写入已安装的技能目录。建议按实际需要保存 `project.json`、`writing/`、`sources/`、`boards/`、`assets/`、`shots/`、`audio/` 和 `exports/`，用稳定 ID 与版本连接各阶段。

提示词、已生成素材、已检查镜头和已导出成片分别记录状态；缺少工具时交付已完成部分并说明缺口。完整目录、依赖与返工约定见 [项目交接规范](Skills/stopmotion-production/references/project-contract.md)。
