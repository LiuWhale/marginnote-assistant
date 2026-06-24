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
- `/status.mnRuntime.ready=true`，且 `runtimeHandlerStale=false`。
- `nativeApiCapabilities` 为当前插件版本。
- 同一 topic/book 的 `single_document_acceptance` 通过。
- 原生可见高亮 evidence 证明页面可见高亮和同 scope `ZHIGHLIGHTS` blob。
- signed/notarized pkg 和跨机器安装 evidence。
