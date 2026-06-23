# Privacy and Permissions

## 本地数据

Codex Companion 默认运行在本机：

```text
http://127.0.0.1:48761
```

MN4 插件会把当前选中文本、当前节点文本、topic id 和 book md5 发给本地 Companion。Companion 会把短会话历史保存在：

```text
~/.codex/marginnote-assistant/sessions
```

事件日志保存在：

```text
~/.codex/marginnote-assistant/events.jsonl
```

## OpenAI 调用

如果没有配置 `OPENAI_API_KEY`，且本机 Codex CLI 也不可用，Companion 不会把文本发到 OpenAI，也不会用本地模板生成问答、卡片、脑图或完整精读。此时只保留本地权限诊断、运行态采证、PDF 缓存和导出等工具能力。

如果配置了 `OPENAI_API_KEY`，资料选中文本、当前节点文本和用户问题会发送给 OpenAI Responses API，用于生成回答或卡片内容。模型和 token 上限由 `.env` 控制：

```text
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.5
OPENAI_MAX_OUTPUT_TOKENS=1800
```

如果在面板中配置 HTTP/HTTPS 代理，OpenAI 请求会经由该代理转发。代理 URL 保存在本机 `companion_settings.json`，`health` 和 `doctor.py` 只显示是否配置代理及 scheme，不在日志中输出完整代理地址。当前发布候选不支持 SOCKS5 代理，避免未安装 PySocks 时产生“看似配置成功、实际未走代理”的状态。

## Codex CLI 调用

如果在设置中选择 `codex_cli`，Companion 会把资料选中文本、当前节点文本和用户问题交给本机 `codex exec --skip-git-repo-check`。插件只检查 `codex` 可执行文件是否存在，不读取或展示 `~/.codex/auth.json`。Codex CLI 后续如何联网、使用哪个账号或模型，由用户本机 Codex CLI 配置决定。

## 原文 PDF

插件默认不修改原文 PDF。卡片和脑图通过 MarginNote 原生 API 写入 MN4 笔记本。

高亮的发布目标也是使用 MarginNote 原生高亮/批注数据。只有当用户主动选择“导出标注 PDF”时，才应生成带标注的 PDF 副本。

当后台 Companion 因 macOS 隐私权限无法直接读取 OneDrive/iCloud 中的当前 PDF 时，用户可以在 MN4 面板设置页点击“缓存PDF”。这会由 MarginNote 插件进程读取当前 PDF，并把 PDF 内容上传到本机 Companion 的 `uploads/pdf-cache` 目录；后续导出标注 PDF 会优先使用该缓存副本。缓存只在本机保存，不修改原始 PDF。

## macOS 权限

当前卡片/脑图功能不需要 Full Disk Access。

以下场景可能需要额外权限：

- 系统级自动点击：需要 Accessibility 辅助功能权限。
- 直接检查或修复 MN4 SQLite：可能需要 Full Disk Access。
- 导出 PDF 到 OneDrive：需要目标目录写入权限。
- 后台 Companion 直接读取 OneDrive/iCloud PDF：可能需要 Full Disk Access；也可先在 MN4 面板中点击“缓存PDF”作为本机缓存路线。

发布版应避免把 SQLite 写入作为默认用户路径。
