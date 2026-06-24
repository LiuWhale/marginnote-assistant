# Release Checklist

## 版本信息

- 插件名：Codex Companion
- 当前发布候选：0.4.21
- MN4 插件 manifest 版本：0.4.21
- Companion 版本：0.4.21
- MN4 扩展目录：`~/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant`
- Companion 目录：`~/.codex/marginnote-assistant`
- LaunchAgent：`~/Library/LaunchAgents/com.codex.paper-companion.plist`

## 发布前检查

0. 发布包一键安装入口

```bash
unzip CodexCompanion-0.4.21-latest-dist.zip
cd CodexCompanion-0.4.21
python3 release_smoke_test.py
python3 release_smoke_test.py --install-dry-run
python3 build_pkg.py --dry-run
./install.sh
```

验收条件：

- zip 根目录包含 `README-FIRST.txt`、`install.sh`、`uninstall.sh`、`Install Codex Companion.command`、`Uninstall Codex Companion.command`、`Refresh MN Runtime.command`、`Restart MarginNote 4.command`、`Collect Native Highlight Evidence.command`、`Collect Single Document Acceptance.command`、`Collect Cross-Machine Evidence.command`、`Build Signed Package.command`、`Notarize Package.command`、`release_smoke_test.py`、`release_acceptance.py`、`single_document_acceptance.py`、`build_pkg.py` 和 `notarize_pkg.py`。
- `python3 release_smoke_test.py` 能离线检查根目录入口、插件文件、Companion 文件、旧 LaunchAgent 迁移 marker 和私有运行文件排除。
- `python3 release_smoke_test.py --install-dry-run` 会把 zip 解压到临时 `HOME`，设置 `CODEX_MN_DRY_RUN=1`，完整运行安装/卸载入口，并验证不会调用 `launchctl`、不会修改真实 MN4 扩展目录、不会运行真实 doctor。
- `python3 prepare_release_handoff.py` 或双击 `Prepare Release Handoff.command` 会生成 `CodexCompanion-release-handoff-*` 文件夹/zip，内含最新 zip/pkg、`release_acceptance.json`、`SHA256SUMS.txt`、当前 blocking/warning gate 下一步和 MN runtime/native/single-document/cross-machine evidence 模板；该包会同步到 OneDrive 的 `Codex Companion/Release Handoff` 目录。交接包只把满足 release gate 的有效证据放进 `evidence/`；stale runtime、旧 handler、`ok=false`、不完整证据、native highlight 事件/数据库 scope 不匹配证据、single-document acceptance 未完成，或 package hash 不匹配当前 zip 的跨机器证据只放进 `diagnostics/evidence/`，不能作为发布通过证明。
- `Refresh MN Runtime.command` 生成的 `CodexCompanion-MNRuntimeEvidence-*.json` 可用 `python3 release_acceptance.py --mn-runtime-evidence <json>` 作为运行态证据；验收只接受 `ready=true`、`webControlsReady=true`、`nativeApiReady=true`、`staleRuntime=false`、`runtimeHandlerStale=false` 且 capability matrix 存在的证据。
- `Restart MarginNote 4.command` 只在用户确认后调用 Companion 的 `restart_marginnote4` 动作，用于让 MN4 重新加载原生 `main.js` handler；它不能使用 `killall`。
- `python3 build_pkg.py --dry-run` 能从最新 zip 生成 pkg payload 和 postinstall 脚本预览；postinstall 必须检测 `/dev/console` 桌面用户，并以该用户身份运行 `install.sh`，不能安装到 root 的 MN4 容器。
- `./install.sh` 会安装 MN4 扩展、安装并启动 Companion，然后运行 `python3 ~/.codex/marginnote-assistant/doctor.py`。
- `./install.sh` 会迁移旧 LaunchAgent label `com.liuwhale.codex-marginnote-assistant`，最终 doctor 应显示 `LaunchAgent loaded: com.codex.paper-companion`。
- `./uninstall.sh` 会卸载 LaunchAgent，并移除 MN4 扩展；默认保留 `~/.codex/marginnote-assistant` 里的日志/会话，便于排错。

如需生成内部测试 pkg：

```bash
python3 build_pkg.py
```

如需生成可分发签名 pkg：

```bash
python3 build_pkg.py --sign-identity "Developer ID Installer: <Team Name> (<Team ID>)"
```

发布维护者也可以双击 `Build Signed Package.command`。该入口会调用 `build_pkg.py --auto-sign`，只在当前钥匙串里恰好有一个 Developer ID Installer 证书时生成桌面上的签名 pkg；没有证书或证书不唯一时会失败并给出明确提示。

签名 pkg 还不是最终可分发包。公发前必须 notarize 并 staple：

```bash
python3 notarize_pkg.py ./release/CodexCompanion-0.4.21-latest.pkg --keychain-profile "CodexNotary"
```

发布维护者也可以双击 `Notarize Package.command`。该入口需要 `NOTARYTOOL_KEYCHAIN_PROFILE`，或 `APPLE_ID`、`APPLE_TEAM_ID`、`APPLE_APP_SPECIFIC_PASSWORD`。`doctor.py` 会用 `xcrun stapler validate` 和 `spctl -a -vv -t install` 把 notarization 作为独立证据；`release_acceptance.py` 会把 `signed_pkg` 和 `notarized_pkg` 分开阻断。

1. 语法检查

```bash
node --check "$HOME/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/main.js"
node --check "$HOME/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/CodexPanelController.js"
node --check "$HOME/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/CodexWebPanelController.js"
node --check "$HOME/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/web/app.js"
/usr/bin/python3 -m py_compile "$HOME/.codex/marginnote-assistant/companion.py"
/usr/bin/python3 -m py_compile "$HOME/.codex/marginnote-assistant/send_action.py"
/usr/bin/python3 -m py_compile "$HOME/.codex/marginnote-assistant/refresh_mn_runtime.py"
/usr/bin/python3 -m py_compile "$HOME/.codex/marginnote-assistant/audit_highlights.py"
/usr/bin/python3 -m py_compile "$HOME/.codex/marginnote-assistant/doctor.py"
/usr/bin/python3 -m py_compile "$HOME/.codex/marginnote-assistant/single_document_acceptance.py"
/usr/bin/python3 -m py_compile "$HOME/.codex/marginnote-assistant/notarize_pkg.py"
python3 -m json.tool "$HOME/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/mnaddon.json" >/dev/null
```

2. Companion 启动

```bash
"$HOME/.codex/marginnote-assistant/start_companion.sh"
curl -s http://127.0.0.1:48761/status | python3 -m json.tool
python3 "$HOME/.codex/marginnote-assistant/doctor.py"
```

`Latest RC package` 应显示 installable clean zip，并确认本地 release 包与 OneDrive 镜像哈希一致。

3. 打开 MN4 notebook 后验证插件事件

```bash
tail -n 30 "$HOME/.codex/marginnote-assistant/events.jsonl"
```

应看到：

- `pluginVersion` 为 `0.4.21`
- `webPanelLoaded`
- `panelShownState`
- `panelKind=webview`
- `panelAutoShown`
- `webControlsReady` 的 controls 至少包含 `promptInput,sendButton,stagedActionLine,clearStagedActionButton,goalActionStrip,primaryActionGrid,mindmapToolPanel,mindmapActionGrid,sourceToolPanel,toolActionGrid`，并且 `missing=""`

4. 鼠标缩放面板

打开面板后拖动右下角缩放柄。验收条件：

- 面板可以缩小和放大。
- 最小尺寸不会小于 390x520。
- 重新触发布局或重开面板后，用户调节后的尺寸不会被固定布局覆盖。
- 事件里可出现 `panelResizeFinished`。

5. 控制面验收

```bash
"$HOME/.codex/marginnote-assistant/send_action.py" settings_update --ai-backend codex_cli --permission read_only --model gpt-5.5 --speed fast
"$HOME/.codex/marginnote-assistant/send_action.py" settings_get
"$HOME/.codex/marginnote-assistant/send_action.py" generate_card --direct --prompt "make a card"
"$HOME/.codex/marginnote-assistant/send_action.py" goal_update --goal-title "读懂当前材料" --goal-detail "生成讲稿、脑图、卡片，并保持原文清洁"
"$HOME/.codex/marginnote-assistant/send_action.py" upload_file --file-name goal-notes.md --file-content "# 当前材料"
"$HOME/.codex/marginnote-assistant/send_action.py" stop_current
"$HOME/.codex/marginnote-assistant/send_action.py" queue_status
"$HOME/.codex/marginnote-assistant/send_action.py" history_list
"$HOME/.codex/marginnote-assistant/send_action.py" settings_update --ai-backend auto --permission notes --speed fast
```

验收条件：

- `read_only` 会阻止 `generate_card`。
- `settings_get` 能看到 `aiBackend=codex_cli`，`/status` 能看到 `ai_backend/codex_cli_available/codex_cli_path`。
- 上传文件能在 `settings_get` 或 `/status` 里看到；`goal_run` 作为一次性长任务执行，不会保存成长期当前目标，目标输入提交后主输入框清空。
- OpenAI Key 留空保存时不会覆盖；填入 Key 后只写入本地 `.env`，不会在 `settings_get` 中回显；点击 `清除Key` 后 `.env` 中的 `OPENAI_API_KEY` 被移除，且清除请求不包含输入框里的临时 key；点击 `试连AI` 会返回后端就绪诊断且不发送测试 prompt、不消耗 token、不回显 key。
- 自定义按钮能通过 `settings_update` 持久化，最多 4 个按钮可显示到主界面。
- `stop_current` 后下一次生成动作会返回 stopped。
- `history_list` 能读取当前会话历史；`history_clear` 可清空当前会话历史。
- 最后权限恢复为 `notes`。

6. 程序化触发完整精读

```bash
"$HOME/.codex/marginnote-assistant/send_action.py" generate_full_reading \
  --topicid CA970092-A137-40D7-9A78-DD76EB407C05 \
  --bookmd5 253dd5804dd4973bcea545ebcc7ee5a760c73581e1a4e25904fd10ae4b8d1246 \
  --prompt "对当前材料生成完整精读草稿，按主线、方法、实验、局限和 defense 组织。"
```

应看到真实 AI 后端返回的草稿结果；`backend` 必须是 `codex-cli` 或 `openai:*`，不能是 `local`、`ai-unavailable` 或 `local:park-knows-template`。在 Web 面板点击“写入 MN”后，事件里应出现：

- `commandsReceived`
- `handleResponse`
- `createCardsFinished`
- `createMindmapFinished` 或重复运行时的 `createMindmapSkipped`
- `commandsAcked`

重复写入同一草稿时，期望事件里出现：

- `createCardsFinished` 中 `requested` 等于草稿卡片数
- `created=0`
- `skipped>=requested`

7. 数据结果检查

```bash
DB="$HOME/Library/Containers/QReader.MarginStudy.easy/Data/Library/Private Documents/MN4NotebookDatabase/0/MarginNotes.sqlite"
sqlite3 "$DB" "select count(*) from ZBOOKNOTE where ZTOPICID='CA970092-A137-40D7-9A78-DD76EB407C05' and ZCOMMENT like '%full-reading:card:%';"
sqlite3 "$DB" "select count(*) from ZBOOKNOTE where ZTOPICID='CA970092-A137-40D7-9A78-DD76EB407C05' and ZCOMMENT like '%full-reading:mindmap:%';"
```

当前完整精读验收目标：

- 草稿卡片来自模型输出拆分，不使用内置模板。
- 脑图根节点和子节点来自同一次模型输出。
- 重复写入同一草稿时能按 Codex 元数据跳过重复节点。

8. 单文档全流程验收

在同一个 topic/book 文档里完成对话/解释、制卡、新建脑图、补到当前脑图、设置保存、上传文件、一次性目标、队列/历史、缓存 PDF、原生高亮和导出标注副本后，收集 action result JSON/JSONL，并运行：

```bash
"$HOME/.codex/marginnote-assistant/send_action.py" settings_update --speed fast --record
"$HOME/.codex/marginnote-assistant/send_action.py" upload_file --file-name notes.md --file-content "# notes" --record
"$HOME/.codex/marginnote-assistant/send_action.py" queue_status --record
```

`--record` 会把 action result 追加到 `$HOME/.codex/marginnote-assistant/release/evidence/action-results.jsonl`。完成同一文档测试后，可双击发布包根目录的 `Collect Single Document Acceptance.command`，或运行：

```bash
python3 "$HOME/.codex/marginnote-assistant/single_document_acceptance.py" \
  --topicid <topicid> \
  --bookmd5 <bookmd5> \
  --events "$HOME/.codex/marginnote-assistant/events.jsonl" \
  --action-results "$HOME/.codex/marginnote-assistant/release/evidence/action-results.jsonl" \
  --output ./codex-companion-single-document-acceptance.json
python3 "$HOME/.codex/marginnote-assistant/release_acceptance.py" \
  --single-document-evidence ./codex-companion-single-document-acceptance.json
```

`single_document_acceptance.py` 会默认从 `release/evidence`、项目根目录和桌面自动发现最新 native highlight evidence；只有需要强制使用某个文件时，才额外传 `--native-highlight-evidence ./native-highlight-evidence.json`。

验收条件：

- 报告 schema 为 `codex-companion-single-document-acceptance-v1`。
- `summary.singleDocumentAcceptance=PASS`，所有 checks 为 `PASS`。
- 所有事件和 action result 均匹配同一个 `topicid/bookmd5`；跨文档证据必须被拒绝。
- 设置页 `本文档验收` 按钮会调用 `single_document_acceptance_summary`，在面板内显示当前文档 PASS/BLOCK 和阻塞项；它用于日常功能验收，不替代最终 `release_acceptance.py` gate。

9. 视觉 QA

截图不是功能验收的主路径，只用于确认 UI：

- 面板可见。
- 没有白屏。
- 标题栏可拖动移动面板。
- 标题栏 `-` / `+` 按钮可缩小和放大面板。
- 按钮文本没有溢出。
- 缩放到最小尺寸后控件仍可读、可点。
- 权限、模型、速度、代理、目标、上传、状态栏队列/停止、队列数量和运行状态行不溢出。
- 设置页“检查权限”能返回当前 PDF、MN4 数据库、导出目录和 PyMuPDF 状态；macOS 拦截时能看到 Full Disk Access 指引，“打开设置”能尝试打开对应系统设置页。
- 设置页“本文档验收”能返回当前 PDF 的按钮/工作流检查结果；“发布验收”仍显示发布 gate，不混在主操作区。
- 设置页“缓存PDF”能触发 `pdfCacheUploadStarted` 和 `pdfCacheUploadPosted` 事件；随后导出标注 PDF 时 Companion 优先使用当前 book 的缓存 PDF 副本。
- 文件子界面只出现上传相关控件，不放停止或队列控件。
- 主界面对话区底部一直显示输入框和“发送”按钮；发送不混入 AI 任务按钮网格。
- 对话页显示独立 `goalRunPanel`，`goalActionStrip` 内的 `目标` 按钮和目标状态同在其中；常用区是 2x2：解释、制卡、新建脑图、精读；`workflowActionPanel` 常驻显示当前脑图区的补到当前/重组当前，以及原文区的高亮/导出/状态；刷新上下文在当前内容区；运行态提示只放刷新和去设置；状态栏只放连接、队列/停止、队列和运行状态。
- 按钮子界面可显示预设按钮、自定义按钮、动作类型和“主界面”开关；被勾选的自定义按钮会显示在主界面常用 prompt 区，未勾选时不自动显示重复的默认 prompt。
- 历史和清空按钮不溢出，点击历史后能在消息区显示历史记录。
- 对话、按钮、设置、文件、历史五个子界面可切换。
- 同一按钮连续点击时不因焦点残留而失效。
- 执行中对话页显示动态进度和已用秒数；`queue_status` 和 `/status` 能返回当前/最近任务的动作、阶段、详情和耗时。
- 生成卡片、脑图或完整精读后先出现待写入草稿；在草稿框编辑内容并用 `## 标题` 分隔卡片后点击“写入 MN”，写入结果应采用编辑后的卡片内容；点击“丢弃”不会写入。
- 对“补到当前脑图/合并脑图”做两次手动验证：未选中 MN 脑图节点时应提示先选中节点且不写入；选中目标节点后写入应把新增节点挂到该节点下，而不是新建根节点。
- 执行中动作按钮不整体置灰，继续点击动作会自动入队；消息后可选择停止当前并直接执行或查看队列状态。
- 状态栏能显示 Companion 结果。

## 当前不能作为发布通过的项

- 原生高亮还没有可靠发布方案。
- 单文档全流程验收证据还未补齐前，最终 `release_acceptance.py` 会继续阻塞 `single_document_acceptance` gate。
- WebView 输入式聊天 UI 和鼠标缩放已实现；仍需跨机器视觉 QA。
- 安装脚本已提供，但还没有签名、图形安装器或跨机器发布验证。
- `repair_knows_highlights` 默认禁用直接写数据库；PDF 标注副本导出已有 PyMuPDF 基础路线和 MN4 进程上传 PDF 缓存路线，native visible highlight 仍需 MN4 原生 API。

完整完成度矩阵见 `RELEASE_STATUS_MATRIX.md`。
当前证据审计见 `CURRENT_RELEASE_AUDIT.md`。
