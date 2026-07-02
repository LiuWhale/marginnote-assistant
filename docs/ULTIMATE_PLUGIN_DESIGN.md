# Codex Companion Ultimate Design: MarginNote Knowledge Agent OS

更新时间：2026-06-28
目标版本：v3.0
状态：终局产品蓝图。当前 0.4.x 是 Chat Mode + Agent Workspace 雏形，不是终局。

## 0. 结论

终局不是当前聊天插件的增强版，也不是“发送、生成脑图、生成卡片、设置、日志、队列”这套体验的加强版。终局产品必须从 AI 对话面板断代到 **MarginNote Knowledge Agent OS**。

> Codex Companion v3.0 是 MarginNote 里的可验证知识操作系统。它把文档、摘录、高亮、卡片、脑图节点、概念、复习任务、外部文件、workflow、技能和自动化请求统一成可浏览、可编辑、可验证、可回滚的知识对象系统。

这句话的重点不是“AI 更会回答”，而是“知识对象可操作”。当前 0.4.x 的主语仍然是 prompt、回答和按钮；v3.0 的主语必须是真实 MarginNote 对象、对象关系、工作流、事务证据和学习覆盖。

终局路线是 **知识编辑工作台 + 自动学习代理**。它仍然是双模式产品，但两个模式职责必须分清：

- `Chat Mode` 用于轻量问答、解释选区、输入自然语言意图。
- `Agent Workspace Mode` 是生产系统，用于对象浏览、真实脑图编辑、卡片覆盖、知识图谱、workflow、技能和账本。
- 聊天是入口，不是终局；Agent Workspace 才是生产系统。
- 产品原则是对象优先、操作优先、证据优先。
- 不得把现有控件堆叠当作终局。
- 只要首屏仍然像聊天框加按钮，就不算终极版。

更直接地说，终极版第一眼不能像“更好看的聊天插件”。它应该像一个在 MarginNote 内运行的 Notebook IDE：左侧是 notebook/source/object 导航，中间是 Mindmap Studio、Card Factory、Knowledge Graph、Workflow Board 等生产工作台，右侧是对象 Inspector、Diff、来源、证据和回滚，底部才是 Command Pane。

## 1. 产品断代路线

| 代际 | 第一眼像什么 | 用户主要操作 | 典型能力 | 不能冒充什么 |
| --- | --- | --- | --- | --- |
| v0.4.x Chat Companion | 聊天面板加工具入口 | prompt、回答、草稿、状态 | 问答、短卡、脑图草稿、配置、缓存、日志 | 不能叫知识工作台 |
| v1.x Study Copilot | 稳定阅读和制卡助手 | 当前材料、选区、目标脑图 | 对标 MN4 自带 AI，稳定全文读取，生成结构化脑图和短卡 | 不能叫原生对象编辑器 |
| v2.x Native Knowledge Editor | MN 原生知识编辑器 | noteId、真实脑图节点、卡片、摘录、Diff | 原地读取、合并、移动、删除建议、回滚和残留证明 | 不能叫全局 Knowledge OS |
| v3.x Notebook Knowledge OS | Notebook Knowledge IDE | notebook 对象图、知识图谱、学习目标、workflow、技能、ledger | 自动精读、重组知识结构、跨文档关联、外部自动化、技能运行、可验证回滚 | 这是终局 |

当前 0.4.x 是 Chat Mode + Agent Workspace 雏形。当前 0.4.x 不是终局。它可以作为迁移脚手架，但不能用来证明 v3 完成。

终局必须和当前版本拉开的可见断层是：用户打开 notebook 后，不发消息也能看到来源清单、真实 MN 对象、现有脑图结构、卡片覆盖、复习缺口、失败事务、推荐 workflow 和回滚证据。当前 0.4.x 做不到的事不能用已有对象区、workflow 区或 ledger 区来掩盖。当前版本还不能稳定浏览整个 notebook 对象库，不能完整原地重构复杂脑图，不能证明所有实体卡片和关系残留，也不能把技能、复习、外部自动化和跨文档知识全部纳入同一个证据系统。

## 2. v3 产品合约

v3 产品合约用来判断设计是否退回当前插件增强版。

### 2.1 第一屏合约

第一屏必须是 `Notebook Knowledge IDE`，不是聊天记录。它要显示来源、真实 MN 对象、现有脑图、卡片覆盖、复习缺口、workflow、失败事务、验证报告和下一步动作。用户不需要先发 prompt 才知道能做什么；工作台应先识别当前对象，再给出这个对象能安全进入的工作面。

默认入口必须能在 Chat Mode 和 Agent Workspace Mode 之间切换，但 v3.0 的默认落点应是 Agent Workspace Mode。Chat 输入只能是 Command Pane，不能占据产品中心。

第一屏必须有可见的 `Knowledge OS Contract`，把产品明确分成对象层、操作层和证据层：

- 对象层：`MNObject`、来源、选区、脑图节点、卡片和关系。
- 操作层：operation plan、Diff、workflow、skill 和确认点。
- 证据层：Verification、Operation Ledger、rollback 和 residual proof。

这个契约必须出现在模式切换和 Command Pane 之前。用户第一眼应该知道自己进入的是 MarginNote 知识工作台，而不是聊天增强版。聊天区只能作为命令入口，不能成为默认视觉中心。

### 2.2 对象合约

所有功能必须围绕可寻址对象运行：`MNObject`、`noteId`、摘录、高亮、卡片、脑图节点、workflow run、ledger item、skill output、external request。回答文本不是系统事实来源，只能是意图或草稿。

从回答按钮升级到对象操作，意味着每个对象都必须回答四件事：

- 它是什么：类型、标识、来源、权限边界。
- 它和谁有关：父子、引用、派生、支持、反驳、对比、复习关系。
- 它能做什么：读材料、浏览 MN 对象、整理脑图、制卡、启动 workflow、运行技能、验证回滚。
- 它有什么证据：原生对象扫描、脑图树缓存、来源摘要、事务、回滚、残留证明。

### 2.3 操作合约

AI 不能直接“生成结果并写入”。任何写入必须变成 operation plan，并经过 dry-run、Diff、用户确认、native apply、verify、ledger、rollback/residual proof。缺任何一环都只能叫预览或草稿。

### 2.4 学习合约

卡片和脑图不是内容输出，而是学习资产。系统必须维护覆盖率、来源、重复、复习队列、知识关系和缺口。复习队列和覆盖率是 Card Factory 的必选闭环，不能只把一段回答切成多张卡或一棵树。

### 2.5 证据合约

日志不是证据。证据必须能回答：哪个对象被改了、原生 noteId 是什么、MarginNote 是否仍存在、拒绝后残留在哪里、能否自动修复。无法证明时状态必须是 `UNKNOWN`，不能显示成功。

### 2.6 扩展合约

技能包不是自定义 prompt。技能必须声明 schema、权限、UI、输入输出、dry-run、rollback、acceptance 和版本迁移。外部 URL/API 自动化只能创建受控 workflow，不能绕过 dry-run、确认、ledger 和回滚。

如果一个版本的主要体验仍然是“问一句、看回答、点生成卡片/脑图、去设置里修问题”，它最多是 Study Copilot，不是 v3。如果用户的高阶工作仍只能靠输入一句话再点回答下方按钮，就不是终局。

如果双模式壳层退化成 AI Copilot 面板，用户看起来能问、能生成、能点按钮，但知识结构仍没有被对象化、事务化和证据化。

## 3. 终局第一屏

v3 第一屏必须直接暴露 notebook 的知识状态，而不是等用户发 prompt 后才解释能做什么。建议布局如下：

| 区域 | 终局职责 | 第一眼必须看到 |
| --- | --- | --- |
| Notebook Navigator | notebook、文档、来源、选区、脑图页、卡片组和技能包入口 | 当前 notebook 的对象范围和授权边界 |
| Knowledge Console | notebook 级状态面板 | source coverage、object coverage、mindmap baseline、card coverage、workflow runs、ledger risk |
| Object Canvas | 当前对象生产区 | Object Browser、Mindmap Studio、Card Factory、Knowledge Graph、Workflow Builder 的入口和当前对象 |
| Inspector | 对象详情与证据 | `noteId`、page、quote、来源、权限、Diff、verification、rollback |
| Command Pane | 自然语言意图输入 | 输入 prompt，但不会遮住对象状态 |

这和当前形态的区别很硬：当前形态是“先问再做”，终局是“先识别对象，再提出可执行工作面”。当前形态的回答是内容中心，终局的 `MNObject` 是内容和动作中心。

## 4. 终局对象系统

v3 的核心不是更多按钮，而是完整对象模型。对象系统至少包括：

- `source`: 当前文档、PDF 缓存、上传文件、路径根、网页、外部文档。
- `mn_object`: note、excerpt、highlight、card、mindmap node、subtree、document、notebook。
- `knowledge_object`: concept、claim、method、formula、evidence、limitation、comparison、review item。
- `operation_object`: operation plan、Diff、transaction、rollback proof、verification report。
- `runtime_object`: workflow run、skill run、external request、callback、ledger item。

每个对象都必须有 `objectId`、kind、identifiers、sourceRef、relations、permissions、availableActions 和 evidence。没有对象 ID 的回答只能作为草稿，不能成为系统事实。

## 5. 体验断代：终局工作台

### 5.1 Knowledge Console

Knowledge Console 是 Agent Workspace Mode 的首页。它不是设置页，也不是聊天页底部状态块。

它必须回答：

- 当前操作对象是谁？
- AI 可见哪些内容？
- 材料、脑图、卡片、复习、workflow、ledger 的覆盖情况如何？
- 有哪些缺口和风险？
- 接下来可以执行什么 workflow？
- 最近有哪些失败、待确认写入和残留对象？

当前的 Knowledge Console Matrix 只能算第一阶段形态。终局要把它升级为可执行知识资产仪表盘：对象覆盖、来源覆盖、脑图基线、卡片覆盖、workflow runtime、Operation Ledger 和验证证据都应该能从这里进入。

### 5.2 Object Browser

Object Browser 必须像 Finder 一样浏览 notebook 对象，而不是只聚合当前消息附近的对象。它以 `MNObject Registry` 为底座，并融合实时 MN 原生对象。

终局 Object Browser 需要做到：

- 浏览完整 notebook 对象，而不是只显示当前回答、当前选区或最近缓存。
- 用 `noteId`、page、quote、document、parent/child、tag、card type 和 workflow evidence 筛选。
- 对每个对象直接打开图谱、活动、账本、来源、复习状态和可用 workflow。
- 没有原生扫描证据时会请求扫描 MN 对象；扫描证据存在后会直接打开 Object Browser。

迁移期可以保留 `object_browser`、`open_object_browser`、`mn_object_registry`、`codex.mn.mnObjectRegistry.v1`、`codex.mn.objectBrowser.v1`、`mnobj:note:<noteId>`、`objectRegistryScanButton`、`request_mn_object_registry_scan`、`scan_mn_objects`、`mnObjectRegistryScanFinished`、`native_object_scan` 和 `扫描 MN` 等运行态入口，但这些名字不是终局验收标准。终局验收看的是用户能否像 Finder 一样浏览 notebook 对象。

### 5.3 Object Graph

Object Graph 展示对象关系，并从关系生成下一步动作。关系至少包括：

- `belongs_to`
- `contains`
- `derived_from`
- `supports`
- `contradicts`
- `compares_with`
- `reviews`
- `manual_relation`
- `knowledge_relation`

第一阶段实体应能表达 Knowledge Index 实体、`entityType/noteId/sourceRef/relations`、`nativeMindmapTreeEvidence`、`mindmap_tree_cache`、`object_graph_relation_save/delete`、`object_graph_manual_relation`、`manualRelation` 和可编辑关系边。

Object Graph 不是只画图。它应该能产生动作：补来源、合并重复卡、创建对比卡、建立先修关系、重组脑图、加入复习队列、打开 Operation Ledger 证据。扫描对象会进入 Object Graph；扫描对象会显示为 `mn_note`，并能形成 `native_object_scan 父子边`。点击扫描对象会打开该对象图谱；点击扫描对象会打开该对象活动和账本。

### 5.4 Mindmap Studio

Mindmap Studio 是真实脑图工作台，不是回答下方按钮的别名。

它必须读取当前真实脑图和选中子树，拿到 noteId、父子关系、标题、正文、来源、颜色、标签和文档绑定。AI 操作表现为节点级 Diff：新增、改名、改正文、移动、合并、建立链接、建议删除。用户能逐节点接受、拒绝、拖动、合并和回滚。重复生成不能产生第二棵重复树。

硬验收：能原地编辑真实现有脑图，而不是重新生成一棵相似的新树。

已有脑图树缓存后会直接打开 Mindmap Studio；没有缓存时才读取现有树。`mindmapTreeReadFinished`、`open_mindmap_studio` 和 `mindmap_tree_cache` 可以作为迁移期证据，但 v3 验收必须看真实 noteId 树能否原地修改和回滚。

### 5.5 Card Factory

Card Factory 不是“把回答切成卡片”。它负责学习覆盖和复习系统。

每张卡必须有 `codex.mn.cardFactory.v1` 或后续 schema 下的卡型、来源、learningGoal、reviewPrompt、章节或概念覆盖、质量风险和复习状态。卡片工厂要能发现缺来源、太长、重复、无复习价值、与脑图脱节的问题。

卡型至少包括概念卡、公式卡、方法卡、证据卡、对比卡、局限卡、复习题卡。

卡片覆盖` 轴会打开 Card Factory。这个迁移期说法不能被误读为终局：终局 Card Factory 必须维护覆盖率、去重、复习队列和替换/合并策略，而不只是打开卡片列表。

### 5.6 Knowledge Graph Studio

Knowledge Graph Studio 是跨 notebook 知识层。用户授权多个文档、课程或项目后，能看到概念之间的支持、反驳、对比、先修、复习关系。跨文档回答必须展示 noteId、page、quote 或 MN link，不能只给自然语言总结。

这层要借鉴 Obsidian bridge 的回链思想、MarginNote 深链、Zotero Connector 的同步元数据和字段模板思想，但必须保持 MarginNote 对象、来源和权限边界。

### 5.7 Workflow Builder

Workflow Builder 是可视化流程，不是队列。它需要能拖拽、保存、复用、迁移、验收和导出 workflow。

启动候选必须继续经过 Workflow Runtime，不能绕过确认点和账本。Object Task Composer`，把对象路线转成任务草案和 workflow 候选；Workflow Builder 再把这些候选升级成可保存、可恢复、可审计的流程。已有 run 后会直接打开 Workflow Builder。

### 5.8 Operation Ledger Explorer

Operation Ledger Explorer 是用户可读证据系统。它必须按对象、文档、workflow、技能、时间、成功/失败、残留状态过滤 ledger。

每条 ledger 应能展开 operation plan、dry-run/apply path、原生命令、原生事件线、native apply、rollback/residual、workflow 确认点、外部 callback 证据和手工关系证据。

### 5.9 Verification Studio

Verification Studio 是最终信任层。它不是日志页，也不是“运行态采证”。它要把 Verification Agent 的报告按对象组织起来，解释哪些已经 PASS，哪些 FAIL，哪些 UNKNOWN，哪些可以自动修复，哪些需要用户重新授权或手动处理。

缺少 native probe 时不能把 Companion 日志冒充成功。Verification Studio 必须能按对象、workflow、技能和时间线解释证据。

### 5.10 Skill Center

Skill Center 是可分享能力市场。用户能安装“精读 VLA 论文”“综述对比”“公式卡生成”“答辩稿”“实验表格审计”等技能。技能不是自定义 prompt；它必须声明输入 schema、权限、UI、dry-run、rollback、acceptance 和版本迁移。

Skill Marketplace 是产品面，不是 prompt 收藏夹。

## 6. 架构断代：七个系统内核

v3 的架构不是“Web 面板 + Companion + 一组 action”。它应该是七个内核支撑的知识操作系统。

| 内核 | 终局职责 | 失败状态 |
| --- | --- | --- |
| Live MN Object Kernel | 把 notebook、document、excerpt、highlight、card、mindmap node、subtree、workflow、ledger、skill output 统一成可寻址对象 | 只能处理当前消息附近内容 |
| Source Registry | 在模型调用前证明材料是否真实可读 | 回答后才说找不到 PDF |
| Operation Compiler | 把自然语言、按钮、技能和外部请求编译为 operation plan | AI 回答直接写入 |
| Transactional Native Editor | 负责 create/update/merge/move/link/delete_suggest、apply、verify、rollback、residual proof | 拒绝只删 outline 或只看日志 |
| Workflow Runtime | 保存、恢复、暂停、确认、重试、验收长任务 | 只有 pending 队列 |
| Skill Runtime | 管理 manifest、schema、权限、UI、dry-run、rollback、acceptance、迁移 | 自定义 prompt 冒充技能 |
| Verification Agent | 产出 PASS、FAIL、UNKNOWN 和修复建议 | 不足证据仍显示成功 |

## 7. External Automation Gateway

External Automation Gateway 借鉴 MarginNote URL API、深链、x-callback-url、Shortcuts、Raycast、本地 CLI、浏览器扩展、Zotero、Obsidian 和文件夹监控。目标不是让外部脚本直接控制 MarginNote，而是把外部入口接入同一套对象、权限、workflow、ledger 和 callback 证据。

可借鉴方向：

- MarginNote URL API 和深链：用于定位 notebook、document、note、excerpt、card 和回跳。
- x-callback-url：用于外部自动化的 success/error 回调。
- Obsidian bridge：用于回链、摘录导入、树状导入和模板化输出。
- Zotero Connector：用于双向同步、字段模板、批量推送、冲突恢复和限流退避。
- 插件开发文档 MCP：用于把 API 文档发现和全文读取做成开发期知识源。

Gateway 的硬规则：

- 外部调用不能直接写 MarginNote。
- 外部请求只能创建 `agentOperation` 或 workflow run。
- 每个请求必须有 requestId、caller、permission、objectRef、contextPolicy、callback 和 ledger。
- 写入前必须经过 dry-run、确认点、native apply、verify。
- 删除和回滚必须二次确认。
- callback success/error 必须回写 Operation Ledger。

外部自动化不能绕过 dry-run、确认、ledger 和回滚。

## 8. 数据断代：数据模型

### 8.1 MNObject

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

### 8.2 Agent Operation

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
  }
}
```

### 8.3 Operation Transaction

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

### 8.4 Skill Manifest

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

## 9. 能力断代

| 工作流 | 用户入口 | Agent 链路 | 成功标准 |
| --- | --- | --- | --- |
| 全文精读到目标脑图 | Workspace 选择文档和目标脑图，或 Chat Mode 提问后升级为 workflow | Source Registry -> 章节解析 -> 读取现有脑图 -> 章节级 Diff -> Card Factory -> dry-run -> 用户确认 -> 写入 -> 验证 -> 复习队列 | 覆盖全文主要章节；来源覆盖可审计；拒绝后 outline 和实体卡片可证明删除 |
| 重组现有脑图 | 选中脑图子树，进入 Mindmap Studio | 读取子树 -> 检测重复/过深/孤立 -> move/merge/update/delete_suggest Diff -> 逐节点确认 -> 原地修改 | 不创建第二棵重复脑图，原树结构被可验证地重排 |
| 选区变复习材料 | 选中 PDF 段落，进入 Card Factory | 解释选区 -> 类型化短卡 -> 来源覆盖审计 -> 写入指定位置 -> 加入复习队列 | 每张卡一个知识点，有来源、有复习价值、无超长卡 |
| 跨文档关联 | Knowledge Graph Studio 授权 notebook 检索 | 取相关对象 -> 生成支持/反驳/对比关系 -> 可选创建链接卡或对比子树 | 回答列出 noteId、页码或 quote，新增关系可查看和撤销 |
| 外部自动化精读 | URL/API/Shortcuts/Raycast/CLI 创建 workflow run | Gateway 认证 -> 创建 workflow run -> dry-run -> 等待确认 -> 写入 -> callback success/error | 外部调用不能绕过权限；requestId、caller、callback、ledger 和验证证据完整 |
| 技能包运行 | Skill Center 安装并运行技能 | 校验 manifest -> 绑定对象 -> 预览步骤 -> 执行 workflow -> 写入/验证/报告 | 技能可复用、可卸载、可升级；写入型技能必须可回滚 |

## 10. 终局反证清单

以下任何一条成立，都说明它不是 v3：

- 如果第一屏仍然需要用户先提问，失败。
- 如果脑图仍然以生成新树为主，失败。
- 如果卡片仍然以回答切块为主，失败。
- 如果拒绝后只能相信日志，失败。
- 如果技能仍然只是 prompt 收藏，失败。
- 如果长任务仍然只是 pending 队列，失败。
- 如果外部自动化能绕过 dry-run、确认点或 ledger，失败。
- 如果跨文档回答不给对象引用、页码、quote 或 MN link，失败。
- 如果缺少 native probe 时仍显示成功，失败。
- 如果用户不能按对象查看发生了什么，失败。

当前预览版 UI 功能验收只证明不退化，不证明 v3 完成。它可以证明任意文档 payload 下工作台能渲染、按钮能路由、基础 native bridge action 能发出；它不能证明真实 MN 原生对象浏览、原地编辑、跨对象验收、残留清理和跨文档知识图谱已经完成。

## 11. v3.0 硬验收

终局验收不按按钮数量算，而按对象覆盖、操作闭环、学习闭环和证据闭环算。

| 验收项 | 终局要求 | 不合格表现 |
| --- | --- | --- |
| 主入口 | 默认进入 Notebook Knowledge IDE，Chat 是辅助入口 | 首屏仍是聊天框加按钮 |
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

## 12. 实现路线

### Phase A: Study Copilot 稳定化

目标：先把 v1.x 做成对标 MN4 自带 AI 的可靠助手。全文读取、选区解释、短卡、结构化脑图、目标脑图选择、缓存状态、历史、设置、AI 后端、更新、日志和错误提示必须稳定。

完成标准：普通用户可以把它当成日常阅读助手，而不是开发者调试面板。

### Phase B: Native Knowledge Editor

目标：进入 v2.x。读取真实现有脑图和 noteId，支持 create/update/merge/move/link/delete_suggest Diff，拒绝后能证明实体卡片和 outline 是否残留。

完成标准：用户能原地编辑当前脑图，不再靠重复生成新树。

### Phase C: Object and Source Kernel

目标：把对象和来源统一成 registry。当前文档、PDF 缓存、上传文件、路径映射、OneDrive/iCloud、本地文件根、外部 URL 和 MN 原生对象都进入同一对象系统。

完成标准：模型调用前能证明材料是否可读，任意对象都能成为 workflow 输入。

### Phase D: Workflow and Skill Runtime

目标：把长任务和技能包变成可保存、可恢复、可验收的运行系统。workflow 有确认点、失败恢复和验收报告；技能有 manifest、权限和回滚规则。

完成标准：精读、重组、综述对比、复习计划、导出报告都能作为 workflow 保存、继续、取消、重试和审计。

### Phase E: Knowledge Graph and Verification Studio

目标：把跨文档知识和证据系统做成终局产品面。Knowledge Graph Studio 维护概念、证据、对比、支持、反驳、先修和复习关系；Verification Studio 证明每次 AI 操作的真实状态。

完成标准：用户能从任意对象追溯来源、关系、写入、失败、回滚、残留和下一步修复。

### Phase F: External Automation Gateway

目标：把 URL API、Shortcuts、Raycast、CLI、浏览器扩展、Zotero、Obsidian 和文件系统 watcher 都接入受控 gateway。

完成标准：外部请求只能创建 workflow 或 agent operation，不能绕过权限、dry-run、确认点、ledger 和验证。

## 13. 当前 0.4.x 的位置

0.4.x 不是终局，但它提供了可迁移脚手架：

- Chat Mode 与 Agent Workspace 的双模式壳层。
- Command Pane 与工作台开始分离。
- Knowledge Console Matrix、Object Intake、Object Task Composer、Workflow Builder Board、Source Registry、Study Program、Notebook Runbook 形成零输入工作台雏形。
- Object Browser、Object Graph、Mindmap Studio、Card Factory、Operation Ledger、Verification Center、External Automation Gateway 和 Skill Runtime 形成第一阶段 product surface。
- Operation Compiler、Workflow Runtime、Transactional Native Editor 和 Verification Agent 形成第一阶段操作闭环。

这些能力是迁移方向，不是完成证明。后续每个版本都必须让对象更真实、写入更可证、学习闭环更完整、外部入口更受控，而不是继续在聊天页上堆按钮。

## 14. 当前到终局的差异表

| 维度 | 当前 0.4.x | v3.0 终局 |
| --- | --- | --- |
| 用户入口 | 先发 prompt，再看回答，再点按钮 | 打开 notebook 就看到对象状态、来源覆盖、脑图缺口、卡片缺口、workflow 和待确认事务 |
| 核心对象 | 当前消息、当前回答、当前选区 | 持久 MNObject、noteId、摘录、高亮、卡片、脑图节点、workflow run、ledger item |
| 脑图 | 生成一棵树或把回答变成树 | 读取真实现有脑图，以 noteId 做 create/update/merge/move/link/delete_suggest Diff |
| 卡片 | 把回答拆成多张卡 | 按学习目标、卡型、来源、覆盖率和复习排程管理卡片 |
| 长任务 | pending 队列、目标、停止 | Workflow Runtime，支持暂停、恢复、确认点、失败恢复、验收报告 |
| 写入 | 草稿、接受、拒绝、回滚尝试 | Transactional Native Editor：plan -> dry-run -> native apply -> verify -> accept/reject -> rollback -> residual proof |
| 证据 | 调试日志、状态消息 | Operation Ledger Explorer，按对象、workflow、技能、事务追溯每次改动 |
| 知识层 | 当前文档上下文、历史、索引 | 跨 notebook Knowledge Graph，显式授权，带 noteId/page/quote/MN link |
| 外部自动化 | 外部接口触发动作 | External Automation Gateway，外部请求只能创建 agentOperation 或 workflow run |
| 扩展 | 自定义 prompt 和按钮 | Skill Center / Skill Marketplace，技能有 manifest、schema、UI、权限、dry-run、rollback、验收和迁移 |
