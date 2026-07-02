# Programmatic Verification

## 为什么不依赖截图

截图只能回答“界面看起来是不是正常”，不能证明插件真的把卡片、脑图或高亮写进了 MarginNote。功能验收应使用程序化证据：

- Companion 返回值。
- 插件事件日志。
- MN4 数据库中的卡片/脑图结果。
- 必要时再做一次视觉 QA。

## 三种触发方式

1. 用户点击 MN4 面板按钮
   - 最接近真实用户。
   - 需要人工或系统级 UI 自动化。

2. Companion 队列
   - 推荐开发验收方式。
   - `send_action.py` 把命令写入 `/marginnote/enqueue`。
   - MN4 插件轮询 `/marginnote/poll` 后执行，仍然用 MN4 原生 API 创建卡片/脑图。

3. macOS Accessibility 点击
   - 可以模拟真实鼠标点击。
   - 需要在系统设置里给 Codex、Terminal 或 `osascript` 辅助功能权限。
   - 当前机器上 `osascript` 被系统拒绝，所以不是可靠主路径。

## 常用命令

检查 Companion：

```bash
"$HOME/.codex/marginnote-assistant/send_action.py" health --direct
```

直接让 Companion 生成响应，不写入 MN4：

```bash
"$HOME/.codex/marginnote-assistant/send_action.py" generate_full_reading --direct
```

通过插件队列写入 MN4：

```bash
"$HOME/.codex/marginnote-assistant/send_action.py" generate_full_reading \
  --topicid CA970092-A137-40D7-9A78-DD76EB407C05 \
  --bookmd5 253dd5804dd4973bcea545ebcc7ee5a760c73581e1a4e25904fd10ae4b8d1246
```

查看最近事件：

```bash
tail -n 50 "$HOME/.codex/marginnote-assistant/events.jsonl"
```

查看最近结构化诊断日志：

```bash
tail -n 50 "$HOME/.codex/marginnote-assistant/logs/diagnostics.jsonl"
```

检查当前发布包：

```bash
python3 release_smoke_test.py release/CodexCompanion-0.4.25-latest-dist.zip
python3 release_smoke_test.py release/CodexCompanion-0.4.25-latest-dist.zip --install-dry-run
```

检查当前运行态：

```bash
curl -fsS http://127.0.0.1:48761/status
```

检查 0.4.25 后 main 的 UI/CLI 回归：

```bash
python3 -m unittest \
  tests.test_companion_controls.CompanionControlsTests.test_codex_cli_retries_transient_cloud_config_timeout \
  tests.test_companion_controls.CompanionControlsTests.test_codex_cli_cloud_config_timeout_message_is_actionable_after_retry \
  tests.test_web_controls_static.WebControlsStaticTests.test_send_button_is_excluded_from_busy_queue_pseudo_label
```

这些测试分别证明：Codex CLI `cloud config bundle` 启动超时会自动重试并给出可操作提示；发送按钮不会被运行中全局 `可排队` 伪元素追加第三行。

检查 Knowledge Agent OS 内核切片：

```bash
python3 -m unittest \
  tests.test_object_kernel \
  tests.test_source_registry \
  tests.test_external_gateway \
  tests.test_transaction_manager \
  tests.test_native_transaction_static \
  tests.test_workflow_engine \
  tests.test_skill_marketplace \
  tests.test_verification_agent \
  tests.test_web_controls_static \
  tests.test_doctor_checks \
  tests.test_ui_functional_acceptance \
  tests.test_single_document_acceptance \
  tests.test_companion_controls.CompanionControlsTests.test_external_gateway_rejects_direct_write_and_strips_secret \
  tests.test_companion_controls.CompanionControlsTests.test_operation_ledger_detail_separates_note_and_card_residuals \
  tests.test_companion_controls.CompanionControlsTests.test_workflow_start_enqueues_safe_steps_and_pauses_at_confirmation \
  tests.test_companion_controls.CompanionControlsTests.test_operation_ledger_lists_and_loads_object_scoped_operations \
  tests.test_companion_controls.CompanionControlsTests.test_skill_runtime_actions_return_operation_plan_and_run_ledger
```

这些测试分别证明：MNObject 已有独立对象内核；Source Registry 能记录来源修复动作；External Automation Gateway 能拒绝外部直接写入、隐藏 secret、记录 callback lifecycle，并把 requestId、caller、action、workflowRunId、callback 证据挂到 Operation Ledger；Transactional Native Editor 证据能分离 note/card rollback 和 residual proof，避免“拒绝后结构删了但卡片残留”被误判为成功；Workflow Runtime v2 已有持久化 run store、下一步读取、恢复和取消事件证据；Skill Runtime v2 会拒绝缺少 `dryRun`、`rollback`、`acceptance` 的写入技能，并能生成 dry-run-first operation plan 和 `codex.mn.skillRun.v1`；Verification Agent 会输出 `codex.mn.verificationReport.v1`，没有 native probe 时是 `UNKNOWN` 而不是假 PASS；`ui_functional_acceptance.py` 会用任意文档 payload 检查 WebView 静态控件、行为 marker、Notebook Workspace 内核、workspace surface action 和无 topic 原生按钮防误触；显式加 `--browser-render` 时会启动本地 headless browser 验证渲染后的 `webview_browser_render`；显式加 `--browser-interaction` 时会通过 DevTools 协议点击 Chat/Workspace、全部 Workspace Navigator 卡片、全部 Workbench tab、Command Pane、设置页和历史页，验证 `webview_browser_interaction`；显式加 `--browser-actions` 时会通过 stub Companion 注入任意 `MNObject` 和 notebook scope，点击 Agent Plan、MN 对象扫描、读取脑图树、Notebook Workspace、Runbook 继续/自动准备、Object Browser 刷新/筛选、Object Graph、对象关系保存/取消、对象活动、Operation Ledger 刷新/筛选、Verification Center、`verificationRepairPlanRecommendedButton`、Knowledge Search、目标脑图状态、health、AI 后端、日志和历史范围按钮，并验证 `webview_browser_actions` 记录了对应 backend action 且没有连接失败 UI；`buttonActionDeltas` 还会证明每个按钮各自让预期 action 计数增加，避免两个按钮复用同一 action 时只靠最终 action 集合误判；显式加 `--browser-write-actions` 时会验证 `webview_browser_write_actions`，覆盖生成脑图树、草稿保存、Mindmap Studio Diff 预览/应用、`mindmapStudioVerifyButton`、`mindmapStudioRollbackButton`、事务验证/证据/probe、加入复习队列，以及 `write_draft`、`accept_ai_edit_transaction`、`reject_ai_edit_transaction` 原生 bridge 调用；WebView、doctor 和 single-document acceptance 会要求 `knowledgeConsolePanel`、`studioCanvasPanel`、`operationLedgerDrawer`、`sourceRegistryPanel`、`verificationReportPanel`、`externalGatewayPanel`、`skillCenterPanel` 这些 Knowledge OS shell anchors。

0.4.25 本机验收中，`runtime_web_controls` 和 `native_api_matrix` 已 PASS；最终 `release_acceptance.py` 仍会因为原生可见高亮、缺 signed/notarized pkg、缺跨机器证据和缺单文档完整 PASS evidence 返回非零。

## 验收判断

队列命令只有在以下链路都出现时才算真正执行：

- `/marginnote/enqueue` 返回 `ok: true`。
- 事件出现 `commandsReceived`。
- 事件出现 `handleResponse`。
- 卡片任务出现 `createCardsFinished`。
- 脑图任务出现 `createMindmapFinished`。
- 事件出现 `commandsAcked`。
- 数据库中能查到新增卡片/脑图节点。

最终发布验收还需要：

- `release_smoke_test.py` 和 `--install-dry-run` 通过。
- `ui_functional_acceptance.py` 对任意文档 payload 返回 `codex-companion-ui-functional-acceptance-v1` 且所有检查 PASS；设置页 `UI 功能验收` 按钮（`uiFunctionalAcceptanceButton`）会调用 `ui_functional_acceptance_summary`，在插件 UI 内运行同一套任意文档验收，并把 `uiFunctionalAcceptanceLine` 渲染为 `UI 功能验收：PASS / 11/11 / 阻塞 0`。`webview_button_coverage` 会枚举每个静态 WebView button，并在按钮没有被归入实际点击、交互点击、写入流程、面板控制、表单/破坏性、文件选择、关闭类或隐藏运行态时失败。发布前推荐再运行 `python3 ui_functional_acceptance.py --browser-render --browser-interaction --browser-actions --browser-write-actions` 采集渲染 DOM、UI 点击、backend action wiring 和写入/事务 bridge wiring 证据。`webview_browser_interaction` 会覆盖全部 Workspace Navigator 卡片、全部 Workbench tab、Command Pane 和设置页上下文范围按钮；`webview_browser_actions` 会覆盖 `sendButton`、发送后清空、`Enter key` 提交、`conversation_new`、`conversationHistoryObjectButton`、`conversationHistoryAllButton`、上下文范围切换、native `context` bridge、`settings_update` 文件路径保存、`update_check`、下载页 `open_url`、`diagnose_permissions`、`open_full_disk_access_settings`、`request_pdf_cache`、`request_native_capability_probe`、`notebook_runbook_preflight_record`、`object_graph`、`object_activity`、`object_graph_relation_save`、`verificationRepairPlanRecommendedButton`、`knowledge_index_search` 和 `mindmap_target_status`。报告中的 `buttonActionDeltas` 必须证明每个映射按钮都让自己的预期 action 计数增加，避免基础 UI 功能只靠人工确认或最终 action 集合误判；同一浏览器会话还会确认设置页真的显示 `UI 功能验收：PASS`。`webview_browser_write_actions` 还会覆盖 `mindmapStudioVerifyButton` 和 `mindmapStudioRollbackButton`。
- `/status.mnRuntime.ready=true`，且 `runtimeHandlerStale=false`。
- `nativeApiCapabilities` 为当前插件版本。
- 同一 topic/book 的 `single_document_acceptance` 通过。
- 原生可见高亮 evidence 证明页面可见高亮和同 scope `ZHIGHLIGHTS` blob。
- signed/notarized pkg 和跨机器安装 evidence。
