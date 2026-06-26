# Codex Companion 发布级产品目标

## 目标

把 Codex 变成一个可在 MarginNote 4 里直接使用的通用工作面板：用户打开资料、论文、笔记或项目材料后，不需要切换到终端，就能在 MN4 侧边面板里对话、运行自定义 prompt、生成原生卡片、生成脑图、建立回链、做可见高亮，并在需要时导出带标注 PDF 副本。论文精读是重点预设场景，但不是产品边界。

本文件定义的是发布级可用产品目标。终极形态另见 `docs/ULTIMATE_PLUGIN_DESIGN.md`，它的边界不是“能聊天、能生成脑图”，也不是当前聊天插件的增强版；终极目标是 **MarginNote Knowledge Agent OS**。终局路线明确采用 **知识编辑工作台 + 自动学习代理**：默认首屏应是 `Notebook Workspace`，显示当前 notebook 的对象、脑图、卡片、知识关系、workflow、复习状态和操作账本；`Chat Mode` 只是快速阅读和意图输入入口，不能成为高阶知识工作的中心。

发布级当前目标和 v3.0 终局必须分开验收：当前 0.4.x 是 Chat Mode + Agent Workspace 雏形，重点是让 MN4 内的 AI 对话、卡片、脑图、目标、历史、设置、缓存、日志、对象面板和事务闭环稳定可用；v3.0 终局则必须以 `Notebook Workspace`、`Knowledge Console`、`Object Browser`、`Mindmap Studio`、`Card Factory`、`Knowledge Graph Studio`、`Workflow Builder`、`Operation Ledger Explorer` 和 `Skill Center` 这些一等产品界面为验收对象。只要高阶工作仍只能靠“聊天后点按钮生成内容”，就只能叫 Agent Workbench 或 Study Copilot，不能叫 Knowledge Agent OS。

## 用户体验原则

- 原文 PDF 保持清洁。默认只创建 MarginNote 原生笔记、脑图和高亮数据；导出带标注 PDF 必须是用户主动触发。
- 普通用户不需要看数据库、不需要写命令、不需要知道 topic id 或 book md5。
- 插件面板必须有清楚状态：Companion 是否运行、当前动作是否成功、写入了多少卡片/节点、高亮是否真的完成。
- 生成内容必须能回到原文位置。卡片和脑图节点要包含 page link 或 native excerpt/link，最终目标是点击节点能跳回论文对应页或选区。
- 视觉验收可以截图，但功能验收不依赖截图。功能应通过插件队列、事件日志和 MN4 数据结果程序化验证。

## v1.0 必须具备

1. 插件 UI
   - MN4 中自动显示或一键打开侧边面板。
   - 面板里有可输入聊天框、固定发送按钮、历史回复区、当前内容上下文状态。
   - 面板窗口必须支持鼠标拖拽缩小/放大，并设置最小宽高，避免控件被压坏。
   - 首屏先提供 `Chat Mode / Agent Workspace` 双模式切换；`Chat Mode` 固定进入对话输入和回答流，`Agent Workspace` 展开对象、操作、知识、工作流工作区，默认入口是对象区的 `Knowledge Console`，不是聊天消息流；`Agent Workspace` 顶部必须有 `Workspace Navigator`，把 `Knowledge Console`、`Mindmap Studio`、`Card Factory`、`Operation Ledger`、`Knowledge Graph`、`Workflow Builder` 和 `Skill Center` 作为一等入口，而不是让用户只理解底层 tab；设置和历史作为独立页面打开，文件路径管理、AI 后端、诊断和低频配置不占用主工作区。
   - 主界面对话区底部必须一直保留输入框和发送按钮；常用自定义按钮只能作为额外快捷入口。
   - 按钮页支持预设模板、自定义 prompt、动作类型选择、是否显示在主界面的开关；预设可以填入输入框或添加成自定义按钮；主界面最多显示 4 个常用自定义按钮。
   - 输入行包括：文本输入框和发送/问 Codex；预设或自定义按钮填入 prompt 后显示 `stagedActionLine`，允许用户先改 prompt，点发送仍按该按钮动作执行；`mainActionStack` 按一次性目标、常用任务、工具区顺序排列；`goalRunPanel` 是独立的一次性目标区，`goalActionStrip` 同时放“设目标”按钮和目标状态；`primaryActionGrid` 是 2x2 主操作，只放解释选中文本、生成卡片、新建脑图、完整精读。
   - `workflowActionPanel` 常驻承载当前脑图工具和原文工具：`mindmapToolPanel` / `mindmapActionGrid` 包括补到当前和重组当前，`sourceToolPanel` / `toolActionGrid` 提供高亮下一选区、导出和状态；其余低频诊断按钮收进设置页，并按 AI 与连接、权限与文件、MN 运行态、验收四组分区；设置页必须区分“高亮采证”、日常“本文档验收”和重型“发布验收”。
   - 按钮点击后必须释放焦点，避免连续点击被焦点态卡住；按钮缺上下文时，按钮短提示必须显示“需选区/需节点/需文档/需能力”等原因。
   - 执行中不能把所有动作按钮置灰；新动作应自动进入 pending 队列，并在对应消息后提供停止当前并直接执行、查看队列状态等引导按钮。
   - 对话页必须显示当前执行进度。
   - 面板必须提供 AI 后端、Codex 权限、模型、速度、HTTP/HTTPS 代理设置，且设置持久化。
   - 面板必须提供一次性目标、上传文件、停止和队列状态；目标必须是主界面按钮级入口，并在运行状态里显示本次目标进度，不能藏在设置页里。
   - 面板必须可查看并清空当前 notebook/book 会话历史。

2. 对话
   - 支持直接输入问题。
   - 支持读取 PDF 选中文本。
   - 支持读取当前选中的 MN 节点标题和正文。
   - 每个 notebook/book 有独立会话历史。
   - 用户可从面板查看或清空当前 notebook/book 的历史记录。

3. 卡片
   - 用 MarginNote 原生 API 创建，不直接写数据库。
   - 卡片包含：原文定位、术语解释、公式拆解、材料作用、证据边界和可追溯原文线索；只有用户明确要求答辩、汇报或讲稿时才追加口述/defense 说法。
   - 对同一篇论文重复生成时要有去重或替换策略，避免无限堆叠。

4. 脑图
   - 支持按论文整体、章节、选中文本生成层级脑图。
   - 节点正文包含原文定位和讲解，不只放标题。
   - 支持把生成脑图挂到当前选中节点下；当用户明确要求补到/合并到当前脑图但没有选中节点上下文时，必须阻断写入并提示用户先选中节点，不能退化成新建根节点。

5. 高亮
   - 必须是 MarginNote 可见的原生高亮或批注，不修改原文 PDF。
   - 高亮必须和卡片/脑图节点有一致的定位关系。
   - 导出 PDF 时生成带标注副本，而不是覆盖原始文件。

6. 安装与发布
   - 提供普通用户可执行的安装包或安装脚本。
   - Companion 支持 launchd 后台启动和卸载。
   - README、产品手册、隐私说明、权限说明、故障排查齐全。

## v0.4.28 当前状态

- 已完成：MN4 WebView 面板已加入真实可见的 `Chat Mode / Agent Workspace` 双模式壳层，`modeSwitchBar/chatModeButton/agentWorkspaceModeButton/modeIntentLine` 是运行态必需控件；`activeProductMode` 默认是 `workspace`，`lastWorkspacePane` 记录上一次非对话工作区，`Chat Mode` 聚焦对话面板，`Agent Workspace` 恢复上一次非对话工作区。`Agent Workspace` 顶部新增 `Workspace Navigator`，`workspaceNavigator/workspaceNavigatorSummary` 和 `workspaceNav...` 控件把 `Knowledge Console`、`Mindmap Studio`、`Card Factory`、`Operation Ledger`、`Knowledge Graph`、`Workflow Builder`、`Skill Center` 作为一等入口，并通过 `activeWorkspaceSurface`、`switchWorkspaceSurface` 跳到对应面板锚点。`Agent Workspace` 包含对象、操作、知识、工作流工作区；默认入口已切到对象区的 `Knowledge Console`，窄面板加载后不再自动回到对话流。右上角保留设置和历史独立页面。对话区固定输入框和发送按钮；对象区显示 `MNObject`、证据、`objectRiskPanel` 风险面板、Object Browser、Object Graph、对象活动和 Operation Ledger；`agent_plan` 会返回 `codex.mn.riskRegister.v1`，包含权限、上下文范围、目标脑图、dry-run 和确认点风险项，Web 控件 `objectRiskSummary/objectRiskList` 会在对象首屏渲染阻断、提醒和通过状态；操作区显示目标脑图、脑图树缓存、Diff、Agent 操作计划、验证和事务中心；知识区显示 Knowledge Graph 状态，并可直接检索当前授权范围内的索引命中；工作流区显示 Workflow Runtime、External Automation Gateway 和 Skill Marketplace 状态，可列出模板、启动模板、查看最近 workflow run，并通过 `workflowRunInspectorPanel` 打开 `codex.mn.workflowRunInspector.v1`，查看每一步的状态、queueId、确认点、提醒/阻断状态和下一步动作；可恢复的失败/阻断 direct 或 queueable 步骤会通过 `workflow_retry_step` 重新入队，写入/确认步骤仍不能自动重试，同时展示/安装声明权限、回滚和验收规则的本地技能包；外部脚本可通过 `/external/workflow/start` 创建 workflow run，并留下 requestId、caller、permission、objectRef、callback 和结果 ledger；`/external/callback/success` 与 `/external/callback/error` 可把外部回调 payload、状态、history 和 receivedCount 写回同一个 request ledger。
- 已完成：Operation Compiler 第一阶段。`agent_plan` 会把当前 `MNObject`、intent、workflow 和权限策略编译成 `codex.mn.operationPlan.v1`、`codex.mn.verificationPlan.v1` 和 `codex.mn.operationCompiler.v1`；操作区新增 `operationCompilerPanel/operationCompilerSummary/operationPlanStats/operationCompilerChecks/operationDryRunDetails/operationCompilerRepairActions`，显示计划步骤、写入数量、验证状态、schema/上下文/权限/dry-run/confirmation/rollback 检查、阻断原因、逐操作 dry-run 明细和第一阶段修复动作。普通 `agent_plan` 现在会在草稿生成前对写入步骤运行 capability-aware dry-run，复用 `operation_runtime.simulate_operation_manifest` 的 native capability / URL API / 权限判断，缺少必要原生能力时会把 operation plan 标成 blocked，而不是等用户写入草稿时才失败。脑图 Diff 局部 apply 阻断时也返回同一份 `codex.mn.perOperationDryRun.v1`，逐节点列出 mutation、noteId、required capability、status、reason 和 verification level。`operationCompiler.repairActions` 会给出可执行恢复入口，例如刷新 MN 能力、打开设置或缓存当前 PDF；Web 前端新增 `operationActionGate`，会根据 Operation Compiler 的 blocked/unknown 状态禁用写入链路和确认类 next action，并在按钮 title 中保留阻断原因；知识检索等只读动作仍可继续。doctor、Web 静态检查和单文档验收已经把这些控件纳入运行态必需项。当前仍是第一阶段编译层，不等于已经完成真实 MN 对象存在性 probe、完整跨对象残留扫描和技能包级 schema 迁移。
- 已完成：`v0.4.28` 发布包会同时生成完整安装 zip 和 MarginNote 原生 `.mnaddon` 插件包；release zip、`.mnaddon` smoke 和 install dry-run 都属于发布前验证项。本机替换后 Companion `/status.pluginVersion` 应为 `0.4.28`；MN4 运行态需要重新打开面板或重启 MN4 后才会上报新版 WebView/native 能力事件。
- 已完成：GitHub 默认 `README.md` 改为英文首页，并提供完整中文 `README.zh-CN.md`；两个 README 顶部互相链接，发布包和 release smoke 都要求同时包含双语 README。
- 已完成：`Mindmap Studio` 第一阶段从“回答下方生成脑图按钮”升级为操作工作台。它不是回答下方按钮的别名，而是在操作区提供 `读取现有脑图`、`预览 Diff`、`应用所选`、`验证事务`、`回滚事务` 五个清晰动作，并把当前真实脑图树、最新 Diff、局部应用结果和最近 AI 编辑事务汇总到四段阶段栏。它会复用 `mn_read_tree`、`mindmap_diff_preview`、`acceptMindmapDiff`、`ai_edit_transaction_verify` 和 `reject_ai_edit_transaction`，当前仍是第一阶段 Studio，后续才会继续补完整原地编辑、颜色/标签/链接保留、跨文档去重和更强的残留证明。
- 已完成：诊断日志脱敏、裁剪、读取和清空逻辑已从 `companion.py` 拆到 `diagnostic_log.py`，保留原 Companion API 名称，减少主服务文件负担；action lifecycle 日志会把当前 `MNObject` 提升成顶层 `objectRef`，便于按选区、卡片、文档或脑图对象追踪失败。
- 已完成：对象工作区提供 Object Graph 第一阶段。`object_graph` 会把当前 `MNObject` 作为 root，把相关历史对话、workflow run、AI 编辑事务、external gateway request、诊断日志和 Knowledge Index 实体转成 `codex.mn.objectGraph.v1` 节点与边；知识实体节点保留 `entityType/noteId/sourceRef/relations`，实体之间的 `supports/contains/...` 关系会成为 `knowledge_relation` 边。它还会读取最近一次 `mn_read_tree`/原生脑图树缓存，把缓存内的 MN note 作为 `mn_note` 节点，把父子层级转成 `contains` 边，并返回 `codex.mn.nativeMindmapTreeEvidence.v1` 证据，证据来源标记为 `mindmap_tree_cache`。新增 `object_graph_relation_save/delete` 可在本地保存用户维护的 `manual_relation` 可编辑关系边，把两个 `MNObject` ID 连起来；每次保存或删除也会进入 `object_graph_manual_relation` Operation Ledger，并保存 `manualRelation` 证据。Web 对象区提供紧凑关系编辑器。Web 面板在对象区常驻显示节点/关系计数，点击图谱节点可以进入历史对话、workflow、事务、Operation Ledger 证据详情、知识检索、请求读取 MN 节点子树或删除手工关系。这是终极 `Object Graph` 的导航层起点，后续还要接入实时 MN 全库原生节点关系、跨 notebook 概念关系和更完整的可编辑关系边。
- 已完成：对象工作区提供 Object Browser 第一阶段。`object_browser` 会把当前焦点 `MNObject`、Object Graph 节点、对象活动条目、Operation Ledger 条目和第一阶段 `MNObject Registry` 条目汇总成 `codex.mn.objectBrowser.v1` 对象清单；`mn_object_registry` 会返回 `codex.mn.mnObjectRegistry.v1`，保存已见对象的 objectRef、firstSeen/lastSeen、seenCount、evidenceTypes 和 topic/book 作用域；保存 `manual_relation` 时会把 from/to 两端对象注册进去，Object Browser 读取时也会把本次看到的对象写回 registry；收到 `mindmapTreeReadFinished` 后会把原生脑图树缓存中的每个 note 登记为 `mnobj:note:<noteId>` / `mindmap_node`，并保留 sourceRef.noteId、parentNoteId 和 nodePath。Web 控件为 `objectBrowserPanel/objectBrowserSummary/objectBrowserTypeFilterSelect/objectBrowserKindFilterInput/objectBrowserSearchInput/objectBrowserFilterButton/objectBrowserList/objectRegistryScanButton`；用户可按 `objectTypeFilter`、`kindFilter` 和 `query` 缩小对象清单，后端会返回 `filters`、`filteredTotal` 和 `unfilteredTotal`，前端 summary 显示筛选后的数量和筛选条件。用户点 `扫描 MN` 后，Web 会调用 `request_mn_object_registry_scan`，Companion 会入队 `scan_mn_objects`，MN4 原生侧扫描当前 notebook 可见 note 对象并回传 `mnObjectRegistryScanFinished`，后端把这些对象以 `native_object_scan` 证据登记进 Registry。扫描对象会进入 Object Graph：`object_graph` 会把这些 registry 条目提升为 `mn_note` 节点，并根据 sourceRef.parentNoteId/nodePath 生成 `native_object_scan 父子边`。每个对象带 `objectType/kind/objectRef/sourceRef/evidence/availableActions/browserAction`，Web 对象区可从这个清单直接刷新图谱、打开活动、打开账本或进入节点动作；点击扫描对象会打开该对象图谱，点击扫描对象会打开该对象活动和账本，并把该 registry objectRef 作为 `mnObject` 传给 Object Graph、Object Activity 和 Operation Ledger。这是终极 `Object Browser` 的起点，目前仍基于已聚合证据、脑图树缓存、主动扫描、筛选搜索和已见对象注册表，不等于实时浏览完整 MN notebook 原生对象库。
- 已完成：对象工作区提供对象活动聚合。`object_activity` 会按当前 `MNObject` 汇总历史对话、workflow run、AI 编辑事务、手工对象关系事件和诊断日志；Web 面板在对象区常驻显示计数和最近活动，并可直接打开对话、查看 workflow、查看事务、打开关系账本详情或展开日志详情。
- 已完成：对象工作区提供 Operation Ledger 第一阶段。`operation_ledger_list/get` 会按当前 `MNObject` 聚合 workflow run、AI 编辑事务、external gateway request 和 `object_graph_manual_relation` 手工关系事件；Web 控件为 `operationLedgerPanel/operationLedgerSummary/operationLedgerTypeFilterSelect/operationLedgerStatusFilterInput/operationLedgerSearchInput/operationLedgerFilterButton/operationLedgerList/operationLedgerDetailPanel`。用户可按 `entryTypeFilter`、`statusFilter` 和 `query` 缩小账本清单，后端返回 `filters`、`filteredTotal` 和 `unfilteredTotal`，前端 summary 显示筛选后的数量和条件。Web 面板在对象区常驻显示账本总数、类型计数和最近条目，并可按 `ledgerId` 在对象区打开证据详情面板，展示 operation plan、dry-run/apply path、native command、native event timeline、native apply、rollback/residual、逐对象 `codex.mn.residualProof.v1`、workflow 确认/阻断状态、external callback evidence 和 `manualRelation` 关系证据。这是终极 `Operation Ledger Explorer` 的起点，目前仍是对象作用域的可筛选证据账本，不等于完整跨文档审计浏览器。
- 已完成：Card Factory 第一阶段。`generate_card` 和完整精读生成短卡时都会返回 `codex.mn.cardFactory.v1` 摘要，每张卡带 `cardType`、`source`、`learningGoal`、`reviewPrompt` 和 `codex.mn.cardFactoryCard.v1` 元数据；草稿保存后继续保留 `card_factory` 和 `card_quality`，AI 编辑确认面板会显示“卡片工厂”摘要、卡型分布、缺来源、长卡和重复标题风险，并提供 `加入复习队列`。Companion 新增 `review_queue_add/list`，把 Card Factory 草稿卡按 topic/book/draft/card 去重写入 `codex.mn.reviewQueue.v1`，知识区显示当前 `MNObject` 作用域下的复习队列摘要和最近卡片。当前仍未完成跨对象去重、替换/合并和覆盖率闭环。
- 已完成（0.4.26）：Codex CLI 若返回 `timed out waiting for cloud config bundle after 15s`，Companion 会自动重试一次；重试后仍失败时显示可操作的代理/登录/网络提示，而不是把原始英文错误直接丢给用户。
- 已完成：对话页按钮按任务分区重排。输入行固定放发送；`stagedActionLine` 显示按钮中心填入后的待发送动作，并允许修改 prompt 后仍按该动作执行；`mainActionStack` 按一次性目标、常用任务、工具区顺序排列；`goalRunPanel` 独立放“设目标”按钮和状态；`primaryActionGrid` 是 2x2 常用区，只包含解释选中、生成卡片、新建脑图和完整精读；`workflowActionPanel` 常驻显示 `mindmapToolPanel` / `mindmapActionGrid` 的补到当前、重组当前，以及 `sourceToolPanel` / `toolActionGrid` 的高亮、导出和状态；缺上下文按钮会显示“需选区/需节点/需文档/需能力”，运行中的可用按钮用“可排队”状态提示，不再像整体置灰；主对话页运行态提示只保留刷新和去设置，设置页诊断入口按 AI 与连接、权限与文件、MN 运行态、验收四组分区，检查连接、本文档验收和发布验收走各自独立按钮。
- 已完成（0.4.26）：发送按钮保留内置两行 `发送 / 可排队`，但全局运行中 `data-busy=queue-available` 的 `::after` 提示已排除 `#sendButton`，避免按钮显示第三行重复 `可排队`。
- 已完成：按钮页提供预设模板、自定义 prompt、动作类型和“主界面”开关；预设模板可填入输入框或添加成自定义按钮，不再一键试用即执行；后端会保存自定义按钮并把主界面置顶按钮限制为最多 4 个；自定义按钮动作支持 `request_native_highlight_selection`。
- 已完成：顶部 AI readiness 状态卡，明确显示当前 AI 后端、本机 Codex CLI 是否发现、OpenAI 是否已配置；状态文案使用“后端已发现”而不是“已完成真实生成”，避免把 CLI 路径发现误认为模型调用已成功；设置页可选择 `auto`、`codex_cli`、`openai_api`、`local`，也可录入或清除 OpenAI Key，并提供无 token 的“试连AI”快速探测。Key 只写入本地 `.env`，不回显到 Web UI 或 settings JSON；清除 Key 只发送 `clearOpenAIKey=true`，不会把输入框里的临时 key 回传。
- 已完成：写入类动作改为草稿可编辑确认模式。生成卡片、生成脑图、完整精读先保存待写入草稿；用户可在草稿框中修改卡片内容，用 `## 标题` 分隔多张卡片；点击“写入 MN”后才调用 MN4 原生 API 创建卡片/脑图，点击“丢弃”会放弃草稿。程序化验收也可通过 `request_draft_write` 入队 `nativeAction=write_draft`，由 MN4 native poll 读取同一个草稿并写入，不依赖鼠标点击 WebView 按钮。
- 已完成：按钮点击后主动释放焦点，避免连续点击时焦点卡在按钮上。
- 已完成：WebView 面板标题栏可拖动移动，右下角可拖拽缩放，标题栏 `-` / `+` 按钮可缩小放大，最小尺寸 390x520，并持久化用户调节后的尺寸和位置。
- 已完成：执行期间动作按钮不整体置灰；继续点击会自动加入 pending 队列，并在消息后显示停止当前并直接执行或查看队列状态。
- 已完成：对话页显示执行进度和已用秒数；运行期间 WebView 会轮询 Companion `/status`，把后端 `run.action/stage/detail` 同步到对话进度消息和底部 `runStateLine`，避免用户只看到计时而不知道后台阶段。
- 已完成：面板内设置 AI 后端、Codex 权限、模型、速度和 HTTP/HTTPS 代理；权限分 `read_only`、`notes`、`full`，写入动作会被权限拦截。强制选择 `codex_cli` 时 Companion 会调用本机 `codex exec --skip-git-repo-check`，自动模式会优先尝试 CLI 再尝试 OpenAI；两者都不可用时生成型动作明确失败，不会回退到内置模板。
- 已完成：设置页提供文件访问权限诊断，能检查当前 PDF、MN4 数据库、导出目录和 PyMuPDF，并在 macOS Full Disk Access 缺失时给出明确修复指引；同时提供“缓存PDF”按钮让 MN4 插件进程上传当前 PDF 到本机 Companion 缓存，提供“刷新MN能力”按钮让插件重新上报 MN 原生 API 能力，提供“运行态采证”按钮写出 `/status.mnRuntime`、`nativeApiCapabilities` 和 doctor 输出 evidence JSON，并提供“打开设置”按钮尝试打开 Full Disk Access 页面。
- 已完成：MN 原生动作矩阵。MN4 插件运行时会上报 `capabilityMatrix`，覆盖卡片、脑图、Undo 分组、写入后刷新、PDF 缓存、原生选区高亮、选区菜单高亮和标注 PDF 导出；Companion、doctor 和设置页会显示每项是 `ready` 还是缺上下文，便于把 MN API 能力和用户可执行动作对齐；`request_native_capability_probe` 可通过队列主动刷新运行时探测事件。
- 已完成：目标是主界面按钮级入口；执行目标会作为一次性长任务启动，只在 `goal_run` 和由目标拆分出的队列任务中显式进入模型上下文，不会保存成长期当前目标；普通聊天、普通制卡和普通脑图不会自动继承旧目标；自动拆分出的后续任务会加入队列。
- 已完成：面板内上传文件或登记本地文件路径；文件摘要会进入模型输入上下文。
- 已完成：状态栏内全局队列/停止一体按钮、队列数量和后端运行状态行；空闲时 `队列` 只刷新/提示 pending 状态，不代替输入框发送；文件页只保留上传。队列状态入口改为消息级引导按钮；停止信号会阻断下一步生成动作，并在长请求返回后阻止继续写入卡片或脑图。WebView 队列泵会自动续跑 raw action；遇到 `nativeAction` 时只显示“等待 MarginNote 原生处理”，不伪造执行、不 ack，交给 MN4 插件原生轮询执行并确认。Companion 会把当前/最近生成动作、阶段、详情和耗时写入 `control/current-run.json`，并通过 `/status` 和 `queue_status` 返回给 UI。
- 已完成：脑图合并保护。`generate_mindmap` 会识别“补到当前脑图/合并脑图”意图，并要求 MN4 payload 带 `selectedNoteId/selectedNoteTitle/selectedNoteText`；缺少选中节点时返回 400 和明确提示，不调用模型、不生成 `mindmap`。MN4 `createMindmap()` 写入层也会拦截旧草稿中 `mergeIntoSelected=true` 但当前没有选中节点的情况，避免误建新根节点。
- 已完成：主对话页顶部提供脑图写入目标选择。Companion 会按当前文档保存 target binding，新建脑图可稳定写入当前文档对应的 Codex 脑图根或用户选择的目标节点，避免切换文章后写入旧脑图。
- 已完成：脑图 Diff 第一阶段。回答下方会显示 `脑图 Diff 预览`，右侧操作区会常驻最近一次 Diff 摘要；用户可以逐节点取消勾选并编辑节点标题/正文。前端会标记 `excluded_by_user`、更新保留/跳过计数，并把标题/正文改动作为 `mindmapNodeEdits` 提交；后端的 `mindmapDiffOperationPlan` 会把保留项和用户跳过项分别记录为 `selected=true/included` 与 `selected=false/excluded_by_user`，局部 apply 使用编辑后的 operation plan。
- 已完成：局部脑图 Diff apply 进入事务中心。`request_mindmap_diff_apply` 会生成 `transactionId`，native `mindmapDiffApplyFinished` 会带回 created/applied noteId、失败数和逐操作验证；Companion 会把它归档到 `aiEditTransactionStatus`，状态先进入 `pending_confirmation`。事务中心提供 `保留 / 回滚 / 验证 / 证据` 操作，回滚会调用 MN 原生 `reject_ai_edit_transaction` 删除本次新增节点并返回残留证据；按钮触发时会把 Companion ledger 中的 `createdNoteIds` 传给原生层，降低插件内存重载后找不到事务的概率。
- 已完成：脑图 Diff 删除建议走二次确认。current-only 节点会生成 `delete_suggest`，普通接受不会直接删除；Web 面板会调用 `request_mindmap_delete_confirmation` 建立 `delete_pending_confirmation` 事务，事务中心显示 `删除 / 忽略`。确认删除后 MN 原生层回传 deleted/failed/failures，忽略则写入 dismissed，不把失败删除计入成功。
- 已完成：面板内查看/清空当前 notebook/book 历史对话；`history_list` / `history_clear` 已有 Companion 接口；conversation 会持久化 `objectRef/mnObjectId`，后端可按当前对象过滤历史会话。
- 已完成：旧版原生按钮面板继续保留，作为 WebView 加载失败时的兜底文件。
- 已完成：Companion 本地服务、Codex CLI 可选后端、OpenAI 可选配置、本地工具/诊断模式。生成型动作必须使用 Codex CLI 或 OpenAI，不用本地模板冒充模型输出。
- 已完成：程序化队列触发，插件轮询后用 MN4 原生 API 写入内容。
- 已完成：完整精读改为真实模型驱动，模型输出会被拆成短卡片和脑图分支，先进入草稿确认再写入 MN。
- 已完成：写入层保留 Codex 元数据去重能力，重复写入时会跳过已有卡片/脑图节点。
- 已完成：发布包根目录一键 `install.sh` / `uninstall.sh`、原生 `.mnaddon` 插件包、只读高亮审计、默认禁用危险的 SQLite 高亮写入；doctor 会检查 zip 根目录安装入口、私有运行文件排除和 OneDrive 哈希一致性。
- 已完成：新增面向普通用户的产品手册 `docs/USER_MANUAL.md`，覆盖安装、首次启动、AI 后端、普通对话、目标、自定义按钮、卡片、脑图、完整精读、高亮、标注 PDF 副本、队列/停止/进度、历史、权限、隐私、常见问题和当前预览版限制；README 已加入该入口，发布包和 OneDrive docs 会同步包含该手册。
- 部分完成：可靠可见的 MarginNote 原生高亮。当前 DB 复制路线不适合作为发布默认方案；官方 `JSBDocumentController.highlightFromSelection()` 路径已接入主界面“高亮下一选区”、自定义按钮、程序化队列和设置页“高亮采证”向导。Web 主按钮现在优先进入一次性的下一次 PDF 选区等待模式，避免点击 Web 面板抢走已有选区；如果当前仍有有效选区则立即尝试官方高亮。插件也会尝试追加到 PDF 选中文本弹出菜单。`documentControllerCandidates()` 已扩展到 `studyController` / `notebookController` 下的 reader/pdf/controller alias 及嵌套 `readerController.documentController`、`pdfController.documentController` 等路径，并在失败事件里输出稳定 `candidateLabels`、`candidateCount` 和 `selectedDocumentControllerLabel`；但还需要在活跃 PDF 选区下验证 `selectionPopupHighlightMenuInstalled`、`nativeHighlightSelectionPosted`、`ZHIGHLIGHTS` blob 和肉眼可见高亮。
- 部分完成：带标注 PDF 副本导出。当前 `export_annotated_pdf` 可用 PyMuPDF 根据选中文本搜索 PDF 文本层，并只在副本中写入 highlight annotation；插件会 best-effort 传入本地 `pdfPath`，Companion 也会只读查询 MN4 `ZBOOK` 并解析 MNDocs，并会优先使用当前 book 的 PDF 缓存副本。当前权限诊断能明确识别 LaunchAgent 的 macOS 文件访问权限问题；剩余风险是在 MN4 内实测“缓存PDF -> 导出PDF”链路、复杂选区和扫描 PDF。
- 未完成：签名、notarization、跨机器发布验证、同一文档完整验收 PASS evidence，以及可见原生高亮证据。当前 `release_acceptance.py` 的基础 gate 已通过 `unit_tests`、`syntax_checks`、`release_zip_smoke`、`install_dry_run`、`runtime_web_controls` 和 `native_api_matrix`；剩余 blocker 为 `native_visible_highlight`、`release_sha256_manifest`、`signed_pkg`、`notarized_pkg`、`cross_machine_install` 和 `single_document_acceptance`。

## 关键技术路线

- 卡片/脑图：继续走 MN4 插件内部 API，避免 Companion 直接写 SQLite。
- UI：迁移到 WebView 面板，实现稳定文本输入、滚动历史和更好的布局。
- 设置/目标/文件/停止/队列：走 Web 面板直接 POST 到本地 Companion；目标按钮位于 `goalRunPanel` 的 `goalActionStrip`，和目标状态行同在对话页底部动作区，队列/停止一体按钮位于全局状态栏，发送入口始终是输入框旁的 `sendButton`，文件页只管上传；卡片/脑图/完整精读先走 Companion 草稿接口，确认后再由 MN4 bridge 调用插件内部 API 写入；自动化可用 `request_draft_write` 把同一草稿交给 native poll 写入；当前 PDF 缓存通过 `codexpaper://upload_pdf` bridge 交给插件原生侧读取文件并上传。
- 功能触发：保留 `/marginnote/action` 和 `/marginnote/enqueue`。开发验收用队列；用户点击用面板按钮。raw action 由 WebView 空闲后拉取执行，native action 由 MN4 插件 native poll 执行并 ack。
- 高亮：优先寻找 MN4 原生 JS API；如果没有公开 API，使用“导出标注 PDF 副本”的可维护降级路径。不要把直接写 `ZHIGHLIGHTS` blob 当发布方案。

## 完成定义

发布版只有在以下条件都满足时才算完成：

- 新用户安装后能在 MN4 内看到 UI 并完成一次材料问答。
- 生成的卡片和脑图在 MN4 内可见，并能回到原文位置。
- 高亮在 MN4 内肉眼可见，且不污染原始 PDF。
- 通过程序化验收脚本能确认 action、事件、卡片数、脑图节点数和高亮数。
- 通过一次视觉 QA 确认面板没有白屏、遮挡、文本溢出。
