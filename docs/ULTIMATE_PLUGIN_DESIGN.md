# Codex Companion Ultimate Design: MarginNote Knowledge Agent OS

更新时间：2026-06-27  
目标版本：v3.0  
状态：终局产品蓝图。当前 0.4.x 是 Chat Mode + Agent Workspace 雏形，不是终局。

## 0. 先把话说清楚

Codex Companion 的终极形态**不是当前聊天插件的增强版**，也不是把当前 0.4.x 已经出现的对象面板、工作流面板、Mindmap Studio、Operation Ledger 换成更大的名字。当前版本有这些入口，只说明工程方向开始正确；它还没有形成终局产品。换句话说，当前 0.4.x 不是终局。

终极形态必须是 **MarginNote Knowledge Agent OS**：一个把 MarginNote 4 里的文档、选区、摘录、高亮、卡片、脑图节点、脑图子树、notebook、外部文件、外部自动化请求和长期知识关系都变成可寻址、可操作、可验证、可回滚对象的知识操作系统。

所以判断终局时不能问“有没有聊天、有没有按钮、有没有脑图”。必须问：

- 用户能不能像 Finder 一样浏览整个 notebook 的知识对象？
- 用户能不能读取并原地编辑真实现有脑图，而不是重新生成一棵相似的新树？
- AI 的写入是否都经过 operation plan、Diff、dry-run、确认、native apply、verify 和 rollback？
- 拒绝或回滚后，系统能不能证明 outline、实体卡片、链接和关系是否仍有残留？
- 卡片是否进入学习目标、卡型、来源、复习队列和覆盖率闭环？
- 跨文档回答是否列出授权范围、对象引用、noteId/page/quote 或 MN link？
- 外部 URL/API 自动化是否也进入权限、workflow、ledger 和 callback 证据？
- 技能包是否是带 schema、UI、权限、验收和迁移的发布对象，而不是自定义 prompt？

终局的产品原则是：**对象优先、操作优先、证据优先**。不得把现有控件堆叠当作终局。聊天是入口，不是终局；Agent Workspace 才是生产系统。从回答按钮升级到对象操作，是当前 0.4.x 到 v3.0 的核心断层。

终局验收不按按钮数量算。默认入口必须能在 Chat Mode 和 Agent Workspace Mode 之间切换；如果不能切换，产品就会退回 AI Copilot 面板：看似能问、能生成、能点按钮，但真实知识结构仍然没有被对象化、事务化和证据化。

只要首屏仍然像聊天框加按钮，就不算终极版。更准确地说：Chat Mode 可以像聊天框，但 Agent Workspace Mode 不能仍然只是聊天页下方的高级按钮区。如果用户的高阶工作仍只能靠输入一句话再点回答下方按钮，就不是终局。

## 1. 代际定义：现在和终局到底差在哪里

| 代际 | 名称 | 用户看到的产品 | 真实能力 | 不能宣称什么 |
| --- | --- | --- | --- | --- |
| v0.4.x | AI Chat Plugin | 在 MN4 里问 AI、生成脑图草稿、生成卡片、看状态和日志 | Chat Mode + Agent Workspace 雏形，已有对象、workflow、ledger、Mindmap Studio 的第一阶段 | 不能说是知识操作系统；不能说已经能稳定管理 notebook 知识结构 |
| v1.x | Native Study Copilot | 对标 MN4 自带 AI，但更可控 | 稳定读取选区、节点、全文缓存、目标脑图，队列、停止、历史、新对话、缓存状态灯成熟 | 不能说能原地重构复杂脑图 |
| v2.x | Native Knowledge Editor | 像一个 MN 原生知识编辑器 | 真实读取脑图、卡片、摘录、高亮，做 Diff、逐节点确认、写入、验证、回滚和残留报告 | 不能说有完整跨 notebook 知识生态 |
| v3.x | MarginNote Knowledge Agent OS | 面向 notebook 的知识 Agent 工作台 | Object Graph、Operation Ledger、Knowledge Graph、Workflow Runtime、External Automation Gateway、Skill Marketplace 全贯通 | 这是终局，必须经发布级验收 |

当前 0.4.x 做得越多，越容易产生错觉：好像已有模块只是缺少 polish。实际上不是。当前 0.4.x 只是在 L2 边缘建立底座，仍然主要围绕“输入 prompt -> 得到回答 -> 点按钮”。终局必须围绕 “选择 MNObject -> 编译操作 -> 预览 Diff -> 原生写入 -> 验证 -> 接受/回滚 -> 账本证据”。

## 2. 双模式产品，不是单一聊天面板

终局必须是**双模式产品**：

- **Chat Mode**：对标 MarginNote 自带 AI 的轻量阅读对话。它保留输入框、上下文可见、选区解释、全文提问、卡片草稿、脑图草稿、队列、停止、新对话和历史。它负责低摩擦入口。
- **Agent Workspace Mode**：面向真实知识结构的生产工作台。它围绕当前 `MNObject`、Object Browser、Object Graph、Mindmap Studio、Card Factory、Workflow Builder、Operation Ledger Explorer、Knowledge Graph Studio、Skill Center 和外部自动化运行。它负责可验证写入。

两个模式要通过明确的信息架构分开，而不是把设置、日志、脑图、工作流、技能全部塞回聊天页。终局 UI 必须有明确的模式状态：

- `modeSwitchBar`
- `chatModeButton`
- `agentWorkspaceModeButton`
- `modeIntentLine`
- `activeProductMode`
- `lastWorkspacePane`
- `Workspace Navigator`
- `workspaceNavigator`

Chat Mode 的回答下面可以有后续动作，例如“生成脑图树”“生成卡片”“转入 Agent Workspace”。但一旦动作会修改真实 MN 对象，就必须进入 Agent Workspace Mode 的工作流，而不是在聊天流里悄悄完成。

## 3. 当前 0.4.x 已有底座，但不是终局

本节只记录已有底座，目的不是证明终局接近完成，而是避免把已有功能误读为完成态。

当前 0.4.x 已经有：

- `MNObject Model`：`agent_plan` 能返回 `codex.mn.mnObject.v1` 和 `codex.mn.riskRegister.v1`。
- `MNObject Registry` 第一阶段：`mn_object_registry` 返回 `codex.mn.mnObjectRegistry.v1`，持久记录已见对象的 objectRef、firstSeen/lastSeen、seenCount、evidenceTypes 和 topic/book 作用域。
- Native object scan：`objectRegistryScanButton` / `扫描 MN` 调用 `request_mn_object_registry_scan`，通过 `scan_mn_objects` 接收 `mnObjectRegistryScanFinished`，并记录 `native_object_scan` 证据。
- Native mindmap cache：`mindmapTreeReadFinished` 后，原生脑图树缓存中的节点会登记为 `mnobj:note:<noteId>` / `mn_note`，保留 noteId、parentNoteId 和 nodePath。
- `object_browser`：返回 `codex.mn.objectBrowser.v1`，前端 `objectBrowserPanel` 能显示当前焦点对象、Object Graph 节点、对象活动、Operation Ledger 条目和 registry 对象，并提供 `browserAction`。
- Object Graph 第一阶段：扫描对象会进入 Object Graph，并根据 sourceRef.parentNoteId/nodePath 生成 `native_object_scan 父子边`。点击扫描对象会打开该对象图谱，点击扫描对象会打开该对象活动和账本。
- Knowledge Index 实体：实体带 `entityType/noteId/sourceRef/relations`，实体关系可转成 `knowledge_relation`。
- Native mindmap tree cache：最近一次 MN 原生脑图树缓存可带 `nativeMindmapTreeEvidence` / `mindmap_tree_cache` 证据。
- 手工关系：`object_graph_relation_save/delete` 可维护本地可编辑关系边，保存/删除事件进入 `object_graph_manual_relation`，并带 `manualRelation` 证据。
- Operation Ledger 第一阶段：`operation_ledger_list/get` 能聚合 workflow、AI 编辑事务、external gateway request 和手工对象关系事件。
- Mindmap Studio 第一阶段：已有 `Mindmap Studio`、读取现有脑图、预览 Diff、应用所选、验证事务、回滚事务。它不是回答下方按钮的别名。
- Card Factory 第一阶段：`generate_card` 返回 `codex.mn.cardFactory.v1`、`cardType`、`learningGoal`、`reviewPrompt`、来源 `source` 和 `codex.mn.cardFactoryCard.v1`，并显示 `卡片工厂` 摘要。
- Workflow Runtime 第一阶段：已有 workflow start/status/list/cancel、外部 workflow start、`codex.mn.workflowRunInspector.v1` 和 `workflow_retry_step`。
- Skill Marketplace 第一阶段：已有本地技能 manifest 和安装状态。

这些底座改变了工程方向，但还没有形成终局。终局必须和当前版本拉开的可见断层是：真实对象浏览、真实脑图编辑、跨 notebook 知识层、复习闭环、残留验证、外部权限网关和技能生态。

## 4. 终局必须和当前版本拉开的可见断层

| 维度 | 当前 0.4.x | 终局 v3.0 |
| --- | --- | --- |
| 主入口 | 对话页为主，工作台是雏形 | Chat Mode 与 Agent Workspace Mode 信息架构分离 |
| 产品中心 | prompt、回答、草稿和按钮 | `MNObject`、operation plan、Diff、native apply、verify、rollback |
| 脑图 | 生成树、补到当前、第一阶段 Diff | 真实脑图工作台：读取现有 noteId 和父子关系，原地 create/update/merge/move/link/delete_suggest |
| 卡片 | 把回答拆成短卡，并做质量提示 | Card Factory：按学习目标、卡型、来源、重复度、覆盖率和复习状态规划 |
| 对象 | 当前对象和第一阶段 registry | Finder 式 Object Browser，浏览完整 notebook 对象和外部对象 |
| 知识 | 当前文档、上传文件、轻量 Knowledge Index | 跨 notebook 知识层，显式维护支持、反驳、对比、先修和复习关系 |
| 自动化 | 队列、workflow 雏形、本地外部接口 | External Automation Gateway，所有外部调用都进入权限、dry-run、ledger 和 callback |
| 信任 | 状态消息、日志、事务中心雏形 | Operation Ledger Explorer，证明改了哪里、能否撤回、回滚后是否残留 |
| 扩展 | 自定义 prompt、本地技能雏形 | Skill Marketplace，技能声明 schema、UI、权限、rollback、验收和版本迁移 |

当前 0.4.x 做不到的事，不能用“已经有对象区”“已经有 workflow 区”“已经有 ledger 面板”来掩盖。v3.0 必须保留一个硬判断：如果用户的高阶工作仍只能靠输入一句话再点回答下方按钮，就不是终局。

v3.0 的硬边界：

- 能像 Finder 一样浏览 notebook 对象，而不是只看当前消息聚合。
- 能原地编辑真实现有脑图，而不是重新生成一棵相似的新树。
- 复习队列和覆盖率是 Card Factory 的必选闭环。
- 外部自动化不能绕过 dry-run、确认、ledger 和回滚。
- 技能包不是自定义 prompt。

## 5. 终局必须出现的九个一等界面

### 5.1 Knowledge Console

Knowledge Console 是 Agent Workspace Mode 的首页，不是设置页，也不是聊天页底部状态块。它显示当前焦点对象、来源、上下文授权、风险、可执行动作、最近事务、待确认写入和残留状态。

它必须回答五个问题：

- 我现在在操作哪个对象？
- AI 能看见哪些内容？
- 这个对象和哪些卡片、脑图、摘录、文档、workflow 有关系？
- 接下来能执行什么动作？
- 已经发生过哪些写入，能不能撤回？

### 5.2 Object Browser

Object Browser 要像 Finder 一样浏览 notebook 对象，而不是只聚合当前消息附近的东西。它至少覆盖：

- notebook
- document
- PDF 选区和摘录
- 高亮
- card
- mindmap node
- mindmap subtree
- external file
- external request
- workflow run
- operation ledger item
- skill output

终局 Object Browser 必须以 `MNObject Registry` 为底座，并能结合实时 MN 原生对象。用户应该能按文档、类型、来源、最近活动、是否可写、是否有残留风险过滤对象，并把任意对象拖入 workflow 或技能输入。

### 5.3 Object Graph

Object Graph 负责展示对象关系。它必须能显示：

- `belongs_to`
- `contains`
- `derived_from`
- `supports`
- `contradicts`
- `compares_with`
- `reviews`
- `manual_relation`
- `knowledge_relation`

终局 Object Graph 不只是图形展示。它必须能从对象关系生成下一步动作：补来源、合并重复卡、生成对比卡、建立先修关系、重组脑图、加入复习队列。

### 5.4 Mindmap Studio

Mindmap Studio 是真实脑图工作台，不是 Markdown 大纲生成器。

它必须：

- 读取当前真实脑图或选中子树。
- 保留 noteId、父子关系、标题、正文、颜色、标签、来源和文档绑定。
- 显示 create/update/merge/move/link/delete_suggest Diff。
- 支持逐节点编辑标题和正文。
- 支持逐节点接受、拒绝、移动、合并和删除建议。
- 删除走二次确认。
- 拒绝或回滚后证明 outline、实体卡片、链接关系和复习队列是否残留。
- 不因“重新生成脑图”而复制第二棵重复树。

终局里的“生成脑图”默认不是新建一棵树，而是先读取目标脑图，再判断是补全、重组、合并还是新建。若当前文章没有目标脑图，必须在页面最上面选择目标脑图或创建新脑图，不能默默写到其他地方。

### 5.5 Card Factory

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

每张卡必须只讲一个知识点，有来源 `source`，有 `cardType`、`learningGoal`、`reviewPrompt`，正文适中，可进入复习队列，可与脑图节点、摘录和概念实体建立关系。终局还必须有跨对象去重、替换/合并、覆盖率、复习排程和来源闭环。

### 5.6 Knowledge Graph Studio

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

### 5.7 Workflow Builder

Workflow Runtime 不是队列。队列只说明“后面还有任务”；workflow 说明“这项知识操作由哪些步骤组成，每步输入输出是什么，哪里需要确认，失败后如何恢复”。

Workflow Builder 必须支持：

- 手动、选区、节点、PDF 缓存完成、外部 API、定时复习触发。
- pending、running、waiting_confirmation、failed、cancelled、verified、rolled_back 状态。
- 暂停、恢复、取消、重试、等待用户确认。
- 每一步的输入对象、输出对象、模型输出、原生动作、失败原因和下一步。
- 导出运行报告。

### 5.8 Operation Ledger Explorer

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

终局必须能证明“AI 到底改了哪里、还能不能撤回、撤回后还剩什么”。

### 5.9 Skill Center

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

技能包必须分为只读技能、写入技能、删除/回滚技能。写入和删除技能默认需要确认，并进入 Operation Ledger。

## 6. 六个不可替代系统层

v3.0 必须由六个系统层支撑。缺少任何一个，产品都会退回 `AI Chat + MN Actions`。

### 6.1 Object Graph

Object Graph 把 MN 内外所有对象建成统一图谱。它依赖 `MNObject Registry`、稳定 identifiers、sourceRef、relations、availableActions 和 permissionBoundary。

硬验收：用户能点开任意对象，看到来源、关系、历史、权限和下一步动作，而不是只看到当前文档名。

### 6.2 Operation Ledger

Operation Ledger 记录所有写入和可审计动作。

硬验收：拒绝或回滚后，系统必须显示哪些 outline 被删、哪些实体卡片被删、哪些 noteId 仍可能残留、为什么残留、下一步怎么修复。

### 6.3 Knowledge Graph

Knowledge Graph 维护长期知识关系，不负责把全文偷偷塞进 prompt。

硬验收：跨文档回答必须列出来源对象和授权范围，用户可清空或禁用 notebook 级知识索引。

### 6.4 Workflow Runtime

Workflow Runtime 把一次性 prompt 变成可恢复、可验证、可确认的知识操作流程。

硬验收：一个“精读全文并生成脑图和卡片”的长任务中断后，用户能看到完成到哪一步、等待哪个确认点、失败在哪里、是否已经写入、能否继续或回滚。

### 6.5 External Automation Gateway

External Automation Gateway 把 URL API、x-callback-url、快捷指令、浏览器脚本、CLI 和其他本地 Agent 接入同一套对象、权限、workflow、ledger 和 callback 证据。

硬验收：外部调用不能直接写 MarginNote。它只能创建 agentOperation 或 workflow run，并经过 dry-run、确认点、native apply、verify 和 callback。

### 6.6 Skill Marketplace

Skill Marketplace 管理技能包安装、运行、升级、禁用和审计。

硬验收：至少能安装一个只读技能和一个写入型技能；写入型技能必须声明 schema、UI、权限、rollback 和验收规则。

## 7. Operation Compiler 与 Agent Operation

终局里，AI 的主要输出不是 Markdown 回答，而是结构化 `agentOperation`。回答可以存在，但写入必须通过 Operation Compiler 变成强约束操作。

```json
{
  "schema": "codex.mn.agentOperation.v1",
  "object": {
    "objectId": "mnobj:selection:...",
    "kind": "selection",
    "title": "PDF 选区",
    "identifiers": {
      "topicid": "T1",
      "bookmd5": "B1",
      "noteId": "",
      "page": 12
    },
    "sourceRef": {
      "quote": "selected evidence...",
      "mnLink": "marginnote4app://..."
    }
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

Operation Compiler 必须负责 schema 检查、上下文范围检查、权限检查、native capability dry-run、Diff 生成、confirmation point 生成、rollback plan 生成和 verification plan 生成。

## 8. 典型终局工作流

| 工作流 | 用户入口 | Agent 链路 | 成功标准 |
| --- | --- | --- | --- |
| 全文精读到目标脑图 | Chat Mode 提问后升级到 Agent Workspace，或在 Workspace 选择文档和目标脑图 | PDF 缓存 -> 章节解析 -> 读取现有脑图 -> 章节级 Diff -> Card Factory -> dry-run -> 用户确认 -> 写入 -> 验证 -> 复习队列 | 覆盖全文主要章节；来源覆盖可审计；拒绝后 outline 和实体卡片可证明删除 |
| 重组现有脑图 | 选中脑图子树，进入 Mindmap Studio | 读取子树 -> 检测重复/过深/孤立 -> move/merge/update/delete_suggest Diff -> 逐节点确认 -> 原地修改 | 不创建第二棵重复脑图，原树结构被可验证地重排 |
| 选区变复习材料 | 选中 PDF 段落，Chat Mode 制卡或 Workspace Card Factory | 解释选区 -> 生成类型化短卡 -> 来源覆盖审计 -> 写入指定位置 -> 加入复习队列 | 每张卡一个知识点，有来源、有复习价值、无超长卡 |
| 跨文档关联 | 在 Knowledge Graph Studio 授权 notebook 检索 | 取相关对象 -> 生成支持/反驳/对比关系 -> 可选创建链接卡或对比子树 | 回答列出 noteId、页码或 quote，新增关系可查看和撤销 |
| 外部自动化精读 | 快捷指令或脚本 POST workflow | Gateway 认证 -> 创建 workflow run -> dry-run -> 等待确认 -> 写入 -> callback success/error | 外部调用不能绕过权限；requestId、caller、callback、ledger 和验证证据完整 |
| 技能包运行 | Skill Center 安装并运行技能 | 校验 manifest -> 绑定对象 -> 预览步骤 -> 执行 workflow -> 写入/验证/报告 | 技能可复用、可卸载、可升级；写入型技能必须可回滚 |

## 9. 实现路线：从 0.4.x 到 v3.0

### Phase A: 双模式壳层

目标：把 Chat Mode 和 Agent Workspace Mode 从信息架构上分开。

完成标准：

- Chat Mode 保持 MN4 自带 AI 式连续对话。
- Agent Workspace Mode 有独立入口、对象首页、工作台导航和空状态。
- Chat 回答可以一键升级为 agentOperation，而不是只露出回答按钮。

### Phase B: Object Registry

目标：把当前临时对象引用升级为持久 `MNObject Registry`。

完成标准：

- 所有出现过的选区、摘录、高亮、卡片、脑图节点、文档、notebook、外部文件都有稳定 objectId。
- registry 记录 firstSeen、lastSeen、sourceRef、identifiers、relations、permissionBoundary 和 evidenceTypes。
- Object Browser 从聚合列表升级为 registry + live MN 原生对象浏览。

### Phase C: Mindmap Studio

目标：把脑图从“生成树”升级为“编辑真实现有树”。

完成标准：

- 读取当前脑图和选中子树时能得到 noteId、父子关系、标题、正文、来源、颜色、标签和文档绑定。
- Diff 支持 create/update/merge/move/link/delete_suggest。
- 拒绝或回滚后，能证明 outline、实体卡片、链接关系和复习队列是否仍残留。

### Phase D: Operation Ledger Explorer

目标：把事务日志升级为用户可读证据系统。

完成标准：

- 用户能按对象、文档、workflow、技能、时间、成功/失败、残留状态过滤 ledger。
- 每条 ledger 可展开原生 command、event timeline、Verification Agent 报告和 rollback evidence。
- 失败信息说明阶段、对象、是否已写入、是否可回滚和下一步。

### Phase E: Knowledge Graph Studio

目标：把 Knowledge Index 升级为跨 notebook 知识图谱。

完成标准：

- 概念、证据、对比、支持、反驳、先修、复习状态和来源回链可查看、编辑、删除。
- 跨文档回答列出引用对象和授权范围。
- 用户可以清空、导出或禁用索引。

### Phase F: Workflow Builder

目标：把队列和模板升级为可保存、可恢复、可验收 workflow。

完成标准：

- workflow 有触发器、上下文范围、步骤、确认点、权限、输出和验收规则。
- workflow run 有可视化 Inspector，能展示 queued/manual/waiting_confirmation/blocked/failed/completed、queueId、确认点、下一步动作和错误原因。
- 支持暂停、恢复、取消、重试、确认、回滚和导出报告。
- 每一步都进入对象活动和 Operation Ledger。

### Phase G: External Gateway

目标：把 URL/API 自动化升级为完整外部入口。

完成标准：

- URL API、x-callback-url、快捷指令、浏览器脚本、CLI 和其他本地 Agent 全部通过 Gateway。
- 外部调用有 requestId、caller、secret、permission、objectRef、callback、dry-run、ledger 和 verify。
- 外部调用不能绕过确认点、删除二次确认、rollback 和 residual report。

### Phase H: Skill Marketplace

目标：把自定义 prompt 升级为可发布技能生态。

完成标准：

- 技能包声明 manifest、schema、UI、权限、rollback、验收和版本迁移。
- 支持安装、禁用、升级、卸载和审计。
- 至少一个只读技能和一个写入型技能通过发布级验收。

## 10. v3.0 发布级完成定义

v3.0 不是“能聊天、能制卡、能生成脑图”就完成。必须满足：

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

## 11. 不能混淆的边界

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
