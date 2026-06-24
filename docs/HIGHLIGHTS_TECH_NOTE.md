# MarginNote 高亮技术说明

## 用户要求

高亮不应修改原文 PDF。默认应使用 MarginNote 自己的高亮/批注系统，这样：

- 原始 PDF 保持干净。
- MN4 内部能显示高亮。
- 用户需要分享时，可以由 MN4 或插件导出带标注 PDF 副本。

## 当前观察

对 MN4 数据库的观察显示，可见高亮不是普通文本行。真正的原生高亮行包含二进制字段，例如：

- `ZHIGHLIGHTS`
- `ZHIGHLIGHT_PIC`

这些字段看起来是 `NSKeyedArchiver` 风格的 plist/blob，内部包含选区、坐标、文字和渲染相关信息。只复制标题、页码或文字并不能保证 MN4 里出现可见高亮。

2026-06-10 的只读审计结果进一步确认：

- Park 论文 canonical topic 中，`Codex-KNOWS-native-highlight` 有 96 行 `ZTYPE=7`，且 96 行都有 `ZHIGHLIGHTS` blob。
- 当前 Park notebook topic 中，也有 96 行 `ZTYPE=7`，但 `ZHIGHLIGHTS` blob 数为 0。
- MN4 app 二进制中能看到 `AppendHighlight`、`TextHighlightTool`、`UpdateAnnotationOfNotes`、`importPdfAnnotations`、`ExportHighlightedPages` 等内部符号，但尚未确认这些能力是否作为稳定 JS 插件 API 暴露。
- 现有 Zotero 插件的 `AnnotationImportService` 只是把 Zotero annotations 转成 MN 子卡片，不会在 PDF 原文处创建 MN4 native visible highlight。

## 为什么不能把直接写数据库作为发布方案

- `ZHIGHLIGHTS` blob 格式不是公开稳定 API。
- 直接写 SQLite 需要 Full Disk Access，普通用户体验差。
- MN4 运行时写库有一致性风险。
- 复制已有 blob 只能服务特定论文/特定选区，不是通用高亮功能。

因此当前 `repair_knows_highlights` 在发布版里默认禁用直接写库。只有显式设置 `CODEX_MN_ALLOW_DB_HIGHLIGHT_WRITE=1` 时才允许实验性写入。

只读审计命令：

```bash
~/.codex/marginnote-assistant/audit_highlights.py
```

## 推荐发布路线

1. 优先查找 MN4 插件 JS API 是否能创建 highlight/annotation。
2. 如果有原生 API，所有高亮通过插件内部 API 创建，Companion 只返回“页码、文本、定位建议、颜色、说明”。
3. 如果没有稳定 API，退而求其次：
   - 在 MN4 内创建带回链的卡片/摘录。
   - 用单独导出器生成带标注 PDF 副本。
   - 明确告诉用户这不是 MN4 原生高亮。

## 当前运行时探测

0.4.x 已加入 `nativeApiCapabilities` 运行时事件。MN4 面板加载时，插件会只读检查
`studyController`、`notebookController`、共享 `resolveDocumentController()` 发现的一组 document-controller 候选、`selectedNote`、`Database` 和
`Application` 上是否暴露 `AppendHighlight`、`highlightFromSelection`、`TextHighlightTool`、`UpdateAnnotationOfNotes`、
`importPdfAnnotations`、`ExportHighlightedPages` 等候选 selector。document-controller 候选包括
`lastDocumentController`、`selectionDocumentController`、`studyController` / `notebookController` 下的
`documentController`、`docController`、`currentDocumentController`、`readerController`、`readerViewController`、
`pdfController`、`pdfViewController`，以及 `currentDocument.documentController/docController` 嵌套路径。

这个探测不会调用这些方法，也不会修改 PDF、SQLite 或笔记。它只把候选方法写入 Companion
事件日志，供 `diagnose_highlights` 和 `doctor.py` 显示。只有探测到稳定候选并完成实际可见高亮验证后，
才可以把高亮从诊断能力升级为发布能力。

2026-06-11 继续核对官方 `marginnoteapp/Addon` API 头文件后，确认 `JSBDocumentController` 公开了：

- `selectionText`
- `isSelectionText`
- `imageFromSelection`
- `highlightFromSelection`

因此 0.4.x 新增了 `request_native_highlight_selection`。它通过 Companion 队列发送
`nativeAction=highlight_current_selection`，由 MN4 插件在轮询时尝试调用最近一次 PDF 选区事件里的
`documentController.highlightFromSelection()`。这条路线仍然保持保守：

- 优先在用户已经有当前 PDF 选区时执行。
- 插件会在 `PopupMenuOnSelection` 里缓存 `documentController`，并尝试往当前 `PopupMenu` 追加“Codex 高亮选区”；这个入口直接调用同一个 `highlightCurrentSelection`，避免用户点 Web 面板按钮时切走焦点丢失选区。
- 2026-06-12 继续增强：Web 面板按钮现在是“高亮下一选区”语义，队列命令带 `preferNextSelection=true`。如果当前没有有效选区，插件会直接记录 `nativeHighlightNextSelectionArmed`，进入一次性的“下一次 PDF 选区自动高亮”模式；如果当前仍有有效选区，则立即走官方 `highlightFromSelection()`。用户回到 PDF 重新选中文字后，`PopupMenuOnSelection` 会先尝试安装“Codex 高亮选区”弹出菜单，再记录 `nativeHighlightNextSelectionConsumed` 并立即走同一个官方 `highlightFromSelection()` 路线。
- 2026-06-11 继续增强：从选区弹出菜单触发时，命令会带 `source=selection-popup-menu` 和 `allowCachedSelectionText=true`。如果菜单点击后 `documentController.selectionText` 暂时读成空，但 `PopupMenuOnSelection` 刚缓存过选中文本，插件不会提前以 `missing-selection` 失败，而是尝试调用官方 `highlightFromSelection()`，并在事件里记录 `usedCachedSelectionText` 和 `selectionTextSource=cached-selection`。这仍然不写 SQLite，也不伪造成功；真正成功必须看到 `nativeHighlightSelectionPosted` 和 MN4 中的可见高亮。
- 未开启下一次选区模式且仍没有 `documentController` 或没有 `selectionText` 时，记录 `nativeHighlightSelectionFailed`，并附带 `candidateLabels`、`candidateCount`、`selectedDocumentControllerLabel`，不伪造高亮。
- 2026-06-11 继续增强：如果运行态能拿到 PDF/reader document controller，但 JSB 无法枚举 `highlightFromSelection` selector，插件不再提前判定不可用，而是尝试调用官方 `highlightFromSelection()`。成功或失败都会记录 `selectorVerified` 和 `attemptedUnverifiedSelector`；失败仍然不会伪造高亮。
- 不写 SQLite，不修改原始 PDF。
- 当前实测在没有活跃选区时得到 `nativeHighlightSelectionFailed reason=missing-document-controller`，但该事件来自共享 resolver 之前的旧 MN4 运行态。重新打开面板或重启 MN4 后，需要确认新的 `nativeApiCapabilities.documentControllerCandidates` 和真实 `nativeHighlightSelectionPosted`。

2026-06-11 11:38 CST 继续增强 `documentControllerCandidates()`：候选路径现在对 `studyController` 和
`notebookController` 都显式保留稳定诊断 label，并继续做去重，覆盖：

- 直接路径：`currentDocumentController`、`readerController`、`readerViewController`、`reader`、`readerView`、`readerVC`、`pdfController`、`pdfViewController`、`pdfReader`、`pdfReaderController`、`pdfDocumentController`、`documentViewController`、`docViewController`、`pdfView`。
- 嵌套路径：`readerController.documentController`、`readerController.docController`、`readerController.currentDocumentController`、`readerViewController.documentController`、`pdfController.documentController`、`pdfViewController.documentController` 及同类 `docController/currentDocumentController` 变体。

这样 `nativeApiCapabilities.documentControllerCandidates`、`nativeHighlightSelectionFailed.candidateLabels` 和
`selectedDocumentControllerLabel` 更稳定，后续能从事件日志直接判断 MN4 当前到底把可高亮的 document controller 暴露在哪个属性上。
这仍然只是发现与诊断能力；只有在活跃 PDF 选区下看到 `nativeHighlightSelectionPosted`、同一 topic/book 作用域内的 `ZHIGHLIGHTS` blob 和页面肉眼可见高亮后，原生高亮才算发布完成。0.4.25 本机运行态已确认 `native_api_matrix` PASS，能找到 `studyController.readerController.currentDocumentController.highlightFromSelection`，但这仍不等价于可见高亮发布证据。`Collect Native Highlight Evidence.command` 现在会先通过 `/marginnote/action` 请求打开中的 MN4 插件执行一次 `request_native_highlight_selection`；如果插件进入 `nativeHighlightNextSelectionArmed`，采证脚本不会立刻结束，而是在默认 90 秒窗口内继续等待用户重新选区后的 `nativeHighlightSelectionPosted` 或 `nativeHighlightSelectionFailed`。最终证据只用最新 posted event 的 topic/book 和同一作用域的 blob 查询结果通过验收；缺 scope、scope 不匹配、blob 行数为 0、本次尝试失败或只是 armed 后超时，都会写进 evidence 并继续阻塞。

2026-06-11 继续增强高亮命令执行：`native_api_capability_matrix` 现在把
`studyController.readerController`、`readerViewController`、`pdfController`、`pdfViewController` 等已存在的
PDF 控制器目标视为可尝试路线。若 selector 不可枚举但控制器存在，矩阵会把 evidence 标为
`unverified-highlightFromSelection-call`，并提示用户在 PDF 中选中文本后尝试官方调用。Web 面板按钮触发的
`highlight_current_selection` 队列命令也会默认允许使用最近一次 `PopupMenuOnSelection` 缓存的选区文本，减少点击浮窗后焦点切走导致的提前失败。

## 当前可用的 PDF 副本导出路线

0.4.x 已把 `export_annotated_pdf` 从占位动作升级为安全降级实现：

- Companion 解析当前文档本地 PDF 路径：优先使用当前 book 的 Companion PDF 缓存副本，其次使用插件传入的 `pdfPath`，否则只读查询 MN4 `ZBOOK` 表并尝试在 MNDocs 根目录下定位 `ZFILE/ZBOOKURL`，最后才使用已知路径映射。
- Companion 从 `selectionText`、`annotationText` 或 `sourceExcerpt` 中提取可搜索文本。
- 本地 PyMuPDF 只打开原始 PDF 读取文本层，在 OneDrive `Codex Companion/exports` 下写出新 PDF。
- 原始 PDF 导出前后会计算 sha256；返回值会明确 `modifiedOriginal=false` 或报告异常。
- 如果没有匹配到文本、没有 PyMuPDF、没有 PDF 路径，动作会失败并说明原因，不会伪造高亮。
- 如果后台 LaunchAgent 没有权限读取 OneDrive 或目标 PDF，动作会返回 `status=PERMISSION` 和 Full Disk Access 说明；这属于 macOS 隐私权限问题，不会写副本或修改原文。用户也可以先在 MN4 设置页点击“缓存PDF”，由 MN4 插件进程把当前 PDF 上传到本机 Companion 缓存，后续导出会优先使用缓存副本。
- 设置页“检查权限”和 `diagnose_permissions` 动作会提前检查当前 PDF、MN4 数据库、导出目录和 PyMuPDF，避免用户只看到导出失败。设置页“缓存PDF”触发 `cache_pdf_from_marginnote`；设置页“打开设置”和 `open_full_disk_access_settings` 会尝试打开 macOS Full Disk Access 页面。`doctor.py` 同步显示 `Companion file access`。

这条路线会在 PDF 副本里写入标准 highlight annotation，适合分享或归档；它不等同于 MN4 内部 native visible highlight，也不会让 MN4 原文视图自动出现高亮。

## 发布验收标准

高亮功能只有同时满足这些条件才算完成：

- MN4 页面中肉眼可见高亮。
- 数据和卡片/脑图节点有对应关系。
- 原文 PDF 文件校验值不变。
- 导出标注 PDF 时产生新文件，不覆盖原文。
- 不要求用户手动打开 SQLite 或授予 Full Disk Access 才能使用基础高亮。
