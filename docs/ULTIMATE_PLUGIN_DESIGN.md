# Codex Companion Ultimate Design: MarginNote Knowledge Agent OS

更新时间：2026-06-27  
目标版本：v3.0  
状态：终局产品蓝图。当前 0.4.x 是 Chat Mode + Agent Workspace 雏形，不是终局。

## 0. 关键纠偏：终局必须换产品主语

用户看到终局设计后如果觉得“和现在功能没什么区别”，说明设计还没有把产品断层说清楚。终局不能只是继续修聊天、按钮、设置、日志、脑图生成和卡片生成。那些能力最多把当前 0.4.x 做成更稳定的 Study Copilot。

终局的主语必须从 **消息和按钮** 换成 **真实 MarginNote 对象和知识工作流**：

- 当前 0.4.x 的主语是“这条回答”。用户输入一句话，AI 输出文字，用户再点回答下方按钮。
- v1.x 的主语是“这份材料”。插件能稳定读选区/全文，能生成短卡和脑图，体验对标 MN4 自带 AI。
- v2.x 的主语是“这个 MN 对象”。插件能读取、编辑、合并、移动、删除和验证真实 noteId、脑图节点、卡片、摘录和关系。
- v3.x 的主语是“这个 notebook 的知识系统”。插件能管理对象库、知识图谱、复习队列、workflow、技能和外部自动化。

因此 v3.0 的默认首屏不能再是聊天框。即使聊天框旁边有 Object Browser、Mindmap Studio、Card Factory、Operation Ledger 和 Workflow Builder，只要用户的主要动作仍是“输入 prompt -> 等回答 -> 点生成按钮”，产品本质仍是 Chat Companion。

v3.0 必须看起来像一个 **Notebook Knowledge IDE**：

- 左侧是 notebook 对象浏览器，而不是消息历史。
- 中间是脑图/卡片/知识图谱/工作流的真实编辑区，而不是回答正文。
- 右侧或底部才是 AI 对话，用来解释、下指令、修改 plan。
- 写入入口是 operation plan、Diff、dry-run、确认点和验证报告，而不是回答下方按钮。
- 失败入口是 ledger、残留对象、回滚证明和恢复动作，而不是一条错误消息。

当前 Agent Workspace 只能作为迁移壳层，不能被当成终局。它的价值是让当前插件逐步具备对象、操作、证据和 workflow 能力；它不是 v3.0 的信息架构本身。v3.0 必须允许未来把当前聊天页降级为 command pane，把回答按钮降级为快捷命令，把当前 settings/logs/status 面板降级为系统抽屉。

### 0.1 终局选择：B + C，而不是 A

终局不走“MarginNote 自带 AI 的超强版”这条路。那条路只会得到一个更会聊天、更会生成脑图的面板，和当前 0.4.x 的差异不够大。

终局路线必须是 **B + C**：

- **B：知识编辑工作台**。主界面像 Finder、IDE 和知识数据库的混合体，中心是真实 MarginNote 对象、对象关系、脑图 Diff、卡片覆盖率、操作账本和验证结果。
- **C：自动学习代理**。代理不是漂在聊天框里的“目标”，而是在工作台里运行的 workflow。它有输入对象、计划、权限、确认点、执行日志、失败恢复和最终验收。

Chat Mode 仍然保留，但它不是终局主产品。Chat Mode 只负责快速阅读问答和把用户意图转成可执行操作。真正的终局入口是 **Notebook Workspace**：打开一个 notebook 或文档后，用户首先看到的是这份材料的知识资产、缺口、待确认编辑、复习状态和可执行工作流，而不是一个空聊天框。

这仍然是一个双模式产品：`Chat Mode` 是低摩擦对话入口，`Agent Workspace Mode` 是生产系统。聊天是入口，不是终局；Agent Workspace 才是生产系统。核心断层是从回答按钮升级到对象操作，从“能生成内容”升级到“能管理、验证、回滚真实 MarginNote 知识对象”。

终局的产品原则仍然是：对象优先、操作优先、证据优先。不得把现有控件堆叠当作终局，也不得用当前 0.4.x 的对象区、工作流区和账本区这些雏形来替代真正的 Notebook Workspace。当前 0.4.x 不是终局。

一句话定义：

> Codex Companion v3.0 是 MarginNote 里的 Notebook Knowledge OS：把文档、摘录、高亮、卡片、脑图、概念、复习、外部文件和自动化请求统一成可浏览、可编辑、可验证、可回滚的知识对象系统。

## 1. 四个不同产品，不允许混淆

| 产品代际 | 第一眼像什么 | 用户主要在操作什么 | 典型动作 | 不能冒充什么 |
| --- | --- | --- | --- | --- |
| v0.4.x AI Chat Plugin | 聊天面板加工具按钮 | prompt、回答、草稿 | 问问题、生成卡片、生成脑图、看状态 | 不能叫知识工作台 |
| v1.x Study Copilot | 稳定的阅读/制卡/脑图助手 | 当前材料、选区、目标脑图 | 对标 MN4 自带 AI；稳定全文读取；生成短卡；生成结构化脑图 | 不能叫原生对象编辑器 |
| v2.x Native Knowledge Editor | MN 原生知识编辑器 | 真实脑图节点、卡片、摘录和 Diff | 读取现有脑图、逐节点改写、合并、移动、删除、回滚、残留证明 | 不能叫全局知识 OS |
| v3.x Notebook Knowledge OS | notebook 工作台 / Knowledge IDE | notebook 对象图、知识图谱、学习目标、workflow、账本、复习系统 | 自动精读、重组知识结构、生成并排程卡片、跨文档对比、外部自动化、技能运行 | 这是终局 |

当前 0.4.x 即使已经出现 Object Browser、Mindmap Studio、Card Factory、Workflow Runtime 和 Operation Ledger，也仍然是第一代产品。原因很简单：用户仍然主要通过“输入一句话、得到回答、点击按钮”来工作。终局必须把主语换掉：

- 不是“回答下面生成脑图”，而是“当前脑图对象有哪些结构缺口，AI 提议了哪些节点级修改”。
- 不是“把回答切成卡片”，而是“这份材料的学习目标覆盖了多少，哪些概念还没有复习卡，哪些卡片重复或太长”。
- 不是“日志里有失败原因”，而是“Operation Ledger 能证明每个 MN 对象被创建、更新、删除、保留或残留”。
- 不是“一个目标持续执行”，而是“一个 workflow 在 Notebook Workspace 里有计划、状态、确认点和验收报告”。

## 2. 终局首屏：Notebook Workspace，而不是聊天页

终局打开后，默认首屏是 `Notebook Workspace`。聊天可以停靠在右侧或底部，但不能占据产品中心。

终局首屏必须包含这些区域：

- **Workspace Header**：当前 notebook、当前文档、目标脑图、授权上下文、AI 后端、MN 原生能力、缓存状态。
- **Knowledge Console**：当前材料的知识资产摘要，包括文档、摘录、高亮、脑图节点、卡片、概念、复习任务、最近 workflow 和风险。
- **Object Browser**：像 Finder 一样浏览 notebook 中的真实 MN 对象和插件对象，支持按文档、类型、标签、最近活动、残留风险、是否可写过滤。
- **Mindmap Studio**：显示真实脑图树和 AI 提议的 Diff，用户逐节点接受、拒绝、改标题、改正文、移动、合并或删除。
- **Card Factory**：显示学习目标、卡型覆盖、来源覆盖、长卡、重复卡、待复习和到期复习。
- **Workflow Console**：显示正在跑的学习代理、步骤、输入输出、确认点、失败恢复和验收报告。
- **Operation Ledger**：显示所有写入和外部请求的证据链，支持按对象追踪、回滚和残留检查。

Chat Mode 的定位：

- 可以解释选区、回答全文问题、把自然语言意图编译成 operation plan。
- 可以提供“转入工作台执行”的按钮。
- 不能绕过 workspace 直接修改真实 MN 对象。
- 不能把回答下方的小按钮当成高阶工作流的主要入口。

如果双模式壳层退化成 AI Copilot 面板，用户看起来能问、能生成、能点按钮，但知识结构仍没有被对象化、事务化和证据化。只要首屏仍然像聊天框加按钮，就不算终极版。

兼容 0.4.x 的运行态 shell 仍然必须保留这些模式状态和控件，作为从当前版本迁移到 Notebook Workspace 的可验证台阶。默认入口必须能在 Chat Mode 和 Agent Workspace Mode 之间切换，但 v3.0 默认落点应是 Notebook Workspace：

- `modeSwitchBar`
- `chatModeButton`
- `agentWorkspaceModeButton`
- `modeIntentLine`
- `activeProductMode`
- `lastWorkspacePane`
- `Workspace Navigator`
- `workspaceNavigator`

终局必须和当前版本拉开的可见断层是：当前 0.4.x 做不到的事不能用已有对象区、workflow 区或 ledger 区来掩盖。当前版本还不能稳定浏览整个 notebook 对象库，不能完整原地重构复杂脑图，不能证明所有实体卡片和关系残留，也不能把技能、复习、外部自动化和跨文档知识全部纳入同一个证据系统。

v3.0 的硬边界：

- 能像 Finder 一样浏览 notebook 对象，而不是只看当前消息聚合。
- 能原地编辑真实现有脑图，而不是重新生成一棵相似的新树。
- 复习队列和覆盖率是 Card Factory 的必选闭环。
- 外部自动化不能绕过 dry-run、确认、ledger 和回滚。
- 技能包不是自定义 prompt。

### 2.1 现有功能在终局里的位置

终局不是删除当前功能，而是重新安放它们。当前功能如果继续放在聊天页中心，会让产品停留在 v1.x；只有把它们迁移到对象和 workflow 体系里，才进入 v2/v3。

| 当前功能 | 现在的位置 | 终局位置 | 迁移动作 |
| --- | --- | --- | --- |
| 发送/可排队 | 聊天输入按钮 | Command Pane | 只负责表达意图；写入类意图必须编译成 operation plan |
| 回答下方生成脑图树 | 回答快捷按钮 | Mindmap Studio | 变成“基于当前对象生成 Diff”，不直接新建重复树 |
| 生成卡片 | 聊天快捷按钮 | Card Factory | 变成按学习目标、卡型、来源、复习队列生成和审计 |
| 目标/长任务 | 聊天运行状态 | Workflow Builder | 变成可保存、可恢复、可验收 workflow run |
| 队列 | pending 任务列表 | Workflow Runtime | 只保留为底层调度，不再承担产品解释 |
| 设置页 | 杂项配置集合 | System Drawer | 只放低频配置、权限、后端、路径、诊断和更新 |
| 日志 | 调试信息 | Operation Ledger Explorer | 变成用户可读证据链，可按对象和事务追溯 |
| 文件路径管理 | 设置子模块 | Source Registry | 变成文件、PDF 缓存、上传资料和 MN 文档的统一来源对象 |
| 自定义按钮 | prompt 列表 | Skill Center / Command Palette | 简单 prompt 是命令；可发布能力必须升级为技能包 |

这张表是产品断层的验收口径：只要这些能力仍然主要停留在聊天页，v3.0 就没有实现。只有当它们都围绕 `MNObject Registry`、Diff、Card Factory、Workflow Runtime 和 Operation Ledger 工作时，当前插件才真正从 Chat Companion 过渡到 Knowledge OS。

## 3. 终局的用户故事必须明显不同

### 3.1 精读一篇论文

当前版流程是：用户问“解读这篇论文”，插件回答，用户再点生成脑图或卡片。

终局流程必须是：

1. 用户打开论文，Notebook Workspace 自动识别当前文档、已有脑图、已有卡片、PDF 缓存、选区和历史操作。
2. Knowledge Console 显示“全文结构覆盖率、已有卡片覆盖率、缺失章节、缺来源卡片、过长卡片、待复习数量、最近失败事务”。
3. 用户选择 `精读论文 workflow`，系统先生成 operation plan，而不是直接生成内容。
4. Mindmap Studio 读取现有脑图，显示“新增 18、更新 12、合并 4、移动 6、建议删除 3”的节点级 Diff。
5. Card Factory 按“概念、公式、方法、实验、局限、对比、复习题”生成短卡，并显示来源和覆盖率。
6. 用户逐批确认。每次写入都进入 Operation Ledger。
7. 验收页输出：覆盖了哪些章节、创建了哪些 noteId、哪些卡片进入复习队列、哪些对象没有写入、哪些需要人工确认。

### 3.2 合并和重组现有脑图

当前版容易变成“又生成一棵树”。

终局必须先读取当前真实脑图，并以现有 noteId 为主键做原地编辑：

- 如果目标脑图不存在，先让用户创建或选择目标脑图。
- 如果已有相似节点，默认提出 merge/update/move，而不是 create。
- 如果删除旧节点，只能提出 delete_suggest，并进入二次确认。
- 拒绝后必须证明 outline、实体卡片、链接关系、复习队列是否仍有残留。

### 3.3 自动学习代理

终局代理不是“按钮点了之后慢慢跑”。它必须是可检查的 workflow：

- 输入对象：当前文档、选区、脑图子树、卡片集合、外部文件或跨文档授权范围。
- 计划：步骤、模型调用、MN 原生动作、权限、dry-run、确认点。
- 执行：每一步有状态、耗时、输出对象和失败原因。
- 确认：写入前必须显示 Diff 或草稿；删除和外部请求必须二次确认。
- 验收：最终生成学习报告、对象覆盖率、复习计划和 Operation Ledger 证据。

## 4. 终局硬验收：这些不满足就不是 v3.0

终局验收不按按钮数量算，也不按“有没有某个面板”算。必须逐项证明：

| 验收项 | 终局要求 | 不合格表现 |
| --- | --- | --- |
| 主入口 | 默认进入 Notebook Workspace，Chat 是辅助入口 | 首屏仍是聊天框加按钮 |
| 对象层 | notebook、document、摘录、高亮、card、mindmap node、subtree、workflow、ledger 都是可寻址对象 | 只能围绕当前消息附近对象工作 |
| 真实脑图编辑 | 读取现有 noteId 和父子关系，做 create/update/merge/move/delete_suggest Diff | 重新生成一棵相似的新树 |
| 卡片系统 | 有学习目标、卡型、来源、去重、覆盖率、复习队列 | 只是把回答拆成多张卡 |
| 代理运行 | workflow 有计划、状态、确认点、失败恢复、验收报告 | 只是长任务或 pending 队列 |
| 写入可信度 | 每次写入都有 operation plan、dry-run、native apply、verify、rollback 和 residual proof | 只显示“成功/失败” |
| 回滚证明 | 拒绝后能检查真实 MN 对象是否仍存在 | 只删除 outline 或只按计数猜测 |
| 跨文档知识 | 明确授权范围，回答列对象引用、page/quote/noteId/MN link | 默认偷偷扫全库或无引用回答 |
| 外部自动化 | URL/API 请求进入权限、dry-run、workflow、ledger 和 callback 证据 | 外部脚本绕过插件账本 |
| 技能生态 | 技能包有 manifest、schema、UI、权限、验收、迁移和回滚规则 | 自定义 prompt 冒充技能 |

如果用户的高阶工作仍只能靠输入一句话再点回答下方按钮，就不是终局。换句话说，如果用户仍然必须靠“输入一句话，然后在回答下面点按钮”，它最多是 AI Chat Plugin 或 Study Copilot，不是 Notebook Knowledge OS。

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

当前 0.4.x 只能称为 Operation Compiler 第一阶段：它已经把写入类意图拆成结构化计划，并把计划、写入数量、原生能力 dry-run 结果、逐操作 `codex.mn.perOperationDryRun.v1` 明细和验证要求暴露给前端和 doctor/单文档验收清单；普通 `agent_plan` 也会在草稿生成前复用写入 dry-run 门槛，缺少必要 native capability 时直接阻断计划。它还没有完成真实 MN 对象存在性 probe、跨对象残留扫描、完整回滚证明和技能包级 schema 迁移。因此它是从“聊天按钮”走向“对象操作系统”的关键断层，不是终局完成证明。

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
