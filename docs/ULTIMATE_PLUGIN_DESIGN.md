# Codex Companion Ultimate Design: MarginNote Knowledge Agent OS

更新时间：2026-06-27  
目标版本：v3.0  
状态：终局产品蓝图。当前 0.4.x 是 Chat Mode + Agent Workspace 雏形，不是终局。

执行计划：`docs/superpowers/plans/2026-06-27-knowledge-agent-os-implementation.md`。该计划把本蓝图拆成 Live MN Object Kernel、Source Registry、External Automation Gateway、Transactional Native Editor、Workflow Runtime、Skill Runtime、Verification Agent、Workspace Reframe、文档与发布 gate 十个工程阶段。

当前实现边界：本分支已经开始把“终局”和“现有聊天插件”拉开到代码层，而不只是文案层。已落地的断层包括对象内核、来源注册、外部自动化网关、事务写入证据、Workflow Runtime v2、Skill Runtime v2 和 Verification Agent v1。Skill Runtime v2 已经能拒绝缺少 `dryRun`/`rollback`/`acceptance` 的写入技能，能安装合格 manifest，能生成 dry-run-first 操作计划，并能记录 skill run ledger。Verification Agent v1 已经能对 transaction、source registry、workflow run 和 skill run 输出 `PASS`/`FAIL`/`UNKNOWN` 报告；没有 native object probe 时必须是 `UNKNOWN`，不能把日志成功冒充真实证明。未完成部分仍包括完整 Notebook Workspace 默认首屏、跨文档 Knowledge Graph Studio、发布级可视化 Verification Center 和真正的可视化 Workflow Builder。

## 0. 核心判断

终局不是“现在插件更强一点”。如果用户看完设计后仍觉得它只是发送、生成脑图、生成卡片、设置、日志和队列的加强版，这个设计就是失败的。

终局产品必须从 **AI 聊天插件** 断代到 **MarginNote Knowledge Agent OS**：

> Codex Companion v3.0 是 MarginNote 里的可验证知识操作系统。它把文档、摘录、高亮、卡片、脑图节点、概念、复习任务、外部文件、workflow、技能和自动化请求统一成可浏览、可编辑、可验证、可回滚的知识对象系统。

这句话的重点不是“AI 更会回答”，而是“知识对象可操作”。当前 0.4.x 的主语仍然是 prompt、回答和按钮。v3.0 的主语必须是真实 MarginNote 对象、对象关系、工作流、事务证据和学习覆盖。

终局路线是 **知识编辑工作台 + 自动学习代理**，不是 **MarginNote 自带 AI 的超强聊天版**。它仍然是双模式产品，但两个模式的职责必须分清：

- `Chat Mode` 继续存在，用于轻量问答、解释选区、输入自然语言意图。
- `Agent Workspace Mode` 是生产系统，用于对象浏览、真实脑图编辑、卡片覆盖、知识图谱、workflow、技能和账本。
- 聊天是入口，不是终局；Agent Workspace 才是生产系统。
- 产品原则是对象优先、操作优先、证据优先。
- 不得把现有控件堆叠当作终局。
- 只要首屏仍然像聊天框加按钮，就不算终极版。
- 如果双模式壳层退化成 AI Copilot 面板，用户看起来能问、能生成、能点按钮，但知识结构仍没有被对象化、事务化和证据化。

## 1. 当前版和终局版的本质差异

| 维度 | 当前 0.4.x | v3.0 终局 |
| --- | --- | --- |
| 用户入口 | 先发 prompt，再看回答，再点按钮 | 打开 notebook 就看到对象状态、来源覆盖、脑图缺口、卡片缺口、workflow 和待确认事务 |
| 核心对象 | 当前消息、当前回答、当前选区 | 持久 MNObject、noteId、摘录、高亮、卡片、脑图节点、workflow run、ledger item |
| 脑图 | 生成一棵树或把回答变成树 | 读取真实现有脑图，以 noteId 做 create/update/merge/move/link/delete_suggest Diff |
| 卡片 | 把回答拆成多张卡 | 按学习目标、卡型、来源、覆盖率和复习排程管理卡片 |
| 长任务 | pending 队列、目标、停止按钮 | Workflow Runtime，支持暂停、恢复、确认点、失败恢复、验收报告 |
| 写入 | 草稿、接受、拒绝、回滚尝试 | Transactional Native Editor：plan -> dry-run -> native apply -> verify -> accept/reject -> rollback -> residual proof |
| 证据 | 调试日志、状态消息 | Operation Ledger Explorer，按对象、workflow、技能、事务追溯每次改动 |
| 知识层 | 当前文档上下文、历史、索引 | 跨 notebook Knowledge Graph，显式授权，带 noteId/page/quote/MN link |
| 外部自动化 | 外部接口触发动作 | External Automation Gateway，外部请求只能创建 agentOperation 或 workflow run |
| 扩展 | 自定义 prompt 和按钮 | Skill Center / Skill Marketplace，技能有 manifest、schema、UI、权限、dry-run、rollback、验收和迁移 |

如果用户的高阶工作仍只能靠输入一句话再点回答下方按钮，就不是终局。它最多是 AI Chat Plugin 或 Study Copilot。

## 2. 四个产品代际

| 代际 | 第一眼像什么 | 用户主要操作 | 典型能力 | 不能冒充什么 |
| --- | --- | --- | --- | --- |
| v0.4.x Chat Companion | 聊天面板加工具按钮 | prompt、回答、草稿、状态 | 问答、短卡、脑图草稿、配置、缓存、日志 | 不能叫知识工作台 |
| v1.x Study Copilot | 稳定的阅读和制卡助手 | 当前材料、选区、目标脑图 | 对标 MN4 自带 AI，稳定全文读取，生成结构化脑图和短卡 | 不能叫原生对象编辑器 |
| v2.x Native Knowledge Editor | MN 原生知识编辑器 | noteId、真实脑图节点、卡片、摘录、Diff | 原地读取、合并、移动、删除建议、回滚和残留证明 | 不能叫全局 Knowledge OS |
| v3.x Notebook Knowledge OS | Notebook Knowledge IDE | notebook 对象图、知识图谱、学习目标、workflow、技能、ledger | 自动精读、重组知识结构、跨文档关联、外部自动化、技能运行、可验证回滚 | 这是终局 |

当前 0.4.x 是 Chat Mode + Agent Workspace 雏形。它已经有 Object Browser、Object Graph、Mindmap Studio、Card Factory、Workflow Runtime、External Automation Gateway 和 Operation Ledger 的第一阶段控件，但这些控件还没有形成完整对象内核、事务内核和知识工作流内核。当前 0.4.x 不是终局。

## 3. 终局首屏

v3.0 默认进入 `Notebook Workspace`，不是空聊天框。默认入口必须能在 Chat Mode 和 Agent Workspace Mode 之间切换，但 v3.0 的默认落点应是 Agent Workspace Mode。

兼容壳层仍需要保留这些运行态控件，作为迁移和验收锚点：

- `modeSwitchBar`
- `chatModeButton`
- `agentWorkspaceModeButton`
- `modeIntentLine`
- `activeProductMode`
- `lastWorkspacePane`
- `Workspace Navigator`
- `workspaceNavigator`

终局首屏分四个区域：

1. **左侧 Object Browser**
   像 Finder 一样浏览 notebook、document、PDF selection、excerpt、highlight、card、mindmap node、subtree、external file、workflow run、ledger item、skill output。

2. **中间 Studio Canvas**
   根据任务显示 Mindmap Studio、Card Factory、Knowledge Graph Studio、Workflow Builder 或 Source Registry。这里是真实对象的编辑区，不是 AI 回答正文。

3. **右侧 Command Pane**
   保留聊天输入、解释、追问和自然语言指令。它可以把意图编译成 operation plan，但不能绕过 workspace 直接写 MarginNote。

4. **底部 Operation Ledger Drawer**
   显示当前对象和当前 workflow 的计划、dry-run、native command、event timeline、verify、rollback、residual proof 和失败恢复动作。

终局必须和当前版本拉开的可见断层是：当前 0.4.x 做不到的事不能用已有对象区、workflow 区或 ledger 区来掩盖。当前版本还不能稳定浏览整个 notebook 对象库，不能完整原地重构复杂脑图，不能证明所有实体卡片和关系残留，也不能把技能、复习、外部自动化和跨文档知识全部纳入同一个证据系统。

## 4. 终局必须出现的新产品形态

这里列的是产品级界面，不是按钮清单。

### 4.1 Knowledge Console

Knowledge Console 是 Agent Workspace Mode 的首页。它不是设置页，也不是聊天页底部状态块。

它必须回答：

- 当前操作对象是谁？
- AI 可见哪些内容？
- 材料、脑图、卡片、复习、workflow、ledger 的覆盖情况如何？
- 有哪些缺口和风险？
- 接下来可以执行什么 workflow？
- 最近有哪些失败、待确认写入和残留对象？

Knowledge Console 支持 zero-message workflow：用户不输入任何 prompt，只打开 notebook，就能看到对象状态、材料覆盖、脑图缺口、卡片缺口、最近失败事务、可执行 workflow 和待确认写入。

### 4.2 Object Browser

Object Browser 必须像 Finder 一样浏览 notebook 对象，而不是只聚合当前消息附近的对象。它以 `MNObject Registry` 为底座，并融合实时 MN 原生对象。

必备对象类型：

- notebook
- document
- PDF selection
- excerpt
- highlight
- card
- mindmap node
- mindmap subtree
- external file
- external request
- workflow run
- operation ledger item
- skill output

第一阶段兼容对象和控件必须继续可追踪：

- `object_browser`
- `objectBrowserPanel`
- `browserAction`
- `mn_object_registry`
- `codex.mn.mnObjectRegistry.v1`
- `mnobj:note:<noteId>`
- `mindmapTreeReadFinished`
- `objectRegistryScanButton`
- `request_mn_object_registry_scan`
- `scan_mn_objects`
- `mnObjectRegistryScanFinished`
- `native_object_scan`
- `扫描 MN`

扫描对象会进入 Object Graph。扫描对象以 `mn_note` 节点出现，并通过 `native_object_scan 父子边` 体现 parent/child 关系。点击扫描对象会打开该对象图谱，点击扫描对象会打开该对象活动和账本。这些行为是第一阶段 object browser 的正确迁移方向，但还不是完整终局。

终局硬验收：能像 Finder 一样浏览 notebook 对象，能按文档、对象类型、来源、最近活动、是否可写、是否有残留风险过滤对象，并把任意对象拖入 workflow 或技能输入。

### 4.3 Object Graph

Object Graph 展示对象关系，并从关系生成下一步动作。

关系类型至少包括：

- `belongs_to`
- `contains`
- `derived_from`
- `supports`
- `contradicts`
- `compares_with`
- `reviews`
- `manual_relation`
- `knowledge_relation`

第一阶段兼容术语必须继续有效：

- `Knowledge Index 实体`
- `entityType/noteId/sourceRef/relations`
- `nativeMindmapTreeEvidence`
- `mindmap_tree_cache`
- `manual_relation`
- `object_graph_relation_save/delete`
- `object_graph_manual_relation`
- `manualRelation`
- `可编辑关系边`

Object Graph 不是只画图。它应该能产生动作：补来源、合并重复卡、创建对比卡、建立先修关系、重组脑图、加入复习队列、打开 Operation Ledger 证据。

### 4.4 Mindmap Studio

Mindmap Studio 是真实脑图工作台，不是 Markdown 大纲生成器。真实脑图工作台必须以现有 noteId 和父子关系为主键。

它必须：

- 读取当前真实脑图或选中子树。
- 保留 noteId、父子关系、标题、正文、颜色、标签、来源和文档绑定。
- 显示 create/update/merge/move/link/delete_suggest Diff。
- 支持逐节点编辑标题和正文。
- 支持逐节点接受、拒绝、移动、合并和删除建议。
- 删除走二次确认。
- 拒绝或回滚后证明 outline、实体卡片、链接关系和复习队列是否残留。
- 不因“重新生成脑图”而复制第二棵重复树。

能原地编辑真实现有脑图，是 v2/v3 的关键断层。终局里的“生成脑图”默认不是新建一棵树，而是先读取目标脑图，再判断是补全、重组、合并还是新建。若当前文章没有目标脑图，必须在页面最上面选择目标脑图或创建新脑图，不能默默写到其他地方。

### 4.5 Card Factory

Card Factory 不是“把回答切块”。它要按学习目标生成可复习、可追溯、可审计的学习对象。

卡片类型至少包括：

- 概念卡
- 公式卡
- 方法卡
- 实验证据卡
- 对比卡
- 局限卡
- 复习题卡
- 讲解卡

每张卡必须只讲一个知识点，有来源 `source`，有 `cardType`、`learningGoal`、`reviewPrompt`，正文适中，可进入复习队列，可与脑图节点、摘录和概念实体建立关系。

第一阶段兼容 schema 和 UI 术语：

- `codex.mn.cardFactory.v1`
- `cardType`
- `learningGoal`
- `reviewPrompt`
- `卡片工厂`

复习队列和覆盖率是 Card Factory 的必选闭环。终局还必须有跨对象去重、替换、合并、覆盖率、复习排程和来源闭环。

### 4.6 Knowledge Graph Studio

Knowledge Graph Studio 维护跨 notebook 知识层。它不是全文缓存，也不是历史搜索。

它必须显式管理：

- 概念
- 公式
- 方法
- 证据
- 假设
- 局限
- 对比
- 支持/反驳
- 先修关系
- 复习状态
- 来源回链

跨 notebook 知识层只有在用户明确授权时参与回答。跨文档回答必须列出对象引用、noteId/page/quote 或 MN link，并显示授权范围。用户必须能清空、导出或禁用索引。

### 4.7 Workflow Builder

Workflow Runtime 不是队列。队列只说明后面还有任务；workflow 说明这项知识操作由哪些步骤组成，每步输入输出是什么，哪里需要确认，失败后如何恢复。

Workflow Builder 必须支持：

- 手动、选区、节点、PDF 缓存完成、外部 API、定时复习触发。
- `pending`、`running`、`waiting_confirmation`、`failed`、`cancelled`、`verified`、`rolled_back` 状态。
- 暂停、恢复、取消、重试、等待用户确认。
- 每一步的输入对象、输出对象、模型输出、原生动作、失败原因和下一步。
- 导出运行报告。

长任务中断后，用户必须能看到完成到哪一步、等待哪个确认点、失败在哪里、是否已经写入、能否继续或回滚。

### 4.8 Operation Ledger Explorer

Operation Ledger 不是开发日志，而是用户信任系统。Operation Ledger Explorer 必须让用户按对象、文档、时间、技能、workflow、成功/失败、残留状态过滤所有 AI 操作。

每次写入必须记录：

- 用户请求
- 当前对象
- 上下文范围
- operation plan
- Diff
- dry-run
- native command
- native event timeline
- created/updated/moved/deleted/suggested noteId
- Verification Agent 报告
- accept/reject
- rollback
- residual objects
- external callback evidence

终局必须能证明 AI 到底改了哪里、还能不能撤回、撤回后还剩什么。

### 4.9 Skill Center / Skill Marketplace

技能包不是自定义 prompt。Skill Center / Skill Marketplace 必须支持可发布技能包：

- manifest
- 输入对象类型
- 输出 operation schema
- prompt
- UI 面板
- 权限要求
- 写入边界
- 是否允许删除
- dry-run 规则
- rollback 规则
- 验收规则
- 版本迁移
- 安全审查

技能包必须分为只读技能、写入技能、删除/回滚技能。写入和删除技能默认需要确认，并进入 Operation Ledger。技能包不是自定义 prompt；外部自动化不能绕过 dry-run、确认、ledger 和回滚。

## 5. 六个不可替代系统内核

v3.0 不是 UI 组合，而是系统内核组合。缺少任何一个，产品都会退回 AI Chat + MN Actions。

### 5.1 Live MN Object Kernel

Live MN Object Kernel 从 MarginNote 原生运行态、URL API、缓存、导入文件和历史 ledger 里建立统一对象库。它不是“当前选区 payload”，而是可持续同步的对象内核。

每个对象必须有：

- 稳定 `objectId`
- 原生 identifiers：topicid、bookmd5、noteId、page、anchor、mnLink
- `sourceRef`
- 权限边界
- 关系
- 最近事件
- 可用动作

硬验收：用户能点开任意对象，看到来源、关系、历史、权限和下一步动作，而不是只看到当前文档名。

### 5.2 Source Registry and Content Access Fabric

Source Registry 统一管理 MN 文档、PDF 缓存、OneDrive/iCloud 路径、上传文件、网页、外部数据和手工绑定。它负责回答“为什么找不到 PDF/全文”，并把每个来源的可读性、权限、缓存时间、哈希和绑定对象写成证据。

终局 Source Registry 不应该藏在设置页。文件路径管理、PDF 缓存、上传资料、URL 来源和外部数据都应该是可浏览的 source object。

### 5.3 Operation Compiler

终局里，AI 的主要输出不是 Markdown 回答，而是结构化 `agentOperation`。回答可以存在，但写入必须通过 Operation Compiler 变成强约束操作。

Operation Compiler 必须负责：

- schema 检查
- 上下文范围检查
- 权限检查
- native capability dry-run
- Diff 生成
- confirmation point 生成
- rollback plan 生成
- verification plan 生成

第一阶段兼容链路继续使用 `Operation Compiler`、operation plan、verification plan、per-operation dry-run。它是从回答按钮升级到对象操作的关键层。

### 5.4 Transactional Native Editor

Transactional Native Editor 把所有写入变成可审计事务。

它必须支持：

- 真实 MN 对象读写
- noteId 存在性 probe
- 逐对象 Diff
- 原生 apply
- 写入后 verify
- accept/reject
- rollback
- residual proof

没有这个内核，脑图拒绝后“删了结构但卡片还在”这类问题会反复出现。

当前实现检查点：

- `transaction_manager.py` 已规范化第一阶段 `codex.mn.operationTransaction.v1`，并在 transaction summary 和 verification 中分离 note/card 证据。
- `codex.mn.residualProof.v1` 已区分 `residualNoteIds` 和 `residualCardIds`，同时保留逐对象 `objects` 明细。
- 原生 `main.js` 的 AI edit reject 路径会回传 `deletedNoteIds`、`deletedCardIds`、`failedNoteIds`、`failedCardIds`；无法确认删除的 card 会返回 `card-delete-unsupported`，不会被计为成功。
- WebView bridge 会把 `createdCardIds` 带回原生侧，避免从账本重建 rollback transaction 时丢失卡片 ID。
- Operation Ledger detail 已显示 note/card 分离的 rollback 和 residual evidence。

### 5.5 Workflow Runtime + Scheduler

Workflow Runtime 是状态机，不是 pending 队列。它负责 workflow 定义、步骤状态、暂停/恢复、确认点、模型调用、MN 原生动作、外部回调、失败恢复、验收报告和可重放记录。

硬验收：一个“精读全文并生成脑图和卡片”的长任务中断后，用户能从具体步骤继续，而不是重新打一遍 prompt。

当前实现检查点：

- `workflow_engine.py` 已提供第一阶段持久化 run store：`create_run`、`update_step`、`next_runnable_step`、`resume_run`、`cancel_run`。
- Companion 启动 workflow 时会保存 `runtimeSchema=codex.mn.workflowRuntime.v2`、`runId`、run events 和 step evidence，同时保留旧 `workflowRun` 响应兼容。
- `workflow_next_step` 和 `workflow_resume` 已接入 Companion action，Workflow Inspector 有对应入口。
- `workflow_cancel` 通过 runtime kernel 标记 open steps 和 run event，不再只是改顶层 status。
- 队列仍是执行细节；workflow step 持有 queueId/evidence，用于 inspector 和 ledger。

### 5.6 Verification Agent

Verification Agent 每次写入后做程序化验收：

- 对象是否存在
- 父子关系是否正确
- 来源是否可追溯
- 卡片是否过长
- 重复是否出现
- 拒绝后残留是否清理
- 外部 callback 是否完成
- 技能验收是否通过

它必须给出 `PASS`、`FAIL`、`UNKNOWN`，而不是一句“已完成”。

## 6. External Automation Gateway

External Automation Gateway 借鉴 MarginNote URL API、x-callback-url、快捷指令、本地脚本、浏览器扩展、Raycast、Obsidian/Zotero 类外部工具和其他本地 agent。它的目标不是让外部脚本直接控制 MarginNote，而是把外部入口接入同一套对象、权限、workflow、ledger 和 callback 证据。

可借鉴方向：

- MarginNote URL API 生态，例如 `Temsys-Shen/url-api-marginnote`，可以提供打开 notebook、定位文档、跳转 note、触发动作和 x-callback 的思路。
- `marginnote4app://` 深链和 x-callback-url 可以成为对象定位、外部回调和跨应用自动化的入口。
- macOS Shortcuts、Raycast、本地 CLI、浏览器脚本可以提交结构化 workflow 请求。
- Zotero、Obsidian、文件系统 watcher 可以作为 Source Registry 或 Knowledge Graph 的来源。

Gateway 的硬规则：

- 外部调用不能直接写 MarginNote。
- 外部请求只能创建 `agentOperation` 或 workflow run。
- 每个请求必须有 requestId、caller、permission、objectRef、contextPolicy、callback 和 ledger。
- 写入前必须经过 dry-run、确认点、native apply、verify。
- 删除和回滚必须二次确认。
- callback success/error 必须回写 Operation Ledger。

外部自动化不能绕过 dry-run、确认、ledger 和回滚。

当前实现检查点：

- `external_gateway.py` 已提供第一阶段协议内核：`normalize_request`、`record_request`、`request_status` 和 `update_callback`。
- `write`、`delete`、`patch`、`create_note`、`create_card`、`mindmap_write` 等外部直接写入动作会被拒绝，返回 `DIRECT_WRITE_FORBIDDEN`。
- `x-success`、`x-error`、callback URL 中的 `secret`、`token`、`api_key`、`authorization` 等 query 字段不会进入状态返回或 Operation Ledger。
- `companion.py` 仍保留旧入口 `/external/workflow/start`、`/external/callback/success`、`/external/callback/error`，但内部请求规范化和 callback lifecycle 已转入 gateway 内核。
- Operation Ledger 的 `external_gateway_request` 项已暴露 `codex.mn.externalGatewayEvidence.v1`，包含 requestId、caller、action、workflowRunId、callback status 和 callback history。

## 7. 关键 schema

### 7.1 MNObject

```json
{
  "schema": "codex.mn.mnObject.v1",
  "objectId": "mnobj:note:NOTE_ID",
  "kind": "mindmap_node",
  "title": "Attention-Guided Safety Filter",
  "identifiers": {
    "topicid": "T1",
    "bookmd5": "B1",
    "noteId": "NOTE_ID",
    "page": 12
  },
  "sourceRef": {
    "documentTitle": "Paper.pdf",
    "quote": "source text",
    "mnLink": "marginnote4app://..."
  },
  "relations": [
    {"type": "derived_from", "targetObjectId": "mnobj:excerpt:E1"}
  ],
  "permissionBoundary": "notes",
  "evidenceTypes": ["native_object_scan", "mindmap_tree_cache"],
  "availableActions": ["open", "read_tree", "make_cards", "start_workflow"]
}
```

### 7.2 Agent Operation

```json
{
  "schema": "codex.mn.agentOperation.v1",
  "object": {
    "objectId": "mnobj:selection:...",
    "kind": "selection"
  },
  "intent": {
    "prompt": "把这个选区做成短卡，并关联之前的内容",
    "workflowId": "selection_to_cards"
  },
  "contextPolicy": {
    "requestedScope": "auto",
    "visibleScope": "selection",
    "explicitFullDocument": false,
    "explicitKnowledgeIndex": true
  },
  "operationPolicy": {
    "permission": "notes",
    "mustDryRunBeforeWrite": true,
    "mustUseAcceptRejectForWrites": true,
    "mustKeepPdfClean": true
  },
  "operationPlan": {
    "schema": "codex.mn.operationPlan.v1",
    "operations": []
  },
  "verificationPlan": {
    "mustVerifyCreatedObjects": true,
    "mustVerifyRollback": true,
    "mustReportResidualObjects": true
  }
}
```

### 7.3 Operation Transaction

```json
{
  "schema": "codex.mn.operationTransaction.v1",
  "transactionId": "txn_...",
  "objectId": "mnobj:note:...",
  "workflowRunId": "run_...",
  "status": "pending_confirmation",
  "dryRun": {"status": "pass"},
  "nativeApply": {
    "createdNoteIds": [],
    "updatedNoteIds": [],
    "movedNoteIds": [],
    "deletedNoteIds": []
  },
  "verification": {
    "status": "unknown",
    "residualObjects": []
  },
  "rollback": {
    "available": true,
    "status": "not_started"
  }
}
```

### 7.4 Skill Manifest

```json
{
  "schema": "codex.mn.skillManifest.v1",
  "skillId": "paper.deep_reading.cn",
  "name": "中文论文精读",
  "version": "1.0.0",
  "inputObjects": ["document", "selection", "mindmap_subtree"],
  "outputs": ["operationPlan", "mindmapDiff", "cardDrafts", "reviewQueueItems"],
  "permissions": ["read", "notes"],
  "requiresConfirmation": true,
  "allowsDelete": false,
  "dryRun": {"required": true},
  "rollback": {"required": true},
  "acceptance": {
    "mustVerifyCreatedObjects": true,
    "mustAttachSources": true,
    "mustCreateLedgerEntry": true
  }
}
```

## 8. 典型终局工作流

| 工作流 | 用户入口 | Agent 链路 | 成功标准 |
| --- | --- | --- | --- |
| 全文精读到目标脑图 | Workspace 选择文档和目标脑图，或 Chat Mode 提问后升级为 workflow | Source Registry -> 章节解析 -> 读取现有脑图 -> 章节级 Diff -> Card Factory -> dry-run -> 用户确认 -> 写入 -> 验证 -> 复习队列 | 覆盖全文主要章节；来源覆盖可审计；拒绝后 outline 和实体卡片可证明删除 |
| 重组现有脑图 | 选中脑图子树，进入 Mindmap Studio | 读取子树 -> 检测重复/过深/孤立 -> move/merge/update/delete_suggest Diff -> 逐节点确认 -> 原地修改 | 不创建第二棵重复脑图，原树结构被可验证地重排 |
| 选区变复习材料 | 选中 PDF 段落，进入 Card Factory | 解释选区 -> 类型化短卡 -> 来源覆盖审计 -> 写入指定位置 -> 加入复习队列 | 每张卡一个知识点，有来源、有复习价值、无超长卡 |
| 跨文档关联 | Knowledge Graph Studio 授权 notebook 检索 | 取相关对象 -> 生成支持/反驳/对比关系 -> 可选创建链接卡或对比子树 | 回答列出 noteId、页码或 quote，新增关系可查看和撤销 |
| 外部自动化精读 | URL/API/Shortcuts/Raycast/CLI 创建 workflow run | Gateway 认证 -> 创建 workflow run -> dry-run -> 等待确认 -> 写入 -> callback success/error | 外部调用不能绕过权限；requestId、caller、callback、ledger 和验证证据完整 |
| 技能包运行 | Skill Center 安装并运行技能 | 校验 manifest -> 绑定对象 -> 预览步骤 -> 执行 workflow -> 写入/验证/报告 | 技能可复用、可卸载、可升级；写入型技能必须可回滚 |

## 9. 实现路线

### Phase A: 双模式壳层

目标：把 Chat Mode 和 Agent Workspace Mode 从信息架构上分开。

完成标准：

- Chat Mode 保持 MN4 自带 AI 式连续对话。
- Agent Workspace Mode 有独立入口、对象首页、工作台导航和空状态。
- Chat 回答可以一键升级为 agentOperation，而不是只露出回答按钮。

### Phase B: Live MN Object Kernel

目标：把当前临时对象引用升级为持久 `MNObject Registry`。

完成标准：

- 所有出现过的选区、摘录、高亮、卡片、脑图节点、文档、notebook、外部文件都有稳定 objectId。
- registry 记录 firstSeen、lastSeen、sourceRef、identifiers、relations、permissionBoundary 和 evidenceTypes。
- Object Browser 从聚合列表升级为 registry + live MN 原生对象浏览。

### Phase C: Source Registry

目标：把全文读取、路径映射、缓存、上传和外部来源统一成 source object。

完成标准：

- 当前文档、PDF 缓存、OneDrive/iCloud 路径、上传文件、网页、URL API 来源和外部文件都可浏览。
- 每个 source object 有可读性、权限、哈希、缓存时间、绑定 MNObject 和失败原因。
- 缺资料时，用户在 Notebook Workspace 里看到可执行修复动作，而不是等模型回答“找不到 PDF”。

### Phase D: Mindmap Studio

目标：把脑图从“生成树”升级为“编辑真实现有树”。

完成标准：

- 读取当前脑图和选中子树时能得到 noteId、父子关系、标题、正文、来源、颜色、标签和文档绑定。
- Diff 支持 create/update/merge/move/link/delete_suggest。
- 拒绝或回滚后，能证明 outline、实体卡片、链接关系和复习队列是否仍残留。

### Phase E: Card Factory and Review Scheduler

目标：把卡片生成升级为学习覆盖系统。

完成标准：

- 以学习目标、卡型、来源、章节覆盖、概念覆盖和复习状态规划卡片。
- 支持跨对象去重、替换、合并、排程和复习队列。
- 卡片和脑图节点、摘录、概念实体之间可建立关系。

### Phase F: Operation Ledger Explorer

目标：把事务日志升级为用户可读证据系统。

完成标准：

- 用户能按对象、文档、workflow、技能、时间、成功/失败、残留状态过滤 ledger。
- 每条 ledger 可展开原生 command、event timeline、Verification Agent 报告和 rollback evidence。
- 失败信息说明阶段、对象、是否已写入、是否可回滚和下一步。

### Phase G: Knowledge Graph Studio

目标：把 Knowledge Index 升级为跨 notebook 知识图谱。

完成标准：

- 概念、证据、对比、支持、反驳、先修、复习状态和来源回链可查看、编辑、删除。
- 跨文档回答列出引用对象和授权范围。
- 用户可以清空、导出或禁用索引。

### Phase H: Workflow Builder

目标：把队列和模板升级为可保存、可恢复、可验收 workflow。

完成标准：

- workflow 有触发器、上下文范围、步骤、确认点、权限、输出和验收规则。
- workflow run 有可视化 Inspector，能展示 queued/manual/waiting_confirmation/blocked/failed/completed、queueId、确认点、下一步动作和错误原因。
- 支持暂停、恢复、取消、重试、确认、回滚和导出报告。
- 每一步都进入对象活动和 Operation Ledger。

### Phase I: External Automation Gateway

目标：把 URL/API 自动化升级为完整外部入口。

完成标准：

- URL API、x-callback-url、快捷指令、浏览器脚本、CLI 和其他本地 agent 全部通过 Gateway。
- 外部调用有 requestId、caller、secret、permission、objectRef、callback、dry-run、ledger 和 verify。
- 外部调用不能绕过确认点、删除二次确认、rollback 和 residual report。

### Phase J: Skill Marketplace

目标：把自定义 prompt 升级为可发布技能生态。

完成标准：

- 技能包声明 manifest、schema、UI、权限、rollback、验收和版本迁移。
- 支持安装、禁用、升级、卸载和审计。
- 至少一个只读技能和一个写入型技能通过发布级验收。

## 10. v3.0 硬验收

终局验收不按按钮数量算，也不按“有没有某个面板”算。必须逐项证明：

| 验收项 | 终局要求 | 不合格表现 |
| --- | --- | --- |
| 主入口 | 默认进入 Notebook Workspace，Chat 是辅助入口 | 首屏仍是聊天框加按钮 |
| 对象层 | notebook、document、摘录、高亮、card、mindmap node、subtree、workflow、ledger 都是可寻址对象 | 只能围绕当前消息附近对象工作 |
| Object Browser | 能像 Finder 一样浏览 notebook 对象 | 只看当前消息聚合结果 |
| 真实脑图编辑 | 读取现有 noteId 和父子关系，做 create/update/merge/move/link/delete_suggest Diff | 重新生成一棵相似的新树 |
| Card Factory | 有学习目标、卡型、来源、去重、覆盖率、复习队列 | 只是把回答拆成多张卡 |
| Workflow Runtime | workflow 有计划、状态、确认点、失败恢复、验收报告 | 只是长任务或 pending 队列 |
| 写入可信度 | 每次写入都有 operation plan、dry-run、native apply、verify、rollback 和 residual proof | 只显示“成功/失败” |
| 回滚证明 | 拒绝后能检查真实 MN 对象是否仍存在 | 只删除 outline 或只按计数猜测 |
| 跨文档知识 | 明确授权范围，回答列对象引用、page/quote/noteId/MN link | 默认偷偷扫全库或无引用回答 |
| 外部自动化 | URL/API 请求进入权限、dry-run、workflow、ledger 和 callback 证据 | 外部脚本绕过插件账本 |
| 技能生态 | 技能包有 manifest、schema、UI、权限、验收、迁移和回滚规则 | 自定义 prompt 冒充技能 |

v3.0 发布级完成定义：

- Chat Mode 与 Agent Workspace Mode 明确分离，用户能在轻量对话和对象工作台之间切换。
- Object Browser 能从 `MNObject Registry` 和实时 MN 原生对象中浏览完整 notebook 对象。
- Object Graph 能显示对象来源、关系、历史和可执行动作。
- Mindmap Studio 能读取真实现有脑图，并对 create/update/merge/move/link/delete_suggest 做逐节点 Diff、确认和验证。
- Card Factory 能按学习目标和卡型规划、去重、替换、审计和加入复习队列。
- Operation Compiler 能把 AI 输出转成强 schema operation plan，并完成权限、上下文、能力和回滚检查。
- Operation Ledger Explorer 能证明每次写入改了哪里、验证是否通过、拒绝/回滚后是否有残留。
- Knowledge Graph Studio 能维护跨 notebook 概念、证据、支持/反驳/对比、先修和复习关系。
- Workflow Builder 能保存、运行、暂停、恢复、取消、重试和导出可验收 workflow。
- External Automation Gateway 能从外部 URL/API 创建 workflow run，并留下 requestId、caller、权限、回调和验证证据。
- Skill Marketplace 至少能安装、升级、禁用和审计一个只读技能和一个写入型技能。
- PDF 缓存、路径映射和上传文件都进入同一对象/上下文系统。
- 日志、ledger 和对象活动可以从任意 MNObject 追溯。
- 发布包包含 `.mnaddon`、安装脚本、双语 README、用户手册、隐私权限说明和 release manifest。

## 11. 当前 0.4.x 的位置

0.4.x 不是终局，但它提供了可迁移脚手架：

- `Chat Mode / Agent Workspace` 双模式壳层。
- `Command Pane` 从 workbench tab 中分离。
- `Workspace Navigator` 让 Knowledge Console、Mindmap Studio、Card Factory、Operation Ledger、Knowledge Graph、Workflow Builder、Skill Center 成为一等入口。
- 第一阶段 `Source Registry` 显示 MN 文档、显式 PDF、PDF 缓存、上传文件和文件搜索根。
- 第一阶段 `Study Program` 显示 zero-message 覆盖率、缺口和推荐 workflow。
- 第一阶段 `Notebook Runbook` 把上下文、MN 对象扫描、脑图基线、操作计划、workflow 和账本排成预检清单。
- 第一阶段 `Operation Compiler` 暴露 operation plan、verification plan、compiler checks 和 per-operation dry-run。
- 第一阶段 `Mindmap Studio` 有读取现有脑图、预览 Diff、应用所选、验证事务、回滚事务。
- 第一阶段 `Card Factory` 返回 `codex.mn.cardFactory.v1`，每张卡带 `cardType`、`learningGoal` 和 `reviewPrompt`。
- 第一阶段 `Object Browser` 聚合当前焦点对象、Object Graph 节点、对象活动、Operation Ledger 条目和 `MNObject Registry` 条目。
- 第一阶段 `Operation Ledger` 能按对象聚合 workflow run、AI 编辑事务、external gateway request 和手工对象关系事件。

这些能力是迁移方向，不是完成证明。它们必须继续被推进到 live object kernel、transactional native editor、verification agent、workflow runtime、skill runtime 和 external gateway，而不是继续在聊天页上堆按钮。

## 12. 不能混淆的边界

以下能力即使做得很好，也仍然不是终极版：

- 聊天 UI 更漂亮。
- 主界面按钮更多。
- 预设 prompt 更多。
- 生成脑图更快。
- 设置页更完整。
- 可以创建卡片和脑图，但不能稳定编辑现有结构。
- 可以删除脑图 outline，但不能证明实体卡片是否残留。
- 可以搜索历史材料，但不显示对象引用、来源和授权范围。
- 可以记录日志，但用户无法按对象和事务理解发生了什么。
- 可以从 URL 触发动作，但外部调用能绕过权限、dry-run、确认点或 ledger。

终局的判断标准只有一个：用户能把 MarginNote 里的任意知识对象交给 Agent，看到它计划怎么改、实际改了什么、验证是否通过、失败后还能怎么撤回或修复。
