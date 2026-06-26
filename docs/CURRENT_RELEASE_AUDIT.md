# Current Release Audit

审计时间：2026-06-27 CST

本文档记录当前 Codex Companion 公开预览版的可验证状态。它不是最终 v1.0 发布承诺，而是当前证据基线。历史条目保留当时版本号和当时判断。

## 版本与包

- 当前发布候选：0.4.33 公开预览版
- MN4 插件 manifest：0.4.33
- Companion：0.4.33
- GitHub Release：`https://github.com/LiuWhale/marginnote-assistant/releases/tag/v0.4.33`
- 最新本地包：`~/.codex/marginnote-assistant/release/CodexCompanion-0.4.33-latest-dist.zip`
- 最新 OneDrive 镜像：`~/Library/CloudStorage/OneDrive-个人/Codex Companion/CodexCompanion-0.4.33-latest-dist.zip`
- 最新 MN4 插件包：`~/.codex/marginnote-assistant/release/CodexCompanion-0.4.33-latest.mnaddon`
- 最新 MN4 插件包 OneDrive 镜像：`~/Library/CloudStorage/OneDrive-个人/Codex Companion/CodexCompanion-0.4.33-latest.mnaddon`
- 当前 zip sha256：见 release 目录和 OneDrive 镜像目录中的外部 `SHA256SUMS.txt`
- 最新本地 pkg：`~/.codex/marginnote-assistant/release/CodexCompanion-0.4.33-latest.pkg`，已生成但未签名、未公证
- 精确 hash：见 release 目录和 OneDrive 镜像目录中的外部 `SHA256SUMS.txt`；当前 `release_sha256_manifest` gate 已覆盖 zip、mnaddon 和 pkg，并已通过。

## 当前证据

### 2026-06-27 v0.4.33 发布候选：Notebook Runbook 工作台

本轮把 0.4.32 的 Command Pane 工作台继续向“Notebook-first”推进。`Notebook Workspace` 不再只是六个摘要卡和动作按钮，而是新增 `Notebook Runbook`：把当前 notebook 的上下文、MN 原生对象扫描、脑图基线、操作计划、workflow runtime 和 Operation Ledger 证据排成可执行检查清单。Chat Mode 仍用于轻量问答；Workspace Mode 则以 runbook、对象、操作、知识和工作流作为第一视觉中心。

主要变化包括：

- 后端 `notebook_workspace` 现在返回 `codex.mn.notebookRunbook.v1`，每一步带 `status`、`tone`、`evidence` 和可执行 `action`。
- WebView 新增 `notebookWorkspaceRunbook/notebookWorkspaceRunbookSummary/notebookWorkspaceRunbookList`，在 Notebook Workspace 中常驻显示 runbook。
- Runbook 动作复用现有 MN 对象扫描、读取脑图树、`agent_plan`、workflow list 和 Operation Ledger list，不绕过权限、确认、Diff 或账本机制。
- `doctor.py`、Web 静态检查和单文档验收 required controls 已更新到 Notebook Runbook 结构。

本轮本地验证结果：

```text
python3 -m unittest discover -s tests
502 tests passed

node --check extension/codex.mn.assistant/main.js
node --check extension/codex.mn.assistant/web/app.js
PASS

python3 -m py_compile companion.py doctor.py release_acceptance.py release_smoke_test.py package_release.py build_pkg.py single_document_acceptance.py prepare_release_handoff.py refresh_mn_runtime.py
PASS

git diff --check
PASS

python3 release_smoke_test.py release/CodexCompanion-0.4.33-latest-dist.zip --mnaddon release/CodexCompanion-0.4.33-latest.mnaddon
PASS, exact artifact hashes are recorded in release/SHA256SUMS.txt and the OneDrive mirror.

python3 release_smoke_test.py release/CodexCompanion-0.4.33-latest-dist.zip --mnaddon release/CodexCompanion-0.4.33-latest.mnaddon --install-dry-run
PASS

python3 build_pkg.py release/CodexCompanion-0.4.33-latest-dist.zip --json
PASS, generated release/CodexCompanion-0.4.33-latest.pkg
```

本轮 artifact：

- `CodexCompanion-0.4.33-latest-dist.zip`
- `CodexCompanion-0.4.33-latest.mnaddon`
- `CodexCompanion-0.4.33-latest.pkg`
- `SHA256SUMS.txt`

当前 release acceptance 剩余阻塞为：`runtime_web_controls`、`native_api_matrix`、`native_visible_highlight`、`signed_pkg`、`notarized_pkg`、`cross_machine_install`、`single_document_acceptance`。其中前两项需要 MN4 重新打开面板或重启后上报 `pluginVersion=0.4.33` 的 WebView/native 事件；其余仍是最终 v1.0/正式发布门槛，不阻止 0.4.33 作为公开预览版发布。

### 2026-06-27 v0.4.31 发布候选：Notebook Workspace 首屏总览

本轮把 0.4.30 之后的开发态归档为 0.4.31 公开预览候选。这个版本继续把产品入口从“聊天框加按钮”推向 notebook/object-first 工作台，但仍不宣称完成最终 v3.0 Knowledge OS。

主要变化包括：

- 新增 `notebook_workspace` 后端动作，返回 `codex.mn.notebookWorkspace.v1`，聚合当前焦点 `MNObject`、Object Browser 计数、当前脑图树缓存、复习队列、workflow run 和 Operation Ledger 计数。
- WebView 在 Workspace Navigator 下方新增 `Notebook Workspace` 总览，显示焦点、对象、脑图、复习、工作流和账本状态。
- 总览动作可直接触发 MN 对象扫描、读取当前脑图树、生成操作计划、查看复习队列、workflow 和账本证据；这些动作复用现有确认/队列/ledger 机制，不绕过写入确认。
- `doctor.py`、Web 静态检查和单文档验收 required controls 已加入 Notebook Workspace 控件，运行态缺失会被 gate 发现。

本轮本地验证结果：

```text
python3 -m unittest tests.test_companion_controls tests.test_web_controls_static tests.test_doctor_checks tests.test_single_document_acceptance tests.test_release_docs
277 tests passed

node --check extension/codex.mn.assistant/main.js
node --check extension/codex.mn.assistant/web/app.js
PASS

python3 -m py_compile companion.py doctor.py release_acceptance.py single_document_acceptance.py
PASS

git diff --check
PASS
```

本轮 artifact：

- `CodexCompanion-0.4.31-latest-dist.zip`
- `CodexCompanion-0.4.31-latest.mnaddon`
- `CodexCompanion-0.4.31-latest.pkg`
- 精确 sha256 不写死在包内文档里；以 release 目录、OneDrive 镜像和 GitHub Release asset 旁边的外部 `SHA256SUMS.txt` 为准。

本机将替换到 0.4.31：MN4 扩展目录 `mnaddon.json` 应为 `0.4.31`，`main.js` 应为 `PluginVersion = '0.4.31'`，Companion `/status.pluginVersion` 应为 `0.4.31`。MN4 运行态仍需重新打开面板或重启 MN4 后才会上报 `pluginVersion=0.4.31` 的 `webControlsReady` 和 `nativeApiCapabilities`。

当前 release acceptance 剩余阻塞仍预计包括：`runtime_web_controls`、`native_api_matrix`、`native_visible_highlight`、`signed_pkg`、`notarized_pkg`、`cross_machine_install`、`single_document_acceptance`。这些是最终 v1.0/正式发布证据，不阻止 0.4.31 作为公开预览版发布。

### 2026-06-27 v0.4.30 发布候选：运行态 handler gate 收紧

本轮把 0.4.29 之后的开发态归档为 0.4.30 公开预览候选。这个版本不是终极 v3.0，而是把后续 v2 原生对象工作台必须依赖的 handler 能力提前变成发布 gate，防止“界面看起来有对象区，但运行态 handler 不支持真实对象操作”的错判。

主要变化包括：

- Companion、doctor 和 release acceptance 的必需 handler fingerprints 增加 `native-mn-object-registry-scan-v1`、`native-mn-object-existence-probe-v1`、`native-mindmap-diff-apply-create-v1` 和 `native-mindmap-delete-suggestion-confirm-v1`。
- 如果 MN4 WebView 仍加载旧 handler，运行态 gate 会明确 BLOCK，而不是继续显示成可发布状态。
- 这与终极产品路线保持一致：当前 0.4.x 仍是 Chat Companion + Agent Workspace 雏形；完整 v2/v3 还需要真实对象浏览、Diff 工作台、事务回滚证明和 Knowledge OS 级工作流。

本轮本地验证结果：

```text
python3 -m unittest discover -s tests
501 tests passed

node --check extension/codex.mn.assistant/main.js
node --check extension/codex.mn.assistant/web/app.js
PASS

python3 -m py_compile companion.py doctor.py release_acceptance.py release_smoke_test.py package_release.py build_pkg.py single_document_acceptance.py prepare_release_handoff.py refresh_mn_runtime.py
PASS

git diff --check
PASS
```

本轮 artifact：

- `CodexCompanion-0.4.30-latest-dist.zip`
- `CodexCompanion-0.4.30-latest.mnaddon`
- `CodexCompanion-0.4.30-latest.pkg`
- 精确 sha256 不写死在包内文档里；以 release 目录、OneDrive 镜像和 GitHub Release asset 旁边的外部 `SHA256SUMS.txt` 为准。

本机将替换到 0.4.30：MN4 扩展目录 `mnaddon.json` 应为 `0.4.30`，`main.js` 应为 `PluginVersion = '0.4.30'`，Companion `/status.pluginVersion` 应为 `0.4.30`。MN4 运行态仍需重新打开面板或重启 MN4 后才会上报 `pluginVersion=0.4.30` 的 `webControlsReady` 和 `nativeApiCapabilities`。

当前 release acceptance 剩余阻塞仍预计包括：`runtime_web_controls`、`native_api_matrix`、`native_visible_highlight`、`signed_pkg`、`notarized_pkg`、`cross_machine_install`、`single_document_acceptance`。这些是最终 v1.0/正式发布证据，不阻止 0.4.30 作为公开预览版发布。

### 2026-06-27 v0.4.29 发布候选：真实对象 probe 与 Knowledge OS 路线纠偏

本轮把 0.4.28 之后的开发态归档为 0.4.29 公开预览候选。主要变化包括：

- AI 编辑事务验证在仍依赖删除计数或失败事件时，会给出 `检查真实 MN 对象` 操作，引导 MN4 原生侧按 noteId 执行对象存在性 probe。
- 事务验证已有 probe 结果时，不再继续提示重复 probe；验证报告会以原生 probe 结果确认残留或清理完成。
- 终极设计从“更强聊天面板”纠偏为四阶段路线：0.4.x Chat Companion、v1.x Study Copilot、v2.x Native Knowledge Editor、v3.x Notebook Knowledge OS。
- README、产品规格和用户手册明确说明当前 Agent Workspace 是迁移壳层，不是 v3.0 终局。

本轮本地验证结果：

```text
python3 -m unittest discover -s tests
498 tests passed

node --check extension/codex.mn.assistant/main.js
node --check extension/codex.mn.assistant/web/app.js
PASS

git diff --check
PASS
```

本轮 artifact：

- `CodexCompanion-0.4.29-latest-dist.zip`
- `CodexCompanion-0.4.29-latest.mnaddon`
- `CodexCompanion-0.4.29-latest.pkg`
- 精确 sha256 不写死在包内文档里；以 release 目录、OneDrive 镜像和 GitHub Release asset 旁边的外部 `SHA256SUMS.txt` 为准。

本机将替换到 0.4.29：MN4 扩展目录 `mnaddon.json` 应为 `0.4.29`，`main.js` 应为 `PluginVersion = '0.4.29'`，Companion `/status.pluginVersion` 应为 `0.4.29`。MN4 运行态仍需重新打开面板或重启 MN4 后才会上报 `pluginVersion=0.4.29` 的 `webControlsReady` 和 `nativeApiCapabilities`。

当前 release acceptance 剩余阻塞仍预计包括：`runtime_web_controls`、`native_api_matrix`、`native_visible_highlight`、`signed_pkg`、`notarized_pkg`、`cross_machine_install`、`single_document_acceptance`。这些是最终 v1.0/正式发布证据，不阻止 0.4.29 作为公开预览版发布。

### 2026-06-27 v0.4.28 发布候选：Agent Workspace 与 Mindmap Studio 第一阶段

本轮把 0.4.27 之后的开发态归档为 0.4.28 公开预览候选。主要变化包括：

- `Chat Mode / Agent Workspace` 双模式壳层和 `Workspace Navigator`，把 `Knowledge Console`、`Mindmap Studio`、`Card Factory`、`Operation Ledger`、`Knowledge Graph`、`Workflow Builder` 和 `Skill Center` 做成一等入口。
- `Mindmap Studio` 第一阶段，提供 `读取现有脑图`、`预览 Diff`、`应用所选`、`验证事务`、`回滚事务`，并汇总真实脑图树、Diff、局部应用和事务状态。它不是回答下方按钮的别名。
- Object Browser / Object Graph / Operation Ledger / Card Factory / Workflow Run Inspector 的第一阶段对象化和证据化能力。

本轮本地验证结果：

```text
python3 -m unittest discover -s tests
490 tests passed

node --check extension/codex.mn.assistant/main.js
node --check extension/codex.mn.assistant/CodexWebPanelController.js
node --check extension/codex.mn.assistant/web/app.js
PASS

python3 release_smoke_test.py release/CodexCompanion-0.4.28-latest-dist.zip --mnaddon release/CodexCompanion-0.4.28-latest.mnaddon
PASS

python3 release_smoke_test.py release/CodexCompanion-0.4.28-latest-dist.zip --mnaddon release/CodexCompanion-0.4.28-latest.mnaddon --install-dry-run
PASS

python3 build_pkg.py release/CodexCompanion-0.4.28-latest-dist.zip --json
PASS unsigned pkg

python3 release_acceptance.py release/CodexCompanion-0.4.28-latest-dist.zip --json
BLOCKED as expected for preview release
```

本轮 artifact：

- `CodexCompanion-0.4.28-latest-dist.zip`
- `CodexCompanion-0.4.28-latest.mnaddon`
- `CodexCompanion-0.4.28-latest.pkg`
- 精确 sha256 不写死在包内文档里，避免文档 hash 改动反过来改变 zip hash；以 release 目录、OneDrive 镜像和 GitHub Release asset 旁边的外部 `SHA256SUMS.txt` 为准。

本机已替换到 0.4.28：MN4 扩展目录 `mnaddon.json` 为 `0.4.28`，`main.js` 为 `PluginVersion = '0.4.28'`，Companion `/status.pluginVersion` 为 `0.4.28`。MN4 运行态仍需重新打开面板或重启 MN4 后才会上报 `pluginVersion=0.4.28` 的 `webControlsReady` 和 `nativeApiCapabilities`。

当前 release acceptance 剩余阻塞：`runtime_web_controls`、`native_api_matrix`、`native_visible_highlight`、`signed_pkg`、`notarized_pkg`、`cross_machine_install`、`single_document_acceptance`。`release_sha256_manifest` 已通过，不再因缺 pkg entry 阻塞。

### 2026-06-25 v0.4.27 发布：补 MarginNote 原生 `.mnaddon` 发布包

本轮确认 MarginNote 用户侧插件文件应提供 `.mnaddon`。示例 `.mnaddon` 是 zip archive，内部 `main.js`、`mnaddon.json`、`web/` 和图标位于压缩包根目录。0.4.27 因此把 release artifact 改为“双包”：

- `CodexCompanion-0.4.27-latest-dist.zip`：完整安装包，包含本地 Companion 服务、MN4 扩展、安装/卸载脚本、诊断和发布验收工具。
- `CodexCompanion-0.4.27-latest.mnaddon`：MarginNote 原生插件包，只包含 MN4 add-on 本体，适合手动导入或更新插件；它不安装本地 Companion 服务。
- `release_smoke_test.py` 新增 `.mnaddon` 检查，要求 `main.js`、`mnaddon.json`、WebView 文件和图标在 archive root，并拒绝嵌套 `codex.mn.assistant/` 根目录。
- `package_release.py` 会把 `.mnaddon` 同步到本地 release 目录和 OneDrive 镜像，并写入外部 `SHA256SUMS.txt`。

验证结果：

```text
python3 -m unittest discover -s tests
371 tests passed

python3 -m py_compile companion.py runtime_config.py update_manager.py doctor.py release_acceptance.py release_smoke_test.py package_release.py prepare_release_handoff.py send_action.py single_document_acceptance.py build_pkg.py notarize_pkg.py
PASS

node --check extension/codex.mn.assistant/web/app.js
PASS

python3 release_smoke_test.py release/CodexCompanion-0.4.27-latest-dist.zip --mnaddon release/CodexCompanion-0.4.27-latest.mnaddon
PASS

python3 release_smoke_test.py release/CodexCompanion-0.4.27-latest-dist.zip --mnaddon release/CodexCompanion-0.4.27-latest.mnaddon --install-dry-run
PASS
```

结论：`v0.4.27` 是补齐 `.mnaddon` 原生插件包格式的公开预览版。它仍不是最终 v1.0，因为原生可见高亮、signed/notarized pkg、跨机器安装和单文档完整验收仍缺发布证据。

### 2026-06-25 v0.4.26 发布：Codex CLI 启动超时与发送按钮重复提示

本轮把 `v0.4.25` 之后 main 分支上的用户可见修复归档为 `v0.4.26`，并重新生成公开下载包：

- Codex CLI 若返回 `Error: timed out waiting for cloud config bundle after 15s`，Companion 会把它识别为启动期网络/代理/登录配置问题，自动重试一次；仍失败时显示中文可操作提示，说明这不是当前 PDF、脑图或 MarginNote 上下文错误。
- 设置页 readiness 文案从“真实 AI 已配置”改成“真实 AI 后端已发现”，避免把“找到 CLI 路径”误解成“已经真实生成成功”。
- 底部发送按钮保持两行 `发送 / 可排队`；全局运行中按钮 `data-busy=queue-available` 的 `::after` 提示已排除 `#sendButton`，避免出现第三行重复 `可排队`。

验证结果：

```text
python3 -m unittest discover -s tests
371 tests passed

python3 -m py_compile companion.py runtime_config.py update_manager.py doctor.py release_acceptance.py release_smoke_test.py package_release.py prepare_release_handoff.py send_action.py single_document_acceptance.py build_pkg.py notarize_pkg.py
PASS

node --check extension/codex.mn.assistant/web/app.js
PASS

python3 release_smoke_test.py release/CodexCompanion-0.4.26-latest-dist.zip
PASS

python3 release_smoke_test.py release/CodexCompanion-0.4.26-latest-dist.zip --install-dry-run
PASS
```

结论：`v0.4.26` 是包含 Codex CLI 超时重试、AI 后端文案澄清和发送按钮重复提示修复的公开预览版。它仍不是最终 v1.0，因为原生可见高亮、signed/notarized pkg、跨机器安装和单文档完整验收仍缺发布证据。

### 2026-06-24 15:11 v0.4.25 双语文档与诊断日志重构发布

本轮把 GitHub 默认 README 改为英文首页，并新增完整中文 `README.zh-CN.md`。两个 README 顶部互相链接，release zip 和 `release_smoke_test.py` 都要求包含双语 README。`README-FIRST.txt` 也提示解压包用户查看英文/中文 README。

代码侧把诊断日志脱敏、裁剪、读取和清空逻辑从 `companion.py` 抽到 `diagnostic_log.py`，保留 `companion.append_diagnostic_log/read_recent_diagnostic_logs/clear_diagnostic_logs` 等原有 API。发布包 smoke 也新增 `companion/diagnostic_log.py` 必需文件检查，避免打包时漏掉新模块。

版本已提升到 `0.4.25`，涉及 Companion、doctor、release acceptance、single-document acceptance、release handoff、MN4 manifest、MN4 `PluginVersion`、README、release checklist、package/smoke/pkg builder 默认版本。当时 `CHANGELOG.md` 已把原 `Unreleased` 内容归档为 `0.4.25 - 2026-06-24`。

验证结果：

```text
python3 -m unittest discover -s tests
368 tests passed

python3 -m py_compile companion.py diagnostic_log.py runtime_config.py update_manager.py doctor.py release_acceptance.py release_smoke_test.py package_release.py prepare_release_handoff.py send_action.py single_document_acceptance.py build_pkg.py notarize_pkg.py
PASS

node --check extension/codex.mn.assistant/web/app.js
node --check extension/codex.mn.assistant/main.js
node --check extension/codex.mn.assistant/CodexWebPanelController.js
PASS

python3 release_smoke_test.py release/CodexCompanion-0.4.25-latest-dist.zip
PASS sha256=e76fc13c4878df9e67d60d2e134eae485bad8c0576604122c844d3d9e3dac8a9 files=108

python3 release_smoke_test.py release/CodexCompanion-0.4.25-latest-dist.zip --install-dry-run
PASS installDryRun=True
```

GitHub Release 已创建：`v0.4.25`，asset 为 `CodexCompanion-0.4.25-latest-dist.zip`，digest 与本地 sha256 一致。

本机插件已替换并重启：`plutil` 显示 MN4 扩展 manifest `version=0.4.25`；Companion `/status` 返回 `pluginVersion=0.4.25`；重启 MarginNote 4 后，`/status.mnRuntime` 显示 `ready=true`、`webControlsReady=true`、`nativeApiReady=true`、`staleRuntime=false`、`runtimeHandlerStale=false`、`missingNativeHandlerFeatures=[]`。

复跑 `release_acceptance.py release/CodexCompanion-0.4.25-latest-dist.zip --json` 后：

```text
PASS: unit_tests, syntax_checks, release_zip_smoke, install_dry_run, runtime_web_controls, native_api_matrix
WARN: release_maintainer_prerequisites
BLOCK: native_visible_highlight, release_sha256_manifest, signed_pkg, notarized_pkg, cross_machine_install, single_document_acceptance
```

结论：0.4.25 是可下载和本机可运行的公开预览版，GitHub/OneDrive/release zip/运行态基础 gate 已对齐；它仍不是最终 v1.0，因为原生可见高亮、signed/notarized pkg、跨机器安装、单文档完整验收和 pkg hash manifest 证据未补齐。

### 2026-06-12 17:05 高亮入口改为下一选区优先

继续处理高亮“点了不好用”的焦点问题：主界面和自定义按钮里的 `request_native_highlight_selection` 从“高亮选区”改为“高亮下一选区”。后端队列命令新增 `preferNextSelection=true`；MN4 native handler 收到后，如果当前没有活跃 PDF 选区，会直接进入一次性的 `nativeHighlightNextSelectionArmed` 等待模式，用户回到原文重新选中文字即可触发；如果当前仍有有效选区，则继续立即调用官方 `highlightFromSelection()`。这避免 Web 面板按钮抢焦点后先失败再让用户理解隐藏流程。

同时把 `PopupMenuOnSelection` observer 注册/注销改成和已安装 DeepL/SearchInEudic 扩展示例一致的 `self` 对象写法，降低 JSB 桥接差异风险。新增/更新测试先红后绿，覆盖 observer 注册对象、`preferNextSelection` payload、Web 主按钮文案和 hint。当前这仍不是可见高亮完成证据；发布 gate 仍要求同一 topic/book 的 `nativeHighlightSelectionPosted`、`ZHIGHLIGHTS` blob 和页面可见高亮。

### 2026-06-12 16:55 主界面按钮分区再收敛

按用户反馈“按钮分布乱、有的不好用”继续调整 Web 面板：`primaryActionGrid` 继续只保留 2x2 高频任务“解释 / 制卡 / 新建脑图 / 精读”；`goalRunPanel` 变成独立的一次性目标区，`goalActionStrip` 只负责目标按钮和目标状态；移除默认折叠的 `secondaryToolsPanel` / `secondaryToolsSummary`，让 `workflowActionPanel` 常驻显示当前脑图工具 `mindmapToolPanel` / `mindmapActionGrid` 和原文工具 `sourceToolPanel` / `toolActionGrid`。状态栏 `runToggleButton` 空闲时改为 `队列`，只刷新/提示 pending 状态，不再代替输入框发送；发送始终由 `sendButton` 负责，避免“开始”和“发送”语义混在一起。

新增/更新静态契约先红后绿：Web 控件清单、doctor、单文档验收和文档测试均要求 `goalRunPanel`、常驻 `workflowActionPanel`、`mindmapToolPanel`、`sourceToolPanel`，并明确不再要求 `secondaryToolsPanel` / `secondaryToolsSummary`；队列按钮测试要求空闲态显示 `队列` 且 `runToggle()` 不再调用 `sendAction('chat')`。定向验证 `python3 -m unittest tests.test_web_controls_static ...` 已通过 88 项。

### 2026-06-12 16:30 PDF 选区菜单 observer 注册补强

继续处理单文档验收剩余的 `selection_popup_highlight` 阻塞。当前事件流没有任何 `selectionPopupHighlight*` 通知类事件，说明问题更接近“插件没有收到 PDF 选区弹出菜单通知”，而不是菜单 item 创建失败。根因假设是旧实现只在 `notebookWillOpen` 注册 `PopupMenuOnSelection` observer；如果插件/Web 面板在 notebook 已打开后热刷新，`notebookWillOpen` 不一定再次触发，导致 observer 漏挂。

本轮新增 `registerSelectionPopupObserver(source)` / `unregisterSelectionPopupObserver(source)`，在 `sceneWillConnect` 即注册 `PopupMenuOnSelection`，`notebookWillOpen` 作为幂等补注册，断开/关闭时注销；插件会记录 `selectionPopupHighlightObserverRegistered`、`selectionPopupHighlightObserverFailed` 等事件。`single_document_acceptance.py` 和 Companion 高亮向导已接入这些事件：如果 observer 已注册但仍没有菜单 installed，会明确提示“observer registered, but no PDF selection popup notification has been observed yet”，不再只显示缺少 `selectionPopupHighlightMenuInstalled`。

新增/更新测试覆盖 observer scene 注册、单文档 observer-only 诊断、Companion 高亮向导 observer-only 状态，并给 native handler 加入 `selection-popup-scene-observer-v1` 指纹。当前打开中的 MN4 进程仍加载旧 `main.js`，`refresh_mn_runtime.py` 已正确报 `runtimeHandlerStale=True`、缺少 `selection-popup-scene-observer-v1`；需要重新打开 Codex 面板或重启 MarginNote 4 后再刷新运行态证据。

### 2026-06-12 16:20 单文档验收自动发现高亮证据

继续处理“有的按钮不好用”的可诊断性问题：`single_document_acceptance.py` 在未传 `--native-highlight-evidence` 时，会自动从 `release/evidence`、release 根目录、项目根目录、当前目录和桌面发现最新 native highlight evidence，并优先使用同一 topic/book 的证据。高亮阻塞现在会在 `detail` 和 `evidence.nativeHighlightEvidence` 中带出 `sourcePath`、`autoDiscovered`、`evidenceScope`、`problems`、`attempt` 和 blob 诊断，不再只显示 `{}`。

新增测试 `test_cli_auto_discovers_default_native_highlight_evidence` 和 release gate nextActions 断言先红后绿。当前真实同文档验收仍为 `13/15`，剩余阻塞是 `native_highlight_visible` 和 `selection_popup_highlight`；其中高亮阻塞已能指出最近 evidence 为 `release/evidence/codex-companion-native-highlight-evidence-current.json`，当前原因是 `native-highlight-attempt-armed-next-selection`、`missing-nativeHighlightSelectionPosted` 和 `native-highlight-blobs-not-ok`。

### 2026-06-12 16:10 主界面按钮抽屉化收敛

本轮按用户反馈“按钮分布乱、有的不好用”继续收敛：`goalActionStrip` 不再单独占一整行，而是内联到常用任务标题区，保留目标按钮和一次性目标状态；`primaryActionGrid` 继续只放 2x2 高频任务“解释 / 制卡 / 新建脑图 / 精读”；`secondaryToolsPanel` 改为默认折叠的工具抽屉，展开后由 `workflowActionPanel` 同时显示当前脑图工具 `mindmapToolPanel` / `mindmapActionGrid` 的“补到当前 / 重组当前”和原文工具 `sourceToolPanel` / `toolActionGrid` 的“高亮 / 导出 / 状态”。运行中可用按钮增加虚线边框和“可排队”提示，避免看起来像整体置灰或坏掉。

新增静态契约 `test_chat_command_bar_uses_primary_tasks_plus_one_collapsed_tool_drawer` 先红后绿，要求主界面只露出常用任务和一个工具抽屉，目标内联在常用任务区，脑图/原文工具同属折叠工具抽屉。同步更新 Web 静态测试、README、产品规格、用户手册、发布矩阵和 checklist。

### 2026-06-12 15:35 按钮分布再次收敛

本轮按“按钮分布乱、有的不好用”继续收敛对话页命令条：`goalToggleButton` 保持在 `goalActionStrip`，和一次性目标状态在同一条；`primaryActionGrid` 只保留 2x2 常用动作“解释 / 制卡 / 新建脑图 / 精读”；当前脑图工具 `mindmapToolPanel` 直接显示“补到当前 / 重组当前”，避免合并脑图入口藏在深层折叠区；原文工具折叠到 `secondaryToolsPanel`，展开后由 `sourceToolPanel` / `toolActionGrid` 显示“高亮 / 导出 / 状态”。

新增静态契约 `test_command_bar_has_separate_goal_quick_mindmap_and_source_tool_rows` 先红后绿，要求目标、常用动作、当前脑图和原文工具四类入口互不混排。同步更新 Web 静态测试、发布文档测试、README、产品规格、发布矩阵和 release checklist。验证结果：`python3 -m unittest tests/test_web_controls_static.py` 通过 83 项；`python3 -m unittest discover tests` 通过 337 项；`python3 -m unittest tests/test_release_docs.py` 通过 2 项；`node --check` 对 Web 面板 JS 和 `main.js` 通过；`python3 -m py_compile` 对关键 Python 脚本通过。运行态刷新证据 `release/evidence/CodexCompanion-MNRuntimeEvidence-command-layout-v12.json` 显示 `ready=true`、`staleRuntime=false`、Web controls 104 个且 `missing=""`。release zip/pkg 已重建并同步 OneDrive，hash 分别为 `9d72254268964eef20df91e5f6f09c3d60b39d14bc9a1cdffd38e05490cbc70d` 和 `d8df44b8c003dc5cd310be0dbad00e7bdb4c372304e6490a3636412edec34be0`；`release_acceptance.py --json` 仍未放行，当前剩余阻塞为 `native_visible_highlight`、`signed_pkg`、`notarized_pkg`、`cross_machine_install` 和 `single_document_acceptance`，`release_sha256_manifest` 已恢复 PASS。

### 2026-06-12 14:25 按钮布局与填入动作最终收敛

本轮继续处理“按钮分布乱、有的不好用”：目标入口从主任务网格移到 `goalActionStrip`，和一次性目标状态放在同一条；`primaryActionGrid` 改为 2x2，只保留“解释 / 制卡 / 脑图 / 精读”；脑图工具与原文工具在窄面板下默认竖排，避免 390px 面板中按钮挤压。按钮中心的预设/自定义“填入”现在会显示 `stagedActionLine`，用户可以修改输入框后再点“发送”，仍按原按钮动作执行；点 `clearStagedActionButton` 可改回普通问 Codex。直接点击主操作按钮会覆盖待发送动作，避免旧 staged action 误触发。

新增/更新静态契约覆盖：目标按钮必须位于 `goalActionStrip`；主操作网格必须是 2x2；`stagedActionLine` 和 `clearStagedActionButton` 必须由 WebView、doctor 和单文档验收同时识别；预设填入后不再因 prompt 被编辑而退化成普通聊天。验证结果：新增测试先红后绿；`python3 -m unittest discover tests` 通过 324 项；Python 语法检查通过；`node --check` 对 Web 面板 JS 和 `main.js` 通过；`python3 doctor.py` 返回 `0 fail, 6 warn, 12 ok`，`MN4 runtime Web controls` 报告 98 controls；`single_document_acceptance_summary` 当前为 12/15，通过 Web controls、聊天/解释、卡片、新建脑图、PDF 缓存、设置、上传、目标、队列、历史和标注 PDF 导出，剩余阻塞为 `mindmap_merge`、`native_highlight_visible`、`selection_popup_highlight`。

发布包已重建并同步 OneDrive；精确 zip/pkg hash 以 release 目录和 OneDrive 镜像目录里的外部 `SHA256SUMS.txt` 为准，避免在包内文档写入自身 hash 后造成自引用漂移。`python3 release_smoke_test.py release/CodexCompanion-0.4.0-latest-dist.zip --install-dry-run` 通过。`release_acceptance.py` 仍按预期 BLOCKED：当前阻塞包括 stale native handler 指纹、可见原生高亮证据、签名 pkg、公证 pkg、跨机器安装证据，以及单文档验收剩余 3 项；本轮没有擅自重启 MarginNote 4。

### 2026-06-12 13:45 本文档验收按钮和设置页诊断分区

本轮继续按用户反馈处理“按钮分布乱、有的不好用”：主对话页当前保持目标状态条、2x2 主操作、脑图工具区和原文工具区，不再继续往主界面塞诊断按钮；设置页“发布与连接”新增 `singleDocumentAcceptanceButton`，独立于 `releaseAcceptanceButton`。`single_document_acceptance_summary` 是轻量的当前文档验收动作，会读取当前 `topicid/bookmd5` 的 `events.jsonl`、默认 `release/evidence/action-results.jsonl` 和最新 native highlight evidence，在面板内显示通过/总数、阻塞项和每项 PASS/BLOCK。它用于判断“当前这篇文档里的按钮是否真的可用”，不替代最终 `release_acceptance.py` 发布 gate。

`single_document_acceptance.py` 的 Web controls 检查同步要求新版按钮分区：`promptInput`、`sendButton`、`stagedActionLine`、`clearStagedActionButton`、`goalActionStrip`、`primaryActionGrid`、`mindmapToolPanel`、`mindmapActionGrid`、`sourceToolPanel` 和 `toolActionGrid`。doctor 必需控件清单也新增 `singleDocumentAcceptanceButton`、`singleDocumentAcceptanceLine` 和 `singleDocumentAcceptanceDetail`，避免运行态缺少这个入口时被误判为完整。

TDD 验证：先加入失败测试，确认旧实现会把缺少 `mindmapToolPanel/mindmapActionGrid` 的 Web controls 当作通过、Web 面板缺 `singleDocumentAcceptanceButton`、Companion 不认识 `single_document_acceptance_summary`；实现后定向测试已通过。WebView cache-bust 已提升到 `command-layout-v5`，非重启热重载后最新 `webControlsReady` 上报 `singleDocumentAcceptanceButton` 和 `singleDocumentAcceptanceLine`，`missing=""`。

当前验证结果：`python3 -m unittest discover -s tests` 通过 317 项；Python/JS 语法检查通过；`python3 release_smoke_test.py release/CodexCompanion-0.4.0-latest-dist.zip --install-dry-run` 通过；doctor 为 `0 fail, 6 warn, 12 ok`，`MN4 runtime Web controls` 为 OK 且报告 94 controls。最新本地和 OneDrive zip/pkg hash 以 release 目录和 OneDrive 镜像目录中的外部 `SHA256SUMS.txt` 为准，避免把自引用 hash 写入包内文档。当前 `release_acceptance.py release/CodexCompanion-0.4.0-latest-dist.zip` 返回 BLOCKED，但 `runtime_web_controls` 已 PASS；剩余阻塞为 `native_api_matrix` handler stale、`native_visible_highlight`、`signed_pkg`、`notarized_pkg`、`cross_machine_install` 和 `single_document_acceptance` evidence。后续还需要对真实 MN4 当前 PDF 点击“本文档验收”，用同一文档补齐 PASS evidence。

### 2026-06-12 13:31 主界面按钮三分区收敛

本轮继续按用户反馈处理“按钮分布乱、有的也不好用”的问题：对话页底部仍固定保留 `promptInput` 和 `sendButton`；按钮中心填入 prompt 后显示 `stagedActionLine`，允许用户先修改输入框，点发送仍按原按钮动作执行；`goalActionStrip` 同时放 `goalToggleButton` 和一次性目标状态；`primaryActionGrid` 改为 2x2，只放“解释 / 制卡 / 脑图 / 精读”；“补脑图 / 重组”移入 `mindmapToolPanel` / `mindmapActionGrid`；“高亮 / 导出 / 高亮状态”保留在 `sourceToolPanel` / `toolActionGrid`，窄面板下脑图/原文工具默认竖排。这样目标、普通生成、脑图结构操作、原文工具和设置诊断不再混在同一组按钮里。

新增/更新静态契约覆盖：doctor/Web 控件清单要求 `stagedActionLine`、`clearStagedActionButton`、`mindmapToolPanel` 和 `mindmapActionGrid`；目标按钮必须位于 `goalActionStrip`；主操作网格必须是 2x2 且只放高频生成入口；补脑图和重组必须位于脑图工具区；高亮、导出和高亮状态必须位于原文工具区；390px 小面板下主操作保持 2 列，脑图工具 2 列，原文工具 3 列。忙碌时继续点击动作会显示“已加入队列”的状态反馈，并继续走统一 `executeAction` 入队路径。

验证结果：新增布局契约先按 TDD 失败，再修改实现后通过；`python3 -m unittest tests.test_web_controls_static` 通过 72 项；`python3 -m unittest discover -s tests` 通过 315 项；`python3 release_smoke_test.py release/CodexCompanion-0.4.0-latest-dist.zip --install-dry-run` 通过；`python3 build_pkg.py release/CodexCompanion-0.4.0-latest-dist.zip --json` 已重建 unsigned pkg。最新 zip hash 为 `7bcb19ea05e8cccd2f383a0ea6c7abd2607498cd2cb584712855862025200f1c`，最新 pkg hash 为 `5fcc5a035b5bb68badadea082b77b2b7e142079cd3d3c6cf8e31751361649376`，本地和 OneDrive `SHA256SUMS.txt` 已同步。

非重启运行态刷新结果：`request_web_panel_reload` 已让 MN4 上报新的 `webControlsReady`，包含 `goalActionStrip`、`primaryActionGrid`、`mindmapToolPanel`、`mindmapActionGrid`、`sourceToolPanel` 和 `toolActionGrid`，`missing=""`；doctor 显示 `MN4 runtime Web controls` 为 OK。`native_api_matrix` 仍因 MN4 宿主脚本 handler 指纹 stale 而阻塞，这需要重新打开 MN4 插件宿主或重启 MarginNote 4 后再刷新原生能力；本轮没有擅自重启 MarginNote 4。

### 2026-06-12 13:16 单文档全流程验收 gate

本轮在按钮布局收敛后新增 `single_document_acceptance.py`，作为“同一篇文档里这些按钮到底好不好用”的结构化验收入口。脚本读取同一 `topicid/bookmd5` 的 `events.jsonl`、action result JSON/JSONL 和 native highlight evidence，检查 Web 控件、MN 原生能力、聊天/解释、制卡、新建脑图、补当前脑图、缓存 PDF、原生高亮、选区菜单、设置、上传、一次性目标、队列、历史和导出标注副本。跨文档证据会被拒绝，例如 `createCardsFinished` 事件来自其它 `bookmd5` 时，`card_write` 会 BLOCK。

`release_acceptance.py` 现在把 `single_document_acceptance` 作为最终硬门槛，并能自动发现 `codex-companion-single-document-acceptance-*.json`。`prepare_release_handoff.py` 已加入 `single-document-acceptance-template.json`、handoff 命令说明和证据分拣：PASS 证据进入 `evidence/`，未完成或 `ok=false` 的证据进入 `diagnostics/evidence/`。发布包根目录现在包含 `single_document_acceptance.py`，doctor 和 smoke test 都会检查该入口。

后续继续补强易用性：`send_action.py --record` 已能把 action、topic/book scope、endpoint、payload 和 result 追加到 `release/evidence/action-results.jsonl`；`single_document_acceptance.py` 在不传 `--action-results` 时会默认读取该文件；发布包根目录新增 `Collect Single Document Acceptance.command`，可双击从当前 MarginNote 默认 topic/book、默认 action-results 日志和最新 native highlight evidence 生成桌面上的 `codex-companion-single-document-acceptance-*.json`。

验证结果：`python3 -m unittest discover -s tests` 通过 314 项；`python3 -m py_compile doctor.py release_acceptance.py release_smoke_test.py package_release.py prepare_release_handoff.py send_action.py single_document_acceptance.py` 通过；`zsh -n 'Collect Single Document Acceptance.command'` 通过；`python3 release_smoke_test.py release/CodexCompanion-0.4.0-latest-dist.zip --install-dry-run` 通过；`python3 build_pkg.py release/CodexCompanion-0.4.0-latest-dist.zip --dry-run --json` 和实际 unsigned pkg 构建均通过。最新 zip/pkg 的精确 hash 只写入 release 和 OneDrive 的外部 `SHA256SUMS.txt`，避免在 zip 内文档写入自身 hash 后造成自引用漂移。

当前 `release_acceptance.py release/CodexCompanion-0.4.0-latest-dist.zip --mn-runtime-evidence release/evidence/CodexCompanion-MNRuntimeEvidence-current.json` 正常返回 BLOCKED：已通过 `unit_tests`、`syntax_checks`、`release_zip_smoke`、`install_dry_run`、`runtime_web_controls`、`native_api_matrix` 和 `release_sha256_manifest`；仍阻塞 `native_visible_highlight`、`signed_pkg`、`notarized_pkg`、`cross_machine_install` 和 `single_document_acceptance`，并保留 `release_maintainer_prerequisites` WARN。重启 MarginNote 4 后，最新 `nativeApiCapabilities.handlerFeatures` 已包含 `native-highlight-prefer-next-selection-v1`，`runtimeHandlerStale=False`。最新 handoff 可由 `prepare_release_handoff.py` 或 `Prepare Release Handoff.command` 生成，并同步到 OneDrive 的 `Codex Companion/Release Handoff` 目录。

### 2026-06-12 17:05 高亮下一选区指纹与 doctor 健康检查

本轮继续加固“高亮下一选区”按钮：已安装 `main.js` 的 `NativeHandlerFeatures` 新增 `native-highlight-prefer-next-selection-v1`，`companion.py`、`doctor.py` 和 `release_acceptance.py` 的 required handler feature 清单同步更新。这样当 Web 面板已经刷新、但 MarginNote 4 进程仍运行旧原生 `main.js` 时，设置页和 doctor 会明确显示缺少 `native-highlight-prefer-next-selection-v1`，提示重新打开 Codex 面板或重启 MarginNote 4，而不是误判原生 handler 已经是最新。

同时修复一个“Companion 未运行”误报来源：doctor 的服务可达性检查改用轻量 `/health` endpoint；`/status` 仍用于展示模型、代理和后端详情，但 `/status` 大 payload 偶发超时不再把服务判为 FAIL。

验证结果：`python3 -m unittest discover tests` 通过 352 项；`python3 -m py_compile companion.py doctor.py single_document_acceptance.py release_acceptance.py package_release.py build_pkg.py` 通过；`node --check` 对已安装扩展的 `main.js` 和 `web/app.js` 通过；`doctor.py` 当前为 `0 fail, 5 warn, 13 ok`；`single_document_acceptance.py` 当前为 `13/15`，仍阻塞 `native_highlight_visible` 和 `selection_popup_highlight`。剩余 WARN/BLOCK 是原生可见高亮证据、当前 MN4 原生 handler stale、pkg 签名/公证、跨机器安装证据、MN 数据库权限和维护者证书/凭证。

2026-06-12 17:12 更新：已通过用户批准执行 `restart_marginnote4`，MarginNote 4 重新打开后运行 `refresh_mn_runtime.py --try-addon-url-reload --output /tmp/codex-mn-runtime-after-restart.json`，结果为 `mnRuntime.ready=True`、`runtimeHandlerStale=False`、`missingNativeHandlerFeatures=[]`，并已保存为 `release/evidence/CodexCompanion-MNRuntimeEvidence-current.json` 和 OneDrive evidence 镜像。随后触发 `request_native_highlight_selection`，运行中 MN4 handler 记录 `nativeHighlightCommandPrepared preferNextSelection=true` 和 `nativeHighlightNextSelectionArmed reason=prefer-next-selection`，证明“高亮下一选区”不再走旧的 missing-selection 分支。新增发布包根目录 `Restart MarginNote 4.command`，当 `Refresh MN Runtime.command` 仍显示旧 handler 时，用户可双击并确认后调用同一路 `restart_marginnote4` 动作。

### 2026-06-12 13:10 主操作区按任务类型重排

本轮继续按用户反馈处理“按钮分布乱、有些按钮不好用”的问题：对话页底部仍固定保留 `promptInput` 和 `sendButton`；一次性目标从任务网格中移出，单独放进 `goalActionStrip`；`primaryActionGrid` 改成 3+3 两行生成区，依次放“解释 / 制卡 / 脑图 / 补脑图 / 重组 / 精读”；原文相关动作放进 `sourceToolPanel`，由 `toolActionGrid` 显示“高亮 / 导出 / 高亮状态”。这样普通生成、一次性目标、原文工具和设置诊断不再混在一个 4 列网格里。

新增/更新静态契约覆盖：doctor/Web 控件清单要求 `goalActionStrip` 和 `sourceToolPanel`，不再要求 `moreToolsPanel` / `moreToolsSummary`；主网格必须只有 6 个生成/脑图动作；高亮、导出和高亮状态必须位于原文工具区；390px 小面板下常用任务和原文工具都使用 3 列布局，按钮仍保持统一高度和提示。

### 2026-06-12 12:46 主操作区 4+4 收敛

本轮继续按用户反馈处理“按钮分布乱、部分入口不好用”的问题：对话页底部仍固定保留 `promptInput` 和 `sendButton`；`primaryActionGrid` 改成稳定的 4+4 两行主操作区，依次放“解释 / 制卡 / 脑图 / 补脑图 / 精读 / 目标 / 高亮 / 导出”。`goalToggleButton` 现在是主操作网格里的同级按钮，不再藏在设置页或标题行；补当前脑图、高亮原文和导出 PDF 也不再藏到深层折叠区。`moreToolsPanel` 只保留低频“重组 / 高亮状态”，避免主界面同时暴露多套运行入口。

按钮中心同步改成模板管理语义：预设模板按钮从“试用”改为“填入”，点击后只把 prompt 和对应动作暂存到输入框，用户点“发送”才按暂存动作执行；若任务正在运行，仍走自动入队。这样预设不会误触发模型请求，也不会绕过发送按钮。用户可继续把预设“添加”为自定义按钮，再决定是否置顶到主界面。

新增/更新静态契约覆盖：主操作网格包含 7 个 `data-action` 主动作和 1 个目标按钮；预设模板必须调用 `stagePromptAction()` 而不是直接 `runPromptAction()`；暂存 prompt 通过发送按钮按原动作执行；主操作按钮在 390px 面板下统一最小高度。验证结果：`python3 -m unittest discover -s tests` 通过 305 项；`python3 -m py_compile companion.py doctor.py release_acceptance.py package_release.py build_pkg.py refresh_mn_runtime.py prepare_release_handoff.py` 通过；`node --check` 对 Web 面板 JS 通过。用系统 Microsoft Edge headless 渲染 390px 宽度检查，主操作区为两行，每行 4 个按钮，8 个按钮高度均为 44px，无横向溢出和文字溢出。

### 2026-06-12 12:34 Runtime handler 指纹 fail-closed

本轮修复一个会影响发布验收可信度的问题：Companion `/status.mnRuntime` 已经有 `requiredNativeHandlerFeatures` / `nativeHandlerFeatures` / `missingNativeHandlerFeatures` 字段，但当 Companion 进程无法从已安装 `main.js` 读到 handler feature 字符串时，旧逻辑会返回空 required 列表，导致运行态可能被误判为不缺 native handler 指纹。现在 `companion.py`、`doctor.py` 和 `release_acceptance.py` 都改成 fail-closed：当前版本要求的 `native-highlight-arm-next-selection-default` 与 `native-highlight-command-prepared` 会始终作为 required handler features；只有最新 `nativeApiCapabilities` 事件显式上报这些 feature，运行态 gate 才能通过。

新增回归测试覆盖三层：Companion 状态、doctor 运行态诊断、release acceptance 证据校验在安装源缺失或不可确认时都必须阻断。验证结果：`python3 -m unittest discover -s tests` 通过 303 项；`python3 -m py_compile companion.py doctor.py release_acceptance.py package_release.py build_pkg.py refresh_mn_runtime.py prepare_release_handoff.py` 通过；`node --check` 对 Web 面板 JS 和 `main.js` 通过。重启 Companion 后，`/status` 当前返回 `ready=False`、`staleRuntime=True`、`runtimeHandlerStale=True`、`runtimeHandlerStaleActions=['native-handler-features']`，并列出两个 missing handler features；doctor 同步显示当前打开的 MN4 面板运行态 stale，缺 `newCustomButtonButton` 和 handler 指纹。下一步仍需重新打开 Codex 面板或重启 MarginNote 4 后采集新的 runtime evidence。

### 2026-06-12 12:24 主按钮布局重排

本轮继续按用户反馈处理“按钮分布乱、部分入口不好用”的问题：对话页命令条改为“输入行 + 常用任务标题行 + 四个主任务 + 折叠工具 + 用户置顶 prompt”。`primaryActionGrid` 只保留“解释 / 制卡 / 脑图 / 精读”四个等宽任务；`goalToggleButton` 仍是主界面按钮级入口，但移到常用任务标题行右侧，避免一次性长任务和普通任务挤在同一个网格里；`moreToolsPanel` 继续折叠“高亮选区 / 导出PDF / 补节点 / 重组”，summary 增加“高亮 / 导出 / 脑图”辅助提示。

按钮中心同步改成管理台：预设模板继续提供“试用”和“添加”，并显示动作类型；自定义按钮列表新增“置顶 / 取消置顶 / 移出”直接操作，新增 `newCustomButtonButton` 清空表单并进入新建状态。doctor 的 Web 控件清单已加入 `newCustomButtonButton`，静态测试会验证目标不在 `primaryActionGrid` 内、主任务网格为四个按钮、工具仍收进 `moreToolsPanel`。

### 2026-06-12 12:05 主界面按钮再收敛

本轮继续按用户反馈整理按钮分布：对话页底部仍固定保留输入框和 `sendButton`；一级常用任务只保留“解释 / 制卡 / 脑图 / 精读 / 目标”五个高频入口；原文和脑图工具不再常驻挤在主操作下方，而是收进 `moreToolsPanel` 的“更多工具”折叠区，展开后仍使用 `toolActionGrid` 提供“高亮选区 / 导出PDF / 补节点 / 重组”。按钮中心也改为模板管理语义：预设 prompt 以 `preset-template-item` 呈现，提供“试用”和“添加”，添加后才进入自定义按钮列表，再由用户决定是否勾选“主界面”。

高亮交互同时补了一条焦点丢失路线：`request_native_highlight_selection` 队列命令带 `armIfMissingSelection=true`；如果 Web 面板按钮让 PDF 选区消失，MN4 插件会记录 `nativeHighlightNextSelectionArmed`，等待用户回到 PDF 重新选中文字；下一次 `PopupMenuOnSelection` 会消费 armed 状态并记录 `nativeHighlightNextSelectionConsumed`，再走官方 `highlightFromSelection()`。这不是可见高亮通过证据，发布 gate 仍要求 `nativeHighlightSelectionPosted`、同 topic/book 的 `ZHIGHLIGHTS` blob 和页面可见高亮。

后续加固：插件端不再依赖后端字段能否被 JSB 正确桥接。`handleNativeQueueCommand()` 对所有 `highlight_current_selection` 队列命令默认设置 `highlightCommand.armIfMissingSelection = true`，并记录 `nativeHighlightCommandPrepared` 诊断事件；`highlightCurrentSelection()` 也会把原生高亮队列命令视作可进入 armed 模式。

验证结果：`python3 -m unittest discover -s tests` 通过 297 项；Python 编译和 `node --check web/app.js main.js` 通过；`release_acceptance.py` 汇总显示 `runtime_web_controls`、`native_api_matrix`、`unit_tests`、`syntax_checks`、`release_zip_smoke`、`install_dry_run` 和 `release_sha256_manifest` 均 PASS。当前打开中的 MN4 通过非破坏 addon reload 仍没有热加载最新原生高亮 handler：无选区采证里队列命令已带 `armIfMissingSelection=true`，但事件仍为 `nativeHighlightSelectionFailed reason=missing-selection`。因此 native visible highlight 仍保持 BLOCK，下一步需要用户重新打开或重启 MarginNote 4 后，在 PDF 中选中文本实测 `nativeHighlightNextSelectionConsumed` / `nativeHighlightSelectionPosted` / 同 scope `ZHIGHLIGHTS` / 页面可见高亮。

### 2026-06-12 11:22 Runtime evidence 防误判

本轮收紧 `release_acceptance.py` 的 MN runtime evidence 校验：即使历史 evidence 自报 `staleRuntime=false`，验收也会读取当前 live extension 的 runtime source 文件（`main.js`、`CodexWebPanelController.js`、`web/index.html`、`web/app.js`、`web/app.css` 等）最新 mtime，并与 evidence 内的 `sourceMtime`、`latestEventTs` 或 `generatedAt` 比较。若当前插件文件更新晚于 evidence，`runtime_web_controls` / `native_api_matrix` 不再被旧 evidence 放行，而会要求重新打开 Codex 面板并刷新 MN 能力。

当前实测：刚调整按钮布局后，`doctor.py --json` 正确显示 MN4 运行态 stale；修复后的 `release_acceptance.py --json` 也同步把 `runtime_web_controls` 和 `native_api_matrix` 标为 BLOCK。这样交接包不会把旧运行态证据误当成新 UI 的发布证明。

### 2026-06-11 16:55 主界面按钮分组与 evidence 自动发现

本轮按用户反馈重新整理 Web 对话页按钮分布：输入行仍固定保留 `promptInput` 和 `sendButton`；常用任务区放五个高频入口“解释 / 制卡 / 脑图 / 精读 / 目标”，目标成为第一排同级的一次性任务按钮；工具区改成一条 `toolActionGrid`，高亮选区、导出 PDF、展开和重组作为紧凑工具按钮，不再嵌套原文/脑图分组；诊断和发布类入口仍留在设置页。新增/更新静态契约要求 `toolActionGrid` 和 `healthCheckButton`，并从 doctor 的必需控件清单中移除旧 `workflowActionGroups`、`goalActionPanel`、`sourceActionGrid`、`mindmapActionGrid` 和 `workflowActionGrid`。

同时修复 release evidence 自动发现：没有显式传入 evidence 路径时，`release_acceptance.py` 会优先返回最新有效 release proof；如果都无效，才返回最新诊断结果。`prepare_release_handoff.py` 会同时复制最新有效 release proof 到 `evidence/`，并保留最新无效诊断到 `diagnostics/evidence/`，避免新生成的一份失败证据遮住旧的有效证据。

验证结果：`python3 -m unittest discover -s tests` 通过 264 项；Python/JS/zsh 语法检查通过；用本机 Microsoft Edge headless 渲染 390px 宽度检查，按钮无横向溢出、无重叠，`webControlsReady` 上报的新控件清单 `missing=""`。

### 2026-06-11 16:20 Release handoff 证据分类

本轮修复 release handoff 的证据归档逻辑：`prepare_release_handoff.py` 不再把 stale runtime、旧 handler 或 `ok=false` 的 evidence 放进正式 `evidence/` 目录。只有满足对应 release gate 的证据才进入 `evidence/`；不完整证据会被复制到 `diagnostics/evidence/`，并在 `RELEASE_HANDOFF.md` 的 `Diagnostic Evidence` 区域标注为 `not release proof`，避免发布交接时把排错附件误认为通过证明。

新增回归测试覆盖 `ok=false` 且 `runtimeHandlerStale=true` 的 MN runtime evidence；该文件现在只会出现在 `diagnostics/evidence/`，不会出现在正式 `evidence/`。

随后进一步收紧跨机器 evidence 归档：`ok=true` 还不够，cross-machine evidence 的 package sha256 必须匹配当前 handoff 所携带的 latest zip，且 `MN4 extension manifest`、`Companion service`、`LaunchAgent` 三个安装检查都为 true，才会进入正式 `evidence/`；旧 zip 的跨机器证据会降级到 `diagnostics/evidence/`。

本轮继续收紧 native highlight evidence 归档：`ok=true` 还不够，handoff 现在要求 `events.latestPosted.event=nativeHighlightSelectionPosted`、`pluginVersion` 匹配当前插件版本、posted event 带 topic/book scope，且 `highlightBlobCheck` 在同一 scope 下 `status=OK`、`native_highlight_blobs>0`，才会进入正式 `evidence/`。缺事件、缺 blob、scope 不匹配或手工伪造的最小 `ok=true` JSON 会降级到 `diagnostics/evidence/`。

### 2026-06-11 12:21 按钮布局收敛与原生高亮采证入口

本轮继续收敛 Web 对话页按钮布局：顶部状态栏只保留连接、开始/停止、队列和运行状态；当前内容区右侧提供“刷新”；底部输入行固定保留 `promptInput` 和 `sendButton`；常用任务区放解释、制卡、脑图、精读和目标；工具区改成一行扁平 `toolActionGrid`，依次放高亮选区、导出标注 PDF、补节点、重组，不再嵌套原文/脑图分组。主界面常用 prompt 只显示用户在按钮页勾选的自定义按钮，最多 4 个；没有勾选时不再自动塞入与主操作重复的默认 prompt。发布包根目录新增 `Collect Native Highlight Evidence.command`，用于真实 PDF 选区高亮后的结构化采证；采证现在会先请求打开中的 MN4 插件执行一次 `request_native_highlight_selection`，等待 `nativeHighlightSelectionPosted` 或 `nativeHighlightSelectionFailed`，再按最新 posted event 的 topic/book 查询同一作用域 `ZHIGHLIGHTS`，拒绝缺 scope、scope 不匹配、blob 为 0 或本次尝试失败的证据。

验证结果：

```text
python3 -m unittest discover -s tests
Ran 205 tests OK

node --check <live extension>/web/app.js
node --check <live extension>/main.js

python3 release_smoke_test.py
python3 release_smoke_test.py --install-dry-run
```

重新生成的 zip/pkg 已同步到 OneDrive；精确 hash 仍只写入 release 目录和 OneDrive 镜像目录中的外部 `SHA256SUMS.txt`。

最新验收摘要：

```text
python3 release_acceptance.py --json
releasable=false
PASS: unit_tests, syntax_checks, release_zip_smoke, install_dry_run, release_sha256_manifest
BLOCK: runtime_web_controls, native_api_matrix, native_visible_highlight, signed_pkg, notarized_pkg, cross_machine_install
WARN: release_maintainer_prerequisites
```

`runtime_web_controls` 和 `native_api_matrix` 当前阻塞的直接原因是刚更新 Web 资源后，MN4 仍在运行旧 Web 控件事件和旧 native probe 事件；需要重新打开 Codex 面板，必要时由用户确认后重启 MarginNote 4，再点“刷新MN能力”重新采证。其余硬阻塞仍是原生可见高亮、签名 pkg、公证 pkg 和跨机器安装证据。

### 2026-06-11 12:04 原生高亮 selector 不可枚举时的尝试路线

当前 MN4 运行态能发现 `studyController.readerController`，但无法枚举 `highlightFromSelection` selector。为避免“控制器存在但 selector 不可枚举”时直接失败，本轮把高亮逻辑改为：只要能拿到 PDF/reader document controller 且有选区文本，就尝试调用官方 `highlightFromSelection()`；事件会记录 `selectorVerified` 和 `attemptedUnverifiedSelector`，成功仍走 `nativeHighlightSelectionPosted`，失败走 `nativeHighlightSelectionFailed reason=exception`，不写 SQLite、不伪造高亮。Web 面板按钮触发的 `highlight_current_selection` 队列命令现在也默认带 `allowCachedSelectionText=true`，并使用最近一次 `PopupMenuOnSelection` 缓存文本，减少点击浮窗后焦点切走导致提前 `missing-selection`。

验证结果：

```text
python3 -m unittest \
  tests.test_resizable_panel_static.ResizablePanelContractTest.test_native_highlight_attempts_official_selector_even_when_bridge_does_not_advertise_it \
  tests.test_resizable_panel_static.ResizablePanelContractTest.test_native_highlight_queue_command_preserves_cached_selection_for_web_button \
  tests.test_resizable_panel_static.ResizablePanelContractTest.test_selection_popup_highlight_uses_cached_selection_without_early_reject
Ran 3 tests OK

python3 -m unittest \
  tests.test_companion_controls.CompanionControlsTests.test_native_api_capability_matrix_allows_unverified_document_controller_highlight_attempt \
  tests.test_companion_controls.CompanionControlsTests.test_native_api_capability_matrix_marks_selection_highlight_ready \
  tests.test_companion_controls.CompanionControlsTests.test_native_api_capability_matrix_explains_missing_selection
Ran 3 tests OK
```

这仍然不是可见高亮完成证据；发布完成仍要求用户在 MN4 PDF 中选中文本后触发，看到 `nativeHighlightSelectionPosted`、同一 topic/book 作用域内的 `ZHIGHLIGHTS` blob 和页面肉眼可见高亮。

### 2026-06-11 11:44 非重启运行态刷新采证

本轮执行：

```text
python3 refresh_mn_runtime.py --try-addon-url-reload --timeout 60 --interval 2 \
  --output ~/Library/CloudStorage/OneDrive-个人/Codex Companion/evidence/CodexCompanion-MNRuntimeEvidence-latest.json
```

脚本尝试了 `marginnote4app://addon/codex.mn.assistant/...` 的 enable/load/reload/open URL，全部返回 open 成功；随后通过 Companion 发送 `request_native_capability_probe`。MN4 插件在 11:43:20 上报了新的 `nativeApiCapabilities`，所以当时的 `release_acceptance.py --json` 已不再把 `native_api_matrix` 列为 blocker。

当时验收摘要：

```text
python3 release_acceptance.py --json
releasable=false
PASS: unit_tests, syntax_checks, release_zip_smoke, install_dry_run, native_api_matrix, release_sha256_manifest
BLOCK: runtime_web_controls, native_visible_highlight, signed_pkg, notarized_pkg, cross_machine_install
WARN: release_maintainer_prerequisites
```

仍未解决的是 WebView 控件运行态：`latestWebEventTs=2026-06-11T10:23:46+0800`，早于当前已安装 Web/插件文件，因此 `runtime_web_controls` 继续阻塞。证据说明非破坏性 addon URL reload 可以触发 native probe，但没有让 MN4 重新加载 WebView 控件事件；下一步需要用户重新打开 Codex 面板，若仍 stale，再由用户确认后重启 MarginNote 4。

### 2026-06-11 11:40 打包、同步与发布验收

本轮重新生成并同步 RC zip/pkg：

```text
release/CodexCompanion-0.4.0-latest-dist.zip
~/Library/CloudStorage/OneDrive-个人/Codex Companion/CodexCompanion-0.4.0-latest-dist.zip
release/CodexCompanion-0.4.0-latest.pkg
~/Library/CloudStorage/OneDrive-个人/Codex Companion/CodexCompanion-0.4.0-latest.pkg
```

精确 hash 只写入 release 目录和 OneDrive 镜像目录中的外部 `SHA256SUMS.txt`，避免把 hash 写进 zip 内文档后造成自引用漂移。

验证结果：

```text
python3 release_smoke_test.py --install-dry-run
[OK] CodexCompanion-0.4.0-latest-dist.zip
sha256=<see external SHA256SUMS.txt>
files=65
installDryRun=True

python3 release_acceptance.py --json
releasable=false
PASS: unit_tests, syntax_checks, release_zip_smoke, install_dry_run, release_sha256_manifest
BLOCK: runtime_web_controls, native_api_matrix, native_visible_highlight, signed_pkg, notarized_pkg, cross_machine_install
WARN: release_maintainer_prerequisites
```

`runtime_web_controls` 和 `native_api_matrix` 当时阻塞的直接原因是 installed plugin assets 晚于最后一次 MN4 runtime event/probe；后续 11:44 非重启刷新已更新 native probe，使 `native_api_matrix` 通过。`runtime_web_controls` 仍需要重新打开 Codex 面板或确认重启 MN4 后采证。`native_visible_highlight` 仍因当前验收 scope 中 `ZHIGHLIGHTS` 行数为 0 而阻塞。pkg 已生成并同步，但仍是 unsigned / not notarized 内测包。

### 2026-06-11 11:38 原生高亮 document controller resolver 扩展

本轮修复 `documentControllerCandidates()` 的候选路径和诊断稳定性。实现现在对 `studyController` 和 `notebookController` 直接保留稳定 label，并继续用去重后的 alias 扫描覆盖更多 MN4 可能暴露 document controller 的属性，包括 `reader`、`readerView`、`readerVC`、`pdfReader`、`pdfReaderController`、`pdfDocumentController`、`documentViewController`、`docViewController`、`pdfView`，以及 `readerController.documentController`、`readerController.docController`、`readerController.currentDocumentController`、`readerViewController.documentController`、`pdfController.documentController`、`pdfViewController.documentController` 等嵌套路径。

这次更新的目标是提升 `nativeApiCapabilities.documentControllerCandidates`、`nativeHighlightSelectionFailed.candidateLabels` 和 `selectedDocumentControllerLabel` 的可诊断性，方便下一轮在活跃 PDF 选区下定位 MN4 真正可用的 `highlightFromSelection()` 控制器。它不等同于已经完成可见高亮发布验收。

验证结果：

```text
python3 -m unittest tests.test_resizable_panel_static.ResizablePanelContractTest.test_native_document_controller_resolution_covers_reader_pdf_aliases_and_nested_controllers tests.test_resizable_panel_static.ResizablePanelContractTest.test_native_document_controller_resolution_uses_shared_candidates_and_diagnostics
Ran 2 tests in 0.060s
OK

node --check installed MN4 extension main.js
OK

node --check installed MN4 extension web/app.js
OK

python3 -m unittest discover -s tests
Ran 204 tests in 4.514s
OK
```

剩余发布阻塞仍包括：MN4 运行态需要重新加载最新插件后采证、活跃 PDF 选区下的 native visible highlight 证据、签名 pkg、公证 pkg、跨机器安装 evidence。

### 2026-06-11 11:29 运行进度后端状态轮询

本轮增强 WebView 运行中进度显示：`startProgress()` 现在会启动 `startProgressStatusPolling()`，每 1.5 秒 GET `http://127.0.0.1:48761/status`；若后端返回 `run.action`、`run.stage` 或 `run.detail`，前端会同步更新对话里的进度消息，并调用 `renderRunState(run)` 更新底部运行状态。`finishProgress()` 会调用 `stopProgressStatusPolling()` 清理轮询器，避免任务结束后继续请求。这样长任务不再只依赖本地计时和静态阶段文本，用户能看到 Companion 当前报告的动作、阶段和详情。

验证结果：

```text
python3 -m unittest tests.test_web_controls_static.WebControlsStaticTests.test_progress_message_polls_backend_run_state_while_busy
OK

python3 -m unittest discover -s tests
Ran 203 tests in 4.779s
OK

python3 -m compileall -q companion.py doctor.py send_action.py release_smoke_test.py release_acceptance.py package_release.py build_pkg.py notarize_pkg.py refresh_mn_runtime.py verify_after_unlock.py audit_highlights.py tests
OK

node --check installed MN4 extension JS files
OK
```

### 2026-06-11 11:25 产品手册与发布包更新

本轮新增面向普通用户的 `docs/USER_MANUAL.md`，并在 README 发布文档列表中加入该入口。手册覆盖安装、首次启动、面板结构、AI 后端、普通对话、目标任务、自定义按钮、生成卡片、生成脑图、完整精读、高亮与原文清洁、标注 PDF 副本导出、文件上下文、队列/停止/进度、历史、权限、推荐工作流、常见问题、隐私数据位置和当前 RC 限制。

验证结果：

```text
python3 -m unittest discover -s tests
Ran 202 tests in 4.990s
OK

python3 -m compileall -q companion.py doctor.py send_action.py release_smoke_test.py release_acceptance.py package_release.py build_pkg.py notarize_pkg.py refresh_mn_runtime.py verify_after_unlock.py audit_highlights.py tests
OK

node --check installed MN4 extension JS files
OK

python3 release_smoke_test.py --install-dry-run
[OK] CodexCompanion-0.4.0-latest-dist.zip
sha256=<see external SHA256SUMS.txt>
files=65
installDryRun=True

unzip -l release/CodexCompanion-0.4.0-latest-dist.zip | rg "USER_MANUAL|README.md|docs/"
... companion/docs/USER_MANUAL.md
```

`release_acceptance.py --json` 仍按预期返回 `releasable=false`。新增手册没有引入包结构或 dry-run 安装问题；当前阻塞仍是 MN4 runtime web controls stale、native visible highlight 未证实、pkg 未签名、pkg 未 notarize、缺跨机器安装证据。精确 zip/pkg hash 仍只写入 release 目录和 OneDrive 镜像目录的外部 `SHA256SUMS.txt`。

### 2026-06-11 10:39 prompt 上下文隔离更新

本轮修复普通对话默认继承旧目标的问题：`build_model_input()` 现在只在 `goal_run` 或显式 `includeGoalContext` 时把 `goal.json` 写入模型输入；普通 `chat`、普通 `generate_card` 和普通 `generate_mindmap` 不再自动携带旧目标，也不再固定加入“答辩准备”或 `defense` 卡片要求。若用户明确输入答辩、汇报或讲稿，模型任务才会追加口述版本和证据边界要求。

验证结果：

```text
python3 -m unittest discover -s tests
Ran 201 tests in 6.802s
OK

find . -maxdepth 2 -name '*.py' -print0 | xargs -0 python3 -m py_compile
OK

node --check installed MN4 extension JS files
OK

python3 release_smoke_test.py --install-dry-run
[OK] CodexCompanion-0.4.0-latest-dist.zip
sha256=<see external SHA256SUMS.txt>
files=64
installDryRun=True

python3 release_acceptance.py --json
releasable=false
PASS: unit_tests, syntax_checks, release_zip_smoke, install_dry_run, runtime_web_controls, native_api_matrix, release_sha256_manifest
BLOCK: native_visible_highlight, signed_pkg, notarized_pkg, cross_machine_install
WARN: release_maintainer_prerequisites
```

精确 zip/pkg hash 只写入 release 目录和 OneDrive 镜像目录中的外部 `SHA256SUMS.txt`，避免 zip 内文档造成自引用漂移。


### 2026-06-11 09:45 发布验收更新

本轮修复了 LaunchAgent 环境下的 release acceptance 单测误报：`test_web_controls_static.py` 和 `test_resizable_panel_static.py` 都可通过 `CODEX_MN_TEST_EXTENSION_DIR` 读取从 release zip 抽取出的扩展副本，避免后台服务因 macOS 隐私权限不能读取真实 MN4 容器而把 `unit_tests` 误判为失败；`test_permission_diagnosis_reports_file_access_and_full_disk_access_guidance` 也把 MN 数据库路径隔离到临时文件，不再碰真实 `MarginNotes.sqlite`。

当前命令行验收结果：

```text
python3 -m unittest discover -s tests
Ran 194 tests in 7.311s
OK

python3 release_smoke_test.py release/CodexCompanion-0.4.0-latest-dist.zip
[OK] release/CodexCompanion-0.4.0-latest-dist.zip
sha256=<see external SHA256SUMS.txt>
files=64

python3 release_acceptance.py release/CodexCompanion-0.4.0-latest-dist.zip
[PASS ] unit_tests
[PASS ] syntax_checks
[PASS ] release_zip_smoke
[PASS ] install_dry_run
[BLOCK] runtime_web_controls
[BLOCK] native_api_matrix
[BLOCK] native_visible_highlight
[PASS ] release_sha256_manifest
[WARN ] release_maintainer_prerequisites
[BLOCK] signed_pkg
[BLOCK] notarized_pkg
[BLOCK] cross_machine_install
```

Companion 服务路径内的 `release_acceptance_summary --direct` 也已验证 `unitTests returncode=0`。命令行环境中 `release_sha256_manifest` 已 PASS，证明本地 release 目录和 OneDrive 镜像目录中的 `SHA256SUMS.txt` 一致，并且覆盖 latest zip/pkg。若从 LaunchAgent/Companion 面板运行时该 gate 显示权限型 BLOCK，原因是 macOS 阻止后台服务读取 OneDrive `SHA256SUMS.txt`，下一步是给 Companion/Python/Terminal Full Disk Access，而不是重新打包。因此当前 RC 的软件包质量门槛已通过，剩余非权限型 BLOCK 项为真实 MN4 运行态重载、原生可见高亮证据、Developer ID 签名、公证和跨机器安装证据。

2026-06-11 09:48 CST 更新：主界面 `mnRuntimeNotice` 新增 `mnRuntimeNoticeAcceptanceButton`，当 MN4 运行态 stale 时，用户可以在对话页直接点“发布验收”查看 gate 和下一步，不再必须切到设置页。doctor 的 required web controls 已加入该按钮；当前未重载的 MN4 面板会把它列入 `runtime_web_controls` absent，这正是需要重新打开面板或重启 MN4 的证据。

2026-06-11 10:03 CST 更新：`release_smoke_test.py` 会读取 release 目录中的 sidecar `SHA256SUMS.txt`，若存在但 latest zip hash 不匹配则 smoke 失败。`doctor.py` 新增 `Release SHA256 manifest` 检查，会验证本地和 OneDrive 的 `SHA256SUMS.txt` 内容一致，并验证其中记录的 latest zip/pkg hash 与真实文件一致。`release_acceptance.py` 新增 `release_sha256_manifest` gate，命令行验收当前为 PASS；面板验收若因 LaunchAgent 读取 OneDrive 被拒，会显示 Full Disk Access 指引。

2026-06-11 10:09 CST 更新：`doctor.py` 新增 `Release maintainer prerequisites` 检查，会读取 `security find-identity -v -p basic` 中的 Developer ID Installer 身份，并检查 `NOTARYTOOL_KEYCHAIN_PROFILE` / `CODEX_MN_NOTARYTOOL_KEYCHAIN_PROFILE` 或 `APPLE_ID`、`APPLE_TEAM_ID`、`APPLE_APP_SPECIFIC_PASSWORD`。`release_acceptance.py` 将该项作为 warning 展示，不作为硬阻塞，因为已经签名/公证过的 pkg 可以在没有本机维护者凭证的机器上被验证。当前本机实测 `missing_developer_id_installer; missing_notary_credentials`，所以它解释了为什么本机不能生成最终 signed/notarized 公发包。

### 插件 manifest

`mnaddon.json` 当前显示：

```json
{
  "addonid": "codex.mn.assistant",
  "author": "liuwhale / Codex",
  "cert_key": "",
  "marginnote_version_min": "4.2.3",
  "title": "Codex Companion",
  "version": "0.4.0"
}
```

结论：MN4 端插件 manifest 已更新为通用 `Codex Companion`，不再是 paper-only 命名。

### Companion 健康与 AI 后端

`curl -s http://127.0.0.1:48761/status` 摘要：

```text
ok True
pid 12259
ai_backend auto
codex_cli_available True
codex_cli_path /Users/liuwhale/.npm-global/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/codex/codex
openai_configured False
model gpt-5.5
speed fast
permission full
proxy http
queue pending 0
run active False
run action generate_mindmap
run stage 失败
run elapsed_seconds 0
```

结论：本地 Companion 正常运行；当前未配置 OpenAI API key，但已发现可用的本机 Codex CLI 原生二进制。`auto` 后端会先尝试 Codex CLI，再按需回退。最近一次 `generate_mindmap` 失败是预期的缺选中节点合并保护验证。

### Codex CLI 真实调用

真实 direct chat 验证：

```bash
python3 send_action.py chat --direct --prompt '请只回答：CODEX_MN_CHAT_OK_0611'
```

返回摘要：

```json
{
  "ok": true,
  "message": "已生成对话回复（codex-cli）。",
  "reply": "CODEX_MN_CHAT_OK_0611",
  "backend": "codex-cli"
}
```

结论：当前版本的生成型动作不再使用本地模板冒充模型输出；`/marginnote/action` 的真实生成路径能调用本机 Codex CLI 并返回最终回答。若 Codex CLI 和 OpenAI 都不可用，问答、卡片、脑图和完整精读会明确返回 `ai-unavailable`。

### WebView 运行时加载

重启 MarginNote 4 后，`events.jsonl` 中出现 0.4.0 运行时事件：

```text
2026-06-11T03:34:34+0800 webControlsReady
pluginVersion 0.4.0
missing ""
minWidth 390
minHeight 520
controls promptInput,sendButton,contextButton,closeButton,tabButtonChat,tabButtonButtons,...,permissionDiagnoseButton,cacheCurrentPdfButton,openPermissionSettingsButton,...
```

doctor 现在更严格地检查新控件和能力矩阵；当前运行态结果：

```text
[OK  ] MN4 runtime WebView        MN4 loaded pluginVersion 0.4.0 and WebView panel
[OK  ] MN4 runtime Web controls   69 controls reported, min=390x520
[OK  ] MN4 native API probe       highlight_candidate=False, export_candidate=False, candidates=0, ready_actions=4, blocked_actions=3, capability_matrix=True
```

结论：非破坏性的 `marginnote4app://addon/...` reload/open 路线已让 MN4 重新上报当前 WebView 控件和原生能力矩阵。doctor 现在按事件顺序判断 runtime handler stale：旧的 `nativeQueueCommandUnknown` 会被后续成功的 `nativeApiCapabilities` 覆盖，不再误报。当前 matrix 已确认卡片、脑图、Undo 分组和写入后刷新 ready；原生 PDF 高亮仍未 ready，因为当前没有活跃 PDF 选区，也未发现 `highlightFromSelection` selector。

2026-06-11 06:52 CST 更新：已安装 `main.js` 又补了一层共享 `documentController` resolver。能力探测和“高亮选区”现在共用同一组候选路径，包括 `lastDocumentController`、`selectionDocumentController`、`studyController.documentController/docController/currentDocumentController/readerController/readerViewController/pdfController/pdfViewController`、`notebookController` 对应路径，以及 `currentDocument.documentController/docController` 嵌套路径。`nativeApiCapabilities` 会上报 `documentControllerCandidates` 和 `selectedDocumentControllerLabel`；`nativeHighlightSelectionFailed` 会上报 `candidateLabels`、`candidateCount` 和 `selectedDocumentControllerLabel`，便于判断 MN4 把选区控制器暴露在哪个属性上。当前已刷新后的 matrix 显示 `selectedDocumentControllerLabel=studyController.readerController`、`targetCount=26`、`ready_actions=4`，但仍未发现可调用的 `highlightFromSelection` selector；需要带真实 PDF 选区再触发弹出菜单或“高亮选区”验证。

2026-06-11 07:07 CST 更新：Companion `/status` 现在新增 `mnRuntime` 字段，直接汇总 MN4 WebView 是否上报、原生能力是否上报、已安装文件是否晚于最近运行态事件、`probe_native_api_capabilities` 是否被旧 handler 当作 unknown。当前实测 `mnRuntime.ready=false`、`staleRuntime=true`、`runtimeHandlerStale=true`，并返回 `nextStep="重新打开 Codex 面板；如果仍旧，重启 MarginNote 4 后再点“刷新MN能力”。"`。Web 设置页新增 `mnRuntimeLine`，会把这个诊断显示给用户，不再只在命令行 doctor/release_acceptance 中看到。

2026-06-11 07:21 CST 更新：发布包根目录新增 `Refresh MN Runtime.command`，调用 `refresh_mn_runtime.py`。该脚本会发送 `request_native_capability_probe`，等待 `/status.mnRuntime` / `nativeApiCapabilities` 更新，运行 `doctor.py`，并把 `CodexCompanion-MNRuntimeEvidence-*.json` 写到桌面；它不退出、不重启 MarginNote 4。短超时实测写出 `/tmp/codex-mn-runtime-evidence-test.json`，其中 `nativeApiCapabilities.available=true`、`mnRuntime.ready=false`、`doctorReturnCode=0`，下一步仍是重新打开 Codex 面板或重启 MN4 后刷新能力。

2026-06-11 08:34 CST 更新：`Refresh MN Runtime.command` 现在默认带 `--try-addon-url-reload`，会先尝试非破坏性的 `marginnote4app://addon/codex.mn.assistant/...` enable/load/reload/open URL，并把每次 `open` 的结果写入 evidence 的 `addonReloadAttempts`。本机实测 `/tmp/codex-mn-runtime-refresh-url-reload.json` 记录 7 次 URL 尝试均返回成功，但 `/status.mnRuntime.ready=false`、`runtimeHandlerStale=true` 仍未解除；随后直接发送 `request_native_capability_probe` 仍被运行态记录为 `nativeQueueCommandUnknown`。这说明 URL 打开没有让 MN4 热重载当前 addon，仍需要重新打开 Codex 面板或重启 MN4 才能加载已安装 `main.js`。

2026-06-11 11:48 CST 更新：Web 对话页按钮已按任务分区重排。该时点曾把主操作区、原文工具区和结构工具区拆开，并把主界面置顶自定义按钮上限从 6 个收紧到 4 个；12:21 后续更新进一步把发送移出 AI 任务网格，把目标移入 AI 任务区，并取消默认 prompt 自动置顶。

### UI/交互变更

当前 0.4.0 已实现并有测试覆盖：

- 主界面对话区底部固定 `promptInput` 和 `sendButton`，自定义按钮不会替代发送入口。
- 目标现在是主操作网格里的按钮级入口：`goalToggleButton` 展开对话页目标面板；`goal_run` 是一次性长任务，返回本次目标和 `goalQueue`，但不会保存成长期当前目标；旧版 `goal.json` 没有 `mode=saved` 时会被忽略，避免历史 defense/精读目标污染普通聊天；`goal_run` 提交后会清空主输入框，避免执行后残留旧目标文本；普通聊天、普通制卡和普通脑图不会自动继承旧目标或默认进入答辩模式。
- 新增“按钮”子界面，包含预设 prompt、自定义 prompt、动作类型和“主界面”开关。
- 自定义按钮会持久化到 `customButtons`，后端最多保留 20 个按钮，并限制最多 4 个显示在主界面；动作类型包含 `request_native_highlight_selection`。
- 主界面按钮已分区：输入行固定发送；一次性目标放在 `goalActionStrip`；常用任务网格提供 3+3 生成按钮：解释、制卡、脑图、补脑图、重组、精读；原文工具放在 `sourceToolPanel`，由 `toolActionGrid` 提供高亮、导出和高亮状态；诊断类入口放到设置页分组，`healthCheckButton` 不再混入任务按钮网格。
- `generate_card` 现在生成更紧凑的短卡：单张正文上限 900 字符；模型输出有标题时按标题拆卡，没有标题的一大段回复会按句子拆成多张短卡，并清理标题里的 Markdown 加粗/反引号装饰，避免把所有内容塞进一张 MN 卡片。
- 发布包根目录提供 `Install Codex Companion.command` / `Uninstall Codex Companion.command` 双击入口，也保留 `install.sh` / `uninstall.sh` 命令行入口；用户解压后可一键安装 MN4 扩展和本地 Companion；内部目录仍保留细分安装脚本供排错使用。根目录还提供 `Refresh MN Runtime.command`，用于刷新并采集 MN4 运行态证据；提供 `Collect Native Highlight Evidence.command`，真实 PDF 选区高亮后可双击生成结构化 native highlight evidence；也提供 `Collect Cross-Machine Evidence.command`，第二用户或第二机器安装后可双击生成结构化 install evidence JSON 到桌面。
- 发布包根目录提供 `release_smoke_test.py`，可在不安装的情况下离线检查 zip 根目录入口、插件文件、Companion 文件、旧 LaunchAgent 迁移 marker 和私有运行文件排除。
- `release_smoke_test.py --install-dry-run` 会把 zip 解压到临时 `HOME`，设置 `CODEX_MN_DRY_RUN=1`，完整运行根目录 `install.sh` / `uninstall.sh`，并验证不会调用真实 `launchctl`、不会修改真实 MN4 扩展目录、不会运行真实 doctor。
- 发布包根目录提供 `release_acceptance.py`，会汇总单元测试、语法检查、zip smoke/dry-run、doctor，并把运行时控件、MN 原生能力矩阵、可见 native highlight、签名 pkg、notarized pkg、跨机器安装证据作为最终发布硬门槛。文本和 JSON 输出都会给每个阻塞 gate 附带 `nextActions`，直接指向需要点击的 MN4 面板按钮、双击命令或命令行备用方式。Companion 新增 `release_acceptance_summary` 动作，Web 设置页“发布验收”按钮可在面板内运行同一验收摘要；若 LaunchAgent/Python 被 macOS 隐私权限拦截，会以权限型阻塞显示。当前 RC 预期返回非零，避免把开发预览误判成可公发版本。native highlight evidence 必须由 `--collect-native-highlight-evidence` 生成结构化 JSON；跨机器证据必须由 `--collect-cross-machine-evidence` 生成结构化 JSON；主机器会校验 schema、目标机器/用户身份、release zip sha256，以及 `MN4 extension manifest`、`Companion service`、`LaunchAgent` 三个安装 doctor 检查。`Collect Native Highlight Evidence.command` 和 `Collect Cross-Machine Evidence.command` 是对应采证命令的双击封装。
- 发布包根目录提供 `build_pkg.py`，可从 zip 生成 macOS `.pkg` 外壳。当前 pkg 构建采用 `pkgbuild --nopayload`：zip 作为 scripts 资源嵌入，postinstall 解压到 `/Users/Shared/Codex Companion/...` 后检测 `/dev/console` 桌面用户，并以该用户身份运行 `install.sh`，避免装到 root 用户目录。构建后会 expand/flatten 清理 pkg scripts 资源中的 AppleDouble `._*` 元数据，当前构建移除了 `Scripts/._CodexCompanion.zip` 和 `Scripts/._postinstall`。
- 发布包根目录提供 `Build Signed Package.command`，会调用 `build_pkg.py --auto-sign`，只在当前钥匙串恰好有一个 Developer ID Installer 证书时生成桌面上的签名 pkg。当前机器 `security find-identity -v -p basic` 显示 `0 valid identities found`，所以该入口会明确失败并提示安装证书或显式传入 `--sign-identity`。
- 发布包根目录提供 `notarize_pkg.py` 和 `Notarize Package.command`。`notarize_pkg.py` 支持 `--keychain-profile`、`NOTARYTOOL_KEYCHAIN_PROFILE` 或 `APPLE_ID` / `APPLE_TEAM_ID` / `APPLE_APP_SPECIFIC_PASSWORD`，会调用 `xcrun notarytool submit --wait`、`xcrun stapler staple`、`xcrun stapler validate` 和 `spctl -a -vv -t install`。真实提交缺凭证时会无 traceback 明确报错；`--dry-run --json` 在无凭证时仍可输出预览命令，并带 `credentialsWarning`。
- 根目录 `install.sh` / `uninstall.sh` 现在用 `/bin/zsh` 调用包内细分脚本，只要求脚本文件存在，不依赖 zip 解压后内部脚本保留 executable bit。
- `install_companion.sh` 会在安装 preferred label `com.codex.paper-companion` 前迁移旧 label `com.liuwhale.codex-marginnote-assistant`，避免旧服务占用端口导致新服务误判启动成功；当前机器已完成迁移。
- 状态栏不再放全局 `queueButton`；保留队列数量 `queueBadge`，并新增 `runStateLine` 显示后端当前/最近任务状态；目标进度由目标执行期间的进度消息和 `runStateLine` 表达，不再把一次性目标固定成长期当前目标。
- 设置页新增 `mnRuntimeLine`，渲染 `/status.mnRuntime`：能区分“等待 MN4 上报”“原生能力未刷新”“MN4 运行态未刷新/handler 过旧”，并给出重新打开面板或重启 MN4 的下一步。
- 设置页新增 `runtimeEvidenceButton`，通过 `collect_mn_runtime_evidence` 在面板内生成 `CodexCompanion-MNRuntimeEvidence-*.json`，内容包含 `/status.mnRuntime`、`nativeApiCapabilities`、`request_native_capability_probe` 结果和 doctor 输出；该路径不会退出或重启 MarginNote 4。
- 忙碌时继续点击动作会自动入队，上一个任务结束后 WebView 队列泵继续执行；消息后提供 `停止当前并直接执行` 和 `查看队列状态`。
- Companion 现在会把当前/最近生成动作写入 `control/current-run.json`，包含 `action/stage/detail/topicid/bookmd5/queue_id/source/elapsed_seconds`；`/status` 和 `queue_status` 都会返回 `run`，`queue_status` 的人类可读回复也包含“运行状态”。
- 脑图合并保护已接入后端和 MN4 写入层：`generate_mindmap` 识别“补到当前脑图/合并脑图”意图后要求当前选中节点上下文；缺少 `selectedNoteId/selectedNoteTitle/selectedNoteText` 时返回 400、不调用模型、不返回 `mindmap`。MN4 `createMindmap()` 对 `mergeIntoSelected=true` 但当前无选中节点的旧草稿会显示提示并发送 `createMindmapFailed reason=missing-selected-node-for-merge`，不再降级创建新根节点。
- WebView 请求层现在会解析 Companion 的非 2xx JSON 响应，保留 `httpStatus`，并优先显示后端 `reply/message`；如果后端已经返回可读 `reply`，草稿/目标/文本失败分支不会再额外刷一条重复模板错误。
- WebView 和 MN4 原生请求层的连接失败不再显示“未知网络错误”；错误文案会包含 `127.0.0.1:48761`、启动 Companion 服务和设置页“运行态采证”的下一步。
- WebView 队列泵会自动续跑 raw action；如果队列头是 `nativeAction`，会显示“等待 MarginNote 原生处理”，不把缓存 PDF、刷新 MN 能力、高亮选区等原生命令误当成文本任务执行，也不会由 WebView ack，仍交给 MN4 插件原生轮询执行并确认。
- MN4 原生高亮的能力探测和执行路径已改成共享 `resolveDocumentController()`；候选路径和选中 label 会进入事件日志，避免只报 `missing-document-controller` 却不知道 MN4 运行时到底尝试过哪些属性。
- 设置页新增“缓存PDF”按钮；WebView 通过 `codexpaper://upload_pdf` bridge 调用原生 `uploadPdfToCompanion`，由 MN4 插件进程读取当前 PDF 并上传到 Companion 的 `cache_pdf_from_marginnote` 动作。后续 `export_annotated_pdf` 会优先使用当前 book 的缓存 PDF 副本。
- 设置页新增“刷新MN能力”按钮；WebView 通过 `request_native_capability_probe` 入队 `probe_native_api_capabilities`，MN4 插件轮询后会重新上报 `nativeApiCapabilities` 和 `capabilityMatrix`。同页“运行态采证”按钮会同时采集当前状态、刷新请求结果和 doctor 输出，便于用户把问题证据直接发给开发者。

### PDF 缓存与标注副本导出

真实运行证据：

```bash
python3 send_action.py request_pdf_cache \
  --topicid AAFA4811-8B3A-46AF-8511-6037060FA23B \
  --bookmd5 253dd5804dd4973bcea545ebcc7ee5a760c73581e1a4e25904fd10ae4b8d1246
```

MN4 插件运行时事件：

```text
2026-06-11T03:09:59+0800 pdfCacheCommandReceived
2026-06-11T03:09:59+0800 pdfCacheUploadStarted candidateIndex=5
2026-06-11T03:09:59+0800 pdfCacheUploadPosted size=2675392
```

结论：不依赖鼠标或截图，Companion 可以向当前 notebook 队列发送 `cache_pdf_from_current_document` 原生命令；MN4 插件进程能读取 iCloud MNDocs 中的当前 PDF，并上传到 Companion 的 PDF 缓存。

随后真实执行：

```bash
python3 send_action.py export_annotated_pdf --direct \
  --topicid AAFA4811-8B3A-46AF-8511-6037060FA23B \
  --bookmd5 253dd5804dd4973bcea545ebcc7ee5a760c73581e1a4e25904fd10ae4b8d1246 \
  --prompt "高亮当前选区"
```

返回摘要：

```text
status OK
backend local:pymupdf-highlight-copy
annotations_created 1
rects_matched 2
modifiedOriginal false
sourcePdf ~/.codex/marginnote-assistant/uploads/pdf-cache/253dd...
outputPdf ~/Library/CloudStorage/OneDrive-个人/Codex Companion/exports/<current-validation-pdf>...codex-highlighted-253dd5804dd4973bcea545ebcc7ee5a7-20260611-031410.pdf
```

用 PyMuPDF 读取输出文件确认：

```text
name_bytes 178
page 1 type Highlight content "Codex Companion: Attention-Guided Safety Filter"
```

结论：`cache_pdf_from_marginnote -> export_annotated_pdf` 链路已在真实验证 PDF 上验证。导出副本写入 OneDrive exports，原始缓存 PDF 哈希前后一致；输出文件名会裁剪到 macOS 单文件名限制内，避免缓存文件名前缀和 bookmd5 重复导致 `File name too long`。

### 原生高亮 API 路线

官方 `marginnoteapp/Addon` API 头文件显示 `JSBDocumentController` 公开：

```text
selectionText
isSelectionText
imageFromSelection
highlightFromSelection
```

本轮新增：

- MN4 插件在 `PopupMenuOnSelection` 事件里保存最近一次 `documentController`。
- MN4 插件在 PDF 选中文本弹出菜单里尝试追加“Codex 高亮选区”，该菜单项直接调用 `highlightCurrentSelection`，减少 Web 面板抢焦点导致选区丢失的概率。
- `nativeApiCapabilities` 现在通过共享 resolver 探测一组 document controller 候选，而不是只看 `documentController` / `docController` / `selectionDocumentController`；事件里会带 `documentControllerCandidates` 和 `selectedDocumentControllerLabel`。
- Companion 新增 `request_native_highlight_selection`，入队 `nativeAction=highlight_current_selection`。
- Web 主界面和自定义按钮动作列表已接入“高亮选区”；自然语言“高亮当前选区/画高亮/加下划线”等意图会路由到 `request_native_highlight_selection`。
- `request_native_highlight_selection` 需要 `full` 权限，`notes` 权限会被 Companion 拦截。
- 2026-06-11 10:45 CST 更新：弹出菜单入口现在会把命令标记为 `source=selection-popup-menu`，并允许使用刚从 `PopupMenuOnSelection` 缓存的选中文本。如果菜单点击后 `documentController.selectionText` 暂时为空，但缓存选区仍在，插件会尝试官方 `highlightFromSelection()`，并在事件中记录 `usedCachedSelectionText` 与 `selectionTextSource=cached-selection`；仍然不写 SQLite、不伪造高亮。
- MN4 插件轮询到该命令后，若存在有效 PDF 选区，会调用 `documentController.highlightFromSelection()`。
- 没有有效选区时，插件返回 `nativeHighlightSelectionFailed`，不写 SQLite、不改 PDF。

真实运行证据：

```bash
python3 send_action.py request_native_highlight_selection \
  --topicid AAFA4811-8B3A-46AF-8511-6037060FA23B \
  --bookmd5 253dd5804dd4973bcea545ebcc7ee5a760c73581e1a4e25904fd10ae4b8d1246 \
  --prompt "Attention-Guided Safety Filter"
```

事件摘要：

```text
2026-06-11T03:34:36+0800 nativeApiCapabilities targetCount=7 selectionDocumentController.exists=false
2026-06-11T03:34:59+0800 nativeQueueCommandReceived nativeAction=highlight_current_selection
2026-06-11T03:34:59+0800 nativeHighlightSelectionFailed reason=missing-document-controller requestedSelectionLength=6
2026-06-11T03:34:59+0800 commandsAcked count=1
```

结论：官方 API 路径已经接入，当前运行态也已重新上报共享 resolver 的候选路径诊断。下一步必须在用户手动选中文本后触发，检查是否出现 `selectionPopupHighlightMenuInstalled`、`nativeHighlightSelectionPosted`、`ZHIGHLIGHTS` blob 和肉眼可见高亮。

### 静态检查与测试

以下检查通过：

```text
python3 -m unittest discover -s tests
Ran 162 tests OK

python3 -m py_compile companion.py send_action.py refresh_mn_runtime.py audit_highlights.py doctor.py release_smoke_test.py release_acceptance.py build_pkg.py notarize_pkg.py package_release.py verify_after_unlock.py
zsh -n install.sh uninstall.sh "Install Codex Companion.command" "Uninstall Codex Companion.command" "Collect Native Highlight Evidence.command" "Collect Cross-Machine Evidence.command" "Refresh MN Runtime.command" "Build Signed Package.command" "Notarize Package.command" install_companion.sh install_extension.sh uninstall_companion.sh start_companion.sh stop_companion.sh package_release.sh verify_when_unlocked.sh run_companion_foreground.sh
node --check <live extension>/web/app.js
node --check <live extension>/main.js
node --check <live extension>/CodexWebPanelController.js
node --check <live extension>/CodexPanelController.js
python3 -m json.tool mnaddon.json
```

结论：当前工作目录脚本和插件 JS 无语法错误；自定义按钮、主界面发送、消息级引导、后端 run state、状态栏 `runStateLine`、`/status.mnRuntime`、设置页 `mnRuntimeLine`、设置页 `runtimeEvidenceButton`、设置页 `releaseAcceptanceButton`、MN4 运行态刷新采证命令、脑图合并选中节点保护、WebView 非 2xx JSON 错误展示、WebView/原生请求连接失败诊断、真实 AI 必需合同、完整精读模型驱动、品牌命名、后端按钮清洗、短卡片拆分、PDF 缓存后端、PDF 缓存诊断、Web 按钮、WebView 队列中 `nativeAction` 延后交给 MN4 原生 poll、原生上传 bridge、命令行导出选区透传、缓存 PDF 导出文件名裁剪、MN 原生动作矩阵、原生高亮选区 UI 入口、full 权限边界、发布包根目录安装入口、LaunchAgent 旧 label 迁移、安装 dry-run、pkg builder、pkg scripts AppleDouble 清理、notarize CLI、notarized_pkg 独立门禁、按事件时间判断 stale runtime、runtime handler stale 诊断、release acceptance gate、面板内 release acceptance 摘要、结构化跨机器 evidence 采集/校验和 doctor 发布包内容检查均有测试覆盖。

### doctor.py

当前使用显式解释器运行：

```bash
python3 doctor.py
```

摘要：

```text
[OK  ] MN4 extension manifest     Codex Companion / 0.4.0
[OK  ] Companion service          pid=18963, model=gpt-5.5, backend=auto, codex_cli=True, openai_configured=False, proxy=http
[OK  ] LaunchAgent                loaded: com.codex.paper-companion
[OK  ] Latest RC package          installable clean zip; local and OneDrive hashes match
[WARN] Latest RC pkg              no signature
[OK  ] MN4 Codex content          codex_notes=196, cards=0, mindmap_nodes=4, highlight_nodes=192
[WARN] Full-reading dedupe        no recent createCardsFinished event proving requested>0, created=0, skipped>=requested
[WARN] Native highlight blobs     0 rows have ZHIGHLIGHTS in the configured validation scope; visible native highlights are not proven
[OK  ] MN4 runtime WebView        MN4 loaded pluginVersion 0.4.0 and WebView panel
[WARN] MN4 runtime Web controls   stale runtime event; installed Web assets changed after the last MN4 event; restart MarginNote 4 or reopen the Codex panel; previous reported_missing=[], absent=['runtimeEvidenceButton', 'mnRuntimeLine', 'nativeCapabilitiesLine', 'nativeCapabilitiesRefreshButton', 'goalStatusLine', 'runStateLine'], min=390x520
[WARN] MN4 native API probe       highlight_candidate=False, export_candidate=False, candidates=0, ready_actions=0, blocked_actions=0, capability_matrix=False; runtime_handler_stale=True; MN4 runtime received probe_native_api_capabilities but treated it as unknown; reopen the Codex panel or restart MarginNote 4 to load installed main.js; stale runtime event; installed plugin assets changed after the last MN4 probe
Summary: 0 fail, 6 warn, 10 ok
```

当前 0 个 FAIL 和 6 个 WARN：

- `Latest RC pkg`：当前 pkg 是 unsigned nopayload 内部测试包，尚未用 Developer ID Installer 签名，也不能通过 notarized/stapled ticket 检查。
- `Full-reading dedupe`：没有最近一次 `createCardsFinished requested>0 created=0 skipped>=requested` 事件。
- `Native highlight blobs`：当前验证范围仍没有可证明的 native visible highlight blob。
- `MN4 runtime Web controls`：当前 MN4 运行态事件早于已安装 Web 文件更新时间；旧事件中还没有 `mnRuntimeLine`、`nativeCapabilitiesLine` 和 `nativeCapabilitiesRefreshButton`。
- `MN4 native API probe`：当前运行时探测事件早于已安装 runtime 文件更新时间；刚刚发送的 `probe_native_api_capabilities` 已被运行态轮询到，但被记录为 `nativeQueueCommandUnknown`，说明运行态 handler 过旧，没有加载已安装 `main.js` 的刷新能力；需要重启或重新加载 MN4 面板后刷新探测事件。
- `Companion file access`：后台 Companion 直接读取当前 MN 数据库仍被 macOS 权限拦截；当前显示 `sourcePdf=OK`、`pdfCache=OK`、`exportDir=OK`，但整体仍是 `PERMISSION`，因为 MN 数据库读权限未完全授权。

备注：当前机器上直接执行 `./doctor.py` 会卡住，文档已统一改为 `python3 doctor.py`，并移除了 `doctor.py` 的可执行位。

### 发布包

最新包：

```text
~/.codex/marginnote-assistant/release/CodexCompanion-0.4.0-latest-dist.zip
~/Library/CloudStorage/OneDrive-个人/Codex Companion/CodexCompanion-0.4.0-latest-dist.zip
~/.codex/marginnote-assistant/release/CodexCompanion-0.4.0-latest.pkg
~/Library/CloudStorage/OneDrive-个人/Codex Companion/CodexCompanion-0.4.0-latest.pkg
```

打包卫生检查：

```text
files 63
BAD_COUNT 0
INSTALL_DRY_RUN True
INSTALL_RETURN_CODE 0
UNINSTALL_RETURN_CODE 0
DRY_RUN_INSTALLED_COMPANION_PY True
DRY_RUN_RENDERED_LAUNCH_AGENT True
REQUIRED README-FIRST.txt True
REQUIRED install.sh True
REQUIRED uninstall.sh True
REQUIRED Install Codex Companion.command True
REQUIRED Uninstall Codex Companion.command True
REQUIRED Collect Native Highlight Evidence.command True
REQUIRED Collect Cross-Machine Evidence.command True
REQUIRED Refresh MN Runtime.command True
REQUIRED Build Signed Package.command True
REQUIRED Notarize Package.command True
REQUIRED release_smoke_test.py True
REQUIRED release_acceptance.py True
REQUIRED build_pkg.py True
REQUIRED notarize_pkg.py True
REQUIRED companion/companion.py True
REQUIRED companion/doctor.py True
REQUIRED companion/refresh_mn_runtime.py True
REQUIRED extension/codex.mn.assistant/main.js True
MODE install.sh 0o755
MODE uninstall.sh 0o755
MODE Install Codex Companion.command 0o755
MODE Uninstall Codex Companion.command 0o755
MODE Collect Native Highlight Evidence.command 0o755
MODE Collect Cross-Machine Evidence.command 0o755
MODE Refresh MN Runtime.command 0o755
MODE Build Signed Package.command 0o755
MODE Notarize Package.command 0o755
MODE release_acceptance.py 0o755
MODE companion/install_companion.sh 0o755
MODE companion/install_extension.sh 0o755
hashes_match True
ZIP_SHA256 see final verification command output
PKG_SHA256 see final verification command output
PKG_DRY_RUN True
PKG_CREATED True
PKG_SIGNATURE no signature
PKG_PAYLOAD_FILES empty
PKG_LOCAL_ONEDRIVE_HASHES_MATCH True
PKG_APPLEDOUBLE_EMPTY True
PKG_REMOVED_APPLEDOUBLE Scripts/._CodexCompanion.zip, Scripts/._postinstall
NOTARIZE_DRY_RUN True
NOTARIZE_CREDENTIALS_MODE dry-run-no-credentials
NOTARIZE_SUBMIT_COMMAND xcrun notarytool submit ... --wait
NOTARIZE_MISSING_CREDENTIALS credentialsWarning without traceback in dry-run; error without traceback for real submit
```

结论：0.4.0 RC 包已同步 OneDrive，根目录带一键安装/卸载入口、smoke 检查、acceptance gate、pkg builder 和 notarization 工具；本地包和 OneDrive 包哈希一致，不包含会话、上传文件、队列、日志、个人设置、目标文件、草稿或 `.env`。`--install-dry-run` 已验证解压后的包可在临时 `HOME` 中走完安装/卸载入口，并且安装脚本不依赖内部脚本 executable bit。doctor 现在会同时检查 latest pkg 的本地/OneDrive hash、payload 文件数、签名状态、stapled ticket 和 Gatekeeper install assessment。
当前 unsigned pkg 也已生成并同步 OneDrive；它是 nopayload 脚本包，`pkgutil --payload-files` 为空，scripts 资源中嵌入 release zip 和 postinstall。当前 pkg 展开后没有 `._*` AppleDouble 元数据。`pkgutil --check-signature` 明确显示 `Status: no signature`，所以它只能算内部测试安装包，不是最终公发签名包。`Build Signed Package.command` 已可自动探测唯一 Developer ID Installer 身份，但当前钥匙串没有有效身份，不能在本机生成真实签名包。`notarize_pkg.py --dry-run --json` 已能在没有 Apple 凭证时生成 notarytool/stapler/spctl 预览命令并返回 `credentialsWarning`；真实 notarization 仍需要 Apple notarization 凭证，当前不能在本机生成真实 notarized pkg。

## 发布状态

当前可以证明：

- Companion 运行正常。
- 插件 manifest 合法且为 `Codex Companion / 0.4.0`。
- MN4 已加载 0.4.0 WebView 面板。
- WebView 面板首屏提供对象、对话、操作、知识、工作流五个工作区；设置和历史作为独立页面打开。
- 主界面固定发送按钮、自定义按钮置顶、主操作/原文工具/设置诊断分区、消息级队列引导、后端运行状态行、权限诊断、缓存 PDF、打开设置和高亮选区入口已进入代码与静态测试清单。
- WebView 队列泵能自动续跑 raw action，并会把 `nativeAction` 留给 MN4 插件原生轮询处理，不会误走聊天/文本生成路径。
- MN 原生动作矩阵已进入插件 runtime event、Companion `status/settings_get`、doctor 和设置页；并新增 `request_native_capability_probe` / `probe_native_api_capabilities` 主动刷新链路。doctor 已能按对应事件时间识别 stale runtime event，并且旧 handler 的 unknown 事件会被后续成功 probe 覆盖。当前 MN4 运行态已上报 `capabilityMatrix=True`、`ready_actions=4`。
- 短卡片生成已收紧：长回复会拆成多张卡，单卡正文上限为 900 字符。
- 本机 Codex CLI 后端能通过 Companion direct chat 返回真实回答。
- 发布包已生成并同步 OneDrive，且 doctor 能检查根目录安装入口、私有运行文件排除和哈希一致性；doctor 的 runtime Web controls gate 已要求新版按钮布局区域 `primaryTaskPanel/primaryActionGrid/workflowActionPanel/toolActionGrid`；`release_smoke_test.py --install-dry-run` 能用临时 `HOME` 验证解压包安装/卸载入口；`Refresh MN Runtime.command` 已随包提供，可双击触发 `refresh_mn_runtime.py` 采集 MN4 runtime evidence；`release_acceptance.py` 已提供最终发布门禁汇总，当前会正确阻断 RC，因为 native visible highlight、签名 pkg、notarized pkg 和跨机器安装证据仍未满足；`--collect-native-highlight-evidence --try-native-highlight` 会先请求 MN4 插件执行一次原生选区高亮，等待 posted/failed 事件，再生成结构化 JSON 并供 `--native-highlight-evidence` 验证，且会校验最新 posted event 与 blob 查询的 topic/book 一致；`--collect-cross-machine-evidence` 已能生成结构化 JSON，主机器会拒绝同一用户/同一机器、hash 不匹配或安装 doctor 检查不完整的 evidence；`Collect Native Highlight Evidence.command` 和 `Collect Cross-Machine Evidence.command` 提供了双击采证入口；`build_pkg.py` 能生成 unsigned nopayload pkg 外壳，并清理 pkg scripts 资源里的 `._*` 元数据；`Build Signed Package.command` 提供了双击签名构建入口，`Notarize Package.command` 提供了双击 notarization 入口，但当前机器缺少 Developer ID Installer 证书和 notarytool 凭证。
- LaunchAgent 已迁移到 preferred label `com.codex.paper-companion`；doctor 会把“只加载旧 label”的状态降级为 WARN。
- 高亮危险写库路径默认禁用。
- `export_annotated_pdf` 已有 PyMuPDF 标注副本导出路径，导出前后校验原 PDF sha256，并已验证会优先使用当前 book 的 PDF 缓存副本。
- 设置页和 doctor 已提供 `diagnose_permissions` 文件访问诊断；设置页还有 `cacheCurrentPdfButton`、`nativeCapabilitiesRefreshButton` 和 `open_full_disk_access_settings` 入口；当前运行态显示 `sourcePdf=OK`、`pdfCache=OK`、`exportDir=OK`，但 MN 数据库仍因 macOS 权限显示 `PERMISSION`。

当前不能证明：

- 当前 notebook 的完整精读写入/去重运行态事件；完整精读现在是模型驱动草稿，不能再用固定 `requested=15` 的旧模板事件作为通过证据。
- 当前 MN4 运行态还不能证明已经加载本轮新增的 native capability UI 控件和 `capabilityMatrix` 事件；需要重启或重新打开 MN4 面板后复测。
- MN4 原文处有可见 native highlight。
- 当前 LaunchAgent 尚未获授权读取 MN 数据库；现在可以证明它能识别并报告 `PERMISSION`。PDF 访问方面，已通过 MN4 插件进程上传缓存并完成标注副本导出。
- 复杂选区和扫描 PDF 标注副本导出。
- 新用户/新机器真实安装验证尚未完成。
- 已有 unsigned pkg builder、签名构建入口和 notarization 工具，但当前机器没有 Developer ID Installer 证书，也没有 notarytool 凭证，还没有真实签名/notarized pkg 或图形安装器实测。

## 下一步

1. 手动在 MN4 PDF 中选中文本，再触发“高亮选区”，验证 `nativeHighlightSelectionPosted`、同一 topic/book 作用域内的 `ZHIGHLIGHTS` blob 和页面可见高亮。
2. 用真实 AI 触发一次完整精读草稿，确认卡片/脑图来自模型输出，写入 MN 后再重复写入同一草稿验证 Codex 元数据去重。
3. 做跨用户安装验证，并准备 Developer ID Installer 证书、notarytool 凭证和签名/notarized 发布包。
