# Codex Companion 发布级产品目标

## 目标

把 Codex 变成一个可在 MarginNote 4 里直接使用的通用工作面板：用户打开资料、论文、笔记或项目材料后，不需要切换到终端，就能在 MN4 侧边面板里对话、运行自定义 prompt、生成原生卡片、生成脑图、建立回链、做可见高亮，并在需要时导出带标注 PDF 副本。论文精读是重点预设场景，但不是产品边界。

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
   - 面板分为对话、按钮、设置、文件、历史五个子界面。
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

## v0.4.25 当前状态

- 已完成：MN4 WebView 面板，含对话、按钮、设置、文件、历史五个子界面，可输入聊天框、固定发送按钮、历史回复、当前上下文预览、问 Codex、解释选中、完整精读、生成卡片、新建脑图、高亮状态、高亮下一选区、导出 PDF 副本、检查连接按钮。
- 已完成：`v0.4.25` 已发布到 GitHub Releases，release zip 已通过 smoke test 和 install dry-run；本机已替换到 0.4.25，Companion `/status.pluginVersion=0.4.25`，MN4 运行态 `mnRuntime.ready=true`、`webControlsReady=true`、`nativeApiReady=true`，运行态 handler features 无缺失。
- 已完成：GitHub 默认 `README.md` 改为英文首页，并提供完整中文 `README.zh-CN.md`；两个 README 顶部互相链接，发布包和 release smoke 都要求同时包含双语 README。
- 已完成：诊断日志脱敏、裁剪、读取和清空逻辑已从 `companion.py` 拆到 `diagnostic_log.py`，保留原 Companion API 名称，减少主服务文件负担。
- 已完成：对话页按钮按任务分区重排。输入行固定放发送；`stagedActionLine` 显示按钮中心填入后的待发送动作，并允许修改 prompt 后仍按该动作执行；`mainActionStack` 按一次性目标、常用任务、工具区顺序排列；`goalRunPanel` 独立放“设目标”按钮和状态；`primaryActionGrid` 是 2x2 常用区，只包含解释选中、生成卡片、新建脑图和完整精读；`workflowActionPanel` 常驻显示 `mindmapToolPanel` / `mindmapActionGrid` 的补到当前、重组当前，以及 `sourceToolPanel` / `toolActionGrid` 的高亮、导出和状态；缺上下文按钮会显示“需选区/需节点/需文档/需能力”，运行中的可用按钮用“可排队”状态提示，不再像整体置灰；主对话页运行态提示只保留刷新和去设置，设置页诊断入口按 AI 与连接、权限与文件、MN 运行态、验收四组分区，检查连接、本文档验收和发布验收走各自独立按钮。
- 已完成：按钮页提供预设模板、自定义 prompt、动作类型和“主界面”开关；预设模板可填入输入框或添加成自定义按钮，不再一键试用即执行；后端会保存自定义按钮并把主界面置顶按钮限制为最多 4 个；自定义按钮动作支持 `request_native_highlight_selection`。
- 已完成：顶部 AI readiness 状态卡，明确显示当前 AI 后端、本机 Codex CLI 是否发现、OpenAI 是否已配置；设置页可选择 `auto`、`codex_cli`、`openai_api`、`local`，也可录入或清除 OpenAI Key，并提供无 token 的“试连AI”快速探测。Key 只写入本地 `.env`，不回显到 Web UI 或 settings JSON；清除 Key 只发送 `clearOpenAIKey=true`，不会把输入框里的临时 key 回传。
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
- 已完成：面板内查看/清空当前 notebook/book 历史对话；`history_list` / `history_clear` 已有 Companion 接口。
- 已完成：旧版原生按钮面板继续保留，作为 WebView 加载失败时的兜底文件。
- 已完成：Companion 本地服务、Codex CLI 可选后端、OpenAI 可选配置、本地工具/诊断模式。生成型动作必须使用 Codex CLI 或 OpenAI，不用本地模板冒充模型输出。
- 已完成：程序化队列触发，插件轮询后用 MN4 原生 API 写入内容。
- 已完成：完整精读改为真实模型驱动，模型输出会被拆成短卡片和脑图分支，先进入草稿确认再写入 MN。
- 已完成：写入层保留 Codex 元数据去重能力，重复写入时会跳过已有卡片/脑图节点。
- 已完成：发布包根目录一键 `install.sh` / `uninstall.sh`、只读高亮审计、默认禁用危险的 SQLite 高亮写入；doctor 会检查 zip 根目录安装入口、私有运行文件排除和 OneDrive 哈希一致性。
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
