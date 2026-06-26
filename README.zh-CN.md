# Codex Companion for MarginNote 4

![Codex Companion cover](assets/cover.png)

[![Latest Release](https://img.shields.io/github/v/release/LiuWhale/marginnote-assistant?label=release)](https://github.com/LiuWhale/marginnote-assistant/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

语言: [English](README.md) | **简体中文**

Codex Companion 是一个运行在 MarginNote 4 里的本地优先 AI 助手插件。它把 Codex / OpenAI 的对话能力接到 MarginNote 当前文档、选区、节点和脑图里，用来解释资料、生成卡片、生成结构化脑图，并在写入前提供可接受/拒绝的 AI 编辑确认。

它不是只服务论文的插件。论文、书籍章节、课程资料、项目文档、会议材料，只要 MarginNote 能打开并暴露上下文，都可以作为输入。

当前公开的 0.4.x 仍是预览版，不能被误认为终局。现在的聊天面板、回答下方按钮、设置页、队列、日志和第一阶段 Agent Workspace 都只是迁移脚手架。长期目标是 **MarginNote Knowledge Agent OS**：一个 Notebook Knowledge IDE，主语不是 prompt 或回答，而是真实 MarginNote note、脑图节点、摘录、卡片、文档、复习任务、workflow 和操作证据。

路线图必须分成四层。`v0.4.x` 是 Chat Companion；`v1.x` 应该成为稳定 Study Copilot，体验对标 MarginNote 自带 AI；`v2.x` 必须成为 Native Knowledge Editor，能读取和编辑现有 `noteId` 对象，并通过 Diff、验证和回滚闭环；`v3.x` 才是 Notebook Knowledge OS，默认打开 `Notebook Workspace`，而不是空聊天框。`Chat Mode` 仍然用于快速阅读问答和输入意图，但会降级成 Object Browser、Mindmap Studio、Card Factory、Knowledge Graph、Workflow Builder 和 Operation Ledger Explorer 旁边的命令面板。每次 AI 写入都应进入带验证和回滚证据的 Operation Ledger；跨 notebook 知识层、工作流运行时、外部 URL/API 自动化和可分享技能包都应成为一等产品界面。

> This project is not affiliated with MarginNote, OpenAI, or Apple.

## 现在能做什么

- 在 MarginNote 4 面板内直接对话，自动使用当前选区、当前节点或当前文档上下文。
- 可在 `Chat Mode` 轻量对话和 `Agent Workspace` 对象工作台之间切换；前者专注连续问答，后者展开对象、操作、知识和工作流。
- `Agent Workspace` 里提供 `Workspace Navigator`，可直接跳到 `Knowledge Console`、`Mindmap Studio`、`Card Factory`、`Operation Ledger`、`Knowledge Graph`、`Workflow Builder` 和 `Skill Center`。
- 手动选择上下文范围：自动、只看选区/节点、读取全文。
- `Agent Workspace` 里显示第一阶段 Operation Compiler。`agent_plan` 会返回结构化 `operationPlan`、`verificationPlan`、编译检查和逐操作 dry-run 证据，写入类动作会先显示计划步骤、写入数量、原生能力状态、节点级阻断原因、确认要求和写后验证义务，再被当成真实 MarginNote 编辑。
- 生成短卡片和结构化脑图，写入前先显示草稿或 AI 编辑确认；制卡会返回 `codex.mn.cardFactory.v1` 卡片工厂摘要，每张卡带 `cardType`、来源、`learningGoal` 和 `reviewPrompt`，确认面板显示卡型和质量风险，并可把本次草稿加入对象级复习队列。
- 脑图写入前先显示 Diff 预览，包含新增、更新、合并、移动、建议删除统计，并支持逐节点保留、跳过、改标题和改正文。
- `Agent Workspace` 里提供第一阶段 `Mindmap Studio`，它不是回答下方按钮的别名，而是脑图对象操作台：`读取现有脑图`、`预览 Diff`、`应用所选`、`验证事务`、`回滚事务` 都在同一个面板里完成。
- 把最新回答一键转成脑图树；接受则保留，拒绝会尝试删除本次新增脑图结构和卡片。
- 在主界面顶部选择脑图写入目标，避免新脑图写到错误的 notebook 或旧页面。
- 支持任务排队：运行中继续发送或点击按钮会进入 pending，下一个任务自动接着跑。
- 支持停止当前生成；停止后不继续写入卡片或脑图。
- 支持当前文档缓存状态灯：缓存中为黄灯，成功为绿灯，失败为红灯。
- 支持历史对话、新对话、设置页、文件路径管理、结构化日志和诊断；历史和日志会携带当前 `MNObject`，便于按选区、卡片、文档或脑图对象追踪操作。
- 对象区提供 Knowledge Console 风险面板；`agent_plan` 会返回 `codex.mn.riskRegister.v1`，把权限、上下文范围、目标脑图、dry-run 和确认点列成可见风险项。
- 对象面板提供 Object Browser，会把当前焦点对象、Object Graph 节点、对象活动、Operation Ledger 条目和第一阶段 `MNObject Registry` 条目汇总成一个可浏览对象列表，每个对象都带可执行动作。它支持按对象类型、kind 和关键词筛选，便于只看 Registry、脑图节点、活动或账本项。MarginNote 上报 `mindmapTreeReadFinished` 后，原生脑图树缓存里的节点会登记为 `mnobj:note:<noteId>` 对象；对象区的 `objectRegistryScanButton` / `扫描 MN` 会触发 `request_mn_object_registry_scan`，向 MN4 原生队列发送 `scan_mn_objects`，再把 `mnObjectRegistryScanFinished` 回传对象写成带 `native_object_scan` 证据的 Registry 条目。扫描对象会进入 Object Graph，显示成 `mn_note` 节点，并生成 `native_object_scan 父子边`；点击扫描对象会打开该对象图谱、该对象活动和账本，保留它的 title、noteId、parentNoteId 和 sourceRef。
- 对象面板提供 Object Graph，会把当前 `MNObject` 和相关历史对话、workflow run、AI 编辑事务、外部自动化请求、诊断证据、Knowledge Index 中的卡片/脑图实体与关系、最近一次 MN 原生脑图树缓存中的节点和父子关系，以及用户手工维护的 `manual_relation` 对象关系连成可点击图谱节点。保存或删除这些手工关系会形成 `object_graph_manual_relation` 账本事件，并带 `manualRelation` 证据。
- 对象面板会汇总当前 `MNObject` 的历史对话、工作流、AI 编辑事务和诊断日志，并可直接打开相关对话、查看 workflow、查看事务或展开日志详情。
- 对象面板提供 Operation Ledger，会按当前 `MNObject` 聚合 workflow run、AI 编辑事务、外部自动化请求和手工对象关系事件；可按账本类型、状态和关键词筛选证据项；点开账本项会在对象区打开证据详情面板，查看 operation plan、dry-run/apply path、原生命令、原生事件线、原生执行、回滚/残留、工作流确认点、外部回调证据和手工关系证据。
- AI 编辑拒绝后支持 MN 原生对象存在性 probe：Companion 可让插件按 `noteId` 检查真实对象是否仍存在，事务验证会用这个结果确认残留，而不是只按 deleted/failed 数量推断。
- 工作流区提供第一阶段 Workflow Run Inspector。最近 workflow run 可以点开，查看每一步的状态、queueId、确认要求、提醒/阻断状态和下一步动作；可恢复的失败/阻断 direct 或 queueable 步骤会显示 `重试`，但写入/确认步骤仍必须走接受或拒绝。
- 支持从 GitHub Releases 检查更新，并打开对应下载页。
- 原始 PDF 默认保持清洁；导出标注 PDF 时生成副本，不覆盖原文。

目标任务是“一次性长任务”，不会保存成长期当前目标。普通聊天、卡片和脑图不会偷偷继承旧的答辩、精读或汇报目标。

## 快速安装

1. 打开 [Latest Release](https://github.com/LiuWhale/marginnote-assistant/releases/latest)。
2. 下载 `CodexCompanion-<version>-latest-dist.zip`。推荐优先使用这个完整安装包，因为它会同时安装 MarginNote 插件和本地 Companion 服务。
3. 解压后双击：

```text
Install Codex Companion.command
```

也可以在解压目录运行：

```bash
./install.sh
```

4. 重启 MarginNote 4。
5. 打开一个 notebook 或文档，从 MarginNote 插件工具栏打开 Codex Companion。

Release 里也会提供 `CodexCompanion-<version>-latest.mnaddon`，这是 MarginNote 原生插件包格式。它只适合导入或更新 MN4 插件本体；本地 Companion 服务仍然需要通过完整 zip 安装并保持运行。

卸载时双击：

```text
Uninstall Codex Companion.command
```

或运行：

```bash
./uninstall.sh
```

## 首次配置

打开插件右上角齿轮进入设置页。

推荐配置：

- `AI 后端`: `auto`
- `模型`: `gpt-5.5`
- `速度`: `fast`
- `Codex CLI`: 如果本机已经安装并登录 Codex CLI，优先用它。
- `OpenAI Key`: 如果不用 Codex CLI，可以填写 OpenAI API Key。

后端含义：

- `auto`: 优先尝试本机 Codex CLI，失败后尝试 OpenAI API。
- `codex_cli`: 强制使用本机 Codex CLI。
- `openai_api`: 强制使用 OpenAI API Key。

没有可用 Codex CLI，也没有 OpenAI Key 时，问答、制卡、脑图和完整精读会失败并显示原因；插件不会用内置模板假装生成了 AI 内容。

发现本机 Codex CLI 只表示“可以尝试这个后端”，不等于已经完成真实生成。真实生成还取决于用户自己的 Codex 登录、账号/模型权限、代理和网络。若 Codex CLI 获取 cloud config bundle 超时，Companion 会自动重试一次；仍失败时会显示可操作的代理/登录/网络提示。

## 日常使用

### 直接问

在主界面输入问题，按 Enter 或点击两行显示的 `发送 / 可排队` 按钮。发送后输入框会清空；如果当前已有任务在跑，新问题会自动进入队列。

### 解释选区

在 PDF 或节点里选中内容，再提问或点击解释类按钮。上下文范围选 `自动` 时，插件会优先使用选区；没有选区时再尝试当前文档。

### 生成脑图树

1. 先在顶部选择脑图写入目标。
2. 对当前回答点击 `生成脑图树`，或直接要求“根据全文生成结构化脑图”。
3. 切到 `Agent Workspace` 的 `Mindmap Studio`，按需要读取现有脑图、预览 Diff、应用所选、验证事务或回滚事务。
4. 插件会在操作台常驻显示新增、更新、合并、移动、建议删除统计。
5. 取消勾选不想写入的节点，或直接在 Diff 面板里修改节点标题/正文；预览会标记跳过节点，并在写入前保存节点编辑。
6. 在回答下方确认：`接受` 写入或局部应用变更，`拒绝` 丢弃本次草稿。

如果当前文档没有合适的脑图页面，先在 MarginNote 中创建或选中目标，再刷新目标列表。这样比静默写入某个旧脑图安全。

### 生成卡片

卡片会尽量拆成短卡片，避免一张卡片过长。生成后先进入草稿或 AI 编辑确认，确认后才写入 MarginNote。当前卡片会带 Card Factory 元数据：`cardType`、来源、`learningGoal`、`reviewPrompt` 和卡片工厂质量摘要，确认面板会提示缺来源、长卡和重复标题，并提供 `加入复习队列`。知识区会显示当前 `MNObject` 作用域下的复习卡数量和最近卡片。

### 新对话和历史

主界面可以开启新对话；历史页是独立页面，用来查看或清理当前 notebook / document 下的对话记录。带有当前 `MNObject` 的会话会保存 `objectRef/mnObjectId`，后续可以只查看某个选区、卡片或文档对象相关的对话。

## 全文读取和缓存

MarginNote 有时只给插件文档名、`bookmd5` 或选区，而不给原始 PDF 路径。这个插件会按下面顺序尝试拿到全文：

1. 使用 MarginNote 当前文档上下文。
2. 根据已知文件路径映射查找本地文件。
3. 在设置页的“文件路径管理”里登记多个搜索根目录。
4. 请求 MarginNote 插件进程缓存当前 PDF 到本机 Companion。

如果 macOS 阻止后台服务读取 OneDrive、iCloud 或沙盒目录，缓存路线通常比让 Python 直接读原文件更稳。主页底部状态灯会显示缓存中、缓存成功或缓存失败。

常见提示解释：

- `Operation not permitted`: macOS 隐私权限阻止后台 Companion 读取文件。
- `没有可解析的本地 PDF 路径`: MarginNote 当前没有暴露原始文件路径，也没有命中已知路径映射。
- `请保持文档在 MarginNote 4 中打开`: 插件正在让 MarginNote 进程自己读取并上传缓存。

## 更新

设置页提供两个低风险更新入口：

- `检查更新`: 查询 `LiuWhale/marginnote-assistant` 的 GitHub Releases。
- `打开下载页`: 打开最新 Release 页面，由用户手动下载安装。

当前默认采用“打开下载页”的更新方式，因为 macOS 权限会阻止后台服务直接写入 MarginNote 扩展目录。这样更可控，也更容易看清当前安装的是哪个版本。

## 权限说明

通常不需要给 MarginNote 插件完整磁盘访问权限。

可能需要额外权限的情况：

- 后台 Companion 直接读取 OneDrive / iCloud / 受保护目录里的文件：给 Terminal、Python 或 Companion 所在运行环境 Full Disk Access。
- 需要系统级自动点击：给对应运行环境 Accessibility 辅助功能权限。
- 导出标注 PDF 到某些云盘目录：需要目标目录写入权限。

插件不会继承 MarginNote 的全部系统权限。MarginNote、WebView、Python Companion 是不同进程，macOS 会分别控制它们能访问的文件和自动化能力。

## 隐私和数据

- 本地 Companion 默认只监听 `127.0.0.1:48761`。
- OpenAI Key 写入本机 `.env`，不会回显到插件界面。
- 使用 `openai_api` 时，当前选区、节点内容、文档片段和用户问题会发送给 OpenAI。
- 使用 `codex_cli` 时，内容会交给本机 `codex exec`，后续联网和账号由你的 Codex CLI 配置决定。
- 原始 PDF 默认不被修改；标注导出会生成副本。
- Release 包不会包含 `.env`、上传文件、日志、队列、草稿、会话或缓存。

更多细节见 [Privacy and Permissions](docs/PRIVACY_AND_PERMISSIONS.md)。

## 常见问题

### 插件显示“Codex Companion 未运行”

先确认本地服务：

```bash
curl http://127.0.0.1:48761/status
```

如果没有响应，重新启动 Companion：

```bash
./start_companion.sh
```

或重新运行安装脚本，让 LaunchAgent 被重新加载。

### 状态显示连接，但发送失败

进入设置页依次检查：

- AI 后端是否可用。
- Codex CLI 是否安装并登录。
- OpenAI Key 是否已保存。
- 代理地址是否只使用支持的 `http://` 或 `https://`。
- 结构化日志里最近一次失败的 `error` 字段。

如果错误里出现 `timed out waiting for cloud config bundle after 15s`，说明 Codex CLI 自己没有及时拿到云端启动配置。先重试一次，再检查代理、Codex 登录和模型/账号权限；配置 OpenAI Key 后，`auto` 模式还能多一个备用后端。

### 为什么有时读不到全文

MarginNote 插件 API 不总是提供原始 PDF 路径。尤其是 OneDrive、iCloud、沙盒缓存、导入副本、多文档 notebook 场景，后台 Companion 可能只能看到文件名或 `bookmd5`。优先使用缓存当前文档和文件路径管理，不建议手工硬编码单个 PDF 路径。

### 拒绝脑图后为什么还有残留卡片

插件会记录本次新增节点并尝试删除对应脑图结构和卡片。MarginNote 原生 API 在部分版本里删除 mind-map outline 和删除 card object 不是同一个动作，因此如果仍有残留，请打开设置页导出日志并提交 issue，日志里会包含本次 edit id 和删除结果。

### npm 安装 Codex CLI 报 `ENOTEMPTY`

通常是全局 `@openai/codex` 目录残留或并发安装造成。先确认没有正在运行的 npm 安装，再清理对应残留目录后重装。不要只清 npm cache，因为 `ENOTEMPTY` 指向的是全局安装目录冲突。

## 日志和诊断

结构化事件日志：

```text
~/.codex/marginnote-assistant/events.jsonl
```

常见运行目录：

```text
~/.codex/marginnote-assistant
~/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant
~/Library/LaunchAgents/com.codex.paper-companion.plist
```

设置页可以查看 Companion health、AI 试连、MarginNote runtime、文件路径管理和最近日志。提交 bug 时，请优先提供：

- 插件版本。
- MarginNote 4 版本。
- 当前动作名称。
- 最近一次错误消息。
- 相关 `events.jsonl` 片段。

## 开发

运行测试：

```bash
python3 -m unittest discover -s tests
```

检查 Python 语法：

```bash
python3 -m py_compile companion.py diagnostic_log.py runtime_config.py update_manager.py doctor.py release_acceptance.py release_smoke_test.py package_release.py prepare_release_handoff.py send_action.py single_document_acceptance.py
```

检查 WebView JavaScript：

```bash
node --check extension/codex.mn.assistant/web/app.js
node --check extension/codex.mn.assistant/main.js
node --check extension/codex.mn.assistant/CodexWebPanelController.js
```

本地启动 Companion：

```bash
./start_companion.sh
```

服务状态：

```bash
curl http://127.0.0.1:48761/status
```

## 打包发布

构建 release zip：

```bash
python3 package_release.py 0.4.30
```

Smoke test：

```bash
python3 release_smoke_test.py release/CodexCompanion-0.4.30-latest-dist.zip --mnaddon release/CodexCompanion-0.4.30-latest.mnaddon
python3 release_smoke_test.py release/CodexCompanion-0.4.30-latest-dist.zip --mnaddon release/CodexCompanion-0.4.30-latest.mnaddon --install-dry-run
```

Release acceptance：

```bash
python3 release_acceptance.py release/CodexCompanion-0.4.30-latest-dist.zip --json
```

Release acceptance 可能因为机器相关证据不足而阻塞，例如原生高亮证据、签名/公证证据、跨机器安装证据。这些是发布证据检查，不代表源码打包失败。

## 仓库结构

```text
.
├── companion.py                 # local HTTP service and action dispatcher
├── runtime_config.py            # runtime defaults and settings sanitizers
├── update_manager.py            # GitHub Release update checks
├── doctor.py                    # local diagnostics
├── release_acceptance.py        # release gate runner
├── package_release.py           # clean release zip builder
├── extension/codex.mn.assistant # MarginNote 4 add-on source
├── tests/                       # unit and static-contract tests
├── docs/                        # user, product, privacy, and release docs
└── assets/                      # README cover and icons
```

## 文档

- [产品手册](docs/USER_MANUAL.md)
- [隐私和权限](docs/PRIVACY_AND_PERMISSIONS.md)
- [发布检查清单](docs/RELEASE_CHECKLIST.md)
- [当前发布审计](docs/CURRENT_RELEASE_AUDIT.md)
- [MarginNote AI 对话对标说明](docs/MN4_AI_CHAT_PARITY.md)

## License

MIT. See [LICENSE](LICENSE).
