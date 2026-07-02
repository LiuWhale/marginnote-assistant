# Codex Companion 产品手册

适用版本：`0.4.41`
更新时间：2026-06-27

Codex Companion 是一个运行在 MarginNote 4 里的通用 Codex 面板。它不是只服务论文的插件：论文精读、课程资料、书籍章节、项目文档、会议材料都可以作为使用对象。它的目标是在不离开 MarginNote 4 的情况下完成对话、解释、制卡、脑图、目标任务、原文定位、可见高亮和导出带标注 PDF 副本。

当前 0.4.x 是可通过 GitHub Releases 安装的公开预览版，不是最终 v1.0。基础问答、草稿制卡、草稿脑图、目标任务、队列、文件上传、PDF 缓存、标注 PDF 副本导出、运行态诊断和双语 README 已经具备；可靠的 MarginNote 原生可见高亮、签名安装包、公证安装包和跨机器验收仍在补证据。

更远的终极目标不是“聊天框加几个按钮”，而是 **MarginNote Knowledge Agent OS**。当前 0.4.x 的聊天页、回答按钮、设置、日志和第一阶段工具/专家工作台都只是过渡壳层；v1.x 才是对标 MarginNote 自带 AI 的 Study Copilot，v2.x 是能原地编辑真实 `noteId` 的 Native Knowledge Editor，v3.x 才是 Notebook Knowledge OS。当前版本默认打开干净的对话页；`工具` 只在需要精读资料、生成脑图、制卡或检查写入时打开；对象、workflow、证据、验证和回滚细节默认收进专家模式。终局需要 Live MN Object Kernel、Source Registry、Operation Compiler、Transactional Native Editor、Workflow Runtime、Skill Runtime 和 Verification Agent 七个系统内核，而不只是更多按钮。

## 这份手册怎么读

如果你只是想先用起来，直接看第 2、3、6、9、10 和 22 节。  
如果你只想了解工具中心和专家模式，看单独手册：[工具中心与专家模式使用手册](AGENT_WORKSPACE_MANUAL.md)。
如果你想判断它能不能发给别人用，重点看第 17、20、21 节。  
如果你在调试“连接正常但动作失败”“按钮点了没反应”“没有高亮”，先看第 19 节。

本文把“已经可用的功能”和“仍在预览版验证的能力”分开写。手册里写“仍在验证”的地方，不应当当作最终 v1.0 发布承诺。

## 产品承诺

Codex Companion 的设计目标是让 MarginNote 4 里的资料处理变成一个连续工作流：

- 不离开 MN4 就能问问题、解释选区、生成卡片和脑图。
- 默认保持原始 PDF 清洁，不覆盖、不直接改原文。
- 所有写入动作先生成草稿，由用户确认后再写入 MN4。
- 目标任务是一次性长任务，不会污染普通聊天。
- 自定义按钮是用户自己的 prompt 入口，不绑定某一篇论文。
- 队列应自动续跑，用户不需要每一步都点确认。
- 错误要显示具体原因和下一步，而不是只显示“未知网络错误”。

## 主要界面地图

| 位置 | 作用 | 典型使用 |
| --- | --- | --- |
| 对话 | 默认首屏，完整显示聊天历史、输入框、发送按钮和 PDF 缓存状态 | 直接提问、解释选区、连续追问，像 MarginNote 自带 AI 一样使用 |
| 工具 | 可选任务中心，默认只显示当前状态、下一步建议和四个大任务按钮 | 解读当前资料、生成/整理脑图、生成复习卡、检查写入/回滚 |
| 专家模式 | 工具页里的可展开诊断区，围绕 `MNObject`、脑图目标、事务、知识索引和 workflow 运行 | 查看对象来源、风险、图谱、账本、验证中心、脑图 Diff、工作流状态和技能状态 |
| Notebook Workspace | 专家模式里的总览，聚合当前焦点对象、资料来源、PDF 缓存、上传文件、文件搜索根、对象数量、脑图树缓存、复习队列、workflow run、Operation Ledger 计数、Study Program 和 Notebook Runbook | 先看 `Source Registry` 确认当前资料是否可读，再看 `Study Program` 的覆盖率、缺口和推荐 workflow；也可以点 `自动准备` 跑安全预检并留下 preflight 账本证据，或点 `继续下一步` 逐步核对来源、扫描 MN 对象、读取当前脑图树、检查卡片覆盖、生成操作计划、检查 workflow 和账本证据 |
| 按钮页 | 管理预设模板和自定义按钮 | 先填入或添加模板，再决定哪些常用 prompt 放到主界面 |
| 设置页 | 后端、模型、权限、代理、诊断 | 配置 Codex CLI/OpenAI，检查权限，刷新 MN 能力 |
| 文件页 | 上传补充材料或登记本地路径 | 给当前资料补充笔记、要求、背景或问题清单 |
| 历史页 | 当前 notebook/book 的历史对话 | 回看或清空当前资料的会话 |
| 状态栏 | 队列/继续/停止、队列数量、运行状态 | 判断任务是否真的在执行、是否卡住 |

## 功能速查

| 你想做什么 | 推荐入口 | 结果 |
| --- | --- | --- |
| 问当前资料一个问题 | 对话页输入框 + 发送 | 一条模型回复 |
| 解释 PDF 选区 | 选中文本后点解释选中 | 针对选区的解释 |
| 生成复习卡片 | 生成卡片按钮或自定义按钮 | 可编辑卡片草稿，确认后写入 MN4 |
| 新建脑图 | 脑图按钮或自定义按钮 | 可编辑脑图草稿，确认后写入 MN4 |
| 补到当前脑图 | 先选中目标 MN 节点，再点当前脑图区的补到当前 | 挂到选中节点下；无选中节点会阻断 |
| 做完整精读 | 目标按钮或完整精读按钮 | 长任务、草稿、卡片、脑图和后续引导 |
| 高亮原文 | 点原文工具里的高亮，必要时回到 PDF 重新选中文字 | 尝试 MN4 原生高亮；0.4.x 仍需完整可见证据 |
| 采集高亮证据 | 设置页高亮采证 | 进入等待选区状态，并显示原生高亮/选区菜单是否通过 |
| 导出带标注 PDF | 缓存 PDF 后点原文工具里的导出 | OneDrive exports 里的副本，不覆盖原文 |
| 检查当前文档按钮是否真的可用 | 工具页 `检查写入/回滚`，或专家模式 Verification Center 的当前文档验收 | 当前 PDF 的按钮/工作流 PASS/BLOCK |
| 判断能不能发给别人 | 设置页发布验收 | release gate、阻塞项和下一步 |
| 诊断为什么失败 | 主工作台 Verification Center 的当前文档验收/安全采证，或设置页检查权限 | 明确的错误原因和下一步 |

## 1. 产品组成

Codex Companion 由两部分组成：

- MarginNote 4 扩展：显示插件面板，读取当前选区和当前节点，用 MN4 原生能力创建卡片、脑图、缓存 PDF 和尝试原生高亮。
- 本地 Companion 服务：监听 `http://127.0.0.1:48761`，负责 AI 请求、队列、草稿、历史、文件、导出 PDF 副本、诊断日志和发布验收。0.4.25 起诊断日志逻辑拆到独立 `diagnostic_log.py` 模块，但面板和 API 行为不变。

普通用户主要使用 MarginNote 4 里的面板，不需要知道 `topicid`、`bookmd5`、数据库路径或命令行参数。

## 2. 安装

从发布包解压后，优先双击包根目录的：

```text
Install Codex Companion.command
```

也可以在包根目录运行：

```bash
./install.sh
```

GitHub Release 也提供 `.mnaddon` 文件，这是 MarginNote 原生插件包格式。它只安装或更新 MN4 插件本体，不会安装本地 Companion 服务；如果只导入 `.mnaddon`，面板能打开但可能提示 Companion 未运行。普通用户仍建议使用完整 zip 安装包。

安装后重新打开 MarginNote 4，打开一本 notebook 或资料，在 MN4 中打开 Codex Companion 面板。

默认安装位置：

```text
~/.codex/marginnote-assistant
~/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant
~/Library/LaunchAgents/com.codex.paper-companion.plist
```

卸载时双击：

```text
Uninstall Codex Companion.command
```

或运行：

```bash
./uninstall.sh
```

## 3. 首次启动检查

打开面板后先看顶部状态和底部状态栏：

- `连接`：表示 Web 面板能访问本地 Companion 服务。
- `AI 后端`：显示当前使用 `auto`、`codex_cli`、`openai_api` 还是 `local`。
- `Codex CLI`：显示本机是否找到 Codex CLI；这只代表可以尝试该后端，不等于已经完成真实模型生成。
- `OpenAI`：显示是否配置 OpenAI API Key。
- `运行状态`：显示当前或最近一次动作的阶段、详情和耗时。
- `队列`：显示待执行任务数量。

如果状态显示连接正常，但动作失败，先进入设置页点：

- `检查权限`
- `刷新MN能力`
- `运行态采证`
- `高亮采证`
- `本文档验收`
- `发布验收`

这些按钮会把问题收敛成具体原因，而不是只显示“未知网络错误”。

## 4. 面板结构

WebView 顶部提供 `对话 / 工具` 双模式切换。默认进入 `对话`：完整聊天历史、输入框、发送按钮和 PDF 缓存状态会铺满可用区域，适合像 MarginNote 自带 AI 一样解释当前选区或连续追问。切到 `工具` 后，插件默认显示一个简化任务中心：`当前状态` 显示材料、脑图和写入状态；`下一步建议` 给出选择 PDF、刷新目标脑图或检查写入等优先动作；`你想做什么` 提供 `解读当前资料`、`生成/整理脑图`、`生成复习卡`、`检查写入/回滚` 四个大按钮。生成类按钮只把可编辑 prompt 放进对话输入框，不会因为误触就直接启动长任务。

工具页底部保留 `专家模式`。展开后才显示 `Workspace Navigator`、`Notebook Workspace`、对象、操作、知识和工作流工作区；底部仍保留输入框和发送按钮，但默认收起对话历史和工作台详情，避免小窗口被诊断模块挤满。`Workspace Navigator` 主要使用下拉菜单，可直接跳到 `Knowledge Console`、`Mindmap Studio`、`Card Factory`、`Operation Ledger`、`Knowledge Graph`、`Workflow Builder` 和 `Skill Center`，这些入口会选中对应工作区并滚动到目标模块。

- `Notebook Workspace`：这是高级工作台里的可选总览，不是默认对话首屏。上半部分显示当前焦点、对象数量、脑图基线、复习队列、workflow 和账本计数。`Source Registry` 会列出当前 MN 文档、显式 PDF、PDF 缓存、上传文件和文件搜索根，并标出哪些来源可读、哪些还需要缓存或权限；如果插件看不到全文，这里会先暴露原因，不再让你等模型回复后才发现“找不到 PDF”。来源区底部有四个直接动作：`缓存当前 PDF` 会请求 MN4 插件读取并上传当前 PDF，`选择 PDF 文件` 用本机文件选择器缓存一个副本，`管理文件路径` 打开设置页的文件路径管理，`刷新上下文` 重新请求当前选区、节点和文档信息。随后 `Study Program` 会给出 zero-message 学习计划：覆盖率分数、资料来源/对象/脑图/复习卡/workflow/账本缺口，以及 `文档精读工作流`、`当前脑图重组工作流`、`选区制卡工作流` 等推荐入口。你不需要先输入一句 prompt 才知道当前材料下一步该做什么；点击推荐 workflow 后仍进入已有 workflow runtime，写入步骤继续受确认点、dry-run 和账本约束。下方的 `Notebook Runbook` 会把当前 notebook 的下一步排成检查清单。Runbook 现在包含确认上下文、核对来源清单、扫描 MN 对象、读取脑图基线、检查卡片覆盖、生成操作计划、检查工作流、核对操作证据八步，每一步都有 `通过 / 需操作 / 阻断 / 等待` 状态、证据行和动作按钮。顶部的 `继续下一步` 会自动执行第一个真正可处理的缺口；`自动准备` 会把安全预检动作组成 `autoPlan` 顺序执行，例如先补来源、请求 MN4 原生对象扫描、补脑图基线和操作计划。它不会直接写入 MarginNote，也不会自动生成卡片；写入仍必须走 Diff、确认和账本。同时每次自动准备都会先记录 `running`，完成或失败后记录 `completed/failed`，并作为 `notebook_runbook_preflight` 出现在 Operation Ledger。Runbook 区会常驻显示最近一次自动准备状态。它的作用是让你先看到“这个 notebook 现在缺什么”，再由工作台带你进入来源、对象、脑图、卡片、工作流或账本，而不是回到聊天消息里找按钮。
- `Object Intake`：这是 Notebook Workspace 里和当前插件拉开差异的对象路由层。它会把当前文档、选区或脑图节点显示为输入对象，然后给出 `读材料`、`看 MN 对象`、`整理脑图`、`做复习卡`、`跑长任务`、`用技能包`、`验证/回滚` 七条路线。每条路线都有状态、证据和动作按钮：缺 PDF 时先进入 Source Registry；缺原生对象扫描时先扫描 MN；已有脑图基线时直接进 Mindmap Studio；制卡进入 Card Factory；长任务进入 Workflow Builder；技能包进入 Skill Center；已有账本证据时进 Verification Center。它的目的不是增加按钮，而是让你不用先问一句“我能做什么”，工作台已经围绕当前对象给出下一步。
- `Object Task Composer`：这是 Object Intake 后面的任务草案层。它不会直接写入 MarginNote，而是把当前对象的路线整理成材料读取预检、对象清单预检、脑图操作草案、卡片学习草案、长任务草案、技能选择草案和验证回滚草案。每个草案都会显示证据、预期输出和写入策略；带 `编译计划` 的草案会把对象和 prompt 送进 Operation Compiler，先生成可审计 plan。脑图、卡片和长任务草案还会显示 workflow 候选和 `启动 workflow` 按钮；启动后走现有 Workflow Runtime，生成类步骤可以入队，写入步骤仍停在确认点，后续才进入 Diff、接受/拒绝和账本验证。
- `Workflow Builder Board`：这是工作流区的第一阶段可视化编排板。它会把任务候选、运行中 workflow、等待确认的写入步骤和已完成/可审计证据分成四列：`draft_candidates`、运行中、`waiting_confirmation`、证据。你可以从候选卡片启动 workflow，也可以从已有 run 卡片打开 Run Inspector。它不是完整 v3 拖拽式 Workflow Builder，但已经把“当前有哪些长任务、哪些卡在确认点、哪些有证据可查”从聊天消息和 pending 计数里抽出来。
- `对象`：显示当前 MarginNote 焦点，包括 PDF 选区、卡片、脑图节点、当前文档或 notebook；同时列出 notebook/document、上下文范围、选区/节点/文档证据，并给出解释对象、生成脑图树、找相关知识等对象级动作。
- 对象区会显示一个 `MNObject` 引用。它是当前选区、节点、文档或脑图的稳定对象描述，包含 objectId、来源页码/quote/path 和可用动作数量；后续历史、写入计划、事务和日志都会引用这个对象。
- Notebook Workspace 首屏有 `Knowledge Console Matrix`。它不需要你先发 prompt，会直接把来源清单、MN 原生对象、脑图基线、卡片覆盖、workflow runtime、Operation Ledger 和验证证据列成状态矩阵。每一项会显示 `通过`、`需操作`、`阻断` 或 `等证据`，并在有安全动作时给出按钮；缺少原生扫描、脑图基线、复习卡、workflow、账本或 Verification Center 证据时不会显示成已完成。`来源清单` 轴在已有可读材料时会打开 Source Registry；缺材料时才显示缓存当前 PDF、选择文件或管理路径。`MN 对象` 轴在没有原生扫描证据时会请求扫描 MN 对象；扫描证据存在后会直接打开 Object Browser，而不是重复扫描。`脑图基线` 轴在没有缓存时会请求读取当前脑图树；已有脑图树缓存后会直接打开 Mindmap Studio，而不是重复发送读取命令。`卡片覆盖` 轴会打开 Card Factory 复习队列和质量状态；`Workflow` 轴在还没有 run 时会读取模板和运行列表，已有 run 后会直接打开 Workflow Builder。点击验证证据轴会切到操作区的 Verification Center，并刷新当前对象的 `PASS / FAIL / UNKNOWN` 报告和推荐修复动作。
- 对象区有 `风险` 面板，来自 `agent_plan` 的 `codex.mn.riskRegister.v1`。它会把权限、上下文范围、目标脑图、dry-run 和确认点列成单独风险项，标出阻断、提醒和通过状态；这样你在执行前能先看到“当前对象能不能写、是否缺目标脑图、是否还没 dry-run、是否需要接受/拒绝确认”。
- 对象区有 `Object Browser` 面板，会把当前焦点对象、Object Graph 节点、对象活动、Operation Ledger 条目和第一阶段 `MNObject Registry` 条目合成一个可浏览对象列表。它用于快速看“围绕这个 MNObject 现在有哪些对象可以继续操作”，每一行右侧按钮会刷新图谱、查看活动、打开账本证据或进入对应节点动作。面板里的 `类型` 下拉、`Kind` 输入和 `关键词` 搜索会一起传给后端 `object_browser`，可用来只看 Registry 对象、`mindmap_node`、活动、账本或标题/ID/sourceRef 命中的对象。当前 registry 会记录插件已经见过的对象，也会在读取当前脑图树后把缓存里的 MN 原生节点登记为 `mnobj:note:<noteId>`；对象区的 `扫描 MN` 按钮对应 `objectRegistryScanButton`，会请求 `request_mn_object_registry_scan`，让 MN4 原生队列执行 `scan_mn_objects`，并把 `mnObjectRegistryScanFinished` 返回的对象保存成 `native_object_scan` 证据。扫描对象会进入 Object Graph，显示成 `mn_note` 节点，并按 sourceRef.parentNoteId/nodePath 形成 `native_object_scan 父子边`；点击扫描对象会打开该对象图谱，点击扫描对象会打开该对象活动和账本，而不是只刷新当前焦点对象；但它还不是完整 notebook 全库浏览器。
- 对象区有 `Object Graph` 面板，会按当前 objectId 把相关历史对话、workflow run、AI 编辑事务、外部自动化请求、诊断证据、已索引的知识实体、最近一次 MN 原生脑图树缓存和用户手工维护关系连成节点。图谱里的 `知识` 节点来自 Knowledge Index，可能是卡片、脑图节点或摘录，并保留 noteId、页码、quote 和支持/包含等关系；图谱里的 `MN节点` 来自当前脑图树缓存，保留 noteId、层级、path 和父子 `contains` 关系；图谱里的手工关系来自本地 `manual_relation`，可通过对象区的“添加关系”把当前 `MNObject` 连到另一个对象 ID。保存或删除手工关系会形成 `object_graph_manual_relation` 账本事件，并保留 `manualRelation` 证据。切换文档、选区或节点后，图谱会按新对象重新读取；点图谱节点可以进入历史对话、workflow、事务、Operation Ledger 证据详情、知识检索、请求 MarginNote 读取某个 MN 节点子树，或删除手工关系。
- 对象区还有 `对象活动` 面板，会按当前 objectId 汇总最近历史对话、workflow run、AI 编辑事务、手工对象关系事件和诊断日志。它更像时间线；图谱用于看关系，活动用于看最近发生了什么。活动条目右侧的按钮可以直接打开历史对话、查看 workflow、查看 AI 编辑事务、打开手工关系账本证据，或把日志详情展开到对话区。
- 对象区还提供 `Operation Ledger` 面板。它不是普通日志，而是按当前 objectId 聚合 workflow run、AI 编辑事务、外部自动化请求和手工对象关系事件；`类型`、`状态` 和 `关键词` 控件会一起传给 `operation_ledger_list`，可用来只看工作流、事务、外部请求、手工关系，或只看 `saved`、`deleted`、`failed`、`pass` 等状态。每条账本项都有 `ledgerId`，点开后会在对象区打开证据详情面板，查看来源 ID、状态、对象、摘要、operation plan、dry-run/apply path、原生命令、原生事件线、原生执行、回滚/残留、workflow 确认/阻断状态、external callback evidence 和手工关系证据，不需要回到聊天消息里找审计信息。现在账本详情还会带 `codex.mn.verificationReport.v1`：`PASS` 表示当前证据证明通过，`FAIL` 表示发现缺失或失败，`UNKNOWN` 表示缺少足够原生 probe，不能把日志成功当成真实证明。当前是第一阶段可筛选证据账本，后续会继续把更多 MN 原生存在性检测和逐节点 verify 并入同一账本。
- `对话`：保留聊天历史、输入框和发送按钮。Enter 和点击发送都可提交；如果当前已有任务在执行，新请求会自动排队。
- `操作`：集中显示目标脑图、当前脑图树缓存、Operation Compiler、Verification Center、Mindmap Studio、最新脑图 Diff 编辑台、Agent 操作计划、下一步动作、执行验证和事务中心。Operation Compiler 会把当前意图先编译成 `operationPlan` 和 `verificationPlan`，显示计划步骤、写入数量、验证状态，以及 schema、上下文、权限、native capability dry-run、确认点和回滚检查；出现阻断时，这里会先告诉你为什么不能把回答当成真实 MN 编辑，并把写入链路或确认类下一步按钮变灰，只保留只读检索等安全动作。阻断面板还会显示第一阶段修复动作，例如刷新 MN 能力、打开设置或缓存当前 PDF。Verification Center 会按当前 `MNObject` 读取 `verification_report_list`，汇总 Operation Ledger、Source Registry 和 Skill Runtime 的 `PASS`、`FAIL`、`UNKNOWN` 报告，并把非 `PASS` 报告中的可执行动作汇总成 `verificationRepairPlan`，在面板中显示 `执行推荐修复` 主按钮和详细动作列表；没有安全推荐动作时主按钮会禁用。看到 `UNKNOWN` 表示缺少足够原生 probe，不代表已经失败，也不能当成真实通过。如果事务报告因为 `native_probe_missing` 处于 `UNKNOWN`，可点 `执行推荐修复` 或报告里的 `检查真实对象`，它会把 `request_mn_object_existence_probe` 放进 MN4 原生队列，让插件按 noteId 检查真实对象是否存在；MN4 回写 probe 结果后，该报告会重新计算，真实对象存在则变为 `PASS`，缺失则变为 `FAIL`。Mindmap Studio 不是回答下方按钮的别名，它是第一阶段脑图对象操作台：点击 `读取现有脑图` 可以刷新真实脑图树，点击 `预览 Diff` 会按当前回答或输入生成变更预览，点击 `应用所选` 会应用当前选中的 Diff，点击 `验证事务` 会刷新最近事务证据，点击 `回滚事务` 会请求 MN4 删除本次事务新增节点并返回残留结果。生成脑图后，即使聊天滚动到别处，最近一次 Diff 的新增/更新/合并/移动/建议删除统计仍会留在这里；接受或拒绝 AI 编辑后，最近事务的回滚状态、事务对象、创建 noteId 和残留 noteId 也会留在这里。局部脑图 Diff apply 也会进入事务中心，显示本次 transactionId、created/applied noteId、失败数和逐操作验证摘要；生成成功后先等待确认，你可以直接点 `保留`，也可以点 `回滚` 删除本次新增节点，或点 `验证/证据` 查看事务报告。如果 Diff 里包含删除建议，普通接受不会直接删除旧卡片；事务中心会另外显示 `删除 / 忽略`，需要你二次确认后才删除目标 noteId。
- `知识`：显示 Knowledge Graph 状态，包括当前索引范围、实体类型统计、关系统计和显式检索入口。你可以直接输入关键词检索当前授权范围内的索引命中，结果会显示实体、摘要、来源和页码线索；它不会默认扫描或注入全库。
- `工作流`：显示 Workflow Runtime、Workflow Builder Board、External Automation Gateway 和 Skill Runtime / Skill Marketplace 的当前状态。这里会列出可用工作流模板、最近 workflow run、本地技能包，以及 `codex.mn.workflowBuilderBoard.v1` 四列板：任务候选、运行中、等待确认和证据。点击候选卡片可按当前对象启动工作流，生成类步骤进入队列，写入类步骤仍需要确认；点击 run 卡片或最近 run 右侧的 `查看` 会打开 Run Inspector，显示每一步的状态、queueId、确认要求、提醒/阻断状态和下一步动作；可恢复的失败/阻断 direct 或 queueable 步骤会显示 `重试`，重试后会重新入队并刷新检查器。写入/确认步骤不会显示重试按钮，仍然必须走接受或拒绝。技能包不再等同于自定义 prompt：写入或删除技能必须通过 manifest 校验，声明 `requiresConfirmation`、`dryRun`、`rollback` 和 `acceptance`；无效技能会被禁用，有效技能可先生成 dry-run-first 操作计划，再记录 `codex.mn.skillRun.v1`。外部脚本、快捷指令或其他本地 Agent 可以 POST 到 `/external/workflow/start` 创建 workflow run；Companion 会记录 requestId、caller、权限、对象引用、callback 和执行结果，仍然沿用同一套权限与确认点。外部系统也可以 POST 到 `/external/callback/success` 或 `/external/callback/error`，把执行结果写回同一个 request ledger。
- `设置`：通过右上角设置进入，配置 AI 后端、模型、速度、权限、代理、OpenAI Key、文件路径、更新、日志和诊断。
- `历史`：通过右上角历史进入，查看或恢复当前 notebook/book 的历史对话。

知识索引不是默认全库扫描。只有你明确问“相关、已有、历史、跨文档、notebook”等问题，或显式启用知识索引时，插件才会把本地索引片段加入模型上下文。索引现在可以保存结构化 MarginNote 实体，包括卡片、脑图节点和摘录的 `noteId`、页码、quote 和关系字段。

卡片草稿会附带质量审计。插件会在写入前标出卡片类型覆盖、正文过长、缺少来源线索和重复标题等风险；这些提示用于人工确认或后续重写，不会自动篡改模型生成内容。

面板可以拖动标题栏移动，可以拖右下角缩放，也可以用标题栏的 `-` / `+` 调整大小。面板会记住用户调整过的位置和尺寸。

## 5. AI 后端和模型

设置页支持四种 AI 后端：

- `auto`：默认模式。优先尝试本机 Codex CLI，再尝试 OpenAI API。
- `codex_cli`：强制使用本机 Codex CLI。适合你已经能在本机使用 Codex CLI 的情况。
- `openai_api`：强制使用 OpenAI API Key。
- `local`：只做本地工具和诊断，不生成问答、卡片、脑图或完整精读内容。

当前默认模型配置是：

```text
model = gpt-5.5
speed = fast
```

在 Codex CLI 后端下，`fast` 档会启用 fast profile，同时使用中等推理深度，目标是兼顾速度和基本推理质量。`balanced` 和 `deep` 会提高超时和输出预算，适合长资料、完整精读和复杂重组。

如果没有可用 Codex CLI，也没有 OpenAI Key，生成型动作会明确失败，不会用本地模板冒充 AI 输出。此时仍可使用权限检查、运行态采证、PDF 缓存、导出标注副本等本地工具。

OpenAI Key 可在设置页填写，也可点 `清除Key` 删除本地保存的 key。Key 写入本地 `.env`，不会回显到面板；清除时只发送清除指令，不会把输入框里的临时 key 再发给后端。

设置页的 readiness 卡片现在使用“真实 AI 后端已发现”这类措辞：它表示发现了 Codex CLI 或 OpenAI Key，但真实生成仍取决于 Codex 登录、账号/模型权限、代理和网络。不要把“已发现 CLI”理解成“已经成功调用模型”。

设置页的 `试连AI` 是快速就绪探测：它检查当前所选后端、Codex CLI 路径/登录态、OpenAI Key 是否存在和代理 scheme。它不会发送测试 prompt，也不会产生模型 token 消耗。

## 6. 普通对话

在主界面输入问题后点击 `发送`。发送后输入框会自动清空。

普通对话会使用当前可见上下文，包括：

- PDF 选中文本
- 当前选中 MN 节点标题
- 当前选中 MN 节点正文
- 当前 notebook/book 信息
- 用户上传或登记的补充文件摘要

普通对话不会自动继承旧目标，也不会默认假设你要答辩。只有当你明确写“答辩”“讲稿”“汇报”“defense”“presentation”等意图时，输出才会偏向讲稿或答辩口径。

## 7. 目标任务

目标是一次性的长任务入口，不是设置项，也不是永久身份。你可以把它理解成“接下来连续执行的一件大事”。

推荐用法：

1. 在目标输入里写清楚任务，例如“精读当前 PDF，生成结构化脑图、短卡片和讲解稿”。
2. 点击 `设目标` 打开目标输入，再点 `执行目标` 启动。
3. 插件会把目标任务拆成后续步骤，并自动把 pending 任务接在当前任务后继续执行。
4. 运行状态会显示本次目标进度；目标完成后不会保存成长期当前目标。

目标上下文只进入 `goal_run` 和由目标拆分出的队列任务。普通聊天、普通制卡和普通脑图不会自动携带旧目标，避免你随便问一句时又被带回旧的答辩任务。

工作流运行会记录当前 `MNObject`。自动入队的解释、制卡、脑图等步骤会携带同一个 objectId，后续状态、历史、日志、事务和回滚可以按“这次到底处理哪个 MN 对象”追踪，而不是只靠 prompt 文本猜。草稿写入和 AI 编辑事务也会继续携带这个对象引用；事务中心会显示本次事务对象。

## 8. 自定义按钮

进入 `按钮` 页可以创建自己的按钮。预设区里的模板不会自动挤到主界面；你可以先点 `填入` 把模板放进输入框，确认后再点发送，也可以点 `添加` 变成自定义按钮后再编辑。每个自定义按钮可以配置：

- 按钮名称
- 动作类型
- prompt 内容
- 是否显示在主界面，也可以在按钮列表里直接置顶或移出

主界面最多显示 4 个常用自定义按钮。更少的主界面按钮更适合日常使用，更多按钮保留在按钮页里；列表里的 `置顶` / `移出` 可以直接调整，不必先进编辑表单。

点击预设或自定义按钮不会立刻执行模型请求，而是把 prompt 和动作填入主界面输入框，并显示待发送状态。你可以继续修改输入框，最后统一点 `发送` 执行；如果发送时已有任务正在运行，新任务会自动进入 pending 队列。

常见动作类型：

- 问答
- 解释选中
- 生成卡片
- 新建脑图
- 完整精读
- 补脑图
- 节点重组
- 高亮下一选区

高亮和导出已经在对话页常驻的原文区。自定义按钮仍可创建同类动作，但不建议重复占用主界面置顶区。

运行中点击主界面的解释、制卡、脑图、精读、补脑图、重组、高亮、导出等动作按钮时，插件不会把所有按钮永久置灰。新任务会自动进入 pending 队列，上一个任务完成后自动继续；消息后会给出 `停止当前并直接执行` 和 `查看队列状态`。

选择等待后，任务会进入队列，并在上一个任务结束后自动继续执行。

## 9. 生成卡片

卡片生成流程是“先草稿，后写入”：

1. 选中文本或选中一个 MN 节点。
2. 点击生成卡片，或用自定义按钮填入制卡 prompt 后点发送。
3. Companion 调用真实 AI 生成短卡片草稿。
4. 面板显示草稿框，你可以直接修改。
5. 点击 `写入 MN` 后，插件才调用 MarginNote 原生 API 创建卡片。

卡片会尽量保持短而密。模型输出有标题时会按标题拆卡；没有标题的一大段内容会按句子拆成多张卡。单张卡正文上限约 900 字符，避免一个卡片长到难以复习。

当前制卡已经接入 Card Factory 第一阶段。生成结果会带 `codex.mn.cardFactory.v1` 卡片工厂摘要；每张卡会带 `cardType`、来源 `source`、`learningGoal` 和 `reviewPrompt`。确认写入前，AI 编辑操作面板会显示卡型分布、缺来源、长卡和重复标题风险。这个摘要用于判断卡片是否适合复习，不会自动替你改写模型内容。

AI 编辑操作面板里的 `加入复习队列` 会把本次草稿卡登记到对象级复习队列。重复点击不会重复加入同一批卡；知识区会显示当前对象作用域下的复习卡总数、到期数、新卡数和最近卡片。这个队列目前是 Card Factory 的第一层复习闭环，后续还会继续扩展跨对象去重、覆盖率和替换/合并。

你也可以在草稿框里用 `## 标题` 分隔多张卡片。

## 10. 新建脑图和补脑图

脑图生成不再只是“给你一段 Markdown 草稿”。在支持 Diff 的路径里，插件会把模型生成的树和当前目标脑图进行对比，再把准备写入的变化展示出来：

1. 选择资料范围：当前选区、当前节点、当前 PDF 或目标任务。
2. 如果要新建结构，点击脑图；如果要补到已有脑图，先选中目标节点，再点击补脑图。
3. 面板显示 `脑图 Diff 预览`，包括新增、更新、合并、移动和建议删除统计。
4. 每个拟写入节点前都有勾选框，并带有标题和正文编辑框。取消勾选后，该节点和子树会被标记为跳过，保留/跳过计数会立即更新；修改标题或正文后，接受时会把改动写回本次草稿和局部执行计划。
5. 点击 `接受` 后，插件会按当前 MN 原生能力选择局部执行或草稿写入；点击 `拒绝` 会丢弃本次草稿。
6. 操作区会保留最近一次脑图 Diff 和脑图验证摘要，方便你滚动聊天后仍能看到 AI 准备改什么、写入是否通过。

当前仍保留 Markdown 草稿作为降级路径。`##` 通常表示一个主要分支，下面的条目会作为子节点或节点正文。终极目标是让主要脑图流程都走 Diff 编辑台，而不是让用户手动读一大段 Markdown。

如果你说“补到当前脑图”“合并到现在的脑图”“挂到这个节点下”，必须先在 MarginNote 里选中目标脑图节点。若没有选中节点，插件会直接停止并提示你先选中节点，不会偷偷新建一棵脑图，也不会把脑图退化成一段文字。

## 11. 完整精读

完整精读适合处理一篇论文、一章书或一份长资料。它通常会生成：

- 结构化摘要
- 关键概念
- 方法流程
- 证据边界
- 卡片草稿
- 脑图草稿
- 可能的后续引导

完整精读不再使用内置内容模板。没有真实 AI 后端时会失败；配置 Codex CLI 或 OpenAI 后才会生成内容。

如果你要答辩讲稿，需要在 prompt 里明确说明。否则完整精读默认按理解、复习和结构化笔记来组织。

## 12. 高亮与原文清洁

产品原则是：默认保持原始 PDF 清洁。

当前有两条路线：

- MarginNote 原生高亮：主界面按钮是 `高亮下一选区`，点击后会让 MN4 插件进入一次性的下一次 PDF 选区自动高亮模式；如果当前已经有有效选区，则立即尝试调用官方 `highlightFromSelection()`。插件连接时会注册 PDF 选区弹出菜单 observer，并尝试在 PDF 选中文本菜单里追加 `Codex 高亮选区`；设置页 `高亮采证` 会启动同一路线，并把当前状态整理成 `waiting_selection`、`verifying`、`failed` 或 `complete`，同时显示原生高亮和 PDF 选区菜单两项是否通过。高亮采证卡片里的 `刷新` 会先请求 MN4 原生侧做一次只读 PDF 选区探针；探针现在同时读取 `selectionText` 和 `imageFromSelection()`，所以文字选区和曲线/区域/图片选区都能被识别。如果显示 `controller 可见，但 selectionText=0 / imageFromSelection=0`，说明插件已经找到当前 PDF controller，但 MarginNote 当前没有暴露可读选区，需要回到 PDF 原文重新选中一小段文字或区域。0.4.x 仍在补可靠可见高亮证据。
- 标注 PDF 副本导出：用户主动触发 `导出标注 PDF` 后，Companion 用 PyMuPDF 生成一个带 highlight annotation 的 PDF 副本，输出到 OneDrive，不覆盖原始 PDF。

发布采证时，打开目标 PDF 后双击发布包里的 `Collect Native Highlight Evidence.command`。推荐先运行命令，再在 90 秒内回到 PDF 重新选中一小段文字；如果当前已经有有效选区也会立即尝试。脚本会先请求打开中的 MN4 插件执行一次 `高亮下一选区`，如果插件进入下一次选区布防状态，会继续等待 posted/failed 结果，并把同 topic/book 的 `ZHIGHLIGHTS` 检查写进桌面 JSON。

主工作台 Verification Center 里的真实 MN4 验收面板会显示总状态、三步清单和 `运行验收流程`。`运行验收流程` 会先调用 `single_document_acceptance_summary` 检查当前文档，再调用 `ui_functional_acceptance_summary` 跑任意文档 WebView gate，最后执行无写入的 MN 能力刷新和高亮采证向导。你也可以单独点 `当前文档验收`、`任意文档 UI 验收` 或 `安全采证`。`当前文档验收` 和 `single_document_acceptance.py` 会自动发现最近的高亮证据；如果仍然 BLOCK，会显示 evidence 路径、attempt 和 problems，便于判断是没有选区、没有 posted 事件，还是数据库里没有同作用域的 `ZHIGHLIGHTS`。

开发和发布前还可以运行 `ui_functional_acceptance.py`，或在设置页点击 `UI 功能验收`。设置页按钮是 `uiFunctionalAcceptanceButton`，会调用 `ui_functional_acceptance_summary`，在面板内把 `uiFunctionalAcceptanceLine` 渲染成 `UI 功能验收：PASS / 11/11 / 阻塞 0`，并在详情里列出每项检查。它不依赖某一篇固定论文，而是用任意文档标题、topic 和 book payload 检查 WebView 控件、按钮覆盖矩阵、Notebook Workspace 内核、Workflow Builder Board、Card Factory 入口、workspace surface action，以及无 notebook scope 时是否禁用原生 MN 扫描/读取脑图按钮。按钮覆盖矩阵对应 `webview_button_coverage`，会枚举每个静态 WebView button；如果新增按钮没有被归入真实点击、交互点击、写入流程、面板控制、表单/破坏性、文件选择、关闭类或隐藏运行态，验收会直接失败。加上 `--browser-render` 时，它会启动本地 headless browser，检查渲染后的高级工作台 DOM 和原生按钮禁用态。加上 `--browser-interaction` 时，它会通过浏览器 DevTools 协议真实点击对话/高级、全部 Workspace Navigator 卡片、全部 Workbench tab、Command Pane、设置页和历史页，确认 UI 状态会切换。加上 `--browser-actions` 时，它会用 stub Companion 注入任意文档 `MNObject` 和 notebook scope，点击主输入 `sendButton`、验证发送后清空、验证 `Enter key` 也会提交、点击 `新对话`、切换上下文范围到全文、刷新上下文 bridge、保存文件路径、检查更新、打开下载页、权限诊断、打开权限设置、缓存当前 PDF、刷新 MN 能力、Agent Plan、MN 对象扫描、读取脑图树、Notebook Workspace、Runbook 继续/自动准备、Object Browser 刷新/筛选、Object Graph、对象关系保存/取消、对象活动、Operation Ledger 刷新/筛选、Verification Center、`verificationRepairPlanRecommendedButton`、知识检索、目标脑图状态、health、AI 后端、日志和历史范围按钮，并确认这些按钮真的发送对应 backend/native action 且没有显示连接失败；同一次浏览器会话还会确认设置页真的显示 `UI 功能验收：PASS`。报告中的 `buttonActionDeltas` 会证明每个按钮各自让对应 action 计数增加，所以 `conversationHistoryObjectButton`、`conversationHistoryAllButton`、`notebook_runbook_preflight_record`、`object_graph`、`object_activity`、`object_graph_relation_save`、`knowledge_index_search` 和 `mindmap_target_status` 这类容易被最终 action 集合掩盖的功能也会被检查。加上 `--browser-write-actions` 时，它还会验证回答下方生成脑图树、草稿保存、AI 编辑接受/拒绝/复习、Mindmap Studio Diff 预览/应用、`mindmapStudioVerifyButton`、`mindmapStudioRollbackButton`、事务验证/证据/probe 和 MN4 原生 bridge 调用。它证明“这个界面对任意文档不是硬编码能打开，并且关键按钮不是空壳”，但不替代需要真实 MN4 运行态和原生高亮证据的 `single_document_acceptance.py`。

如果报告显示 observer 已注册但没有 PDF 选区通知，请重新打开 Codex 面板或重启 MarginNote 4，再回到同一 PDF 重新选中一小段原文；这能区分“插件没收到选区通知”和“收到了通知但菜单安装失败”。

如果点击 `高亮下一选区` 没有效果，优先检查：

- 是否真的在 PDF 页面里选中了文字；若刚点按钮后选区消失，请回到 PDF 重新选一小段文字
- 设置页 `刷新MN能力` 后是否显示原生高亮能力 ready
- 高亮采证的 `刷新` 是否显示 `selectionText=0 / imageFromSelection=0`；如果是，说明当前没有可读 PDF 文字或区域选区，不是模型或 Companion 停止工作
- `运行态采证` 里是否出现高亮失败原因
- 当前资料是否是扫描 PDF 或没有文本层

默认不会直接写 MarginNote SQLite 高亮 blob，也不会修改原始 PDF。

## 13. 导出带标注 PDF 副本

导出标注 PDF 的输出目录是：

```text
~/Library/CloudStorage/OneDrive-个人/Codex Companion/exports
```

导出逻辑：

1. 优先使用 MN4 插件进程上传的当前 PDF 缓存。
2. 如果没有缓存，尝试使用插件 payload 中的 `pdfPath`。
3. 再尝试只读查询 MN4 资料记录。
4. 在副本中写 highlight annotation。
5. 校验原始 PDF hash，确认未修改原文。

如果导出失败且提示权限问题，给 Terminal、Codex、Python 或 Companion 所在运行环境 Full Disk Access 后再试。

## 14. 文件与上下文

文件页可以上传小文本文件，也可以登记本地文件路径。文件摘要会进入模型上下文，适合补充：

- 论文笔记
- 课程讲义
- 老师要求
- 答辩问题清单
- 项目背景
- 你手写的阅读问题

不要把敏感材料随便交给远程 OpenAI API 后端。若只想本地使用，请选择 Codex CLI 或确认自己的 Codex 环境策略。

## 15. 队列、停止和进度

状态栏的队列/停止是一体按钮：

- 空闲时：显示 `队列`；点击只刷新/提示 pending 状态，不会代替输入框发送。发送请始终用输入框右侧的 `发送`。
- 有 pending 任务时：显示 `继续`，点击后直接执行下一个等待任务。
- 运行时：用于请求停止。

停止不是强制杀死已经发出的底层 HTTP 或 CLI 进程，而是在请求返回后阻止继续执行后续生成、写入卡片或写入脑图。长请求可能仍需要等当前模型调用返回。

运行中继续点按钮时，插件会自动把新任务加入 pending 队列。pending 任务会在上一个任务完成后自动继续，不需要再点确认；需要抢占时再点消息里的 `停止当前并直接执行`。

进度不只显示时间。面板会显示当前动作、阶段、详情和耗时；任务运行期间，前端还会定时读取 `/status`，把后端 `run.action`、`run.stage`、`run.detail` 同步到对话进度消息和底部运行状态。

## 16. 历史记录

历史页按当前 notebook/book 保存会话。你可以：

- 查看当前资料的历史问答
- 按当前 `MNObject` 过滤对象相关会话，例如只看某个 PDF 选区、卡片或当前文档对应的历史
- 清空当前资料的历史

历史记录用于连续阅读同一份资料，不用于跨所有文档共享永久记忆。对象级历史会保存 `objectRef`，其中包含 objectId、kind、title 和来源线索；这让后续对象检查器能够回答“这个对象之前解释过什么、写入过什么、失败过什么”。

## 17. 权限模式

设置页支持三档权限：

- `read_only`：只允许问答、解释、诊断、目标、上传和队列/停止。
- `notes`：允许创建 MarginNote 原生卡片、脑图和完整精读写入。适合日常使用。
- `full`：为导出、实验性高风险动作预留。

高风险数据库写入默认仍禁用。即使选择 `full`，也不会默认直接写 SQLite 高亮。

## 18. 推荐工作流

### 理解一段原文

1. 在 PDF 里选中文本。
2. 点击 `解释选中` 或直接输入问题。
3. 需要复习时点击生成卡片。
4. 检查草稿，确认后写入 MN。

### 精读一篇论文或章节

1. 打开目标 PDF 或 notebook。
2. 在目标里写清楚“精读当前资料，生成短卡、脑图和关键问题”。
3. 启动目标任务。
4. 等待 pending 任务自动执行。
5. 在草稿阶段编辑卡片和脑图。
6. 确认写入 MN。

### 补到当前脑图

1. 在 MN4 中先选中目标脑图节点。
2. 输入“把下面内容补到当前脑图，并保持节点短小”。
3. 点击生成脑图，或用自定义按钮填入对应 prompt 后点发送。
4. 若插件提示缺少选中节点，回到 MN4 重新点中节点后再试。

### 做可导出的标注 PDF

1. 在 PDF 中选中文本。
2. 先点 `缓存PDF`，让 MN4 进程上传当前 PDF 缓存。
3. 点 `导出标注 PDF`。
4. 到 OneDrive `Codex Companion/exports` 查看副本。

## 19. 常见问题

### “Codex Companion 未运行”

含义：Web 面板访问不到 `127.0.0.1:48761`。

处理：

```bash
~/.codex/marginnote-assistant/start_companion.sh
```

如果仍失败，运行：

```bash
python3 ~/.codex/marginnote-assistant/doctor.py
```

### “真实 AI 未配置”

含义：当前没有可用 Codex CLI，也没有 OpenAI Key。生成问答、卡片、脑图和完整精读不会用模板代替 AI。

处理：

- 设置页选择 `auto` 或 `codex_cli`，确认 Codex CLI 可用。
- 或设置页填写 OpenAI Key 并选择 `openai_api`。

### Codex CLI 提示 cloud config bundle 超时

如果消息里出现：

```text
Error: timed out waiting for cloud config bundle after 15s
```

含义：插件已经启动了 Codex CLI，但 CLI 自己在 15 秒内没有拿到云端启动配置。这通常是代理链路、网络抖动、Codex 登录状态或账号/模型权限问题，不是当前 PDF、脑图或 MarginNote 上下文问题。

当前 main 分支已对这个错误做了两件事：

- 自动重试一次。
- 重试后仍失败时，把原始错误改成可操作的代理/登录/网络提示。

处理：

1. 重试一次同样的问题。
2. 确认设置页代理地址和本机代理端口一致。
3. 在终端里确认 Codex CLI 已登录并能执行一个最短 prompt。
4. 如果希望 `auto` 模式有备用路线，设置 OpenAI Key。

### 状态显示连接，但请求失败

常见原因：

- Companion 服务刚重启，WebView 持有旧状态。
- MarginNote 面板还没加载最新插件文件。
- LaunchAgent/Python 被 macOS 隐私权限拦截。
- 代理配置错误。
- 后端返回了 400/500，但 UI 只看到连接层失败。

处理顺序：

1. 设置页点 `检查权限`。
2. 设置页点 `试连AI`，确认 AI 后端不是本地诊断模式。
3. 设置页点 `运行态采证`。
4. 设置页点 `本文档验收`，先确认当前 PDF 里的按钮和工作流缺哪一步。
5. 准备发给别人或打包前再点 `发布验收`。
6. 需要时重新打开 Codex 面板。
7. 仍 stale 时，再按发布验收给出的恢复动作确认重启 MarginNote 4。

### 按钮灰了或点了没反应

当前设计不应整体禁用所有按钮。运行中点击按钮应该出现消息级引导。

如果连续点击没反应，可能是 MN4 WebView 焦点或运行态没有刷新。先点空白处再点按钮，随后运行 `运行态采证`。若证据显示 stale runtime，重新打开面板或重启 MN4。

发送按钮本身应只显示两行：`发送` 和 `可排队`。如果看到两行以上的重复 `可排队`，说明 WebView 仍加载了旧 CSS；重新打开插件面板，必要时重新安装或同步最新扩展文件。

### 生成脑图很慢

脑图生成比普通问答慢，因为它要让模型组织层级、拆节点、保留上下文，还要进入草稿和写入流程。长 PDF、完整精读、`deep` 档或网络代理都会增加耗时。

想要更快：

- 先对选区或当前章节生成，而不是整篇。
- 使用 `fast`。
- 让 prompt 明确“节点短小，每层不超过 N 个”。

### 发送按钮跑很久，不知道是否在工作

看状态栏 `运行状态` 和消息里的动态进度。正常情况下，运行中的对话进度会同步 `/status` 中的 `run.action`、`run.stage`、`run.detail`。若它长时间停在同一阶段，点设置页 `运行态采证`，确认后台是否仍在执行、是否卡在模型调用、队列或 MN4 原生动作。

### 让我合并脑图，却只生成文字

正确行为应是：有选中节点时生成可写入脑图草稿；没有选中节点时直接提示先选中节点并停止。

如果只得到普通文字，说明当前动作被当作普通聊天执行了。请使用 `脑图` 或 `补脑图` 按钮；如果在输入框里写“补到当前脑图/合并到现在脑图”，也要先选中目标节点。

### 一个卡片太长

在草稿框里用 `## 标题` 手动拆分，或在 prompt 中写：

```text
每张卡片不超过 300 字，按 ## 分隔，不要把所有内容塞进一张卡。
```

当前后端也会尽量按标题和句子拆卡，并限制单张正文长度。

### 没有高亮

0.4.x 的 MarginNote 原生可见高亮仍在验证。优先点设置页 `高亮采证`，然后回到 PDF 重新选中一小段文字；面板会显示原生高亮和选区菜单是否通过。如果只是想日常高亮，可以直接点原文区 `高亮下一选区`，再回到 PDF 选中文字；如果当前页面已有真实选区，也会立即尝试消费这次选区。也可以直接双击 `Collect Native Highlight Evidence.command` 让采证命令主动请求一次高亮，并在 90 秒内等待你重新选区后的 posted/failed 结果。如果失败，运行 `刷新MN能力` 和 `运行态采证`。需要可导出的结果时，优先使用 `导出标注 PDF` 生成副本。

### 安装包打不开或提示不受信任

当前 GitHub Release 提供完整 zip 安装包和 MN4 原生 `.mnaddon` 插件包；`.pkg` 路线仍缺 Developer ID Installer 签名和 Apple notarization 证据，适合内部维护，不适合作为最终 v1.0 公发安装器。最终对外发布需要签名、公证和跨机器安装证据。

## 20. 隐私和数据位置

本地 Companion 默认只监听：

```text
127.0.0.1:48761
```

主要数据位置：

```text
~/.codex/marginnote-assistant/sessions
~/.codex/marginnote-assistant/uploads
~/.codex/marginnote-assistant/drafts
~/Library/CloudStorage/OneDrive-个人/Codex Companion
```

OpenAI Key 写在：

```text
~/.codex/marginnote-assistant/.env
```

原始 PDF 默认保持清洁。只有用户主动导出标注副本时，才会在 OneDrive exports 目录生成带标注的 PDF 副本。

## 21. 当前预览版限制

截至 2026-07-02，`v0.4.41` 是当前公开预览版发布候选；本轮目标是完成 GitHub Release、双语 README、release zip smoke、`.mnaddon` smoke、install dry-run 和本机 0.4.41 安装替换；MN4 运行态需要重新打开面板或重启 MN4 后才会上报新版 WebView/native 能力事件。当前仍有这些发布阻塞：

- MarginNote 原生可见高亮仍缺活跃 PDF 选区下的完整证据。
- `release_sha256_manifest` 已覆盖 zip、`.mnaddon` 和 `.pkg` 并通过；当前阻塞不再来自 artifact hash manifest。
- 当前 `.pkg` 未签名、未 notarize。
- 还缺第二用户或第二机器的结构化安装验收。
- 还缺同一文档完整按钮/工作流验收 PASS evidence。

这些限制不影响使用 `v0.4.41` zip 或 `.mnaddon` 作为公开预览版继续试用，但影响“发给别人当最终正式产品”的判断。

## 22. 给用户的最短使用路径

如果只想先用起来：

1. 双击 `Install Codex Companion.command`。
2. 重开 MarginNote 4。
3. 打开一份资料和 Codex Companion 面板。
4. 设置页确认 `Codex CLI` 或 `OpenAI` 至少一个可用。
5. 在 PDF 中选一段文字。
6. 点 `解释选中` 或直接输入问题。
7. 点 `生成卡片`，编辑草稿后写入 MN。
8. 需要新结构时点 `脑图`；需要补到现有脑图时先选中目标节点，再点 `补脑图`。
9. 需要标注 PDF 时点 `缓存PDF`，再点原文区的 `导出`。
