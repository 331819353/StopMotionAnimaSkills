# 项目交接规范

## 目录与状态

建议目录按实际产物创建：`project.json`、`writing/`、`sources/`、`boards/`、`assets/`、`shots/`、`audio/`、`exports/`。不建立空壳文件冒充阶段完成。

`project.json` 至少保存：

- `project_id`、`mode`（story / explainer / hybrid）、`brief`（受众、主题、风格、时长、语言、比例、预算）、`assumptions`。
- `production_mode`（full_frame / layered_assets）及选择依据／用户指定方式。
- `output`（width、height、fps）以及 `motion_policy`（初始 hold 节奏、材质、允许的离散变换）；最终 fps 必须在分镜锁定前确定。
- `versions`：剧本、来源表、视觉规范、分镜、资产和时间轴的当前版本。
- `artifacts`：每项的 id、path、version、status、depends_on。状态为 planned / draft / checked / rendered / stale / blocked，不混淆审核通过和已渲染。
- `changes`：原因、受影响 ID、失效项、已完成修复；`blockers`：缺失工具或信息的实际影响。

可采用适合项目的 JSON / Markdown 表格保存详细产物，稳定 ID 和引用关系必须一致。整个项目 JSON 不等同于合成脚本所读的镜头 JSON。

## 稳定 ID

推荐 `BEAT_001` 情节／讲解节拍、`CLM_001` 科普论断、`SRC_001` 来源、`SH_001` 镜头、`AST_001` 资产族、`AST_001_P03` 姿态、`AUD_001` 声音。修改版本不重命名实体；新实体才分配新 ID。文件名应能找回相应 ID。

## 剧本交接

每个节拍至少写：ID、情节或知识目标、可见的素材状态变化、对白／旁白、声音、预计时长、关联资产、结束状态。故事还记录 setup/payoff 与时间线；科普记录 claim_ids 和模型限制；混合模式两者都要。

故事记录两张顺序表：真实事件顺序、播放顺序，并另列观众知识状态。科普默认记录解释依赖关系，不强迫交叉时间线；涉及历史／过程再记录时间。

## 镜头卡

每个镜头包含：

- id、script_version、beat_ids、claim_ids（如适用）、场景、时间线（如适用）、画面目的。
- fps、frame_count、全片顺序、构图、画幅、相机状态、地面／支点、图层与遮挡。
- 起始姿态、预备、动作突破、停格、反应、结束状态；用本镜头零起点帧区间 `[start,end)` 标注。所有区间必须落在镜头帧数内。
- asset_ids、pose_ids、source_ids、接触对、文字标注、声音 cue 与其帧区间。
- 进入／离开画面的方向、视线、持物、落脚点等连续性要求。
- 涉及阅读／展示时，记录信息所在面、人物／相机各自可见面及阅读方向；观众说明层另记来源实体、内容版本、指向锚点、位置和帧区间，并区分可见区域放大与隐藏内容示意。
- 科普的示意类型、简化、误读风险与检查结果。
- 关键知识的 claim_id、对应图像／状态对比、支持该论断的可见关系、配套短句／标签及其指向与显露区间；真实证据和示意分别标明来源或简化。
- status、依赖版本、预览路径、未解决问题。

镜头目的可以由多个图层共同承担，不能机械地“一句话旁白配一张图”。总时长用实际镜头帧数计算，不靠散文估计。

## 资产索引

每项保存：id、family_id、version、path、kind、generation_status、parent_reference、生成／编辑方式、所用实际提示词、画布像素、透明要求、pivot、角度、光向、比例、姿态语义、接触点、可复用范围、依赖镜头、检查状态。

角色资产另记录 `composition_unit`（whole_character / character_prop_group）、`included_entity_ids`、`mutually_exclusive_layers`、角色母版版本、完整姿态 ID、实际支撑点与接触位置。结构以母版为准，角色分件不得标为生产可用。背景、独立对象和科普模型不受角色整图粒度限制。

组合的所有成员在 included_entity_ids 内明确列出；切换到组合时关闭相同实体的独立层，脱离后按同一几何与状态交还独立层。组合与独立素材不能重复叠放。项目资产索引可包含这些语义字段，基础合成 JSON 仍只使用其已实现字段。

`pivot` 是源图片坐标中的支点，不是裁剪后的想当然中心。相同家族统一画布和单位尺度；不同姿态在支点对齐后检查视觉跳动。母版定义的身份、结构、表面与材质特征必须视觉检查，文件名一致不能证明身份一致。

## 整画面交接

整画面记录composition_unit=full_frame、scene_master_id、phase_master_id、target_state_id、参考职责、固定地标、允许变化集合和检查状态。完整PNG保留全画布，不输出角色拼装层；角色三视图不充当场景尺度或当前物品状态。新阶段生产母版需要相应检查通过；失败帧派生的诊断分支单列，不进入正式依赖。

## 连续性生产数据

按 [连续性与物理规范](continuity-and-physics.md) 保存 scale_lock（世界尺度、几何与相机）、entity_states（适用属性、所属实体／参考系、存在与可见性）、events（状态变化及原因）和 action_paths（动作依赖、资源、空间路径、支撑／归属交接，按需填写）。每镜引用 state_in / state_out、scale_lock_id 和 action_ids；姿态引用相同版本。

现实实体与科普模型使用不同 ID；多时间结构按事件时间快照恢复。组合继承成员状态，换图不重置，子对象按其所属参考系变化。字段用于项目语义检查，不把未实现字段塞进基础合成器 JSON。

## 提示词交接

按 [提示词分层与绑定](prompt-contract.md) 保存精确实际提示词及其 rule_version、project_id、规范版本、shot_id／asset_id、母版引用和适用的几何／状态／动作参数来源。引用 ID 之外，工具必须看到完成当前任务所需的具体值和实际参考。通用技能不保存具体作品设定；历史调用不被后续修订覆写。

## 配音交接

按 [Fish Audio MCP 规范](../../stopmotion-finish/references/fish-audio.md) 在项目中保存 `speaker_id → voice_id` 映射及选择依据、验证状态。每段 `AUD_*` 记录剧本版本、原文与实际送入文本／标签、说话人、音色 ID、真实工具／可得设置、结果链接与本地路径、实测时长和音频参数、检查状态、依赖镜头及整数帧 cue。只保存实际获得的数据，不保存 OAuth 凭据。

音色表的用户分类与服务端查询／实际监听结果分开记录；音色或台词改变时标记受影响音频、镜头计时和字幕失效。音频应可独立返修，不因单句变化重生全片配音。

## 合成数据

逐帧合成脚本只接收 [镜头时间轴格式](../../stopmotion-animate/references/timeline-format.md)。它与镜头卡、资产索引通过真实 ID 和版本相连。音频／剪辑可另存时间轴，但 cue 用整数帧与确定 fps 对齐。

基础脚本不渲染复杂蒙版、相机或音频。这些效果需转成预处理图层或用实际可用的合成工具完成。不得在 JSON 中写未实现字段后声称已应用。

## 变更传播

按 depends_on 找出受影响产物并标 stale，修复和复查后再改状态。知识事实改变时，不能只更新旁白而保留错误示意；资产轮廓改变时回查遮挡、接触与姿态锚点。完整影片重新导出不等于所有素材必须重生。
