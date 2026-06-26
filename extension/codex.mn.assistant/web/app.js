(function() {
  var state = {
    busy: false,
    runActive: false,
    currentQueueId: '',
    context: {},
    contextScope: 'auto',
    contextScopeInitialized: false,
    lastPromptFromSelection: '',
    settings: {},
    customButtons: [],
    goal: {},
    files: [],
    queue: {pending: 0},
    pdfCache: {state: 'unknown'},
    mindmapTarget: {state: 'unknown', target: {}, options: []},
    mindmapTreeCache: {schema: 'codex.mn.mindmapTreeCache.v1', available: false},
    mindmapDiffApply: {schema: 'codex.mn.mindmapDiffApplyStatus.v1', available: false},
    latestMindmapDiff: null,
    aiEditTransactionStatus: {schema: 'codex.mn.aiEditTransactionStatus.v1', available: false},
    contextDocumentKey: '',
    autoPdfCacheRequestedKey: '',
    openaiConfigured: false,
    codexCliAvailable: false,
    codexCliPath: '',
    aiBackend: 'auto',
    mnApi: {},
    draft: null,
    pendingAiEditDrafts: {},
    progressTimer: null,
    progressStatusTimer: null,
    progressStatusInFlight: false,
    progressBody: null,
    progressStartedAt: 0,
    progressRequestId: '',
    progressAction: '',
    progressStage: '',
    progressDetail: '',
    pendingGuideAction: '',
    pendingGuidePrompt: '',
    latestAssistantReply: '',
    stagedAction: '',
    stagedPrompt: '',
    stagedLabel: '',
    lastSourcePdfPath: '',
    nativeApiCapabilities: {},
    drainingQueue: false,
    queuePumpTimer: null,
    contextAutoRefreshTimer: null,
    nativeHighlightWizardTimer: null,
    deferredNativeQueueIds: {},
    update: {},
    updateAutoChecked: false,
    pluginVersion: '',
    conversationId: '',
    sessionId: '',
    conversationHistoryScope: 'document',
    conversations: [],
    notebookWorkspace: {schema: 'codex.mn.notebookWorkspace.v1', available: false},
    notebookWorkspaceInFlight: false,
    objectBrowser: {schema: 'codex.mn.objectBrowser.v1', available: false},
    objectBrowserInFlight: false,
    objectRegistryScanInFlight: false,
    objectBrowserLastId: '',
    objectGraph: {schema: 'codex.mn.objectGraph.v1', available: false},
    objectGraphInFlight: false,
    objectGraphLastId: '',
    objectActivity: {schema: 'codex.mn.objectActivity.v1', available: false},
    objectActivityInFlight: false,
    objectActivityLastId: '',
    operationLedger: {schema: 'codex.mn.operationLedger.v1', available: false},
    operationLedgerDetail: null,
    operationLedgerInFlight: false,
    operationLedgerLastId: '',
    diagnosticLogs: [],
    agentOperation: null,
    agentPlanInFlight: false,
    agentPlanRefreshTimer: null,
    agentPlanLastKey: '',
    knowledgeWorkspace: {schema: 'codex.mn.knowledgeWorkspace.v1', available: false},
    workflowWorkspace: {schema: 'codex.mn.workflowWorkspace.v1', available: false},
    workflowRunInspector: null,
    activeProductMode: 'workspace',
    lastWorkspacePane: 'object',
    activeWorkspaceSurface: 'console',
    activeWorkbenchPane: 'object'
  };
  var MAIN_PINNED_BUTTON_LIMIT = 4;
  var requiredControlIds = [
    'aiChatShell',
    'modeSwitchBar',
    'chatModeButton',
    'agentWorkspaceModeButton',
    'modeIntentLine',
    'workspaceNavigator',
    'workspaceNavigatorSummary',
    'workspaceNavConsoleButton',
    'workspaceNavMindmapStudioButton',
    'workspaceNavCardFactoryButton',
    'workspaceNavLedgerExplorerButton',
    'workspaceNavKnowledgeGraphButton',
    'workspaceNavWorkflowBuilderButton',
    'workspaceNavSkillCenterButton',
    'notebookWorkspacePanel',
    'notebookWorkspaceTitle',
    'notebookWorkspaceSummary',
    'notebookWorkspaceRefreshButton',
    'notebookWorkspaceFocus',
    'notebookWorkspaceObjectCount',
    'notebookWorkspaceMindmap',
    'notebookWorkspaceReview',
    'notebookWorkspaceWorkflow',
    'notebookWorkspaceLedger',
    'notebookWorkspaceActions',
    'workbenchTabs',
    'workbenchTabObject',
    'workbenchTabDialog',
    'workbenchTabOperation',
    'workbenchTabKnowledge',
    'workbenchTabWorkflow',
    'workbenchLayout',
    'objectWorkspacePanel',
    'dialogWorkspacePanel',
    'operationWorkspacePanel',
    'knowledgeWorkspacePanel',
    'workflowWorkspacePanel',
    'objectWorkspaceTitle',
    'objectWorkspaceMeta',
    'objectWorkspaceScope',
    'objectRiskPanel',
    'objectRiskSummary',
    'objectRiskList',
    'objectBrowserPanel',
    'objectBrowserRefreshButton',
    'objectRegistryScanButton',
    'objectBrowserTypeFilterSelect',
    'objectBrowserKindFilterInput',
    'objectBrowserSearchInput',
    'objectBrowserFilterButton',
    'objectBrowserSummary',
    'objectBrowserList',
    'objectGraphPanel',
    'objectGraphRefreshButton',
    'objectGraphRelationAddButton',
    'objectGraphSummary',
    'objectGraphNodes',
    'objectGraphRelationEditor',
    'objectGraphRelationTargetInput',
    'objectGraphRelationTypeInput',
    'objectGraphRelationLabelInput',
    'objectGraphRelationNoteInput',
    'objectGraphRelationSaveButton',
    'objectGraphRelationCancelButton',
    'objectActivityPanel',
    'objectActivityRefreshButton',
    'objectActivitySummary',
    'objectActivityList',
    'operationLedgerPanel',
    'operationLedgerRefreshButton',
    'operationLedgerSummary',
    'operationLedgerTypeFilterSelect',
    'operationLedgerStatusFilterInput',
    'operationLedgerSearchInput',
    'operationLedgerFilterButton',
    'operationLedgerList',
    'operationLedgerDetailPanel',
    'operationLedgerDetailTitle',
    'operationLedgerDetailMeta',
    'operationLedgerDetailEvidence',
    'operationLedgerDetailCloseButton',
    'operationWorkspaceTitle',
    'operationWorkspaceMeta',
    'operationCompilerPanel',
    'operationCompilerSummary',
    'operationPlanStats',
    'operationCompilerChecks',
    'operationDryRunDetails',
    'operationCompilerRepairActions',
    'operationWorkspaceNextActions',
    'mindmapStudioPanel',
    'mindmapStudioSummary',
    'mindmapStudioCurrentTree',
    'mindmapStudioDiffStage',
    'mindmapStudioApplyStage',
    'mindmapStudioTransactionStage',
    'mindmapStudioReadTreeButton',
    'mindmapStudioPreviewDiffButton',
    'mindmapStudioApplySelectedButton',
    'mindmapStudioVerifyButton',
    'mindmapStudioRollbackButton',
    'mindmapStudioStatusLine',
    'knowledgeWorkspaceTitle',
    'knowledgeWorkspaceSummary',
    'knowledgeWorkspaceScope',
    'knowledgeWorkspaceEntities',
    'knowledgeWorkspaceRelations',
    'knowledgeWorkspaceReviewQueue',
    'knowledgeWorkspaceReviewList',
    'knowledgeWorkspaceSearchInput',
    'knowledgeWorkspaceSearchButton',
    'knowledgeWorkspaceResults',
    'knowledgeWorkspaceActions',
    'workflowWorkspaceTitle',
    'workflowWorkspaceSummary',
    'workflowWorkspaceRuns',
    'workflowWorkspaceGateway',
    'workflowWorkspaceSkills',
    'workflowWorkspaceSkillsList',
    'workflowWorkspaceTemplates',
    'workflowWorkspaceRecentRuns',
    'workflowRunInspectorPanel',
    'workflowRunInspectorTitle',
    'workflowRunInspectorSummary',
    'workflowRunInspectorSteps',
    'workflowRunInspectorCloseButton',
    'workflowWorkspaceActions',
    'mindmapTreeCacheStatus',
    'mindmapTreeCacheText',
    'mindmapTreeRefreshButton',
    'mindmapTreePreviewList',
    'mindmapDiffWorkbench',
    'mindmapDiffWorkbenchTitle',
    'mindmapDiffWorkbenchSummary',
    'mindmapDiffWorkbenchPreview',
    'operationWorkspaceVerification',
    'settingsButton',
    'newConversationButton',
    'conversationHistoryButton',
    'conversationHistoryScopeLine',
    'conversationHistoryAllButton',
    'conversationHistoryObjectButton',
    'promptInput',
    'sendButton',
    'stopButton',
    'contextButton',
    'contextScopeAutoButton',
    'contextScopeSelectionButton',
    'contextScopeDocumentButton',
    'closeButton',
    'liveHistory',
    'contextSourceLine',
    'aiReadinessLine',
    'aiReadinessDetail',
    'selectionPreview',
    'updateNotice',
    'updateNoticeText',
    'statusPill',
    'pdfCacheBanner',
    'pdfCacheBannerLight',
    'pdfCacheBannerText',
    'pdfCacheFileBannerButton',
    'pdfCacheFileInput',
    'pdfCacheFileButton',
    'mindmapTargetBar',
    'mindmapTargetLight',
    'mindmapTargetSelect',
    'mindmapTargetRefreshButton',
    'agentWorkbenchBar',
    'agentWorkbenchLight',
    'agentWorkbenchLine',
    'agentWorkbenchDetail',
    'agentPlanRefreshButton',
    'mindmapDiffApplyStatus',
    'mindmapDiffApplyLight',
    'mindmapDiffApplyText',
    'aiEditTransactionCenter',
    'aiEditTransactionTitle',
    'aiEditTransactionSummary',
    'aiEditTransactionNotes',
    'contextLine',
    'readinessPanel',
    'mnApiStatusLine',
    'mnApiBackendSelect',
    'mnUrlApiSecretInput',
    'clearMnUrlApiSecretButton',
    'conversationHistoryPage',
    'conversationHistoryList',
    'conversationHistoryCloseButton',
    'fileSearchRootsInput',
    'fileSearchRootsStatusLine',
    'logsStatusLine',
    'logsList'
  ];
  var presetButtons = [
    {
      title: '精读材料',
      action: 'generate_full_reading',
      prompt: '对当前材料做完整精读：背景、问题、关键概念、公式/符号、方法链条、证据、局限、讲稿。区分原文事实、推断和解释；卡片和脑图节点要短；能回源时给页码、原文摘录和回链。'
    },
    {
      title: '文档问答',
      action: 'chat',
      prompt: '只基于当前文档、选区或上传上下文回答。每个关键结论后给 [参考] 第X页：原文摘录 (marginnote4app://page/...)；没有证据时说 当前文档中未找到相关信息。'
    },
    {
      title: '脑图问答',
      action: 'chat',
      prompt: '只基于当前选中 MN 节点或脑图卡片内容回答；引用用 [来源] 原文摘录 (marginnote4app://note/...)；不要根据标题猜；找不到就说 脑图中未找到相关信息。'
    },
    {
      title: '证据制卡',
      action: 'generate_card',
      prompt: '把当前选区或节点整理成短卡；包含标题、原文摘录、解释、边界、复述和页码/回链。每张卡正文要短，不把整段回答塞进一张卡。'
    },
    {
      title: '证据脑图',
      action: 'generate_mindmap',
      prompt: '生成覆盖全文章节的详细脑图大纲；使用 Markdown 层级：## 一级主题、### 二级主题、#### 三级细节点；长文目标覆盖主要章节、18-30 个二级主题、40-80 个三级细节点；每个叶子节点带简短依据、页码/回链；末尾给覆盖统计；不要编造不存在的内容。'
    },
    {
      title: '总结选中',
      action: 'chat',
      prompt: '总结当前选中内容：提炼核心观点、关键术语、上下文作用和可复述版本。'
    },
    {
      title: '解释选中',
      action: 'explain_selection',
      prompt: '解释当前选中内容：拆开术语、公式、符号、隐含假设和容易误解的地方。'
    },
    {
      title: '复习题',
      action: 'generate_card',
      prompt: '基于当前材料生成 5 道复习题，含答案、依据、易错点、来源链接/页码；没有依据则说明，不要编造。'
    },
    {
      title: '讲稿',
      action: 'generate_full_reading',
      prompt: '生成 30 秒、60 秒和 3 分钟讲稿；标注事实、解释和可能被追问的问题；引用关键原文摘录和页码。'
    },
    {
      title: '生成卡片',
      action: 'generate_card',
      prompt: '把当前选中内容或当前节点整理成一张 MarginNote 卡片，包含定位、解释、重点、页码、原文摘录和可复述说法。'
    },
    {
      title: '生成脑图',
      action: 'generate_mindmap',
      prompt: '把当前内容整理成完整层级脑图。要求覆盖全文章节和核心逻辑，使用 Markdown 层级：## 一级主题、### 二级主题、#### 三级细节点；节点标题简洁，正文包含解释、依据、页码/原文线索；末尾给覆盖统计。'
    },
    {
      title: '补脑图',
      action: 'expand_node',
      prompt: '补到当前选中的 MarginNote 节点下面，生成可直接合并到该节点下的短子节点；不要新建一棵脑图。'
    },
    {
      title: '重组脑图',
      action: 'reorganize_mindmap',
      prompt: '基于当前选中的脑图节点生成非破坏性的重组建议分支，不删除原节点，只追加新的分组结构。'
    },
    {
      title: '高亮下一选区',
      action: 'request_native_highlight_selection',
      prompt: '进入下一次 PDF 选区自动高亮；如果当前已有有效选区则立即尝试，不伪造高亮。'
    }
  ];

  function byId(id) {
    return document.getElementById(id);
  }

  function clip(text, limit) {
    var value = text ? String(text) : '';
    if (value.length <= limit) return value;
    return value.substring(0, limit) + '...';
  }

  function setText(id, text) {
    var el = byId(id);
    if (el) el.textContent = text || '';
  }

  function setValue(id, value) {
    var el = byId(id);
    if (el) el.value = value || '';
  }

  function getValue(id) {
    var el = byId(id);
    return el ? el.value : '';
  }

  function valueOf(id) {
    return getValue(id);
  }

  function textNode(tag, className, text) {
    var node = document.createElement(tag || 'div');
    if (className) node.className = className;
    node.textContent = text || '';
    return node;
  }

  function setChecked(id, checked) {
    var el = byId(id);
    if (el) el.checked = !!checked;
  }

  function getChecked(id) {
    var el = byId(id);
    return !!(el && el.checked);
  }

  function newRequestId() {
    return (
      Date.now().toString(16) +
      Math.random().toString(16).slice(2, 10)
    ).slice(0, 24);
  }

  function normalizeContextScope(scope) {
    var value = String(scope || 'auto').replace(/^\s+|\s+$/g, '').toLowerCase();
    if (value === 'selection' || value === 'selected' || value === '选区') return 'selection';
    if (value === 'document' || value === 'full' || value === 'fulltext' || value === 'full_text' || value === '全文') {
      return 'document';
    }
    return 'auto';
  }

  function currentContextScope() {
    state.contextScope = normalizeContextScope(state.contextScope);
    return state.contextScope;
  }

  function setContextScope(scope) {
    state.contextScope = normalizeContextScope(scope);
    renderContextScopeButtons();
    renderContextSourceLine(state.context || {});
    renderContextPreview();
    renderSettingsContextMeta(state.context || {});
    scheduleAgentPlanRefresh();
    updateActionAvailability();
  }

  function renderContextScopeButtons() {
    var scope = currentContextScope();
    var buttons = document.querySelectorAll('button[data-context-scope]');
    for (var i = 0; i < buttons.length; i++) {
      var buttonScope = normalizeContextScope(buttons[i].getAttribute('data-context-scope'));
      var active = buttonScope === scope;
      buttons[i].className = 'scope-button' + (active ? ' active' : '');
      buttons[i].setAttribute('aria-pressed', active ? 'true' : 'false');
    }
  }

  function renderStopButton() {
    var button = byId('stopButton');
    if (!button) return;
    button.className = 'small-button danger-lite ai-chat-stop-button' + (isActiveRun() ? '' : ' hidden');
  }

  function isActiveRun() {
    return !!(state.busy || state.runActive);
  }

  function setBusyButtons(busy) {
    var buttons = document.querySelectorAll('button[data-action]');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute('data-busy', busy ? 'queue-available' : 'ready');
    }
    updateActionAvailability();
    renderStopButton();
  }

  function updateRunToggleButton() {
    var button = byId('runToggleButton');
    if (!button) return;
    var pending = state.queue && state.queue.pending !== undefined ? parseInt(state.queue.pending || 0, 10) : 0;
    if (isActiveRun()) {
      button.textContent = '停止';
      button.disabled = false;
      button.className = 'danger-button run-toggle-button';
      button.setAttribute('data-state', 'busy');
      return;
    }
    if (pending > 0) {
      button.textContent = '继续';
      button.disabled = false;
      button.className = 'small-button run-toggle-button';
      button.setAttribute('data-state', 'pending');
      return;
    }
    button.textContent = '队列';
    button.disabled = false;
    button.className = 'small-button run-toggle-button';
    button.setAttribute('data-state', 'idle');
  }

  function releaseButtonFocus(currentTarget) {
    window.setTimeout(function() {
      if (currentTarget && currentTarget.blur) currentTarget.blur();
    }, 0);
  }

  function isTextInputElement(el) {
    if (!el) return false;
    var tag = String(el.tagName || '').toLowerCase();
    return tag === 'textarea' ||
      tag === 'select' ||
      tag === 'input' ||
      el.isContentEditable === true;
  }

  function isTextInputActive() {
    return isTextInputElement(document.activeElement);
  }

  function releaseTextInputFocus(id) {
    var el = byId(id);
    if (!el || !el.blur) return;
    window.setTimeout(function() {
      if (document.activeElement === el) el.blur();
    }, 0);
  }

  function bindButton(id, handler) {
    var el = byId(id);
    if (!el) return;
    el.addEventListener('click', function(ev) {
      releaseButtonFocus(ev.currentTarget);
      handler(ev);
    });
  }

  function switchTab(name) {
    var buttons = document.querySelectorAll('.tab-button');
    var panels = document.querySelectorAll('.tab-panel');
    for (var i = 0; i < buttons.length; i++) {
      var activeButton = buttons[i].getAttribute('data-tab') === name;
      buttons[i].className = 'tab-button' + (activeButton ? ' active' : '');
      buttons[i].setAttribute('aria-selected', activeButton ? 'true' : 'false');
    }
    for (var j = 0; j < panels.length; j++) {
      var activePanel = panels[j].getAttribute('data-panel') === name;
      panels[j].className = 'tab-panel' + (activePanel ? ' active' : '');
    }
  }

  function buildMessage(role, text) {
    var article = document.createElement('article');
    article.className = 'message ' + role;
    var roleEl = document.createElement('div');
    roleEl.className = 'message-role';
    roleEl.textContent = role === 'user' ? '你' : 'Codex';
    var bodyEl = document.createElement('div');
    bodyEl.className = 'message-body';
    bodyEl.textContent = text || '';
    article.appendChild(roleEl);
    article.appendChild(bodyEl);
    return {article: article, body: bodyEl};
  }

  function addMessageWithExtra(role, text, extraBuilder) {
    var targets = [byId('liveHistory'), byId('history')];
    var primaryBody = null;
    for (var i = 0; i < targets.length; i++) {
      if (!targets[i]) continue;
      var item = buildMessage(role, text);
      if (extraBuilder) extraBuilder(item.article, item.body);
      targets[i].appendChild(item.article);
      targets[i].scrollTop = targets[i].scrollHeight;
      if (!primaryBody) primaryBody = item.body;
    }
    return primaryBody;
  }

  function addMessage(role, text) {
    return addMessageWithExtra(role, text, null);
  }

  function addAssistantReplyWithActions(text) {
    var replyText = String(text || '');
    state.latestAssistantReply = replyText;
    return addMessageWithExtra('assistant', replyText, function(article) {
      article.appendChild(buildReplyAgentActions(replyText));
    });
  }

  function buildReplyMindmapPrompt(replyText) {
    var answer = String(replyText || state.latestAssistantReply || '').replace(/^\s+|\s+$/g, '');
    var outlineRule = '输出必须是 Markdown 层级大纲：## 一级主题、### 二级主题、#### 三级细节点。覆盖全文章节或回答中的完整逻辑链；长文尽量形成 18-30 个二级主题、40-80 个三级细节点；每个节点标题不超过 28 个汉字，说明不超过 80 个汉字；不要把整段回答塞进一张卡；末尾用“覆盖统计：...”说明覆盖章节、二级主题和三级细节点数量。';
    return '[create_card_tree] 根据上面的回答创建一个结构化的脑图树（使用markdown大纲格式）。' +
      '\n' + outlineRule + '\n\n上面的回答：\n' + answer;
  }

  function defaultReplyAgentActions() {
    return [
      {
        id: 'create_card_tree',
        label: '生成脑图树',
        action: 'generate_mindmap',
        scope: 'latest_reply'
      }
    ];
  }

  function agentNextActionsForReply() {
    var actions = state.agentOperation && state.agentOperation.nextActions ? state.agentOperation.nextActions : [];
    if (!actions.length) actions = defaultReplyAgentActions();
    return actions.slice(0, 3);
  }

  function operationActionIsWriteCapable(item) {
    item = item || {};
    var action = String(item.action || '');
    if (item.requiresConfirmation || item.requiresDraft) return true;
    return [
      'workflow_start',
      'operation_plan_preview',
      'mindmap_diff_preview',
      'write_draft',
      'request_native_highlight_selection',
      'mindmap_diff_apply'
    ].indexOf(action) >= 0;
  }

  function operationCompilerGateReason(operation) {
    operation = operation || {};
    var plan = operation.operationPlan || {};
    var dryRun = plan.dryRun || {};
    var compiler = operation.operationCompiler || {};
    var status = String(compiler.status || plan.status || '').toLowerCase();
    var planStatus = String(plan.status || '').toLowerCase();
    var dryStatus = String(dryRun.status || '').toLowerCase();
    var checks = compiler.checks || [];
    var detail = '';
    for (var i = 0; i < checks.length; i++) {
      if (!checks[i]) continue;
      if (checks[i].tone === 'block' || checks[i].status === 'blocked' || checks[i].status === 'unknown') {
        detail = checks[i].detail || checks[i].status || checks[i].label || '';
        break;
      }
    }
    if (!detail && dryRun.message) detail = dryRun.message;
    if (!detail && dryStatus) detail = 'dry-run: ' + dryStatus;
    if (status === 'blocked' || status === 'block' || planStatus === 'blocked' || dryStatus === 'blocked') {
      return 'Operation Compiler 阻断：' + (detail || '当前写入计划未通过能力、权限或 dry-run 检查。');
    }
    if (status === 'unknown' || planStatus === 'unknown' || dryStatus === 'unknown') {
      return 'Operation Compiler 待确认：' + (detail || '当前写入计划仍有 native capability 未确认。');
    }
    return '';
  }

  function operationActionGate(item, operation) {
    if (!operationActionIsWriteCapable(item)) {
      return {blocked: false, status: 'ready', reason: ''};
    }
    var reason = operationCompilerGateReason(operation || state.agentOperation || {});
    return {
      blocked: !!reason,
      status: reason ? 'blocked' : 'ready',
      reason: reason
    };
  }

  function formatKnowledgeSearchResult(result) {
    result = result || {};
    var matches = result.matches || [];
    if (!matches.length) return result.message || '知识索引没有命中相关内容。';
    var lines = [result.message || ('知识索引命中 ' + matches.length + ' 条。')];
    for (var i = 0; i < matches.length && i < 5; i++) {
      var item = matches[i] || {};
      lines.push('- ' + (item.title || item.kind || '索引项') + '：' + clip(item.snippet || '', 160));
    }
    return lines.join('\n');
  }

  function formatMindmapDiffResult(result) {
    result = result || {};
    var diff = result.mindmapDiff || {};
    var summary = diff.summary || {};
    return result.reply || (
      '脑图 Diff 预览\n' +
      '新增 ' + (summary.createCount || 0) +
      ' / 更新 ' + (summary.updateCount || 0) +
      ' / 合并 ' + (summary.mergeCount || 0) +
      ' / 重复 ' + (summary.duplicateCount || 0)
    );
  }

  function mindmapDiffSummaryLine(result) {
    result = result || {};
    var diff = result.mindmapDiff || {};
    var summary = diff.summary || {};
    return '新增 ' + (summary.createCount || 0) +
      ' / 更新 ' + (summary.updateCount || 0) +
      ' / 合并 ' + (summary.mergeCount || 0) +
      ' / 重复 ' + (summary.duplicateCount || 0);
  }

  function mindmapDiffMetaText(result) {
    result = result || {};
    var diff = result.mindmapDiff || {};
    var summary = diff.summary || {};
    var operations = diff.operations && diff.operations.length ? diff.operations : [];
    var lines = [
      '拟写入节点 ' + (summary.proposedCount || 0) + '，当前树节点 ' + (summary.currentCount || 0) + '。'
    ];
    if (result.mindmapTreeCache && result.mindmapTreeCache.nodeCount) {
      lines.push('已使用最新读取的当前脑图缓存：' + result.mindmapTreeCache.nodeCount + ' 个节点。');
    }
    for (var i = 0; i < operations.length && i < 6; i++) {
      var op = operations[i] || {};
      lines.push('- ' + (op.op || 'op') + '：' + clip(op.title || '未命名节点', 72));
    }
    if (operations.length > 6) lines.push('- 还有 ' + (operations.length - 6) + ' 个变更未展开。');
    return lines.join('\n');
  }

  function mindmapDiffPlanText(result) {
    result = result || {};
    var plan = result.mindmapDiffOperationPlan || {};
    var capabilities = plan.requiredCapabilities && plan.requiredCapabilities.length ? plan.requiredCapabilities : [];
    return '局部操作 ' + (plan.operationCount || 0) +
      ' / 跳过 ' + (plan.skippedCount || 0) +
      ' / 能力 ' + (capabilities.length ? capabilities.join(', ') : '无额外能力');
  }

  function mindmapDiffApplyBoundaryText(result) {
    result = result || {};
    var plan = result.mindmapDiffOperationPlan || {};
    var boundary = plan.applyBoundary || {};
    var blocked = boundary.blockedLocalMutations && boundary.blockedLocalMutations.length ? boundary.blockedLocalMutations : [];
    var executable = boundary.directlyExecutableMutations && boundary.directlyExecutableMutations.length ? boundary.directlyExecutableMutations : [];
    return '局部执行：' + (boundary.localApplyStatus || 'unknown') +
      ' / 当前写入：' + (boundary.currentApplyPath || 'draft_tree_write') +
      ' / 接受按钮：' + (boundary.acceptButtonBehavior || 'writes_pruned_proposed_tree') +
      ' / 可直接执行：' + (executable.length ? executable.join(', ') : '无') +
      ' / 未接原生执行器：' + (blocked.length ? blocked.join(', ') : '无');
  }

  function renderMindmapDiffRows(result) {
    result = result || {};
    var diff = result.mindmapDiff || {};
    var operations = diff.operations && diff.operations.length ? diff.operations : [];
    var list = document.createElement('div');
    list.className = 'mindmap-diff-row-list';
    for (var i = 0; i < operations.length; i++) {
      var op = operations[i] || {};
      var proposedPath = String(op.proposedPath || '');
      var row = document.createElement('div');
      row.className = 'mindmap-diff-row';
      row.setAttribute('data-proposed-path', proposedPath);
      row.setAttribute('data-selection-state', 'included');

      var checkbox = document.createElement('input');
      checkbox.className = 'mindmap-diff-checkbox';
      checkbox.type = 'checkbox';
      checkbox.checked = true;
      checkbox.value = proposedPath;
      checkbox.setAttribute('data-proposed-path', proposedPath);
      if (proposedPath === '0') checkbox.disabled = true;
      checkbox.addEventListener('change', function(ev) {
        var current = ev.currentTarget;
        var parent = current && current.closest ? current.closest('.mindmap-diff-row') : null;
        if (parent) parent.setAttribute('data-selection-state', current.checked ? 'included' : 'excluded_by_user');
        updateMindmapDiffSelectionSummary(current ? current.closest('.mindmap-diff-operation') : null);
      });
      row.appendChild(checkbox);

      var text = document.createElement('div');
      text.className = 'mindmap-diff-row-text';

      var title = document.createElement('div');
      title.className = 'mindmap-diff-row-title';
      title.textContent = (op.op || 'op') + ' · ' + (op.title || '未命名节点');
      text.appendChild(title);

      var titleInput = document.createElement('input');
      titleInput.className = 'mindmap-diff-title-input';
      titleInput.type = 'text';
      titleInput.value = op.title || '未命名节点';
      titleInput.setAttribute('data-proposed-path', proposedPath);
      titleInput.setAttribute('data-original-title', op.title || '未命名节点');
      text.appendChild(titleInput);

      var body = document.createElement('div');
      body.className = 'mindmap-diff-row-body';
      body.textContent = [
        op.reason || '',
        op.targetParent ? ('目标：' + op.targetParent) : '',
        op.shortBody ? clip(op.shortBody, 92) : ''
      ].filter(Boolean).join(' / ');
      text.appendChild(body);

      var originalBody = op.shortBody || op.bodyPreview || '';
      var bodyInput = document.createElement('textarea');
      bodyInput.className = 'mindmap-diff-body-input';
      bodyInput.value = originalBody;
      bodyInput.setAttribute('data-proposed-path', proposedPath);
      bodyInput.setAttribute('data-original-body', originalBody);
      text.appendChild(bodyInput);

      row.appendChild(text);
      list.appendChild(row);
    }
    if (!operations.length) {
      var empty = document.createElement('div');
      empty.className = 'mindmap-diff-row empty';
      empty.textContent = '没有可逐项预览的脑图变更。';
      list.appendChild(empty);
    }
    return list;
  }

  function updateMindmapDiffSelectionSummary(panel) {
    if (!panel) return;
    var summary = panel.querySelector ? panel.querySelector('.mindmap-diff-selection-summary') : null;
    if (!summary) return;
    var boxes = panel.querySelectorAll ? panel.querySelectorAll('.mindmap-diff-checkbox') : [];
    var total = boxes.length;
    var selected = 0;
    for (var i = 0; i < boxes.length; i++) {
      if (boxes[i].checked) selected += 1;
    }
    summary.textContent = '节点选择：保留 ' + selected + ' / 跳过 ' + (total - selected);
  }

  function setMindmapDiffBusy(panel, busy) {
    if (!panel) return;
    var controls = panel.querySelectorAll('button, input');
    for (var i = 0; i < controls.length; i++) {
      controls[i].disabled = !!busy || controls[i].getAttribute('data-proposed-path') === '0';
    }
  }

  function setMindmapDiffStatus(panel, text, stateName) {
    if (!panel) return;
    if (stateName) panel.setAttribute('data-state', stateName);
    var status = panel.querySelector('.mindmap-diff-status');
    if (status) status.textContent = text || '';
  }

  function mindmapDiffDraftId(panel) {
    if (panel) {
      var panelDraftId = panel.getAttribute('data-draft-id') || '';
      if (panelDraftId) return panelDraftId;
    }
    return state.draft && state.draft.id ? state.draft.id : '';
  }

  function selectedMindmapDiffExclusions(panel) {
    var exclusions = [];
    if (!panel) return exclusions;
    var inputs = panel.querySelectorAll('.mindmap-diff-checkbox');
    for (var i = 0; i < inputs.length; i++) {
      var path = inputs[i].getAttribute('data-proposed-path') || inputs[i].value || '';
      if (!path || inputs[i].checked || inputs[i].disabled) continue;
      exclusions.push(path);
    }
    return exclusions;
  }

  function mindmapDiffNodeEdits(panel) {
    var edits = [];
    if (!panel) return edits;
    var rows = panel.querySelectorAll('.mindmap-diff-row');
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      var checkbox = row.querySelector ? row.querySelector('.mindmap-diff-checkbox') : null;
      if (checkbox && (!checkbox.checked || checkbox.disabled)) continue;
      var titleInput = row.querySelector ? row.querySelector('.mindmap-diff-title-input') : null;
      var bodyInput = row.querySelector ? row.querySelector('.mindmap-diff-body-input') : null;
      var proposedPath = row.getAttribute('data-proposed-path') || '';
      if (!proposedPath) continue;
      var title = titleInput ? String(titleInput.value || '').replace(/^\s+|\s+$/g, '') : '';
      var body = bodyInput ? String(bodyInput.value || '').replace(/^\s+|\s+$/g, '') : '';
      var originalTitle = titleInput ? String(titleInput.getAttribute('data-original-title') || '').replace(/^\s+|\s+$/g, '') : '';
      var originalBody = bodyInput ? String(bodyInput.getAttribute('data-original-body') || '').replace(/^\s+|\s+$/g, '') : '';
      var edit = {proposedPath: proposedPath};
      if (title && title !== originalTitle) edit.title = title;
      if (body !== originalBody) edit.body = body;
      if (edit.title !== undefined || edit.body !== undefined) edits.push(edit);
    }
    return edits;
  }

  function applyMindmapDiffDraftEdits(draftId, panel, done) {
    var exclusions = selectedMindmapDiffExclusions(panel);
    var nodeEdits = mindmapDiffNodeEdits(panel);
    if (!exclusions.length && !nodeEdits.length) {
      done();
      return;
    }
    if (!draftId) {
      done();
      return;
    }
    setMindmapDiffBusy(panel, true);
    setMindmapDiffStatus(panel, '正在保存逐节点编辑...', 'pending');
    postCompanion('draft_update', {
      id: draftId,
      excludedMindmapPaths: exclusions,
      mindmapNodeEdits: nodeEdits
    }, function(result) {
      if (!result || !result.ok) {
        setMindmapDiffBusy(panel, false);
        setMindmapDiffStatus(panel, result && result.message ? result.message : '保存逐节点编辑失败。', 'error');
        addFailureMessage('保存脑图 Diff 编辑失败', result);
        return;
      }
      if (result.draft) state.draft = result.draft;
      setMindmapDiffStatus(panel, '已保存 ' + exclusions.length + ' 个排除项、' + nodeEdits.length + ' 个节点编辑，准备写入。', 'pending');
      done();
    }, {showReply: false});
  }

  function applyMindmapDiffExclusions(draftId, panel, done) {
    applyMindmapDiffDraftEdits(draftId, panel, done);
  }

  function mindmapDiffPlanAfterExclusions(panel) {
    var plan = panel && panel._mindmapDiffOperationPlan ? panel._mindmapDiffOperationPlan : null;
    if (!plan) return null;
    var exclusions = selectedMindmapDiffExclusions(panel);
    var excluded = {};
    for (var i = 0; i < exclusions.length; i++) excluded[exclusions[i]] = true;
    var operations = plan.operations && plan.operations.length ? plan.operations : [];
    var kept = [];
    for (var j = 0; j < operations.length; j++) {
      var proposedPath = String(operations[j].proposedPath || '');
      if (proposedPath && excluded[proposedPath]) continue;
      kept.push(operations[j]);
    }
    var cloned = {};
    for (var key in plan) {
      if (Object.prototype.hasOwnProperty.call(plan, key)) cloned[key] = plan[key];
    }
    cloned.operations = kept;
    cloned.operationCount = kept.length;
    cloned.skippedCount = (plan.skippedCount || 0) + exclusions.length;
    return cloned;
  }

  function mindmapDiffPlanAfterUserEdits(panel) {
    var plan = mindmapDiffPlanAfterExclusions(panel);
    if (!plan) return null;
    var nodeEdits = mindmapDiffNodeEdits(panel);
    if (!nodeEdits.length) return plan;
    var editsByPath = {};
    for (var i = 0; i < nodeEdits.length; i++) editsByPath[nodeEdits[i].proposedPath] = nodeEdits[i];
    var operations = [];
    var sourceOperations = plan.operations && plan.operations.length ? plan.operations : [];
    for (var j = 0; j < sourceOperations.length; j++) {
      var operation = {};
      for (var key in sourceOperations[j]) {
        if (Object.prototype.hasOwnProperty.call(sourceOperations[j], key)) operation[key] = sourceOperations[j][key];
      }
      var edit = editsByPath[String(operation.proposedPath || '')];
      if (edit) {
        if (edit.title !== undefined) operation.title = edit.title;
        if (edit.body !== undefined) operation.bodyPreview = edit.body;
        operation.userEdited = true;
      }
      operations.push(operation);
    }
    plan.operations = operations;
    return plan;
  }

  function isMindmapDiffDeleteSuggestionOperation(operation) {
    operation = operation || {};
    var mutation = String(operation.mutation || '');
    var op = String(operation.op || '');
    return mutation === 'delete_suggest' || mutation === 'delete' || op === 'suggest_delete_mindmap_node';
  }

  function mindmapDiffApplyOperations(panel) {
    var plan = mindmapDiffPlanAfterUserEdits(panel);
    var operations = plan && plan.operations && plan.operations.length ? plan.operations : [];
    var out = [];
    for (var i = 0; i < operations.length; i++) {
      var operation = operations[i] || {};
      if (!isMindmapDiffDeleteSuggestionOperation(operation)) out.push(operation);
    }
    return out;
  }

  function mindmapDiffApplyPlan(panel) {
    var plan = mindmapDiffPlanAfterUserEdits(panel);
    if (!plan) return null;
    var applyOperations = mindmapDiffApplyOperations(panel);
    var deleteOperations = mindmapDiffDeleteSuggestionOperations(panel);
    var nextPlan = {};
    for (var key in plan) {
      if (Object.prototype.hasOwnProperty.call(plan, key)) nextPlan[key] = plan[key];
    }
    nextPlan.operations = applyOperations;
    nextPlan.operationCount = applyOperations.length;
    nextPlan.skippedDeleteSuggestionCount = deleteOperations.length;
    nextPlan.applyBoundary = {};
    var boundary = plan.applyBoundary && typeof plan.applyBoundary === 'object' ? plan.applyBoundary : {};
    for (var boundaryKey in boundary) {
      if (Object.prototype.hasOwnProperty.call(boundary, boundaryKey)) nextPlan.applyBoundary[boundaryKey] = boundary[boundaryKey];
    }
    nextPlan.applyBoundary.skippedDeleteSuggestionCount = deleteOperations.length;
    return nextPlan;
  }

  function canApplyMindmapDiffLocally(panel) {
    var operations = mindmapDiffApplyOperations(panel);
    if (!operations.length) return false;
    for (var i = 0; i < operations.length; i++) {
      var operation = operations[i] || {};
      if (!mindmapDiffOperationCanApplyLocally(operation)) return false;
    }
    return true;
  }

  function mindmapDiffDeleteSuggestionOperations(panel) {
    var plan = mindmapDiffPlanAfterUserEdits(panel);
    var operations = plan && plan.operations && plan.operations.length ? plan.operations : [];
    var out = [];
    for (var i = 0; i < operations.length; i++) {
      var operation = operations[i] || {};
      if (isMindmapDiffDeleteSuggestionOperation(operation)) out.push(operation);
    }
    return out;
  }

  function requestMindmapDeleteConfirmation(panel) {
    var deleteOperations = mindmapDiffDeleteSuggestionOperations(panel);
    if (!deleteOperations.length) return;
    var plan = mindmapDiffPlanAfterUserEdits(panel);
    if (!plan) return;
    var confirmationPlan = {};
    for (var key in plan) {
      if (Object.prototype.hasOwnProperty.call(plan, key)) confirmationPlan[key] = plan[key];
    }
    confirmationPlan.operations = deleteOperations;
    confirmationPlan.operationCount = deleteOperations.length;
    postCompanion('request_mindmap_delete_confirmation', {
      mindmapDiffOperationPlan: confirmationPlan,
      draftId: mindmapDiffDraftId(panel)
    }, function(result) {
      if (!result || !result.ok) {
        addFailureMessage('创建删除建议确认事务失败', result || {});
        return;
      }
      if (result.aiEditTransactionStatus) renderAiEditTransactionCenter(result.aiEditTransactionStatus);
      setMindmapDiffStatus(panel, '删除建议已进入事务中心，需二次确认。', 'pending');
    }, {showReply: false});
  }

  function mindmapDiffOperationCanApplyLocally(operation) {
    var mutation = String(operation.mutation || '');
    var op = String(operation.op || '');
    if (mutation === 'delete_suggest' || mutation === 'delete' || op === 'suggest_delete_mindmap_node') return false;
    if (mutation === 'create' || op === 'create_mindmap_node') return true;
    if (!(mutation === 'update' || mutation === 'merge' || mutation === 'move' ||
        op === 'update_mindmap_node' || op === 'merge_mindmap_node' || op === 'move_mindmap_node')) {
      return false;
    }
    return mindmapDiffOperationRequirementsReady(operation);
  }

  function mindmapDiffOperationRequirementsReady(operation) {
    var requirements = operation && operation.requires && operation.requires.length ? operation.requires : [];
    if (!requirements.length) return false;
    for (var i = 0; i < requirements.length; i++) {
      var requirement = String(requirements[i] || '');
      if (!requirement || requirement === 'nativeMindmap') continue;
      if (!nativeCapabilityReady(requirement)) return false;
    }
    return true;
  }

  function mindmapDiffOperationMutation(operation) {
    operation = operation || {};
    var mutation = String(operation.mutation || '');
    var op = String(operation.op || '');
    if (mutation) return mutation;
    if (op.indexOf('create') >= 0) return 'create';
    if (op.indexOf('update') >= 0) return 'update';
    if (op.indexOf('merge') >= 0) return 'merge';
    if (op.indexOf('move') >= 0) return 'move';
    if (op.indexOf('delete') >= 0) return 'delete_suggest';
    return op || 'unknown';
  }

  function mindmapDiffMutationLabel(mutation) {
    mutation = String(mutation || '');
    if (mutation === 'create') return '新增';
    if (mutation === 'update') return '更新';
    if (mutation === 'merge') return '合并';
    if (mutation === 'move') return '移动';
    if (mutation === 'delete_suggest' || mutation === 'delete') return '建议删除';
    return mutation || '未知';
  }

  function mindmapDiffWorkbenchOperations(result) {
    result = result || {};
    var plan = result.mindmapDiffOperationPlan || {};
    if (plan.operations && plan.operations.length) return plan.operations;
    var diff = result.mindmapDiff || {};
    return diff.operations && diff.operations.length ? diff.operations : [];
  }

  function mindmapDiffWorkbenchCounts(result, operations) {
    result = result || {};
    operations = operations || [];
    var summary = (result.mindmapDiff && result.mindmapDiff.summary) || {};
    var operationCounts = {
      create: 0,
      update: 0,
      merge: 0,
      move: 0,
      suggestDelete: 0
    };
    for (var i = 0; i < operations.length; i++) {
      var mutation = mindmapDiffOperationMutation(operations[i]);
      if (mutation === 'create') operationCounts.create += 1;
      else if (mutation === 'update') operationCounts.update += 1;
      else if (mutation === 'merge') operationCounts.merge += 1;
      else if (mutation === 'move') operationCounts.move += 1;
      else if (mutation === 'delete_suggest' || mutation === 'delete') operationCounts.suggestDelete += 1;
    }
    return {
      create: summary.createCount !== undefined ? summary.createCount : operationCounts.create,
      update: summary.updateCount !== undefined ? summary.updateCount : operationCounts.update,
      merge: summary.mergeCount !== undefined ? summary.mergeCount : operationCounts.merge,
      move: summary.moveCount !== undefined ? summary.moveCount : operationCounts.move,
      suggestDelete: summary.suggestDeleteCount !== undefined ? summary.suggestDeleteCount : (
        summary.deleteSuggestCount !== undefined ? summary.deleteSuggestCount : operationCounts.suggestDelete
      )
    };
  }

  function renderMindmapDiffWorkbench(result) {
    if (arguments.length && result && result.mindmapDiff) {
      state.latestMindmapDiff = {
        mindmapDiff: result.mindmapDiff,
        mindmapDiffOperationPlan: result.mindmapDiffOperationPlan || null,
        draftId: result.draftId || (state.draft && state.draft.id ? state.draft.id : ''),
        mindmapTreeCache: result.mindmapTreeCache || null
      };
    }
    result = state.latestMindmapDiff || null;
    var panel = byId('mindmapDiffWorkbench');
    var preview = byId('mindmapDiffWorkbenchPreview');
    if (!panel || !preview) return;
    if (!result || !result.mindmapDiff) {
      panel.className = 'mindmap-diff-workbench idle';
      setText('mindmapDiffWorkbenchTitle', '脑图 Diff 编辑台');
      setText('mindmapDiffWorkbenchSummary', '等待 AI 生成脑图 Diff 预览。');
      var empty = document.createElement('div');
      empty.className = 'mindmap-diff-workbench-row empty';
      empty.textContent = '生成脑图树后，这里会保留最近一次新增、更新、合并、移动和建议删除的变更预览。';
      replaceElementChildren(preview, [empty]);
      renderMindmapStudioPanel();
      return;
    }
    var operations = mindmapDiffWorkbenchOperations(result);
    var counts = mindmapDiffWorkbenchCounts(result, operations);
    var boundary = (result.mindmapDiffOperationPlan && result.mindmapDiffOperationPlan.applyBoundary) || {};
    var localReadyCount = 0;
    for (var i = 0; i < operations.length; i++) {
      var operation = operations[i] || {};
      if (mindmapDiffOperationCanApplyLocally(operation)) localReadyCount += 1;
    }
    var blockedCount = Math.max(0, operations.length - localReadyCount);
    var localStatus = boundary.localApplyStatus || (operations.length && !blockedCount ? 'all_local' : 'draft_tree_write');
    panel.className = 'mindmap-diff-workbench ' + (blockedCount ? 'pending' : 'ready');
    setText('mindmapDiffWorkbenchTitle', '脑图 Diff 编辑台 / 最近一次预览');
    setText(
      'mindmapDiffWorkbenchSummary',
      '新增 ' + counts.create +
      ' / 更新 ' + counts.update +
      ' / 合并 ' + counts.merge +
      ' / 移动 ' + counts.move +
      ' / 建议删除 ' + counts.suggestDelete +
      ' / 局部执行 ' + localReadyCount + '/' + operations.length +
      ' / 状态 ' + localStatus
    );
    var rows = [];
    for (var j = 0; j < operations.length && j < 8; j++) {
      var item = operations[j] || {};
      var mutation = mindmapDiffOperationMutation(item);
      var row = document.createElement('div');
      row.className = 'mindmap-diff-workbench-row';
      row.setAttribute('data-mutation', mutation);
      var title = document.createElement('div');
      title.className = 'mindmap-diff-workbench-row-title';
      title.textContent = mindmapDiffMutationLabel(mutation) + ' · ' + clip(item.title || item.targetTitle || '未命名节点', 64);
      row.appendChild(title);
      var body = document.createElement('div');
      body.className = 'mindmap-diff-workbench-row-body';
      body.textContent = [
        item.targetParent ? ('目标：' + clip(item.targetParent, 46)) : '',
        item.reason ? clip(item.reason, 72) : '',
        mindmapDiffOperationCanApplyLocally(item) ? '可局部执行' : '需草稿写入或人工确认'
      ].filter(Boolean).join(' / ');
      row.appendChild(body);
      rows.push(row);
    }
    if (!rows.length) {
      var noRows = document.createElement('div');
      noRows.className = 'mindmap-diff-workbench-row empty';
      noRows.textContent = '本次 Diff 没有可显示的节点级操作。';
      rows.push(noRows);
    } else if (operations.length > rows.length) {
      var more = document.createElement('div');
      more.className = 'mindmap-diff-workbench-row empty';
      more.textContent = '还有 ' + (operations.length - rows.length) + ' 个变更未展开。';
      rows.push(more);
    }
    replaceElementChildren(preview, rows);
    renderMindmapStudioPanel();
  }

  function applyMindmapDiffLocalOperations(panel) {
    var plan = mindmapDiffApplyPlan(panel);
    if (!plan || !plan.operations || !plan.operations.length) {
      setMindmapDiffStatus(panel, '没有可局部应用的脑图操作。', 'error');
      requestMindmapDeleteConfirmation(panel);
      return;
    }
    setMindmapDiffBusy(panel, true);
    setMindmapDiffStatus(panel, '正在排队局部脑图操作...', 'pending');
    postCompanion('request_mindmap_diff_apply', {
      mindmapDiffOperationPlan: plan,
      draftId: mindmapDiffDraftId(panel)
    }, function(result) {
      if (!result || !result.ok) {
        setMindmapDiffBusy(panel, false);
        setMindmapDiffStatus(panel, result && result.message ? result.message : '局部脑图操作排队失败。', 'error');
        addFailureMessage('局部应用脑图 Diff 失败', result);
        return;
      }
      setMindmapDiffStatus(panel, '已排队局部脑图操作，等待 MN4 插件执行。', 'accepted');
      renderQueue(result.queue || state.queue || {});
      requestMindmapDeleteConfirmation(panel);
    }, {showReply: false});
  }

  function acceptMindmapDiff(panel) {
    var draftId = mindmapDiffDraftId(panel);
    var applyOperations = mindmapDiffApplyOperations(panel);
    var deleteOperations = mindmapDiffDeleteSuggestionOperations(panel);
    if (canApplyMindmapDiffLocally(panel)) {
      applyMindmapDiffDraftEdits(draftId, panel, function() {
        applyMindmapDiffLocalOperations(panel);
      });
      return;
    }
    if (!applyOperations.length && deleteOperations.length) {
      requestMindmapDeleteConfirmation(panel);
      return;
    }
    if (!draftId) {
      setMindmapDiffStatus(panel, '没有可写入的脑图草稿。', 'error');
      addMessage('assistant', '没有可写入的脑图草稿。');
      return;
    }
    applyMindmapDiffDraftEdits(draftId, panel, function() {
      writeAcceptedDraft(draftId, panel);
      requestMindmapDeleteConfirmation(panel);
    });
  }

  function rejectMindmapDiff(panel) {
    var draftId = mindmapDiffDraftId(panel);
    if (!draftId) {
      setMindmapDiffStatus(panel, '没有可丢弃的脑图草稿。', 'error');
      addMessage('assistant', '没有可丢弃的脑图草稿。');
      return;
    }
    setMindmapDiffBusy(panel, true);
    setMindmapDiffStatus(panel, '正在丢弃脑图草稿...', 'rejected');
    postCompanion('draft_delete', {id: draftId}, function(result) {
      if (!result || result.ok === false) {
        setMindmapDiffBusy(panel, false);
        setMindmapDiffStatus(panel, result && result.message ? result.message : '丢弃草稿失败。', 'error');
        addFailureMessage('丢弃脑图草稿失败', result);
        return;
      }
      if (state.draft && state.draft.id === draftId) renderDraft(null);
      setMindmapDiffStatus(panel, '已拒绝并丢弃脑图草稿。', 'rejected');
    }, {showReply: false});
  }

  function buildMindmapDiffOperationPanel(result) {
    result = result || {};
    var panel = document.createElement('section');
    panel.className = 'mindmap-diff-operation';
    panel.setAttribute('data-state', 'pending');
    panel.setAttribute('data-draft-id', result.draftId || (state.draft && state.draft.id ? state.draft.id : ''));
    panel._mindmapDiffOperationPlan = result.mindmapDiffOperationPlan || null;

    var title = document.createElement('div');
    title.className = 'mindmap-diff-title';
    title.textContent = '脑图 Diff 预览';
    panel.appendChild(title);

    var summary = document.createElement('div');
    summary.className = 'mindmap-diff-summary';
    summary.textContent = mindmapDiffSummaryLine(result);
    panel.appendChild(summary);

    var meta = document.createElement('div');
    meta.className = 'mindmap-diff-meta';
    meta.textContent = mindmapDiffMetaText(result);
    panel.appendChild(meta);

    var plan = document.createElement('div');
    plan.className = 'mindmap-diff-plan';
    plan.textContent = mindmapDiffPlanText(result);
    panel.appendChild(plan);

    var boundary = document.createElement('div');
    boundary.className = 'mindmap-diff-boundary';
    boundary.textContent = mindmapDiffApplyBoundaryText(result);
    panel.appendChild(boundary);

    var selectionSummary = document.createElement('div');
    selectionSummary.className = 'mindmap-diff-selection-summary';
    selectionSummary.textContent = '节点选择：保留 0 / 跳过 0';
    panel.appendChild(selectionSummary);

    panel.appendChild(renderMindmapDiffRows(result));
    window.setTimeout(function() {
      updateMindmapDiffSelectionSummary(panel);
    }, 0);

    var actions = document.createElement('div');
    actions.className = 'mindmap-diff-actions';

    var accept = document.createElement('button');
    accept.className = 'mindmap-diff-accept';
    accept.type = 'button';
    accept.textContent = '接受';
    accept.addEventListener('click', function(ev) {
      releaseButtonFocus(ev.currentTarget);
      acceptMindmapDiff(panel);
    });
    actions.appendChild(accept);

    var reject = document.createElement('button');
    reject.className = 'mindmap-diff-reject';
    reject.type = 'button';
    reject.textContent = '拒绝';
    reject.addEventListener('click', function(ev) {
      releaseButtonFocus(ev.currentTarget);
      rejectMindmapDiff(panel);
    });
    actions.appendChild(reject);
    panel.appendChild(actions);

    var status = document.createElement('div');
    status.className = 'mindmap-diff-status';
    status.textContent = '等待确认';
    panel.appendChild(status);
    return panel;
  }

  function renderMindmapDiffOperation(result) {
    renderMindmapDiffWorkbench(result);
    addMessageWithExtra('assistant', '', function(article, body) {
      if (body) body.className = 'message-body empty';
      article.appendChild(buildMindmapDiffOperationPanel(result));
    });
  }

  function operationPlanSummaryLine(result) {
    result = result || {};
    var dryRun = result.dryRun || {};
    return 'Dry-run：' + (dryRun.status || 'unknown') +
      ' / 操作数 ' + (dryRun.operationCount || 0) +
      ' / 阻断 ' + (dryRun.blockedCount || 0) +
      ' / 未确认 ' + (dryRun.unknownCount || 0);
  }

  function operationPlanMetaText(result) {
    result = result || {};
    var dryRun = result.dryRun || {};
    var operationPlan = result.operationPlan || {};
    var target = operationPlan.target || {};
    var checks = dryRun.checks && dryRun.checks.length ? dryRun.checks : [];
    var lines = [
      dryRun.message || result.message || '已生成写入计划预览。',
      '目标：' + (target.label || target.rootTitle || target.mode || '当前 MN 上下文')
    ];
    for (var i = 0; i < checks.length && i < 6; i++) {
      var check = checks[i] || {};
      var detail = check.status || 'unknown';
      if (check.reason) detail += ' / ' + check.reason;
      lines.push('- ' + (check.op || check.opId || 'operation') + '：' + detail);
    }
    if (checks.length > 6) lines.push('- 还有 ' + (checks.length - 6) + ' 个检查未展开。');
    return lines.join('\n');
  }

  function setOperationPlanBusy(panel, busy) {
    if (!panel) return;
    var buttons = panel.querySelectorAll('button');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].disabled = !!busy;
    }
  }

  function setOperationPlanStatus(panel, text, stateName) {
    if (!panel) return;
    if (stateName) panel.setAttribute('data-state', stateName);
    var status = panel.querySelector('.operation-plan-status');
    if (status) status.textContent = text || '';
  }

  function operationPlanDraftId(panel) {
    if (panel) {
      var panelDraftId = panel.getAttribute('data-draft-id') || '';
      if (panelDraftId) return panelDraftId;
    }
    return state.draft && state.draft.id ? state.draft.id : '';
  }

  function acceptOperationPlan(panel) {
    var draftId = operationPlanDraftId(panel);
    if (!draftId) {
      setOperationPlanStatus(panel, '没有可写入的草稿。', 'error');
      addMessage('assistant', '没有可写入的草稿。');
      return;
    }
    writeAcceptedDraft(draftId, panel);
  }

  function rejectOperationPlan(panel) {
    var draftId = operationPlanDraftId(panel);
    if (!draftId) {
      setOperationPlanStatus(panel, '没有可丢弃的草稿。', 'error');
      addMessage('assistant', '没有可丢弃的草稿。');
      return;
    }
    setOperationPlanBusy(panel, true);
    setOperationPlanStatus(panel, '正在丢弃写入草稿...', 'rejected');
    postCompanion('draft_delete', {id: draftId}, function(result) {
      if (!result || result.ok === false) {
        setOperationPlanBusy(panel, false);
        setOperationPlanStatus(panel, result && result.message ? result.message : '丢弃草稿失败。', 'error');
        addFailureMessage('丢弃写入草稿失败', result);
        return;
      }
      if (state.draft && state.draft.id === draftId) renderDraft(null);
      setOperationPlanStatus(panel, '已拒绝并丢弃写入草稿。', 'rejected');
    }, {showReply: false});
  }

  function buildOperationPlanPanel(result) {
    result = result || {};
    var dryRun = result.dryRun || {};
    var blocked = parseInt(dryRun.blockedCount || 0, 10) || 0;
    var panel = document.createElement('section');
    panel.className = 'operation-plan-panel';
    panel.setAttribute('data-state', blocked ? 'blocked' : 'pending');
    panel.setAttribute('data-draft-id', result.draftId || (state.draft && state.draft.id ? state.draft.id : ''));

    var title = document.createElement('div');
    title.className = 'operation-plan-title';
    title.textContent = '写入计划预览';
    panel.appendChild(title);

    var summary = document.createElement('div');
    summary.className = 'operation-plan-summary';
    summary.textContent = operationPlanSummaryLine(result);
    panel.appendChild(summary);

    var meta = document.createElement('div');
    meta.className = 'operation-plan-meta';
    meta.textContent = operationPlanMetaText(result);
    panel.appendChild(meta);

    var actions = document.createElement('div');
    actions.className = 'operation-plan-actions';

    var accept = document.createElement('button');
    accept.className = 'operation-plan-accept';
    accept.type = 'button';
    accept.textContent = blocked ? '已阻断' : '接受';
    accept.disabled = !!blocked;
    accept.addEventListener('click', function(ev) {
      releaseButtonFocus(ev.currentTarget);
      acceptOperationPlan(panel);
    });
    actions.appendChild(accept);

    var reject = document.createElement('button');
    reject.className = 'operation-plan-reject';
    reject.type = 'button';
    reject.textContent = '拒绝';
    reject.addEventListener('click', function(ev) {
      releaseButtonFocus(ev.currentTarget);
      rejectOperationPlan(panel);
    });
    actions.appendChild(reject);
    panel.appendChild(actions);

    var status = document.createElement('div');
    status.className = 'operation-plan-status';
    status.textContent = blocked ? 'dry-run 已阻断，不能写入。' : '等待确认';
    panel.appendChild(status);
    return panel;
  }

  function renderOperationPlanPreview(result) {
    addMessageWithExtra('assistant', '', function(article, body) {
      if (body) body.className = 'message-body empty';
      article.appendChild(buildOperationPlanPanel(result));
    });
  }

  function runAgentNextAction(item, replyText) {
    item = item || {};
    var actionId = String(item.id || '');
    var action = String(item.action || '');
    var label = item.label || actionLabel(action);
    if (actionId === 'create_card_tree' || action === 'generate_mindmap') {
      executeAction('generate_mindmap', buildReplyMindmapPrompt(replyText), label || '生成脑图树');
      return;
    }
    if (action === 'operation_plan_preview') {
      var draftId = state.draft && state.draft.id ? state.draft.id : '';
      if (!draftId) {
        addMessage('assistant', '需要先生成并保存一个待写入草稿，才能预览写入计划。');
        return;
      }
      postCompanion('operation_plan_preview', {draftId: draftId}, function(result) {
        if (!result || !result.ok) {
          addFailureMessage('预览写入计划失败', result);
          return;
        }
        renderOperationPlanPreview(result);
      }, {showReply: false});
      return;
    }
    if (action === 'mindmap_diff_preview') {
      var mindmapDraftId = state.draft && state.draft.id ? state.draft.id : '';
      if (!mindmapDraftId) {
        addMessage('assistant', '需要先生成并保存一个待写入脑图草稿，才能预览脑图 Diff。');
        return;
      }
      postCompanion('mindmap_diff_preview', {
        draftId: mindmapDraftId,
        mindmapTarget: state.mindmapTarget && state.mindmapTarget.target ? state.mindmapTarget.target : {}
      }, function(result) {
        if (!result || !result.ok) {
          addFailureMessage('预览脑图 Diff 失败', result);
          return;
        }
        renderMindmapDiffOperation(result);
      }, {showReply: false});
      return;
    }
    if (action === 'knowledge_index_search') {
      postCompanion('knowledge_index_search', {query: replyText || state.latestAssistantReply || promptValue()}, function(result) {
        if (!result || !result.ok) {
          addFailureMessage('检索相关知识失败', result);
          return;
        }
        addMessage('assistant', formatKnowledgeSearchResult(result));
      }, {showReply: false});
      return;
    }
    if (action === 'workflow_start') {
      postCompanion('workflow_start', {
        workflowId: item.workflowId || (state.agentOperation && state.agentOperation.intent ? state.agentOperation.intent.workflowId : ''),
        prompt: replyText || state.latestAssistantReply || promptValue()
      }, function(result) {
        renderControls(result || {});
        if (!result || !result.ok) addFailureMessage('启动工作流失败', result);
      });
      return;
    }
    if (action) {
      executeAction(action, replyText || state.latestAssistantReply || promptValue(), label);
    }
  }

  function buildReplyAgentActions(replyText) {
    var wrapper = document.createElement('div');
    wrapper.className = 'reply-mindmap-actions';
    var actions = agentNextActionsForReply();
    for (var i = 0; i < actions.length; i++) {
      (function(item) {
        item = item || {};
        var button = document.createElement('button');
        var actionId = String(item.id || '');
        var gate = operationActionGate(item, state.agentOperation || {});
        button.className = 'small-button ' + (actionId === 'create_card_tree' ? 'reply-mindmap-tree-button' : 'reply-agent-action-button') + (gate.blocked ? ' blocked' : '');
        button.type = 'button';
        button.textContent = item.label || actionLabel(item.action || '');
        button.setAttribute('data-agent-next-action', actionId || item.action || 'action');
        button.setAttribute('data-operation-gate-status', gate.status);
        if (gate.blocked) {
          button.disabled = true;
          button.title = gate.reason;
        }
        button.addEventListener('click', function(ev) {
          releaseButtonFocus(ev.currentTarget);
          if (gate.blocked) {
            addMessage('assistant', gate.reason);
            return;
          }
          runAgentNextAction(item, replyText);
        });
        wrapper.appendChild(button);
      })(actions[i]);
    }
    return wrapper;
  }

  function runGuideItem(item) {
    item = item || {};
    if (item.kind === 'queue_status') {
      refreshQueue();
      return;
    }
    if (item.kind === 'enqueue') {
      enqueueAction(item.action, item.prompt || '');
      return;
    }
    if (item.kind === 'stop_then_run') {
      stopCurrent();
      window.setTimeout(function() {
        executeAction(item.action, item.prompt || '', item.userText || item.title || actionLabel(item.action));
      }, 350);
      return;
    }
    if (item.kind === 'stop') {
      stopCurrent();
      return;
    }
    executeAction(item.action, item.prompt || '', item.userText || item.title || actionLabel(item.action));
  }

  function addGuideMessage(title, items) {
    items = items || [];
    if (!items.length) return;
    var targets = [byId('liveHistory'), byId('history')];
    for (var i = 0; i < targets.length; i++) {
      if (!targets[i]) continue;
      var built = buildMessage('assistant', title || '后续引导');
      var actions = document.createElement('div');
      actions.className = 'guide-actions';
      for (var j = 0; j < items.length; j++) {
        (function(item) {
          var button = document.createElement('button');
          button.className = 'small-button guide-button';
          button.type = 'button';
          button.textContent = item.title || actionLabel(item.action);
          button.setAttribute('data-guide-action', item.kind || item.action || 'action');
          button.addEventListener('click', function(ev) {
            releaseButtonFocus(ev.currentTarget);
            runGuideItem(item);
          });
          actions.appendChild(button);
        })(items[j]);
      }
      built.article.appendChild(actions);
      targets[i].appendChild(built.article);
      targets[i].scrollTop = targets[i].scrollHeight;
    }
  }

  function showFollowUpGuides(action, prompt) {
    if (!isAllowedPromptAction(action)) return;
    var basePrompt = prompt || promptValue() || state.lastPromptFromSelection || '';
    var items = [];
    if (action !== 'generate_card') {
      items.push({title: '直接执行：生成卡片', action: 'generate_card', prompt: basePrompt, userText: '生成卡片'});
    }
    if (action !== 'generate_mindmap') {
      items.push({title: '直接执行：新建脑图', action: 'generate_mindmap', prompt: basePrompt, userText: '新建脑图'});
    }
    if (action !== 'expand_node') {
      items.push({title: '直接执行：补脑图', action: 'expand_node', prompt: basePrompt, userText: '补脑图'});
    }
    if (action !== 'reorganize_mindmap') {
      items.push({title: '直接执行：重组脑图', action: 'reorganize_mindmap', prompt: basePrompt, userText: '重组脑图'});
    }
    items.push({title: '查看队列状态', kind: 'queue_status'});
    addGuideMessage('后续引导', items.slice(0, 4));
  }

  function clearMessages() {
    var liveHistory = byId('liveHistory');
    var history = byId('history');
    if (liveHistory) liveHistory.innerHTML = '';
    if (history) history.innerHTML = '';
  }

  function renderHistoryItems(items) {
    clearMessages();
    items = items || [];
    if (!items.length) {
      addMessage('assistant', '暂无历史对话。');
      return;
    }
    for (var i = 0; i < items.length; i++) {
      var item = items[i] || {};
      addMessage(item.role === 'user' ? 'user' : 'assistant', item.content || '');
    }
  }

  function renderNewConversationMessage() {
    clearMessages();
    addMessage('assistant', '已开启新对话。当前对话仍会绑定这篇文档；历史可从右上角“历史”恢复。');
  }

  function setCurrentConversation(conversation) {
    conversation = conversation || {};
    state.conversationId = String(conversation.conversationId || '');
    state.sessionId = String(conversation.sessionId || '');
  }

  function currentMnObjectRef() {
    var operation = state.agentOperation || {};
    var mnObject = operation.mnObject || {};
    var object = operation.object || {};
    var workspaceFocus = state.notebookWorkspace && state.notebookWorkspace.focusObject ? state.notebookWorkspace.focusObject : {};
    var sourceRef = mnObject.sourceRef || object.sourceRef || {};
    return {
      objectId: String(mnObject.objectId || object.mnObjectId || workspaceFocus.objectId || ''),
      kind: String(mnObject.kind || object.kind || workspaceFocus.kind || ''),
      title: String(mnObject.title || object.title || workspaceFocus.title || ''),
      sourceRef: sourceRef || workspaceFocus.sourceRef || {}
    };
  }

  function renderConversationHistoryScope() {
    var objectRef = currentMnObjectRef();
    var objectReady = !!objectRef.objectId;
    var objectButton = byId('conversationHistoryObjectButton');
    var allButton = byId('conversationHistoryAllButton');
    if (allButton) allButton.className = 'scope-button' + (state.conversationHistoryScope !== 'object' ? ' active' : '');
    if (objectButton) {
      objectButton.className = 'scope-button' + (state.conversationHistoryScope === 'object' ? ' active' : '');
      objectButton.disabled = !objectReady;
      objectButton.title = objectReady ? '只看当前对象相关历史' : '等待当前 MNObject';
    }
    if (state.conversationHistoryScope === 'object' && !objectReady) {
      state.conversationHistoryScope = 'document';
      if (allButton) allButton.className = 'scope-button active';
      if (objectButton) objectButton.className = 'scope-button';
    }
    var label = '历史范围：当前文档';
    if (state.conversationHistoryScope === 'object' && objectReady) {
      label = '历史范围：当前对象 / ' + (objectRef.kind || 'object') + ' / ' + clip(objectRef.title || objectRef.objectId, 64);
    }
    setText('conversationHistoryScopeLine', label);
  }

  function conversationHistoryPayload() {
    var payload = {};
    if (state.conversationHistoryScope === 'object') {
      var objectRef = currentMnObjectRef();
      if (objectRef.objectId) payload.mnObjectId = objectRef.objectId;
    }
    return payload;
  }

  function refreshConversationHistory() {
    renderConversationHistoryScope();
    postCompanion('conversation_list', conversationHistoryPayload(), function(result) {
      state.conversations = result.conversations || [];
      renderConversationList(state.conversations);
    }, {showReply: false});
  }

  function openConversationHistory() {
    closeConfigPage();
    var page = byId('conversationHistoryPage');
    if (page) page.className = 'config-page';
    refreshConversationHistory();
  }

  function closeConversationHistory() {
    var page = byId('conversationHistoryPage');
    if (page) page.className = 'config-page hidden';
  }

  function renderConversationList(items) {
    var list = byId('conversationHistoryList');
    if (!list) return;
    list.innerHTML = '';
    items = items || [];
    if (!items.length) {
      var empty = document.createElement('div');
      empty.className = 'conversation-empty';
      empty.textContent = '当前文档还没有历史对话。';
      list.appendChild(empty);
      return;
    }
    for (var i = 0; i < items.length; i++) {
      (function(item) {
        item = item || {};
        var row = document.createElement('article');
        row.className = 'conversation-list-item' + (item.sessionId && item.sessionId === state.sessionId ? ' active' : '');
        var main = document.createElement('div');
        main.className = 'conversation-list-main';
        var title = document.createElement('div');
        title.className = 'conversation-list-title';
        title.textContent = item.title || '新对话';
        var meta = document.createElement('div');
        meta.className = 'conversation-list-meta';
        meta.textContent = (item.updatedAt || '未保存') + ' / ' + (item.messageCount || 0) + ' 条消息';
        var preview = document.createElement('div');
        preview.className = 'conversation-list-preview';
        preview.textContent = item.lastMessage || '无预览';
        main.appendChild(title);
        main.appendChild(meta);
        main.appendChild(preview);
        var objectRef = item.objectRef || {};
        if (objectRef.objectId || objectRef.kind || objectRef.title) {
          var objectLine = document.createElement('div');
          objectLine.className = 'conversation-list-object';
          objectLine.setAttribute('data-mn-object-id', String(objectRef.objectId || ''));
          objectLine.textContent = '对象：' + (objectRef.kind || 'object') + ' / ' + clip(objectRef.title || objectRef.objectId, 64);
          main.appendChild(objectLine);
        }
        var actions = document.createElement('div');
        actions.className = 'conversation-list-actions';
        var loadButton = document.createElement('button');
        loadButton.className = 'small-button primary-lite';
        loadButton.type = 'button';
        loadButton.textContent = '打开';
        loadButton.addEventListener('click', function(ev) {
          releaseButtonFocus(ev.currentTarget);
          loadConversation(item);
        });
        var deleteButton = document.createElement('button');
        deleteButton.className = 'small-button danger-lite';
        deleteButton.type = 'button';
        deleteButton.textContent = '删除';
        deleteButton.addEventListener('click', function(ev) {
          releaseButtonFocus(ev.currentTarget);
          deleteConversation(item);
        });
        actions.appendChild(loadButton);
        actions.appendChild(deleteButton);
        row.appendChild(main);
        row.appendChild(actions);
        list.appendChild(row);
      })(items[i]);
    }
  }

  function newConversation() {
    postCompanion('conversation_new', {}, function(result) {
      if (!result || !result.ok) {
        addFailureMessage('新对话失败', result);
        return;
      }
      setCurrentConversation(result.conversation || {});
      renderNewConversationMessage();
      closeConversationHistory();
    }, {showReply: false});
  }

  function loadConversation(item) {
    item = item || {};
    if (!item.sessionId) return;
    var payload = conversationHistoryPayload();
    payload.sessionId = item.sessionId;
    postCompanion('conversation_load', payload, function(result) {
      if (!result || !result.ok) {
        addFailureMessage('加载历史对话失败', result);
        return;
      }
      setCurrentConversation(result.conversation || item);
      renderHistoryItems(result.history || []);
      closeConversationHistory();
    }, {showReply: false});
  }

  function deleteConversation(item) {
    item = item || {};
    if (!item.sessionId) return;
    if (window.confirm && !window.confirm('删除这条历史对话？')) return;
    var payload = conversationHistoryPayload();
    payload.sessionId = item.sessionId;
    postCompanion('conversation_delete', payload, function(result) {
      if (!result || !result.ok) {
        addFailureMessage('删除历史对话失败', result);
        return;
      }
      if (item.sessionId === state.sessionId) {
        state.conversationId = '';
        state.sessionId = '';
        renderNewConversationMessage();
      }
      refreshConversationHistory();
    }, {showReply: false});
  }

  function isBrowserPreview() {
    return window.location && /^https?:$/.test(String(window.location.protocol || ''));
  }

  function bridge(path, params) {
    var query = [];
    params = params || {};
    for (var key in params) {
      if (Object.prototype.hasOwnProperty.call(params, key)) {
        query.push(encodeURIComponent(key) + '=' + encodeURIComponent(params[key] || ''));
      }
    }
    if (isBrowserPreview()) return;
    window.location.href = 'codexpaper://' + path + (query.length ? '?' + query.join('&') : '');
  }

  function missingControlIds() {
    var missing = [];
    for (var i = 0; i < requiredControlIds.length; i++) {
      if (!byId(requiredControlIds[i])) missing.push(requiredControlIds[i]);
    }
    return missing;
  }

  function reportControlsReady() {
    var missing = missingControlIds();
    bridge('event', {
      name: 'webControlsReady',
      controls: requiredControlIds.join(','),
      missing: missing.join(','),
      minWidth: '390',
      minHeight: '520'
    });
  }

  function reportActionResponse(action, result) {
    result = result || {};
    var cards = result.cards || [];
    var cardCount = cards && cards.length !== undefined ? cards.length : 0;
    var hasMindmap = result.mindmap ? true : false;
    var message = result.reply || result.message || (result.ok ? '完成' : '失败');
    bridge('event', {
      name: 'handleResponse',
      action: String(action || ''),
      message: String(message || '').substring(0, 500),
      cards: String(cardCount),
      hasMindmap: hasMindmap ? 'true' : 'false'
    });
  }

  function companionPayload(action, extra) {
    var payload = {};
    var ctx = state.context || {};
    for (var key in ctx) {
      if (Object.prototype.hasOwnProperty.call(ctx, key)) payload[key] = ctx[key];
    }
    extra = extra || {};
    for (var extraKey in extra) {
      if (Object.prototype.hasOwnProperty.call(extra, extraKey)) payload[extraKey] = extra[extraKey];
    }
    if (!payload.conversationId && state.conversationId) payload.conversationId = state.conversationId;
    if (!payload.sessionId && state.sessionId) payload.sessionId = state.sessionId;
    var mnObject = state.agentOperation && state.agentOperation.mnObject ? state.agentOperation.mnObject : null;
    if (mnObject && mnObject.objectId && !payload.mnObject && !payload.mnObjectId) payload.mnObject = mnObject;
    payload.action = action;
    payload.source = payload.source || 'marginnote4-web-panel';
    payload.contextScope = currentContextScope();
    if (!payload.mindmapTarget && state.mindmapTarget && state.mindmapTarget.target) {
      payload.mindmapTarget = state.mindmapTarget.target;
    }
    return payload;
  }

  function parseCompanionResult(xhr) {
    var result = null;
    try {
      result = JSON.parse(xhr.responseText || '{}');
    } catch (err) {
      result = {ok: false, message: 'Companion 返回不是 JSON'};
    }
    result = result || {};
    result.httpStatus = xhr.status || 0;
    if (xhr.status >= 400) {
      result.ok = false;
      if (!result.message) result.message = 'Companion 请求失败：HTTP ' + xhr.status;
    }
    return result;
  }

  function displayCompanionResult(result, showReply, action) {
    result = result || {};
    if (result.message) window.CodexPanel.setStatus({text: result.message});
    if (showReply && result.reply) {
      if (action === 'chat' || action === 'explain_selection') {
        addAssistantReplyWithActions(result.reply);
      } else {
        addMessage('assistant', result.reply);
      }
      result.replyShown = true;
    }
    return result;
  }

  function addFailureMessage(prefix, result) {
    result = result || {};
    if (result.replyShown) return;
    var message = result.message || 'unknown error';
    if (result.httpStatus) message += ' (HTTP ' + result.httpStatus + ')';
    addMessage('assistant', prefix + '：' + message);
  }

  function companionConnectionFailureResult() {
    return {
      ok: false,
      httpStatus: 0,
      message: 'Companion 未运行或无法连接：无法连接 127.0.0.1:48761。请启动本地 Companion 服务；如果状态仍显示连接，请在设置页点“运行态采证”生成诊断 JSON。'
    };
  }

  function postCompanion(action, extra, done, options) {
    options = options || {};
    var xhr = new XMLHttpRequest();
    xhr.open('POST', 'http://127.0.0.1:48761/marginnote/action', true);
    xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    setProgressStage(
      '正在等待 Companion 返回',
      '请求已发送到本地 Companion；如果走 Codex CLI 或 OpenAI，这一步会等待模型生成文字。'
    );
    xhr.onreadystatechange = function() {
      if (xhr.readyState !== 4) return;
      setProgressStage('已收到结果', 'Companion 已返回，正在解析结果并更新面板。');
      var result = displayCompanionResult(parseCompanionResult(xhr), options.showReply !== false, action);
      if (done) done(result || {});
    };
    xhr.onerror = function() {
      var result = companionConnectionFailureResult();
      setProgressStage('连接失败', result.message);
      finishProgressStage('连接失败', result.message);
      window.CodexPanel.setStatus({text: result.message});
      if (done) done(result);
    };
    xhr.send(JSON.stringify(companionPayload(action, extra)));
  }

  function postCompanionPath(path, action, extra, done) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', 'http://127.0.0.1:48761' + path, true);
    xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    if (path === '/marginnote/draft') {
      setProgressStage('正在保存草稿', '模型结果已生成，正在保存到本地草稿确认区。');
    } else if (path === '/marginnote/enqueue') {
      setProgressStage('正在加入队列', '当前任务未结束，新动作正在发送到 Companion 队列。');
    } else {
      setProgressStage('正在等待 Companion 返回', '请求已发送到本地 Companion，正在等待处理结果。');
    }
    xhr.onreadystatechange = function() {
      if (xhr.readyState !== 4) return;
      setProgressStage('已收到结果', 'Companion 已返回，正在更新界面状态。');
      var result = displayCompanionResult(parseCompanionResult(xhr), false, action);
      if (done) done(result || {});
    };
    xhr.onerror = function() {
      var result = companionConnectionFailureResult();
      setProgressStage('连接失败', result.message);
      finishProgressStage('连接失败', result.message);
      window.CodexPanel.setStatus({text: result.message});
      if (done) done(result);
    };
    xhr.send(JSON.stringify(companionPayload(action, extra)));
  }

  function postCompanionSilent(action, extra) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', 'http://127.0.0.1:48761/marginnote/action', true);
    xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    xhr.send(JSON.stringify(companionPayload(action, extra)));
  }

  function agentObjectLabel(kind) {
    var labels = {
      selection: 'PDF 选区',
      note: '卡片/节点',
      document: '当前文档',
      mindmap: '目标脑图',
      unknown: '未识别对象'
    };
    return labels[kind] || kind || '未识别对象';
  }

  function agentRiskLabel(status) {
    var labels = {
      read_only: '只读',
      write_pending_confirmation: '写入需确认',
      blocked: '已阻断',
      not_available: '未检查'
    };
    return labels[status] || status || '未检查';
  }

  function workspaceSurfacePane(surface) {
    var map = {
      console: 'object',
      mindmap_studio: 'operation',
      card_factory: 'knowledge',
      ledger_explorer: 'object',
      knowledge_graph: 'knowledge',
      workflow_builder: 'workflow',
      skill_center: 'workflow'
    };
    return map[surface] || 'object';
  }

  function workspaceSurfaceAnchor(surface) {
    var map = {
      console: 'objectWorkspacePanel',
      mindmap_studio: 'mindmapDiffWorkbench',
      card_factory: 'knowledgeWorkspaceReviewQueue',
      ledger_explorer: 'operationLedgerPanel',
      knowledge_graph: 'knowledgeWorkspacePanel',
      workflow_builder: 'workflowWorkspaceTemplates',
      skill_center: 'workflowWorkspaceSkills'
    };
    return map[surface] || 'objectWorkspacePanel';
  }

  function workspaceSurfaceFromPane(pane) {
    var map = {
      object: 'console',
      operation: 'mindmap_studio',
      knowledge: 'knowledge_graph',
      workflow: 'workflow_builder'
    };
    return map[pane] || 'console';
  }

  function workspaceSurfaceSummary(surface) {
    var map = {
      console: 'Knowledge Console：当前对象、风险、关系和账本入口。',
      mindmap_studio: 'Mindmap Studio：围绕目标脑图、Diff、局部执行和验证工作。',
      card_factory: 'Card Factory：查看卡型质量、复习队列和学习目标。',
      ledger_explorer: 'Operation Ledger：查看写入证据、回滚状态和残留对象。',
      knowledge_graph: 'Knowledge Graph：查看实体、关系、索引范围和检索结果。',
      workflow_builder: 'Workflow Builder：查看模板、最近 run、确认点和重试入口。',
      skill_center: 'Skill Center：查看技能包权限、安装状态、回滚和验收规则。'
    };
    return map[surface] || map.console;
  }

  function focusWorkspaceSurfaceAnchor(anchorId) {
    var anchor = byId(anchorId);
    if (!anchor) return;
    anchor.classList.add('workspace-surface-focus');
    try {
      anchor.scrollIntoView({block: 'nearest', inline: 'nearest'});
    } catch (err) {
      anchor.scrollIntoView();
    }
    window.setTimeout(function() {
      anchor.classList.remove('workspace-surface-focus');
    }, 900);
  }

  function renderWorkspaceNavigator() {
    var surface = state.activeWorkspaceSurface || 'console';
    var buttons = document.querySelectorAll('.workspace-nav-card');
    for (var i = 0; i < buttons.length; i++) {
      var active = buttons[i].getAttribute('data-workspace-surface') === surface;
      if (active) buttons[i].classList.add('active');
      else buttons[i].classList.remove('active');
      buttons[i].setAttribute('aria-selected', active ? 'true' : 'false');
    }
    setText('workspaceNavigatorSummary', workspaceSurfaceSummary(surface));
  }

  function notebookWorkspaceCardText(label, value, detail) {
    var text = label + '：' + (value || '等待');
    if (detail) text += ' / ' + detail;
    return text;
  }

  function runNotebookWorkspaceAction(item) {
    item = item || {};
    var action = String(item.action || '');
    var surface = String(item.surface || '');
    var payload = item.payload || {};
    if (surface) switchWorkspaceSurface(surface);
    if (action === 'request_mn_object_registry_scan') {
      if (state.objectRegistryScanInFlight) return;
      state.objectRegistryScanInFlight = true;
      postCompanion('request_mn_object_registry_scan', Object.assign({source: 'notebook-workspace'}, payload), function(result) {
        state.objectRegistryScanInFlight = false;
        if (!result || result.ok === false) {
          addFailureMessage('MN 对象扫描请求失败', result || {});
          return;
        }
        refreshNotebookWorkspace(false);
        refreshObjectBrowser(false);
      }, {showReply: false});
      return;
    }
    if (action === 'mn_read_tree') {
      requestMindmapTreeRead();
      return;
    }
    if (action === 'agent_plan') {
      refreshAgentPlan(true);
      return;
    }
    if (action === 'review_queue_list') {
      refreshKnowledgeWorkspace(true);
      return;
    }
    if (action === 'workflow_list') {
      refreshWorkflowWorkspace(true);
      return;
    }
    if (action === 'operation_ledger_list') {
      refreshOperationLedger(true, payload);
      return;
    }
    if (action) {
      postCompanion(action, payload, function(result) {
        renderControls(result || {});
        if (!result || result.ok === false) addFailureMessage('Notebook Workspace 动作失败', result || {});
      }, {showReply: false});
    }
  }

  function renderNotebookWorkspace(data) {
    if (arguments.length) state.notebookWorkspace = data || {};
    data = state.notebookWorkspace || {};
    var focus = data.focusObject || {};
    var objects = data.objects || {};
    var mindmap = data.mindmap || {};
    var review = data.reviewQueue || {};
    var workflows = data.workflows || {};
    var ledger = data.ledger || {};
    var readiness = data.readiness || {};
    var title = data.documentTitle || data.bookmd5 || data.topicid || '当前 notebook 工作台';
    setText('notebookWorkspaceTitle', clip(title, 84));
    setText(
      'notebookWorkspaceSummary',
      '当前 notebook 的对象、脑图、复习、workflow 和账本总览。' +
        ' 权限：' + (readiness.permission || '未知') +
        ' / MN API：' + (readiness.mnApiAvailable ? '可用' : '未确认')
    );
    setText('notebookWorkspaceFocus', notebookWorkspaceCardText('焦点', agentObjectLabel(focus.kind), clip(focus.title || focus.objectId || '等待 MNObject', 50)));
    setText('notebookWorkspaceObjectCount', notebookWorkspaceCardText('对象', objects.total || 0, 'Registry ' + (objects.registry || 0) + ' / 图谱 ' + (objects.graph || 0)));
    setText('notebookWorkspaceMindmap', notebookWorkspaceCardText('脑图', mindmap.status || 'missing', (mindmap.nodeCount || 0) + ' 节点 ' + (mindmap.rootTitle ? ('/ ' + clip(mindmap.rootTitle, 34)) : '')));
    setText('notebookWorkspaceReview', notebookWorkspaceCardText('复习', review.total || 0, '到期 ' + (review.due || 0) + ' / 新卡 ' + (review.new || 0)));
    setText('notebookWorkspaceWorkflow', notebookWorkspaceCardText('工作流', workflows.runCount || 0, workflows.latestStatus || 'none'));
    setText('notebookWorkspaceLedger', notebookWorkspaceCardText('账本', ledger.total || 0, '证据项'));
    var target = byId('notebookWorkspaceActions');
    if (!target) return;
    var actions = data.primaryActions || [];
    if (!actions.length) {
      replaceElementChildren(target, []);
      return;
    }
    var nodes = [];
    for (var i = 0; i < Math.min(actions.length, 6); i++) {
      (function(item) {
        item = item || {};
        var button = document.createElement('button');
        button.className = 'notebook-workspace-action ' + (item.tone || 'secondary');
        button.type = 'button';
        button.textContent = item.label || actionLabel(item.action || '');
        button.title = item.detail || '';
        button.setAttribute('data-notebook-workspace-action', item.id || item.action || 'action');
        button.addEventListener('click', function(ev) {
          releaseButtonFocus(ev.currentTarget);
          runNotebookWorkspaceAction(item);
        });
        nodes.push(button);
      })(actions[i]);
    }
    replaceElementChildren(target, nodes);
  }

  function refreshNotebookWorkspace(manual) {
    if (state.notebookWorkspaceInFlight) return;
    state.notebookWorkspaceInFlight = true;
    postCompanion('notebook_workspace', {}, function(result) {
      state.notebookWorkspaceInFlight = false;
      if (!result || result.ok === false) {
        if (manual) addFailureMessage('刷新 Notebook Workspace 失败', result || {});
        return;
      }
      var workspace = result.notebookWorkspace || {};
      renderNotebookWorkspace(workspace);
      if (result.objectBrowser) renderObjectBrowser(result.objectBrowser);
      if (result.operationLedger) renderOperationLedger(result.operationLedger);
      if (result.mindmapTreeCache) renderMindmapTreeCacheStatus(result.mindmapTreeCache);
      if (result.reviewQueue) {
        renderKnowledgeWorkspace(Object.assign({}, state.knowledgeWorkspace || {}, {
          reviewQueue: result.reviewQueue,
          reviewQueueSummary: result.reviewQueue.summary || {},
          reviewItems: result.reviewQueue.items || []
        }));
      }
      if (result.workflowWorkspace) renderWorkflowWorkspace(result.workflowWorkspace);
    }, {showReply: false});
  }

  function switchWorkspaceSurface(surface) {
    surface = String(surface || 'console');
    var valid = {
      console: true,
      mindmap_studio: true,
      card_factory: true,
      ledger_explorer: true,
      knowledge_graph: true,
      workflow_builder: true,
      skill_center: true
    };
    if (!valid[surface]) surface = 'console';
    state.activeWorkspaceSurface = surface;
    state.activeProductMode = 'workspace';
    switchWorkbenchPane(workspaceSurfacePane(surface), {fromWorkspaceSurface: true});
    renderWorkspaceNavigator();
    var anchorId = workspaceSurfaceAnchor(surface);
    window.setTimeout(function() {
      focusWorkspaceSurfaceAnchor(anchorId);
    }, 0);
  }

  function renderProductMode() {
    var mode = state.activeProductMode === 'chat' ? 'chat' : 'workspace';
    var shell = byId('aiChatShell');
    if (shell) shell.setAttribute('data-product-mode', mode);
    var buttons = document.querySelectorAll('.mode-switch-button');
    for (var i = 0; i < buttons.length; i++) {
      var active = buttons[i].getAttribute('data-product-mode') === mode;
      if (active) buttons[i].classList.add('active');
      else buttons[i].classList.remove('active');
      buttons[i].setAttribute('aria-selected', active ? 'true' : 'false');
    }
    setText(
      'modeIntentLine',
      mode === 'chat'
        ? '当前：Chat Mode，保持轻量对话、选区解释和回答后续动作。'
        : '当前：Agent Workspace，围绕 MNObject、脑图、知识、账本和 workflow 操作。'
    );
  }

  function switchProductMode(mode) {
    mode = String(mode || 'workspace') === 'chat' ? 'chat' : 'workspace';
    state.activeProductMode = mode;
    if (mode === 'chat') {
      switchWorkbenchPane('dialog', {fromProductMode: true});
    } else {
      var pane = state.activeWorkbenchPane === 'dialog' ? state.lastWorkspacePane : state.activeWorkbenchPane;
      switchWorkbenchPane(pane || state.lastWorkspacePane || 'object', {fromProductMode: true});
    }
    renderProductMode();
  }

  function switchWorkbenchPane(pane, options) {
    pane = String(pane || 'object');
    if (pane !== 'object' && pane !== 'dialog' && pane !== 'operation' && pane !== 'knowledge' && pane !== 'workflow') pane = 'object';
    if (pane === 'dialog') {
      state.activeProductMode = 'chat';
    } else {
      state.activeProductMode = 'workspace';
      state.lastWorkspacePane = pane;
      if (!options || !options.fromWorkspaceSurface) {
        state.activeWorkspaceSurface = workspaceSurfaceFromPane(pane);
      }
    }
    state.activeWorkbenchPane = pane;
    var panels = document.querySelectorAll('.workbench-panel');
    for (var i = 0; i < panels.length; i++) {
      var active = panels[i].getAttribute('data-workbench-pane') === pane;
      if (active) panels[i].classList.add('active');
      else panels[i].classList.remove('active');
    }
    var tabs = document.querySelectorAll('.workbench-tab');
    for (var t = 0; t < tabs.length; t++) {
      var tabActive = tabs[t].getAttribute('data-workbench-pane') === pane;
      if (tabActive) tabs[t].classList.add('active');
      else tabs[t].classList.remove('active');
    }
    renderProductMode();
    renderWorkspaceNavigator();
  }

  function renderKnowledgeSearchResults(result) {
    var target = byId('knowledgeWorkspaceResults');
    if (!target) return;
    result = result || state.knowledgeWorkspace || {};
    var matches = result.matches || result.searchMatches || [];
    if (!matches.length) {
      replaceElementChildren(target, [
        textNode('div', 'knowledge-workspace-result empty', result.message || '暂无知识命中；可以先索引当前选区、节点或文档。')
      ]);
      return;
    }
    var nodes = [];
    for (var i = 0; i < Math.min(matches.length, 8); i++) {
      (function(match) {
        match = match || {};
        var row = document.createElement('div');
        row.className = 'knowledge-workspace-result';
        var title = document.createElement('div');
        title.className = 'knowledge-workspace-result-title';
        title.textContent = (match.title || '未命名知识') + (match.entityType ? (' / ' + match.entityType) : '');
        var snippet = document.createElement('div');
        snippet.className = 'knowledge-workspace-result-snippet';
        snippet.textContent = clip(match.snippet || match.text || '', 220);
        var meta = document.createElement('div');
        meta.className = 'knowledge-workspace-result-meta';
        var sourceRef = match.sourceRef || {};
        meta.textContent = [
          match.source || 'index',
          sourceRef.documentTitle || match.bookmd5 || '',
          sourceRef.page !== undefined ? ('p.' + sourceRef.page) : '',
          match.score !== undefined ? ('score ' + match.score) : ''
        ].filter(Boolean).join(' / ');
        var actions = document.createElement('div');
        actions.className = 'knowledge-workspace-result-actions';
        var useButton = document.createElement('button');
        useButton.className = 'small-button knowledge-workspace-use';
        useButton.type = 'button';
        useButton.textContent = '引用提问';
        useButton.addEventListener('click', function(ev) {
          releaseButtonFocus(ev.currentTarget);
          setValue('promptInput', '结合这条知识解释：' + (match.title || '') + '\n' + (match.snippet || ''));
          switchWorkbenchPane('dialog');
          byId('promptInput').focus();
        });
        actions.appendChild(useButton);
        row.appendChild(title);
        if (snippet.textContent) row.appendChild(snippet);
        row.appendChild(meta);
        row.appendChild(actions);
        nodes.push(row);
      })(matches[i]);
    }
    replaceElementChildren(target, nodes);
  }

  function renderKnowledgeReviewQueue(queue) {
    queue = queue || {};
    if (queue.reviewQueue) queue = queue.reviewQueue;
    var summary = queue.summary || queue.reviewQueueSummary || {};
    var items = queue.items || queue.reviewItems || [];
    var total = summary.totalCount !== undefined ? summary.totalCount : items.length;
    var due = summary.dueCount !== undefined ? summary.dueCount : 0;
    var newCount = summary.newCount !== undefined ? summary.newCount : 0;
    setText('knowledgeWorkspaceReviewQueue', '复习队列：' + total + ' 张 / 到期 ' + due + ' / 新卡 ' + newCount);
    var target = byId('knowledgeWorkspaceReviewList');
    if (!target) return;
    if (!items.length) {
      replaceElementChildren(target, [
        textNode('div', 'knowledge-review-item empty', 'Card Factory 复习卡会显示在这里。')
      ]);
      return;
    }
    var nodes = [];
    for (var i = 0; i < Math.min(items.length, 6); i++) {
      var item = items[i] || {};
      var source = item.source || {};
      var row = document.createElement('div');
      row.className = 'knowledge-review-item';
      var title = document.createElement('div');
      title.className = 'knowledge-review-title';
      title.textContent = clip(item.title || item.reviewPrompt || '未命名复习卡', 90);
      var prompt = document.createElement('div');
      prompt.className = 'knowledge-review-prompt';
      prompt.textContent = clip(item.reviewPrompt || item.body || '', 150);
      var meta = document.createElement('div');
      meta.className = 'knowledge-review-meta';
      meta.textContent = [
        item.cardType || 'card',
        item.state || 'new',
        item.mnObjectId || '',
        source.noteId ? ('note ' + source.noteId) : '',
        source.page !== undefined ? ('p.' + source.page) : ''
      ].filter(Boolean).join(' / ');
      row.appendChild(title);
      if (prompt.textContent) row.appendChild(prompt);
      row.appendChild(meta);
      nodes.push(row);
    }
    replaceElementChildren(target, nodes);
  }

  function searchKnowledgeWorkspace(query) {
    query = String(query || valueOf('knowledgeWorkspaceSearchInput') || state.latestAssistantReply || promptValue() || '').trim();
    if (!query) {
      renderKnowledgeSearchResults({ok: false, message: '请输入检索关键词，或先在对话里提出问题。', matches: []});
      return;
    }
    setValue('knowledgeWorkspaceSearchInput', query);
    postCompanion('knowledge_index_search', {query: query}, function(result) {
      if (result && result.ok !== false) {
        state.knowledgeWorkspace = Object.assign({}, state.knowledgeWorkspace || {}, {lastQuery: query, matches: result.matches || []});
        renderKnowledgeSearchResults(result);
      } else {
        renderKnowledgeSearchResults(result || {ok: false, message: '知识检索失败。', matches: []});
      }
    }, {showReply: false});
  }

  function renderKnowledgeWorkspace(data) {
    if (arguments.length) state.knowledgeWorkspace = data || {};
    data = state.knowledgeWorkspace || {};
    var operation = state.agentOperation || {};
    var knowledge = operation.knowledge || {};
    var ctx = state.context || {};
    var status = data.status || data.index || {};
    var entityTypes = status.entityTypes || data.entityTypes || {};
    var entityCount = data.entityCount || status.entityCount || status.totalEntities || knowledge.count || 0;
    var relationCount = data.relationCount || status.relationCount || 0;
    var scope = data.scope || status.scope || ctx.topicid || ctx.bookmd5 || '当前文档';
    setText('knowledgeWorkspaceTitle', 'Knowledge Graph');
    setText(
      'knowledgeWorkspaceSummary',
      knowledge.enabled
        ? ('知识索引：启用 / 命中 ' + (knowledge.count || 0) + ' 条。')
        : '知识索引默认不注入；只有显式要求相关、历史、跨文档或 notebook 时启用。'
    );
    setText('knowledgeWorkspaceScope', '范围：' + scope + ' / 策略：显式启用');
    var typeParts = [];
    for (var key in entityTypes) {
      if (Object.prototype.hasOwnProperty.call(entityTypes, key)) typeParts.push(key + ':' + entityTypes[key]);
    }
    setText('knowledgeWorkspaceEntities', '实体：' + entityCount + (typeParts.length ? ' / ' + typeParts.join(' / ') : ' / 等待索引状态'));
    setText('knowledgeWorkspaceRelations', '关系：' + relationCount + ' / 支持、反驳、对比和来源回链仍按授权范围显示');
    renderKnowledgeReviewQueue(data.reviewQueue || data.review_queue || data);
    renderKnowledgeSearchResults(data);
    var actions = byId('knowledgeWorkspaceActions');
    if (actions) {
      replaceElementChildren(actions, [
        buildWorkbenchActionButton('检索相关知识', 'knowledge_index_search', '围绕当前对象检索索引', 'knowledge'),
        buildWorkbenchActionButton('刷新知识状态', 'knowledge_index_status', '读取实体和关系统计', 'knowledge')
      ]);
    }
  }

  function renderWorkflowTemplates(data) {
    var target = byId('workflowWorkspaceTemplates');
    if (!target) return;
    data = data || state.workflowWorkspace || {};
    var templates = data.workflowTemplates || data.templates || [];
    if (!templates.length) {
      replaceElementChildren(target, [
        textNode('div', 'workflow-workspace-template empty', '等待 workflow 模板列表。')
      ]);
      return;
    }
    var nodes = [];
    for (var i = 0; i < Math.min(templates.length, 6); i++) {
      (function(item) {
        item = item || {};
        var row = document.createElement('div');
        row.className = 'workflow-workspace-template';
        row.setAttribute('data-workflow-template-id', String(item.id || ''));
        var title = document.createElement('div');
        title.className = 'workflow-workspace-template-title';
        title.textContent = item.title || item.id || '未命名工作流';
        var meta = document.createElement('div');
        meta.className = 'workflow-workspace-template-meta';
        meta.textContent = [
          item.trigger || 'manual',
          (item.stepCount || 0) + ' steps',
          (item.confirmationPoints || []).length + ' confirm'
        ].join(' / ');
        var button = document.createElement('button');
        button.className = 'small-button workflow-workspace-start';
        button.type = 'button';
        button.textContent = '启动';
        button.addEventListener('click', function(ev) {
          releaseButtonFocus(ev.currentTarget);
          startWorkflowTemplate(item.id || '');
        });
        row.appendChild(title);
        row.appendChild(meta);
        row.appendChild(button);
        nodes.push(row);
      })(templates[i]);
    }
    replaceElementChildren(target, nodes);
  }

  function renderWorkflowRuns(data) {
    var target = byId('workflowWorkspaceRecentRuns');
    if (!target) return;
    data = data || state.workflowWorkspace || {};
    var runs = data.workflowRuns || data.runs || [];
    if (!runs.length) {
      replaceElementChildren(target, [
        textNode('div', 'workflow-workspace-run empty', '最近启动的 workflow run 会显示在这里。')
      ]);
      return;
    }
    var nodes = [];
    for (var i = 0; i < Math.min(runs.length, 5); i++) {
      (function(run) {
      run = run || {};
      var row = document.createElement('div');
      row.className = 'workflow-workspace-run';
      row.setAttribute('data-workflow-run-id', String(run.id || ''));
      var title = document.createElement('div');
      title.className = 'workflow-workspace-run-title';
      title.textContent = run.title || run.workflowTitle || run.workflowId || run.id || 'workflow run';
      var meta = document.createElement('div');
      meta.className = 'workflow-workspace-run-meta';
      meta.textContent = [
        run.status || 'unknown',
        run.queuedCount !== undefined ? ('queued ' + run.queuedCount) : '',
        run.waitingConfirmationCount !== undefined ? ('confirm ' + run.waitingConfirmationCount) : '',
        run.mnObjectKind || ''
      ].filter(Boolean).join(' / ');
      var button = document.createElement('button');
      button.className = 'small-button workflow-workspace-open-run';
      button.type = 'button';
      button.textContent = '查看';
      button.addEventListener('click', function(ev) {
        releaseButtonFocus(ev.currentTarget);
        openWorkflowRunInspector(run.id || '');
      });
      row.appendChild(title);
      row.appendChild(meta);
      row.appendChild(button);
      nodes.push(row);
      })(runs[i]);
    }
    replaceElementChildren(target, nodes);
  }

  function workflowRunInspectorStep(step) {
    step = step || {};
    var row = document.createElement('div');
    var tone = step.statusTone || 'idle';
    row.className = 'workflow-run-inspector-step ' + tone;
    row.setAttribute('data-workflow-step-id', String(step.stepId || ''));
    row.setAttribute('data-workflow-step-action', String(step.action || ''));
    var title = document.createElement('div');
    title.className = 'workflow-run-inspector-step-title';
    title.textContent = (step.index ? (step.index + '. ') : '') + (step.title || step.action || '工作流步骤');
    var status = document.createElement('div');
    status.className = 'workflow-run-inspector-step-status ' + tone;
    status.textContent = [
      step.status || 'unknown',
      step.nextAction ? ('next ' + step.nextAction) : '',
      step.queueId ? ('queue ' + step.queueId) : ''
    ].filter(Boolean).join(' / ');
    var message = document.createElement('div');
    message.className = 'workflow-run-inspector-step-message';
    message.textContent = step.message || (step.requiresConfirmation ? '等待确认。' : '等待运行状态更新。');
    row.appendChild(title);
    row.appendChild(status);
    row.appendChild(message);
    if (step.retryable) {
      var actions = document.createElement('div');
      actions.className = 'workflow-run-inspector-step-actions';
      var retryButton = document.createElement('button');
      retryButton.className = 'small-button workflow-run-inspector-retry';
      retryButton.type = 'button';
      retryButton.textContent = '重试';
      retryButton.addEventListener('click', function(ev) {
        releaseButtonFocus(ev.currentTarget);
        retryWorkflowRunStep(step.retryAction || {
          workflowRunId: state.workflowRunInspector && state.workflowRunInspector.workflowRunId,
          workflowStepId: step.stepId || ''
        });
      });
      actions.appendChild(retryButton);
      row.appendChild(actions);
    }
    return row;
  }

  function renderWorkflowRunInspector(inspector) {
    if (arguments.length) state.workflowRunInspector = inspector || null;
    inspector = state.workflowRunInspector || {};
    var panel = byId('workflowRunInspectorPanel');
    var stepsTarget = byId('workflowRunInspectorSteps');
    if (!panel || !stepsTarget) return;
    if (!inspector || !inspector.workflowRunId) {
      panel.className = 'workflow-run-inspector-panel idle';
      setText('workflowRunInspectorTitle', '选择 workflow run 查看步骤');
      setText('workflowRunInspectorSummary', '排队、确认点、阻塞和下一步动作会显示在这里。');
      replaceElementChildren(stepsTarget, [
        textNode('div', 'workflow-run-inspector-step empty', '尚未打开 workflow run。')
      ]);
      return;
    }
    panel.className = 'workflow-run-inspector-panel ' + (inspector.statusTone || 'idle');
    var counts = inspector.stepCounts || {};
    setText(
      'workflowRunInspectorTitle',
      (inspector.title || inspector.workflowId || 'workflow run') + ' / ' + clip(inspector.workflowRunId || '', 16)
    );
    setText(
      'workflowRunInspectorSummary',
      '状态：' + (inspector.status || 'unknown') +
        ' / 步骤 ' + (counts.total || 0) +
        ' / 排队 ' + (counts.queued || 0) +
        ' / 待确认 ' + (counts.waitingConfirmation || 0) +
        ' / 手动 ' + (counts.manual || 0)
    );
    var steps = inspector.steps || [];
    if (!steps.length) {
      replaceElementChildren(stepsTarget, [
        textNode('div', 'workflow-run-inspector-step empty', '该 workflow run 没有步骤记录。')
      ]);
      return;
    }
    var nodes = [];
    for (var i = 0; i < steps.length; i++) nodes.push(workflowRunInspectorStep(steps[i]));
    replaceElementChildren(stepsTarget, nodes);
  }

  function openWorkflowRunInspector(runId) {
    var cleanId = String(runId || '');
    if (!cleanId) return;
    postCompanion('workflow_status', {workflowRunId: cleanId}, function(result) {
      if (!result || result.ok === false) {
        addFailureMessage('读取 workflow run 失败', result || {});
        return;
      }
      renderWorkflowRunInspector(result.runInspector || {});
      switchWorkbenchPane('workflow');
    }, {showReply: false});
  }

  function retryWorkflowRunStep(payload) {
    payload = payload || {};
    if (!payload.workflowRunId && state.workflowRunInspector) {
      payload.workflowRunId = state.workflowRunInspector.workflowRunId || '';
    }
    postCompanion('workflow_retry_step', payload, function(result) {
      if (!result || result.ok === false) {
        addFailureMessage('重试 workflow step 失败', result || {});
        if (result && result.runInspector) renderWorkflowRunInspector(result.runInspector);
        return;
      }
      renderWorkflowRunInspector(result.runInspector || {});
      refreshWorkflowWorkspace(false);
    }, {showReply: false});
  }

  function closeWorkflowRunInspector() {
    state.workflowRunInspector = null;
    renderWorkflowRunInspector(null);
  }

  function startWorkflowTemplate(workflowId) {
    var prompt = promptValue() || state.latestAssistantReply || state.lastPromptFromSelection || '';
    postCompanion('workflow_start', {workflowId: workflowId || '', prompt: prompt}, function(result) {
      renderControls(result || {});
      if (!result || result.ok === false) addFailureMessage('启动工作流失败', result || {});
      else refreshWorkflowWorkspace(false);
    }, {showReply: true});
  }

  function renderWorkflowSkills(data) {
    var target = byId('workflowWorkspaceSkillsList');
    if (!target) return;
    data = data || state.workflowWorkspace || {};
    var skills = data.workflowSkills || data.skills || [];
    if (!skills.length) {
      replaceElementChildren(target, [
        textNode('div', 'workflow-workspace-skill empty', '等待 Skill Marketplace 技能包清单。')
      ]);
      return;
    }
    var nodes = [];
    for (var i = 0; i < Math.min(skills.length, 6); i++) {
      (function(skill) {
        skill = skill || {};
        var row = document.createElement('div');
        row.className = 'workflow-workspace-skill' + (skill.installed ? ' installed' : '');
        row.setAttribute('data-workflow-skill-id', String(skill.id || ''));
        var title = document.createElement('div');
        title.className = 'workflow-workspace-skill-title';
        title.textContent = (skill.installed ? '已安装 · ' : '') + (skill.title || skill.id || '未命名技能');
        var meta = document.createElement('div');
        meta.className = 'workflow-workspace-skill-meta';
        meta.textContent = [
          skill.permission || 'read_only',
          skill.requiresConfirmation ? '需确认' : '只读/无需确认',
          skill.rollback && skill.rollback.strategy ? ('rollback ' + skill.rollback.strategy) : ''
        ].filter(Boolean).join(' / ');
        var button = document.createElement('button');
        button.className = 'small-button workflow-workspace-install';
        button.type = 'button';
        button.textContent = skill.installed ? '已安装' : '安装';
        button.disabled = !!skill.installed;
        button.addEventListener('click', function(ev) {
          releaseButtonFocus(ev.currentTarget);
          installWorkflowSkill(skill.id || '');
        });
        row.appendChild(title);
        row.appendChild(meta);
        row.appendChild(button);
        nodes.push(row);
      })(skills[i]);
    }
    replaceElementChildren(target, nodes);
  }

  function installWorkflowSkill(skillId) {
    postCompanion('skill_install', {skillId: skillId || ''}, function(result) {
      if (result && result.ok !== false) {
        var marketplace = result.marketplace || {};
        state.workflowWorkspace = Object.assign({}, state.workflowWorkspace || {}, {
          workflowSkills: marketplace.skills || [],
          skillCount: marketplace.skillCount || 0,
          installedSkillCount: marketplace.installedCount || 0
        });
        renderWorkflowWorkspace(state.workflowWorkspace);
      } else {
        addFailureMessage('安装技能失败', result || {});
      }
    }, {showReply: false});
  }

  function renderWorkflowWorkspace(data) {
    if (arguments.length) state.workflowWorkspace = data || {};
    data = state.workflowWorkspace || {};
    if (Array.isArray(data)) {
      data = {workflowRuns: data};
      state.workflowWorkspace = data;
    }
    var operation = state.agentOperation || {};
    var workflow = operation.workflow || {};
    var runs = data.runs || data.workflowRuns || [];
    var runCount = data.runCount !== undefined ? data.runCount : runs.length;
    var mnApi = state.mnApi || {};
    var gatewayBackend = mnApi.backend || mnApi.mn_api_backend || 'auto';
    var skillCount = data.skillCount || (data.workflowSkills && data.workflowSkills.length) || (data.skills && data.skills.length) || 0;
    setText('workflowWorkspaceTitle', 'Workflow Runtime');
    setText(
      'workflowWorkspaceSummary',
      '当前 workflow：' + (workflow.title || workflow.id || '等待匹配') + ' / 可保存、排队、确认和验证。'
    );
    setText('workflowWorkspaceRuns', '运行：' + runCount + ' 个 workflow run / 最近状态：' + (data.latestStatus || data.status || '等待状态'));
    setText('workflowWorkspaceGateway', 'External Automation Gateway：' + gatewayBackend + ' / requestId、权限和回调会进入 ledger');
    setText('workflowWorkspaceSkills', 'Skill Marketplace：' + skillCount + ' 个技能包 / 已安装 ' + (data.installedSkillCount || data.installedCount || 0) + ' 个 / 写入技能需声明权限、回滚和验收规则');
    renderWorkflowSkills(data);
    renderWorkflowTemplates(data);
    renderWorkflowRuns(data);
    renderWorkflowRunInspector(state.workflowRunInspector);
    var actions = byId('workflowWorkspaceActions');
    if (actions) {
      replaceElementChildren(actions, [
        buildWorkbenchActionButton('启动工作流', 'workflow_start', '基于当前对象启动推荐工作流', 'workflow'),
        buildWorkbenchActionButton('刷新运行状态', 'workflow_list', '读取 workflow run 列表', 'workflow')
      ]);
    }
  }

  function operationCompilerTone(status) {
    var value = String(status || '').toLowerCase();
    if (value === 'blocked' || value === 'block' || value === 'failed' || value === 'error') return 'block';
    if (value === 'needs_dry_run' || value === 'waiting_dry_run' || value === 'not_available' || value === 'required' || value === 'warn') return 'warn';
    if (value === 'ready' || value === 'read_only' || value === 'pass' || value === 'not_required') return 'pass';
    return 'idle';
  }

  function operationPlanStat(label, value, tone) {
    var node = document.createElement('div');
    node.className = 'operation-plan-stat ' + operationCompilerTone(tone);
    var labelNode = document.createElement('span');
    labelNode.textContent = label;
    var valueNode = document.createElement('strong');
    valueNode.textContent = value;
    node.appendChild(labelNode);
    node.appendChild(valueNode);
    return node;
  }

  function operationCompilerCheckRow(check) {
    check = check || {};
    var row = document.createElement('div');
    row.className = 'operation-compiler-check ' + operationCompilerTone(check.tone || check.status);
    var badge = document.createElement('span');
    badge.className = 'operation-compiler-check-badge';
    badge.textContent = check.label || check.id || 'Check';
    var text = document.createElement('span');
    text.className = 'operation-compiler-check-text';
    text.textContent = (check.status || 'unknown') + (check.detail ? (' / ' + check.detail) : '');
    row.appendChild(badge);
    row.appendChild(text);
    return row;
  }

  function runOperationCompilerRepairAction(action) {
    action = action || {};
    var handler = String(action.handler || '');
    if (handler === 'refreshNativeCapabilities') {
      refreshNativeCapabilities();
      return;
    }
    if (handler === 'openConfigPage') {
      openConfigPage();
      return;
    }
    if (handler === 'cacheCurrentPdf') {
      cacheCurrentPdf();
      return;
    }
    if (handler === 'openPermissionSettings') {
      openPermissionSettings();
      return;
    }
    addMessage('assistant', action.detail || action.label || '这个修复动作暂未绑定处理器。');
  }

  function renderOperationCompilerRepairActions(compiler) {
    var target = byId('operationCompilerRepairActions');
    if (!target) return;
    compiler = compiler || {};
    var actions = compiler.repairActions || [];
    if (!actions.length) {
      replaceElementChildren(target, []);
      return;
    }
    var nodes = [];
    for (var i = 0; i < actions.length && i < 4; i++) {
      (function(action) {
        action = action || {};
        var button = document.createElement('button');
        button.className = 'operation-compiler-repair-button';
        button.type = 'button';
        button.textContent = action.label || action.id || '修复';
        button.title = action.detail || '';
        button.setAttribute('data-operation-repair-action', action.id || action.handler || 'repair');
        button.addEventListener('click', function(ev) {
          releaseButtonFocus(ev.currentTarget);
          runOperationCompilerRepairAction(action);
        });
        nodes.push(button);
      })(actions[i]);
    }
    replaceElementChildren(target, nodes);
  }

  function renderOperationDryRunDetails(plan) {
    var target = byId('operationDryRunDetails');
    if (!target) return;
    plan = plan || {};
    var dryRun = plan.dryRun || {};
    var perOperation = dryRun.perOperation || {};
    var items = Array.isArray(perOperation.items) ? perOperation.items : [];
    var status = String(perOperation.status || dryRun.status || 'idle');
    target.className = 'operation-dry-run-details ' + operationCompilerTone(status);
    if (perOperation.schema !== 'codex.mn.perOperationDryRun.v1' || !items.length) {
      var empty = document.createElement('div');
      empty.className = 'operation-dry-run-row empty';
      empty.textContent = dryRun.message || '逐节点 dry-run 明细会显示每个操作的 noteId、能力和阻断原因。';
      replaceElementChildren(target, [empty]);
      return;
    }
    var rows = [];
    var title = document.createElement('div');
    title.className = 'operation-dry-run-title';
    title.textContent =
      '逐节点 Dry-run：' +
      (perOperation.blockedCount || 0) + ' 阻断 / ' +
      (perOperation.unknownCount || 0) + ' 未确认 / ' +
      (perOperation.readyCount || 0) + ' 可执行';
    rows.push(title);
    for (var i = 0; i < items.length && i < 8; i++) {
      var item = items[i] || {};
      var row = document.createElement('div');
      var tone = operationCompilerTone(item.status);
      row.className = 'operation-dry-run-row ' + tone;
      row.setAttribute('data-operation-dry-run-status', String(item.status || 'unknown'));
      row.setAttribute('data-operation-id', String(item.opId || ''));
      row.setAttribute('data-note-id', String(item.noteId || ''));
      row.setAttribute('data-verification-level', String(item.verificationLevel || ''));
      var badge = document.createElement('strong');
      badge.textContent = item.status || 'unknown';
      var text = document.createElement('span');
      text.textContent =
        (item.title || item.opId || item.op || '操作') +
        ' / ' + (item.mutation || item.op || 'op') +
        (item.noteId ? (' / noteId ' + item.noteId) : '') +
        (item.requiredCapabilities && item.requiredCapabilities.length ? (' / ' + item.requiredCapabilities.join('、')) : '') +
        (item.reason ? (' / ' + item.reason) : '') +
        (item.verificationLevel ? (' / ' + item.verificationLevel) : '');
      row.appendChild(badge);
      row.appendChild(text);
      rows.push(row);
    }
    if (items.length > 8) {
      var more = document.createElement('div');
      more.className = 'operation-dry-run-row empty';
      more.textContent = '还有 ' + (items.length - 8) + ' 个 dry-run 操作未展开。';
      rows.push(more);
    }
    replaceElementChildren(target, rows);
  }

  function renderOperationCompilerPanel(operation) {
    operation = operation || {};
    var panel = byId('operationCompilerPanel');
    if (!panel) return;
    var plan = operation.operationPlan || {};
    var verification = operation.verificationPlan || {};
    var compiler = operation.operationCompiler || {};
    var planStatus = compiler.status || plan.status || 'idle';
    var writeCount = plan.writeCount || 0;
    panel.className = 'operation-compiler-panel ' + operationCompilerTone(planStatus);
    setText(
      'operationCompilerSummary',
      plan.schema
        ? (
            'Operation Compiler：' + (compiler.status || plan.status || 'unknown') +
            ' / workflow ' + (plan.workflowId || '未匹配') +
            ' / capabilities ' + ((plan.requiredCapabilities || []).length || 0)
          )
        : 'Operation Compiler：等待把当前对象和 workflow 编译成 operation plan。'
    );
    var stats = byId('operationPlanStats');
    if (stats) {
      replaceElementChildren(stats, [
        operationPlanStat('Plan', plan.operationCount !== undefined ? String(plan.operationCount) : '未生成', plan.status || planStatus),
        operationPlanStat('Write', String(writeCount), writeCount ? 'warn' : 'pass'),
        operationPlanStat('Verify', verification.status || '等待', verification.status || 'idle')
      ]);
    }
    var checks = byId('operationCompilerChecks');
    if (checks) {
      var checkItems = compiler.checks || [];
      if (!checkItems.length) {
        replaceElementChildren(checks, [operationCompilerCheckRow({label: '等待', status: 'idle', detail: 'Schema、上下文、权限、dry-run 和验证检查会显示在这里。'})]);
      } else {
        var rows = [];
        for (var i = 0; i < checkItems.length && i < 6; i++) rows.push(operationCompilerCheckRow(checkItems[i]));
        replaceElementChildren(checks, rows);
      }
    }
    renderOperationDryRunDetails(plan);
    renderOperationCompilerRepairActions(compiler);
  }

  function refreshKnowledgeWorkspace(manual) {
    postCompanion('knowledge_index_status', {}, function(result) {
      if (result && result.ok !== false) {
        renderKnowledgeWorkspace(Object.assign({}, state.knowledgeWorkspace || {}, result));
      }
      else if (manual) addFailureMessage('刷新知识状态失败', result || {});
    }, {showReply: false});
    var objectRef = currentMnObjectRef();
    postCompanion('review_queue_list', {mnObject: objectRef, mnObjectId: objectRef.objectId || ''}, function(result) {
      if (result && result.ok !== false) {
        renderKnowledgeWorkspace(Object.assign({}, state.knowledgeWorkspace || {}, {
          reviewQueue: result,
          reviewQueueSummary: result.summary || {},
          reviewItems: result.items || []
        }));
      } else if (manual) {
        addFailureMessage('刷新复习队列失败', result || {});
      }
    }, {showReply: false});
  }

  function refreshWorkflowWorkspace(manual) {
    postCompanion('workflow_list', {}, function(result) {
      if (result && result.ok !== false) renderWorkflowWorkspace(result);
      else if (manual) addFailureMessage('刷新工作流状态失败', result || {});
    }, {showReply: false});
    postCompanion('mn_api_status', {}, function(result) {
      if (result && result.ok !== false) {
        renderMnApiStatus(result);
        renderWorkflowWorkspace(state.workflowWorkspace || {});
      } else if (manual) {
        addFailureMessage('刷新外部自动化网关状态失败', result || {});
      }
    }, {showReply: false});
    postCompanion('skill_marketplace_status', {}, function(result) {
      if (result && result.ok !== false) {
        state.workflowWorkspace = Object.assign({}, state.workflowWorkspace || {}, {
          workflowSkills: result.skills || [],
          skillCount: result.skillCount || 0,
          installedSkillCount: result.installedCount || 0
        });
        renderWorkflowWorkspace(state.workflowWorkspace || {});
      } else if (manual) {
        addFailureMessage('刷新技能市场失败', result || {});
      }
    }, {showReply: false});
  }

  function renderWorkbenchPanels() {
    var operation = state.agentOperation || {};
    var mnObject = operation.mnObject || {};
    var object = operation.object || {};
    var workflow = operation.workflow || {};
    var intent = operation.intent || {};
    var policy = operation.operationPolicy || {};
    var risk = policy.risk || {};
    var contextPolicy = operation.contextPolicy || {};
    var ctx = state.context || {};
    var objectKind = object.kind || (ctx.selectionText ? 'selection' : (ctx.selectedNoteTitle ? 'note' : (ctx.documentTitle ? 'document' : 'unknown')));
    var objectTitle = object.title || ctx.selectedNoteTitle || ctx.documentTitle || agentObjectLabel(objectKind);
    var visibleScope = contextPolicy.visibleScope || currentContextScope() || 'auto';
    var topic = ctx.topicid || ctx.notebookid || '';
    var doc = ctx.documentTitle || ctx.bookTitle || ctx.bookmd5 || '';
    var target = state.mindmapTarget && state.mindmapTarget.target ? state.mindmapTarget.target : {};
    var targetLabel = target.label || target.rootTitle || target.selectedNoteTitle || '未确认目标脑图';
    var workflowTitle = workflow.title || intent.workflowTitle || intent.workflowId || '等待 workflow';
    var riskLabel = agentRiskLabel(risk.status);

    setText('objectWorkspaceTitle', agentObjectLabel(objectKind) + ' / ' + clip(objectTitle, 42));
    setText('objectWorkspaceMeta', 'Notebook：' + (topic || '未识别') + ' / 文档：' + (doc ? clip(doc, 80) : '未识别'));
    setText('objectWorkspaceScope', '上下文范围：' + visibleScope + ' / 目标脑图：' + clip(targetLabel, 48));
    setText('operationWorkspaceTitle', workflowTitle);
    setText('operationWorkspaceMeta',
      '风险：' + riskLabel +
      ' / Dry-run：' + (risk.dryRunStatus || 'not_available') +
      ' / 确认点：' + ((risk.confirmationPoints || []).length || 0)
    );
    renderOperationCompilerPanel(operation);
    renderObjectWorkspaceMnObject(mnObject, object);
    renderObjectRiskPanel(policy.riskRegister || {}, risk);
    renderObjectWorkspaceEvidence(objectKind, ctx);
    renderObjectWorkspaceActions(objectKind);
    renderObjectBrowser();
    renderObjectGraph();
    renderObjectActivity();
    renderOperationLedger();
    renderOperationLedgerDetail();
    var currentObjectId = mnObject.objectId || object.mnObjectId || '';
    if (currentObjectId && currentObjectId !== state.objectBrowserLastId) {
      state.objectBrowserLastId = currentObjectId;
      refreshObjectBrowser(false);
    }
    if (currentObjectId && currentObjectId !== state.objectGraphLastId) {
      state.objectGraphLastId = currentObjectId;
      refreshObjectGraph(false);
    }
    if (currentObjectId && currentObjectId !== state.objectActivityLastId) {
      state.objectActivityLastId = currentObjectId;
      refreshObjectActivity(false);
    }
    if (currentObjectId && currentObjectId !== state.operationLedgerLastId) {
      state.operationLedgerLastId = currentObjectId;
      state.operationLedgerDetail = null;
      renderOperationLedgerDetail();
      refreshOperationLedger(false);
    }
    renderOperationWorkspaceActions(operation);
    renderOperationWorkspaceVerification();
    renderKnowledgeWorkspace();
    renderWorkflowWorkspace();
  }

  function replaceElementChildren(node, children) {
    if (!node) return;
    while (node.firstChild) node.removeChild(node.firstChild);
    children = children || [];
    for (var i = 0; i < children.length; i++) node.appendChild(children[i]);
  }

  function buildWorkbenchEvidenceItem(label, ready) {
    var item = document.createElement('div');
    item.className = 'workbench-evidence-item' + (ready ? ' ready' : '');
    item.textContent = label;
    return item;
  }

  function renderObjectWorkspaceMnObject(mnObject, object) {
    mnObject = mnObject || {};
    object = object || {};
    var sourceRef = mnObject.sourceRef || object.sourceRef || {};
    var actionCount = (mnObject.availableActions || []).length || object.availableActionCount || 0;
    var objectId = mnObject.objectId || object.mnObjectId || '';
    var idLine = objectId ? ('MNObject：' + objectId + ' / 动作 ' + actionCount) : 'MNObject：等待对象 ID';
    var sourceParts = [];
    if (sourceRef.page !== null && sourceRef.page !== undefined && sourceRef.page !== '') sourceParts.push('第 ' + sourceRef.page + ' 页');
    if (sourceRef.documentTitle) sourceParts.push(clip(sourceRef.documentTitle, 42));
    if (sourceRef.quote) sourceParts.push('quote: ' + clip(sourceRef.quote, 64));
    if (sourceRef.path) sourceParts.push('path: ' + clip(sourceRef.path, 72));
    setText('objectWorkspaceObjectId', idLine);
    setText('objectWorkspaceSourceRef', sourceParts.length ? ('来源：' + sourceParts.join(' / ')) : '来源：等待 sourceRef');
  }

  function objectRiskItem(item) {
    item = item || {};
    var row = document.createElement('div');
    var tone = String(item.tone || '');
    row.className = 'object-risk-row' + (tone ? (' ' + tone) : '');
    row.setAttribute('data-risk-id', String(item.id || 'risk'));
    var badge = document.createElement('span');
    badge.className = 'object-risk-badge';
    badge.textContent = item.label || '风险';
    var body = document.createElement('span');
    body.className = 'object-risk-text';
    body.textContent = (item.status || 'unknown') + (item.detail ? (' / ' + item.detail) : '');
    row.appendChild(badge);
    row.appendChild(body);
    return row;
  }

  function renderObjectRiskPanel(riskRegister, fallbackRisk) {
    riskRegister = riskRegister || {};
    fallbackRisk = fallbackRisk || {};
    var panel = byId('objectRiskPanel');
    var summary = byId('objectRiskSummary');
    var list = byId('objectRiskList');
    if (!panel || !summary || !list) return;
    var items = riskRegister.items || [];
    var registerSummary = riskRegister.summary || {};
    if (!items.length) {
      panel.className = 'object-risk-panel idle';
      summary.textContent = '风险：等待对象风险评估。';
      replaceElementChildren(list, [objectRiskItem({
        id: 'waiting',
        label: '等待',
        status: fallbackRisk.status || 'unknown',
        detail: '刷新 Agent 计划后显示权限、上下文、目标脑图、dry-run 和确认点。'
      })]);
      return;
    }
    var blocked = registerSummary.blockedCount || 0;
    var warnings = registerSummary.warningCount || 0;
    panel.className = 'object-risk-panel ' + (blocked ? 'blocked' : (warnings ? 'warn' : 'ready'));
    summary.textContent =
      '风险：' + agentRiskLabel(registerSummary.status || fallbackRisk.status) +
      ' / 阻断 ' + blocked +
      ' / 提醒 ' + warnings +
      ' / 项 ' + (registerSummary.itemCount || items.length);
    var nodes = [];
    for (var i = 0; i < items.length && nodes.length < 6; i++) {
      nodes.push(objectRiskItem(items[i]));
    }
    replaceElementChildren(list, nodes);
  }

  function renderObjectWorkspaceEvidence(objectKind, ctx) {
    var target = byId('objectWorkspaceEvidence');
    if (!target) return;
    ctx = ctx || state.context || {};
    var items = [
      buildWorkbenchEvidenceItem('选区：' + (compactText(ctx.selectionText || ctx.selectedText || ctx.activeSelectionText) ? '可用' : '未选中'), objectKind === 'selection'),
      buildWorkbenchEvidenceItem('节点：' + (compactText(ctx.selectedNoteTitle || ctx.selectedNoteText || ctx.selectedNoteId || ctx.noteId || ctx.noteid) ? '可用' : '未选中'), objectKind === 'note'),
      buildWorkbenchEvidenceItem('文档：' + (compactText(ctx.documentTitle || ctx.bookmd5 || ctx.docmd5 || ctx.pdfPath || ctx.documentPath) ? '可用' : '未识别'), objectKind === 'document')
    ];
    replaceElementChildren(target, items);
  }

  function objectWorkspaceActionsForKind(objectKind) {
    var basePrompt = state.latestAssistantReply || state.lastPromptFromSelection || promptValue();
    return [
      {id: 'object_explain', label: '解释对象', action: 'chat', prompt: basePrompt || '解释当前 MarginNote 对象。'},
      {id: 'object_mindmap', label: '生成脑图树', action: 'generate_mindmap', prompt: basePrompt},
      {id: 'object_related', label: '找相关知识', action: 'knowledge_index_search', prompt: basePrompt}
    ].slice(0, objectKind === 'unknown' ? 1 : 3);
  }

  function renderObjectWorkspaceActions(objectKind) {
    var target = byId('objectWorkspaceActions');
    if (!target) return;
    var actions = objectWorkspaceActionsForKind(objectKind);
    var nodes = [];
    for (var i = 0; i < actions.length; i++) {
      (function(item, index) {
        var button = document.createElement('button');
        button.className = 'workbench-action-button' + (index === 0 ? ' primary' : '');
        button.type = 'button';
        button.textContent = item.label;
        button.setAttribute('data-object-workbench-action', item.id || item.action || 'action');
        button.addEventListener('click', function(ev) {
          releaseButtonFocus(ev.currentTarget);
          if (item.action === 'knowledge_index_search') {
            runAgentNextAction(item, item.prompt || state.latestAssistantReply || promptValue());
            return;
          }
          executeAction(item.action || 'chat', item.prompt || promptValue(), item.label);
        });
        nodes.push(button);
      })(actions[i], i);
    }
    replaceElementChildren(target, nodes);
  }

  function buildWorkbenchActionButton(label, action, hint, pane) {
    var button = document.createElement('button');
    button.className = 'workbench-action-button';
    button.type = 'button';
    button.textContent = label || actionLabel(action || '');
    button.title = hint || '';
    button.setAttribute('data-' + (pane || 'generic') + '-workbench-action', action || 'action');
    button.addEventListener('click', function(ev) {
      releaseButtonFocus(ev.currentTarget);
      if (action === 'knowledge_index_status') {
        refreshKnowledgeWorkspace(true);
        return;
      }
      if (action === 'workflow_list') {
        refreshWorkflowWorkspace(true);
        return;
      }
      if (action === 'workflow_start' || action === 'knowledge_index_search') {
        runAgentNextAction({label: label, action: action}, state.latestAssistantReply || promptValue());
        return;
      }
      executeAction(action || 'chat', promptValue(), label || actionLabel(action || ''));
    });
    return button;
  }

  function objectBrowserKindLabel(objectType, kind) {
    var type = String(objectType || '');
    var value = String(kind || '');
    if (type === 'focus') return '当前';
    if (type === 'registry') return 'Registry';
    if (type === 'object_graph') return objectGraphKindLabel(value);
    if (type === 'object_activity') return '活动';
    if (type === 'operation_ledger') return operationLedgerKindLabel(value);
    return '对象';
  }

  function objectBrowserSearchQuery() {
    return String(valueOf('objectBrowserSearchInput') || '').trim();
  }

  function objectBrowserFilterPayload() {
    return {
      objectTypeFilter: String(valueOf('objectBrowserTypeFilterSelect') || '').trim(),
      kindFilter: String(valueOf('objectBrowserKindFilterInput') || '').trim(),
      query: objectBrowserSearchQuery()
    };
  }

  function objectBrowserRow(kind, title, meta, item) {
    item = item || {};
    var browserAction = item.browserAction || {};
    var row = document.createElement('div');
    row.className = 'object-browser-row';
    row.setAttribute('data-browser-kind', String(kind || 'object'));
    var badge = document.createElement('span');
    badge.className = 'object-browser-badge';
    badge.textContent = kind || '对象';
    var body = document.createElement('span');
    body.className = 'object-browser-text';
    body.textContent = (title || '未命名对象') + (meta ? (' / ' + meta) : '');
    row.appendChild(badge);
    row.appendChild(body);
    if (browserAction.action) {
      var openButton = document.createElement('button');
      openButton.className = 'small-button object-browser-open';
      openButton.type = 'button';
      openButton.textContent = browserAction.label || '打开';
      openButton.setAttribute('data-browser-action', String(browserAction.action || ''));
      openButton.addEventListener('click', function(ev) {
        releaseButtonFocus(ev.currentTarget);
        openObjectBrowserItem(item);
      });
      row.appendChild(openButton);
    }
    return row;
  }

  function openObjectBrowserItem(item) {
    item = item || {};
    var descriptor = item.browserAction || {};
    var action = String(descriptor.action || '');
    if (!action) return;
    if (action === 'object_graph') {
      refreshObjectGraph(true, descriptor.payload || {});
      return;
    }
    if (action === 'object_activity') {
      refreshObjectActivity(true, descriptor.payload || {});
      return;
    }
    if (action === 'operation_ledger_list') {
      refreshOperationLedger(true, descriptor.payload || {});
      return;
    }
    if (action === 'operation_ledger_get') {
      openOperationLedgerEntry({ledgerAction: descriptor});
      return;
    }
    if (item.objectType === 'object_graph') {
      openObjectGraphNode({
        graphAction: descriptor,
        title: item.title,
        nodeType: item.kind,
        sourceId: item.browserId,
        summary: item.summary
      });
      return;
    }
    openObjectActivityItem({
      activityAction: descriptor,
      event: item.title || item.kind || '',
      level: item.status || '',
      requestId: item.browserId || '',
      message: item.summary || ''
    });
  }

  function renderObjectBrowser(browser) {
    if (arguments.length) state.objectBrowser = browser || {};
    browser = state.objectBrowser || {};
    var panel = byId('objectBrowserPanel');
    var summary = byId('objectBrowserSummary');
    var list = byId('objectBrowserList');
    if (!panel || !summary || !list) return;
    var objectRef = currentMnObjectRef();
    if (!objectRef.objectId) {
      panel.className = 'object-browser-panel idle';
      summary.textContent = '等待当前对象浏览器。';
      replaceElementChildren(list, [objectBrowserRow('等待', '刷新 Agent 计划后显示对象浏览器', '')]);
      return;
    }
    if (state.objectBrowserInFlight) {
      panel.className = 'object-browser-panel pending';
      summary.textContent = 'Object Browser：正在读取 ' + objectRef.objectId;
      return;
    }
    if (!browser.ok) {
      panel.className = 'object-browser-panel idle';
      summary.textContent = 'Object Browser：尚未读取 / ' + objectRef.objectId;
      replaceElementChildren(list, [objectBrowserRow('等待', '点击刷新读取当前对象浏览器', '')]);
      return;
    }
    var counts = browser.counts || {};
    var filters = browser.filters || {};
    var filterLabels = [];
    if (filters.objectTypeFilter) filterLabels.push('类型=' + filters.objectTypeFilter);
    if (filters.kindFilter) filterLabels.push('Kind=' + filters.kindFilter);
    if (filters.query) filterLabels.push('搜索=' + filters.query);
    var total = counts.total || 0;
    var unfilteredTotal = counts.unfilteredTotal;
    var totalLabel = typeof unfilteredTotal === 'number' && unfilteredTotal !== total
      ? (total + ' / ' + unfilteredTotal)
      : String(total);
    panel.className = 'object-browser-panel ready';
    summary.textContent =
      '对象 ' + totalLabel +
      ' / Registry ' + (counts.registry || 0) +
      ' / 图谱 ' + (counts.object_graph || 0) +
      ' / 活动 ' + (counts.object_activity || 0) +
      ' / 账本 ' + (counts.operation_ledger || 0) +
      (filterLabels.length ? (' / 筛选：' + filterLabels.join('，')) : '');
    var rows = [];
    var objects = browser.objects || [];
    for (var i = 0; i < objects.length && rows.length < 10; i++) {
      rows.push(objectBrowserRow(
        objectBrowserKindLabel(objects[i].objectType, objects[i].kind),
        objects[i].title || objects[i].browserId || '对象',
        objects[i].status || objects[i].summary || '',
        objects[i]
      ));
    }
    if (!rows.length) rows.push(objectBrowserRow('空', '当前对象暂无可浏览对象', ''));
    replaceElementChildren(list, rows);
  }

  function refreshObjectBrowser(manual) {
    var objectRef = currentMnObjectRef();
    if (!objectRef.objectId || state.objectBrowserInFlight) {
      renderObjectBrowser();
      return;
    }
    state.objectBrowserInFlight = true;
    renderObjectBrowser();
    var filters = objectBrowserFilterPayload();
    postCompanion('object_browser', Object.assign({
      mnObject: objectRef,
      mnObjectId: objectRef.objectId,
      limit: 12
    }, filters), function(result) {
      state.objectBrowserInFlight = false;
      if (!result || !result.ok) {
        state.objectBrowser = {ok: false, message: result && result.message ? result.message : 'Object Browser 读取失败。'};
        renderObjectBrowser();
        if (manual) addFailureMessage('Object Browser 读取失败', result || {});
        return;
      }
      renderObjectBrowser(result);
    }, {showReply: false});
  }

  function requestObjectRegistryScan() {
    if (state.objectRegistryScanInFlight) return;
    var objectRef = currentMnObjectRef();
    var sourceRef = objectRef.sourceRef || {};
    state.objectRegistryScanInFlight = true;
    window.CodexPanel.setStatus({text: '正在请求 MN 扫描当前 notebook 对象'});
    postCompanion('request_mn_object_registry_scan', {
      mnObject: objectRef,
      mnObjectId: objectRef.objectId || '',
      selectedNoteId: sourceRef.noteId || '',
      limit: 240,
      source: 'object-browser-scan-button'
    }, function(result) {
      state.objectRegistryScanInFlight = false;
      if (!result || result.ok === false) {
        addFailureMessage('MN 对象扫描请求失败', result || {});
        return;
      }
      window.CodexPanel.setStatus({text: result.message || '已请求 MN 扫描对象，等待原生插件回传 Registry。'});
      setTimeout(function() {
        refreshObjectBrowser(true);
      }, 1200);
    }, {showReply: false});
  }

  function objectGraphKindLabel(nodeType) {
    var value = String(nodeType || '');
    if (value === 'mn_object') return '对象';
    if (value === 'manual_mn_object') return '手工对象';
    if (value === 'conversation') return '对话';
    if (value === 'workflow_run') return '工作流';
    if (value === 'ai_edit_transaction') return '事务';
    if (value === 'external_gateway_request') return '外部';
    if (value === 'diagnostic_log') return '日志';
    if (value === 'knowledge_entity') return '知识';
    if (value === 'mn_note') return 'MN节点';
    return '节点';
  }

  function objectGraphNode(kind, title, meta, item) {
    item = item || {};
    var graphAction = item.graphAction || {};
    var row = document.createElement('div');
    row.className = 'object-graph-node';
    row.setAttribute('data-graph-kind', String(kind || 'node'));
    var badge = document.createElement('span');
    badge.className = 'object-graph-badge';
    badge.textContent = kind || '节点';
    var body = document.createElement('span');
    body.className = 'object-graph-text';
    body.textContent = (title || '未命名节点') + (meta ? (' / ' + meta) : '');
    row.appendChild(badge);
    row.appendChild(body);
    if (graphAction.action) {
      var openButton = document.createElement('button');
      openButton.className = 'small-button object-graph-open';
      openButton.type = 'button';
      openButton.textContent = graphAction.label || '打开';
      openButton.setAttribute('data-graph-action', String(graphAction.action || ''));
      openButton.addEventListener('click', function(ev) {
        releaseButtonFocus(ev.currentTarget);
        openObjectGraphNode(item);
      });
      row.appendChild(openButton);
    }
    return row;
  }

  function openObjectGraphNode(item) {
    item = item || {};
    var descriptor = item.graphAction || {};
    var action = String(descriptor.action || '');
    if (!action) return;
    if (action === 'operation_ledger_get') {
      openOperationLedgerEntry({ledgerAction: descriptor});
      return;
    }
    if (action === 'mn_read_tree') {
      postCompanion('mn_read_tree', descriptor.payload || {}, function(result) {
        if (!result || !result.ok) {
          addFailureMessage('读取 MN 节点子树失败', result || {});
          return;
        }
        renderControls(result || {});
        addMessage('assistant', result.message || '已请求读取 MN 节点子树。');
      }, {showReply: false});
      return;
    }
    if (action === 'object_graph_relation_delete') {
      postCompanion('object_graph_relation_delete', descriptor.payload || {}, function(result) {
        if (!result || !result.ok) {
          addFailureMessage('删除对象关系失败', result || {});
          return;
        }
        addMessage('assistant', result.message || '已删除对象关系。');
        refreshObjectBrowser(true);
        refreshObjectGraph(true);
      }, {showReply: false});
      return;
    }
    openObjectActivityItem({
      activityAction: descriptor,
      event: item.title || item.nodeType || '',
      level: item.status || '',
      requestId: item.sourceId || '',
      message: item.summary || ''
    });
  }

  function renderObjectGraph(graph) {
    if (arguments.length) state.objectGraph = graph || {};
    graph = state.objectGraph || {};
    var panel = byId('objectGraphPanel');
    var summary = byId('objectGraphSummary');
    var list = byId('objectGraphNodes');
    if (!panel || !summary || !list) return;
    var objectRef = currentMnObjectRef();
    if (!objectRef.objectId) {
      panel.className = 'object-graph-panel idle';
      summary.textContent = '等待当前对象图谱。';
      replaceElementChildren(list, [objectGraphNode('等待', '刷新 Agent 计划后显示对象图谱', '')]);
      return;
    }
    if (state.objectGraphInFlight) {
      panel.className = 'object-graph-panel pending';
      summary.textContent = 'Object Graph：正在读取 ' + objectRef.objectId;
      return;
    }
    if (!graph.ok) {
      panel.className = 'object-graph-panel idle';
      summary.textContent = 'Object Graph：尚未读取 / ' + objectRef.objectId;
      replaceElementChildren(list, [objectGraphNode('等待', '点击刷新读取当前对象图谱', '')]);
      return;
    }
    var counts = graph.counts || {};
    panel.className = 'object-graph-panel ready';
    summary.textContent =
      '节点 ' + (counts.nodes || 0) +
      ' / 关系 ' + (counts.edges || 0) +
      ' / 对话 ' + (counts.conversation || 0) +
      ' / 操作 ' + ((counts.workflow_run || 0) + (counts.ai_edit_transaction || 0) + (counts.external_gateway_request || 0)) +
      ' / 手工 ' + (counts.manual_relation || 0);
    var rows = [];
    var nodes = graph.nodes || [];
    for (var i = 0; i < nodes.length && rows.length < 9; i++) {
      if (!nodes[i] || nodes[i].nodeType === 'mn_object') continue;
      rows.push(objectGraphNode(
        objectGraphKindLabel(nodes[i].nodeType),
        nodes[i].title || nodes[i].sourceId || nodes[i].nodeId || '图谱节点',
        nodes[i].status || nodes[i].updatedAt || nodes[i].summary || '',
        nodes[i]
      ));
    }
    if (!rows.length) rows.push(objectGraphNode('空', '当前对象暂无关联图谱节点', ''));
    replaceElementChildren(list, rows);
  }

  function refreshObjectGraph(manual, overridePayload) {
    var objectPayload = overridePayload || {};
    var objectRef = currentMnObjectRef();
    var objectId = objectPayload.mnObjectId || objectRef.objectId;
    if (!objectId || state.objectGraphInFlight) {
      renderObjectGraph();
      return;
    }
    state.objectGraphInFlight = true;
    renderObjectGraph();
    var graphPayload = Object.assign({}, objectPayload, {
      mnObjectId: objectPayload.mnObjectId || objectRef.objectId,
      mnObject: objectPayload.mnObject || objectRef,
      limit: objectPayload.limit || 9
    });
    postCompanion('object_graph', graphPayload, function(result) {
      state.objectGraphInFlight = false;
      if (!result || !result.ok) {
        state.objectGraph = {ok: false, message: result && result.message ? result.message : 'Object Graph 读取失败。'};
        renderObjectGraph();
        if (manual) addFailureMessage('Object Graph 读取失败', result || {});
        return;
      }
      renderObjectGraph(result);
    }, {showReply: false});
  }

  function openObjectGraphRelationEditor() {
    var objectRef = currentMnObjectRef();
    if (!objectRef.objectId) {
      addMessage('assistant', '请先刷新 Agent 计划或在 MN4 中选中一个对象，再添加对象关系。');
      return;
    }
    var editor = byId('objectGraphRelationEditor');
    if (!editor) return;
    editor.className = 'object-graph-relation-editor';
    if (!getValue('objectGraphRelationTypeInput')) setValue('objectGraphRelationTypeInput', 'related_to');
  }

  function closeObjectGraphRelationEditor() {
    var editor = byId('objectGraphRelationEditor');
    if (editor) editor.className = 'object-graph-relation-editor hidden';
  }

  function saveObjectGraphRelation() {
    var objectRef = currentMnObjectRef();
    var targetId = String(getValue('objectGraphRelationTargetInput') || '').trim();
    var relationType = String(getValue('objectGraphRelationTypeInput') || '').trim() || 'related_to';
    var label = String(getValue('objectGraphRelationLabelInput') || '').trim();
    var note = String(getValue('objectGraphRelationNoteInput') || '').trim();
    if (!objectRef.objectId) {
      addMessage('assistant', '保存对象关系失败：当前没有可用 MNObject。');
      return;
    }
    if (!targetId) {
      addMessage('assistant', '保存对象关系失败：请填写目标对象 ID。');
      return;
    }
    postCompanion('object_graph_relation_save', {
      mnObject: objectRef,
      targetObject: {objectId: targetId, kind: 'manual', title: targetId, sourceRef: {}},
      relation: relationType,
      label: label || relationType,
      note: note
    }, function(result) {
      if (!result || !result.ok) {
        addFailureMessage('保存对象关系失败', result || {});
        return;
      }
      setValue('objectGraphRelationTargetInput', '');
      setValue('objectGraphRelationLabelInput', '');
      setValue('objectGraphRelationNoteInput', '');
      closeObjectGraphRelationEditor();
      addMessage('assistant', result.message || '已保存对象关系。');
      refreshObjectBrowser(true);
      refreshObjectGraph(true);
    }, {showReply: false});
  }

  function objectActivityRow(kind, title, meta, item) {
    item = item || {};
    var activityAction = item.activityAction || {};
    var row = document.createElement('div');
    row.className = 'object-activity-row';
    row.setAttribute('data-activity-kind', String(kind || 'item'));
    var badge = document.createElement('span');
    badge.className = 'object-activity-badge';
    badge.textContent = kind || '活动';
    var body = document.createElement('span');
    body.className = 'object-activity-text';
    body.textContent = (title || '未命名活动') + (meta ? (' / ' + meta) : '');
    row.appendChild(badge);
    row.appendChild(body);
    if (activityAction.action) {
      var openButton = document.createElement('button');
      openButton.className = 'small-button object-activity-open';
      openButton.type = 'button';
      openButton.textContent = activityAction.label || '打开';
      openButton.setAttribute('data-activity-action', String(activityAction.action || ''));
      openButton.addEventListener('click', function(ev) {
        releaseButtonFocus(ev.currentTarget);
        openObjectActivityItem(item);
      });
      row.appendChild(openButton);
    }
    return row;
  }

  function openObjectActivityItem(item) {
    item = item || {};
    var descriptor = item.activityAction || {};
    var action = String(descriptor.action || '');
    var payload = descriptor.payload || {};
    if (!action) return;
    if (action === 'conversation_load') {
      postCompanion('conversation_load', payload, function(result) {
        if (!result || !result.ok) {
          addFailureMessage('加载对象历史对话失败', result || {});
          return;
        }
        setCurrentConversation(result.conversation || {});
        renderHistoryItems(result.history || []);
        switchWorkbenchPane('dialog');
      }, {showReply: false});
      return;
    }
    if (action === 'workflow_status') {
      postCompanion('workflow_status', payload, function(result) {
        if (!result || !result.ok) {
          addFailureMessage('读取对象工作流失败', result || {});
          return;
        }
        var summary = result.summary || {};
        addMessage('assistant',
          '对象工作流：' + (summary.title || summary.workflowId || payload.workflowRunId || '') +
          '\n状态：' + (summary.status || '') +
          '\n排队：' + (summary.queuedCount || 0) +
          ' / 等待确认：' + (summary.waitingConfirmationCount || 0)
        );
        switchWorkbenchPane('dialog');
      }, {showReply: false});
      return;
    }
    if (action === 'ai_edit_transaction_get') {
      postCompanion('ai_edit_transaction_get', payload, function(result) {
        if (!result || !result.ok) {
          addFailureMessage('读取对象事务失败', result || {});
          return;
        }
        var tx = result.transaction || {};
        addMessage('assistant',
          '对象事务：' + (tx.transactionId || payload.transactionId || '') +
          '\n状态：' + (tx.status || '') +
          '\n创建：' + (tx.createdCount || 0) +
          ' / 删除：' + (tx.deletedCount || 0) +
          ' / 失败：' + (tx.failedCount || 0)
        );
        switchWorkbenchPane('dialog');
      }, {showReply: false});
      return;
    }
    if (action === 'operation_ledger_get') {
      openOperationLedgerEntry({ledgerAction: descriptor});
      return;
    }
    if (action === 'log_detail') {
      addMessage('assistant',
        '对象日志：' + (item.event || payload.event || '') +
        '\n级别：' + (item.level || '') +
        '\n请求：' + (item.requestId || payload.requestId || '') +
        '\n消息：' + (item.message || '')
      );
      switchWorkbenchPane('dialog');
    }
  }

  function renderObjectActivity(activity) {
    if (arguments.length) state.objectActivity = activity || {};
    activity = state.objectActivity || {};
    var panel = byId('objectActivityPanel');
    var summary = byId('objectActivitySummary');
    var list = byId('objectActivityList');
    if (!panel || !summary || !list) return;
    var objectRef = currentMnObjectRef();
    if (!objectRef.objectId) {
      panel.className = 'object-activity-panel idle';
      summary.textContent = '等待当前对象活动。';
      replaceElementChildren(list, [objectActivityRow('等待', '刷新 Agent 计划后显示对象活动', '')]);
      return;
    }
    if (state.objectActivityInFlight) {
      panel.className = 'object-activity-panel pending';
      summary.textContent = '对象活动：正在读取 ' + objectRef.objectId;
      return;
    }
    if (!activity.ok) {
      panel.className = 'object-activity-panel idle';
      summary.textContent = '对象活动：尚未读取 / ' + objectRef.objectId;
      replaceElementChildren(list, [objectActivityRow('等待', '点击刷新读取当前对象活动', '')]);
      return;
    }
    var counts = activity.counts || {};
    panel.className = 'object-activity-panel ready';
    summary.textContent =
      '对话 ' + (counts.conversations || 0) +
      ' / 工作流 ' + (counts.workflowRuns || 0) +
      ' / 事务 ' + (counts.transactions || 0) +
      ' / 关系 ' + (counts.manualRelations || 0) +
      ' / 日志 ' + (counts.logs || 0);
    var rows = [];
    var conversations = activity.conversations || [];
    var workflows = activity.workflowRuns || [];
    var transactions = activity.transactions || [];
    var manualRelations = activity.manualRelations || [];
    var logs = activity.logs || [];
    for (var c = 0; c < conversations.length && rows.length < 8; c++) {
      rows.push(objectActivityRow('对话', conversations[c].title || '历史对话', conversations[c].updatedAt || conversations[c].lastMessage || '', conversations[c]));
    }
    for (var w = 0; w < workflows.length && rows.length < 8; w++) {
      rows.push(objectActivityRow('工作流', workflows[w].title || workflows[w].workflowId || 'workflow', workflows[w].status || '', workflows[w]));
    }
    for (var t = 0; t < transactions.length && rows.length < 8; t++) {
      rows.push(objectActivityRow('事务', transactions[t].transactionId || 'AI 编辑事务', transactions[t].status || '', transactions[t]));
    }
    for (var r = 0; r < manualRelations.length && rows.length < 8; r++) {
      rows.push(objectActivityRow('手工关系', manualRelations[r].label || manualRelations[r].relation || '对象关系', manualRelations[r].status || '', manualRelations[r]));
    }
    for (var l = 0; l < logs.length && rows.length < 8; l++) {
      rows.push(objectActivityRow('日志', logs[l].event || '诊断日志', logs[l].message || logs[l].level || '', logs[l]));
    }
    if (!rows.length) rows.push(objectActivityRow('空', '当前对象暂无历史活动', ''));
    replaceElementChildren(list, rows);
  }

  function refreshObjectActivity(manual, overridePayload) {
    var objectPayload = overridePayload || {};
    var objectRef = currentMnObjectRef();
    var objectId = objectPayload.mnObjectId || objectRef.objectId;
    if (!objectId || state.objectActivityInFlight) {
      renderObjectActivity();
      return;
    }
    state.objectActivityInFlight = true;
    renderObjectActivity();
    var activityPayload = Object.assign({}, objectPayload, {
      mnObjectId: objectPayload.mnObjectId || objectRef.objectId,
      mnObject: objectPayload.mnObject || objectRef,
      limit: objectPayload.limit || 6
    });
    postCompanion('object_activity', activityPayload, function(result) {
      state.objectActivityInFlight = false;
      if (!result || !result.ok) {
        state.objectActivity = {ok: false, message: result && result.message ? result.message : '对象活动读取失败。'};
        renderObjectActivity();
        if (manual) addFailureMessage('对象活动读取失败', result || {});
        return;
      }
      renderObjectActivity(result);
    }, {showReply: false});
  }

  function operationLedgerRow(kind, title, meta, item) {
    item = item || {};
    var ledgerAction = item.ledgerAction || {};
    var row = document.createElement('div');
    row.className = 'operation-ledger-row';
    row.setAttribute('data-ledger-kind', String(kind || 'entry'));
    var badge = document.createElement('span');
    badge.className = 'operation-ledger-badge';
    badge.textContent = kind || '账本';
    var body = document.createElement('span');
    body.className = 'operation-ledger-text';
    body.textContent = (title || '未命名账本项') + (meta ? (' / ' + meta) : '');
    row.appendChild(badge);
    row.appendChild(body);
    if (ledgerAction.action) {
      var openButton = document.createElement('button');
      openButton.className = 'small-button operation-ledger-open';
      openButton.type = 'button';
      openButton.textContent = ledgerAction.label || '查看';
      openButton.setAttribute('data-ledger-action', String(ledgerAction.action || ''));
      openButton.addEventListener('click', function(ev) {
        releaseButtonFocus(ev.currentTarget);
        openOperationLedgerEntry(item);
      });
      row.appendChild(openButton);
    }
    return row;
  }

  function operationLedgerKindLabel(entryType) {
    var value = String(entryType || '');
    if (value === 'workflow_run') return '工作流';
    if (value === 'ai_edit_transaction') return '事务';
    if (value === 'external_gateway_request') return '外部';
    if (value === 'object_graph_manual_relation') return '手工关系';
    return '账本';
  }

  function operationLedgerSearchQuery() {
    return String(valueOf('operationLedgerSearchInput') || '').trim();
  }

  function operationLedgerFilterPayload() {
    return {
      entryTypeFilter: String(valueOf('operationLedgerTypeFilterSelect') || '').trim(),
      statusFilter: String(valueOf('operationLedgerStatusFilterInput') || '').trim(),
      query: operationLedgerSearchQuery()
    };
  }

  function operationLedgerEvidenceRow(label, value, tone) {
    var row = document.createElement('div');
    row.className = 'operation-ledger-evidence-row' + (tone ? (' ' + tone) : '');
    var key = document.createElement('span');
    key.className = 'operation-ledger-evidence-key';
    key.textContent = label || '证据';
    var text = document.createElement('span');
    text.className = 'operation-ledger-evidence-value';
    text.textContent = value || '无';
    row.appendChild(key);
    row.appendChild(text);
    return row;
  }

  function closeOperationLedgerDetail() {
    state.operationLedgerDetail = null;
    renderOperationLedgerDetail();
  }

  function renderOperationLedgerDetail(result) {
    if (arguments.length) state.operationLedgerDetail = result || null;
    result = state.operationLedgerDetail || null;
    var panel = byId('operationLedgerDetailPanel');
    var title = byId('operationLedgerDetailTitle');
    var meta = byId('operationLedgerDetailMeta');
    var evidenceTarget = byId('operationLedgerDetailEvidence');
    if (!panel || !title || !meta || !evidenceTarget) return;
    if (!result || !result.ok) {
      panel.className = 'operation-ledger-detail-panel idle';
      title.textContent = '选择账本项查看证据';
      meta.textContent = '事务验证、工作流确认点和外部回调会显示在这里。';
      replaceElementChildren(evidenceTarget, [operationLedgerEvidenceRow('等待', '尚未打开账本项。', 'empty')]);
      return;
    }
    var entry = result.entry || {};
    var record = result.record || {};
    var evidence = result.evidence || {};
    var verification = evidence.verification || {};
    var callback = evidence.callback || {};
    var workflow = evidence.workflow || {};
    var operationChain = evidence.operationChain || {};
    var manualRelation = evidence.manualRelation || {};
    var rows = [
      operationLedgerEvidenceRow('类型', operationLedgerKindLabel(entry.entryType)),
      operationLedgerEvidenceRow('状态', entry.status || evidence.status || 'unknown'),
      operationLedgerEvidenceRow('来源 ID', entry.sourceId || record.requestId || record.transactionId || record.id || ''),
      operationLedgerEvidenceRow('对象', (entry.objectRef && entry.objectRef.objectId) || ''),
      operationLedgerEvidenceRow('摘要', entry.summary || evidence.summary || '')
    ];
    if (evidence.schema) {
      rows.push(operationLedgerEvidenceRow('证据', evidence.summary || evidence.status || evidence.schema));
    }
    if (verification.schema) {
      rows.push(operationLedgerEvidenceRow(
        '验证：状态',
        (verification.summary || verification.status || '已生成') +
          ' / 创建 ' + (verification.createdCount || 0) +
          ' / 删除 ' + (verification.deletedCount || 0) +
          ' / 剩余 ' + (verification.remainingCount || 0),
        verification.status === 'pass' || verification.status === 'PASS' ? 'pass' : ''
      ));
      rows.push(operationLedgerEvidenceRow('验证：事务', verification.transactionId || record.transactionId || ''));
      if (verification.remainingNoteIds && verification.remainingNoteIds.length) {
        rows.push(operationLedgerEvidenceRow('验证：残留 noteId', verification.remainingNoteIds.join(', '), 'warn'));
      }
    }
    if (callback.schema) {
      rows.push(operationLedgerEvidenceRow(
        '回调',
        (callback.status || 'unknown') +
          ' / 收到 ' + (callback.receivedCount || 0) + ' 次' +
          (callback.receivedAt ? (' / ' + callback.receivedAt) : '')
      ));
      if (callback.message) rows.push(operationLedgerEvidenceRow('回调消息', callback.message));
    }
    if (workflow.schema) {
      rows.push(operationLedgerEvidenceRow(
        '工作流',
        (workflow.status || 'unknown') +
          ' / 排队 ' + (workflow.queuedCount || 0) +
          ' / 待确认 ' + (workflow.waitingConfirmationCount || 0) +
          ' / 阻断 ' + (workflow.blockedCount || 0)
      ));
      if (workflow.blockedStepIds && workflow.blockedStepIds.length) {
        rows.push(operationLedgerEvidenceRow('阻断步骤', workflow.blockedStepIds.join(', '), 'warn'));
      }
      if (workflow.waitingStepIds && workflow.waitingStepIds.length) {
        rows.push(operationLedgerEvidenceRow('待确认步骤', workflow.waitingStepIds.join(', ')));
      }
    }
    if (manualRelation.schema) {
      rows.push(operationLedgerEvidenceRow('关系对象', (manualRelation.fromObjectId || '') + ' -> ' + (manualRelation.toObjectId || '')));
      rows.push(operationLedgerEvidenceRow('关系类型', manualRelation.relation || 'related_to'));
      rows.push(operationLedgerEvidenceRow('关系标签', manualRelation.label || ''));
      if (manualRelation.note) rows.push(operationLedgerEvidenceRow('关系说明', manualRelation.note));
      rows.push(operationLedgerEvidenceRow('关系状态', manualRelation.status || evidence.status || 'unknown'));
    }
    if (operationChain.schema) {
      var operationPlan = operationChain.operationPlan || {};
      var dryRun = operationChain.dryRun || {};
      var nativeCommand = operationChain.nativeCommand || {};
      var nativeEventTimeline = operationChain.nativeEventTimeline || [];
      var nativeApply = operationChain.nativeApply || {};
      var rollback = operationChain.rollback || {};
      var residual = operationChain.residual || {};
      rows.push(operationLedgerEvidenceRow(
        '操作链',
        '计划 ' + (operationPlan.operationCount || 0) +
          ' / dry-run ' + (dryRun.status || 'unknown') +
          ' / path ' + (((dryRun.applyBoundary || {}).currentApplyPath) || '')
      ));
      if (nativeCommand.schema) {
        rows.push(operationLedgerEvidenceRow(
          '原生命令',
          (nativeCommand.nativeAction || 'native') +
            ' / queue ' + (nativeCommand.queueId || '未记录') +
            ' / 操作 ' + (nativeCommand.operationCount || 0)
        ));
      }
      if (nativeEventTimeline.length) {
        rows.push(operationLedgerEvidenceRow(
          '事件线',
          nativeEventTimeline.length + ' 个事件 / ' +
            (nativeEventTimeline[0].event || 'start') +
            ' -> ' +
            (nativeEventTimeline[nativeEventTimeline.length - 1].event || 'end')
        ));
      }
      if (nativeApply.schema) {
        rows.push(operationLedgerEvidenceRow(
          '原生执行',
          (nativeApply.nativeAction || 'native') +
            ' / 应用 ' + (nativeApply.appliedCount || 0) +
            ' / 失败 ' + (nativeApply.failedCount || 0) +
            ' / 创建 ' + ((nativeApply.createdNoteIds || []).length || 0),
          nativeApply.failedCount ? 'warn' : 'pass'
        ));
      }
      if (rollback.schema) {
        rows.push(operationLedgerEvidenceRow(
          '回滚',
          (rollback.status || 'unknown') +
            ' / 已删 ' + (rollback.deletedCount || 0) +
            ' / 失败 ' + (rollback.failedCount || 0) +
            (rollback.requiresConfirmation ? ' / 等待确认' : '')
        ));
      }
      if (residual.schema) {
        rows.push(operationLedgerEvidenceRow(
          '残留',
          '剩余 ' + (residual.remainingCount || 0) +
            ((residual.remainingNoteIds || []).length ? (' / ' + residual.remainingNoteIds.join(', ')) : ''),
          residual.remainingCount ? 'warn' : 'pass'
        ));
      }
    }
    panel.className = 'operation-ledger-detail-panel ready';
    title.textContent = entry.title || entry.ledgerId || 'Operation Ledger 详情';
    meta.textContent = 'ledgerId：' + (entry.ledgerId || '') + ' / updated：' + (entry.updatedAt || entry.createdAt || '');
    replaceElementChildren(evidenceTarget, rows);
  }

  function openOperationLedgerEntry(item) {
    item = item || {};
    var descriptor = item.ledgerAction || {};
    var payload = descriptor.payload || {};
    if (!payload.ledgerId) return;
    postCompanion('operation_ledger_get', payload, function(result) {
      if (!result || !result.ok) {
        addFailureMessage('读取 Operation Ledger 失败', result || {});
        return;
      }
      renderOperationLedgerDetail(result);
      switchWorkbenchPane('object');
    }, {showReply: false});
  }

  function renderOperationLedger(ledger) {
    if (arguments.length) state.operationLedger = ledger || {};
    ledger = state.operationLedger || {};
    var panel = byId('operationLedgerPanel');
    var summary = byId('operationLedgerSummary');
    var list = byId('operationLedgerList');
    if (!panel || !summary || !list) return;
    var objectRef = currentMnObjectRef();
    if (!objectRef.objectId) {
      panel.className = 'operation-ledger-panel idle';
      summary.textContent = '等待当前对象账本。';
      replaceElementChildren(list, [operationLedgerRow('等待', '刷新 Agent 计划后显示对象账本', '')]);
      return;
    }
    if (state.operationLedgerInFlight) {
      panel.className = 'operation-ledger-panel pending';
      summary.textContent = 'Operation Ledger：正在读取 ' + objectRef.objectId;
      return;
    }
    if (!ledger.ok) {
      panel.className = 'operation-ledger-panel idle';
      summary.textContent = 'Operation Ledger：尚未读取 / ' + objectRef.objectId;
      replaceElementChildren(list, [operationLedgerRow('等待', '点击刷新读取当前对象账本', '')]);
      return;
    }
    var counts = ledger.counts || {};
    var filters = ledger.filters || {};
    var filterLabels = [];
    if (filters.entryTypeFilter) filterLabels.push('类型=' + operationLedgerKindLabel(filters.entryTypeFilter));
    if (filters.statusFilter) filterLabels.push('状态=' + filters.statusFilter);
    if (filters.query) filterLabels.push('搜索=' + filters.query);
    var total = counts.total || 0;
    var unfilteredTotal = counts.unfilteredTotal;
    var totalLabel = typeof unfilteredTotal === 'number' && unfilteredTotal !== total
      ? (total + ' / ' + unfilteredTotal)
      : String(total);
    panel.className = 'operation-ledger-panel ready';
    summary.textContent =
      '总计 ' + totalLabel +
      ' / 工作流 ' + (counts.workflow_run || 0) +
      ' / 事务 ' + (counts.ai_edit_transaction || 0) +
      ' / 外部 ' + (counts.external_gateway_request || 0) +
      ' / 关系 ' + (counts.object_graph_manual_relation || 0) +
      (filterLabels.length ? (' / 筛选：' + filterLabels.join('，')) : '');
    var rows = [];
    var entries = ledger.entries || [];
    for (var i = 0; i < entries.length && rows.length < 8; i++) {
      rows.push(operationLedgerRow(
        operationLedgerKindLabel(entries[i].entryType),
        entries[i].title || entries[i].sourceId || entries[i].ledgerId || '账本项',
        entries[i].status || entries[i].updatedAt || '',
        entries[i]
      ));
    }
    if (!rows.length) rows.push(operationLedgerRow('空', '当前对象暂无 Operation Ledger', ''));
    replaceElementChildren(list, rows);
  }

  function refreshOperationLedger(manual, overridePayload) {
    var objectPayload = overridePayload || {};
    var objectRef = currentMnObjectRef();
    var objectId = objectPayload.mnObjectId || objectRef.objectId;
    if (!objectId || state.operationLedgerInFlight) {
      renderOperationLedger();
      return;
    }
    state.operationLedgerInFlight = true;
    renderOperationLedger();
    var ledgerPayload = Object.assign({}, objectPayload, {
      mnObjectId: objectPayload.mnObjectId || objectRef.objectId,
      mnObject: objectPayload.mnObject || objectRef,
      limit: objectPayload.limit || 8
    }, operationLedgerFilterPayload());
    postCompanion('operation_ledger_list', ledgerPayload, function(result) {
      state.operationLedgerInFlight = false;
      if (!result || !result.ok) {
        state.operationLedger = {ok: false, message: result && result.message ? result.message : 'Operation Ledger 读取失败。'};
        renderOperationLedger();
        if (manual) addFailureMessage('Operation Ledger 读取失败', result || {});
        return;
      }
      renderOperationLedger(result);
    }, {showReply: false});
  }

  function renderOperationWorkspaceActions(operation) {
    var target = byId('operationWorkspaceNextActions');
    if (!target) return;
    var actions = operation && operation.nextActions && operation.nextActions.length ? operation.nextActions.slice(0, 4) : defaultReplyAgentActions();
    var nodes = [];
    for (var i = 0; i < actions.length; i++) {
      (function(item, index) {
        item = item || {};
        var button = document.createElement('button');
        button.className = 'workbench-action-button' + (index === 0 ? ' primary' : '');
        button.type = 'button';
        button.textContent = item.label || actionLabel(item.action || '');
        button.setAttribute('data-operation-workbench-action', item.id || item.action || 'action');
        var gate = operationActionGate(item, operation || state.agentOperation || {});
        button.setAttribute('data-operation-gate-status', gate.status);
        if (gate.blocked) {
          button.disabled = true;
          button.className += ' blocked';
          button.title = gate.reason;
        }
        button.addEventListener('click', function(ev) {
          releaseButtonFocus(ev.currentTarget);
          if (gate.blocked) {
            addMessage('assistant', gate.reason);
            return;
          }
          runAgentNextAction(item, state.latestAssistantReply || promptValue());
        });
        nodes.push(button);
      })(actions[i], i);
    }
    replaceElementChildren(target, nodes);
  }

  function renderOperationWorkspaceVerification() {
    var status = state.mindmapDiffApply || {};
    var verification = status.verification || {};
    var summary = status.summary || verification.summary || '';
    if (!summary && !status.available) summary = '验证：等待操作结果';
    else summary = '验证：' + summary;
    setText('operationWorkspaceVerification', summary);
    renderMindmapStudioPanel();
  }

  function latestMindmapDiffOperationPanel() {
    var panels = document.querySelectorAll('.mindmap-diff-operation');
    if (!panels || !panels.length) return null;
    return panels[panels.length - 1];
  }

  function latestAiEditTransactionId() {
    var status = state.aiEditTransactionStatus || {};
    var latest = status.latest || {};
    var verification = status.verification || {};
    return String(latest.transactionId || verification.transactionId || '');
  }

  function mindmapStudioStage(stageId, stateName, text) {
    var stage = byId(stageId);
    if (!stage) return;
    stage.className = 'mindmap-studio-stage ' + (stateName || 'idle');
    var strong = stage.querySelector ? stage.querySelector('strong') : null;
    if (strong) strong.textContent = text || '';
  }

  function mindmapStudioStatusLine() {
    var tree = state.mindmapTreeCache || {};
    var diff = state.latestMindmapDiff || {};
    var apply = state.mindmapDiffApply || {};
    var tx = state.aiEditTransactionStatus || {};
    var parts = [];
    parts.push(tree.available ? ('树 ' + (tree.nodeCount || 0) + ' 节点') : '树未读取');
    parts.push(diff && diff.mindmapDiff ? 'Diff 已生成' : 'Diff 未生成');
    parts.push(apply.available ? ('验证 ' + (apply.status || (apply.verification && apply.verification.status) || 'unknown')) : '未执行');
    parts.push(latestAiEditTransactionId() ? '有事务' : '无事务');
    if (tx.summary) parts.push(clip(tx.summary, 80));
    return 'Mindmap Studio：' + parts.join(' / ');
  }

  function renderMindmapStudioPanel() {
    var panel = byId('mindmapStudioPanel');
    if (!panel) return;
    var tree = state.mindmapTreeCache || {};
    var diff = state.latestMindmapDiff || null;
    var apply = state.mindmapDiffApply || {};
    var txId = latestAiEditTransactionId();
    var diffSummary = diff && diff.mindmapDiff ? mindmapDiffSummaryLine(diff) : '等待预览';
    var treeTitle = tree.available ? clip(tree.rootTitle || tree.selectedNoteTitle || '当前脑图', 28) + ' / ' + (tree.nodeCount || 0) + ' 节点' : '未读取';
    var applyStatus = apply.available ? (apply.summary || (apply.verification && apply.verification.summary) || '已收到执行验证') : '等待执行';
    var txText = txId ? clip(txId, 32) : '暂无事务';
    var ready = tree.available || (diff && diff.mindmapDiff) || apply.available || txId;
    panel.className = 'mindmap-studio-panel ' + (ready ? 'ready' : 'idle');
    setText('mindmapStudioSummary', 'Mindmap Studio：读取现有脑图、预览 Diff、应用所选变更，并验证或回滚事务。');
    mindmapStudioStage('mindmapStudioCurrentTree', tree.available ? 'ready' : (String(tree.status || '') === 'pending' ? 'pending' : 'idle'), treeTitle);
    mindmapStudioStage('mindmapStudioDiffStage', diff && diff.mindmapDiff ? 'ready' : 'idle', diffSummary);
    mindmapStudioStage('mindmapStudioApplyStage', apply.available ? ((apply.status || (apply.verification && apply.verification.status)) === 'pass' ? 'ready' : 'pending') : 'idle', applyStatus);
    mindmapStudioStage('mindmapStudioTransactionStage', txId ? 'pending' : 'idle', txText);
    setText('mindmapStudioStatusLine', mindmapStudioStatusLine());
    var applyButton = byId('mindmapStudioApplySelectedButton');
    if (applyButton) applyButton.disabled = !latestMindmapDiffOperationPanel();
    var verifyButton = byId('mindmapStudioVerifyButton');
    if (verifyButton) verifyButton.disabled = !txId;
    var rollbackButton = byId('mindmapStudioRollbackButton');
    if (rollbackButton) rollbackButton.disabled = !txId;
  }

  function previewMindmapDiffFromStudio() {
    switchWorkspaceSurface('mindmap_studio');
    runAgentNextAction({action: 'mindmap_diff_preview', label: '预览脑图 Diff'}, state.latestAssistantReply || promptValue());
  }

  function applyMindmapStudioSelectedDiff() {
    switchWorkspaceSurface('mindmap_studio');
    var panel = latestMindmapDiffOperationPanel();
    if (!panel) {
      addMessage('assistant', '需要先生成脑图 Diff 预览，才能应用所选变更。');
      renderMindmapStudioPanel();
      return;
    }
    acceptMindmapDiff(panel);
    renderMindmapStudioPanel();
  }

  function verifyMindmapStudioTransaction() {
    var transactionId = latestAiEditTransactionId();
    if (!transactionId) {
      addMessage('assistant', '当前没有可验证的脑图事务。');
      return;
    }
    refreshAiEditTransactionVerification(transactionId);
  }

  function rollbackMindmapStudioTransaction() {
    var transactionId = latestAiEditTransactionId();
    if (!transactionId) {
      addMessage('assistant', '当前没有可回滚的脑图事务。');
      return;
    }
    rollbackAiEditTransaction(transactionId);
  }

  function agentBarClass(operation) {
    if (!operation) return 'agent-workbench-bar idle';
    var policy = operation.operationPolicy || {};
    var risk = policy.risk || {};
    var riskStatus = String(risk.status || '');
    if (riskStatus === 'blocked') return 'agent-workbench-bar blocked';
    if (riskStatus === 'write_pending_confirmation') return 'agent-workbench-bar warn';
    if (riskStatus === 'read_only') return 'agent-workbench-bar ready';
    return 'agent-workbench-bar pending';
  }

  function renderAgentWorkbench(operation) {
    if (arguments.length) state.agentOperation = operation || null;
    operation = state.agentOperation || null;
    var bar = byId('agentWorkbenchBar');
    if (!bar) return;
    var line = byId('agentWorkbenchLine');
    var detail = byId('agentWorkbenchDetail');
    if (!operation) {
      bar.className = 'agent-workbench-bar idle';
      setText('agentWorkbenchLine', 'Agent：等待当前对象');
      setText('agentWorkbenchDetail', '选区、卡片、脑图节点或文档会生成可审计操作计划。');
      renderWorkbenchPanels();
      return;
    }
    var object = operation.object || {};
    var intent = operation.intent || {};
    var workflow = operation.workflow || {};
    var contextPolicy = operation.contextPolicy || {};
    var knowledge = operation.knowledge || {};
    var policy = operation.operationPolicy || {};
    var risk = policy.risk || {};
    var objectTitle = object.title || agentObjectLabel(object.kind);
    var workflowTitle = workflow.title || intent.workflowTitle || intent.workflowId || '未匹配工作流';
    var riskLabel = agentRiskLabel(risk.status);
    bar.className = agentBarClass(operation);
    if (line) {
      line.textContent = 'Agent：' + agentObjectLabel(object.kind) + ' / ' + clip(objectTitle, 34) + ' / ' + clip(workflowTitle, 34);
    }
    if (detail) {
      detail.textContent =
        '上下文：' + (contextPolicy.visibleScope || 'auto') +
        ' / 风险：' + riskLabel +
        ' / 确认点：' + ((risk.confirmationPoints || []).length || 0) +
        ' / 知识索引：' + (knowledge.enabled ? ('启用 ' + (knowledge.count || 0)) : '未启用');
    }
    renderWorkbenchPanels();
  }

  function renderMindmapDiffApplyStatus(status) {
    if (arguments.length) state.mindmapDiffApply = status || {};
    status = state.mindmapDiffApply || {};
    var bar = byId('mindmapDiffApplyStatus');
    var text = byId('mindmapDiffApplyText');
    if (!bar || !text) return;
    var schema = String(status.schema || 'codex.mn.mindmapDiffApplyStatus.v1');
    var verification = status.verification || {};
    var operationVerification = verification.operationVerification || [];
    var failedVerificationCount = verification.failedVerificationCount || status.failedCount || 0;
    if (!status.available) {
      bar.className = 'mindmap-diff-apply-status idle hidden';
      text.textContent = '脑图验证：等待局部执行结果';
      renderOperationWorkspaceVerification();
      return;
    }
    var current = String(status.status || verification.status || 'unknown');
    var className = current === 'pass' ? 'pass' : (current === 'block' || failedVerificationCount ? 'block' : 'pending');
    bar.className = 'mindmap-diff-apply-status ' + className;
    text.textContent =
      '脑图验证：' + (status.summary || verification.summary || '已收到局部执行验证。') +
      ' / schema ' + schema +
      ' / 操作 ' + (operationVerification.length || status.appliedCount || 0) +
      ' / 失败 ' + failedVerificationCount;
    renderOperationWorkspaceVerification();
  }

  function aiEditTransactionActionAllowed(latest, verification, action) {
    latest = latest || {};
    verification = verification || {};
    var actions = latest.availableActions || verification.availableActions || [];
    if (actions && actions.length) {
      for (var i = 0; i < actions.length; i++) {
        if (String(actions[i]) === action) return true;
      }
      return false;
    }
    var status = String(latest.status || verification.transactionStatus || '');
    if (action === 'retain' || action === 'rollback') return status === 'ready' || status === 'pending_confirmation';
    if (action === 'confirm_delete' || action === 'dismiss') return status === 'delete_pending_confirmation';
    return action === 'verify' || action === 'evidence';
  }

  function makeAiEditTransactionActionButton(label, className, disabled, handler) {
    var button = document.createElement('button');
    button.className = className;
    button.type = 'button';
    button.textContent = label;
    button.disabled = !!disabled;
    button.addEventListener('click', function(ev) {
      releaseButtonFocus(ev.currentTarget);
      if (button.disabled) return;
      handler();
    });
    return button;
  }

  function renderAiEditTransactionActions(latest, verification) {
    var actions = byId('aiEditTransactionActions');
    if (!actions) return;
    latest = latest || {};
    verification = verification || {};
    var transactionId = String(latest.transactionId || verification.transactionId || '');
    var deleteMode = String(latest.status || verification.transactionStatus || '') === 'delete_pending_confirmation';
    var nodes = [
      deleteMode
        ? makeAiEditTransactionActionButton(
            '删除',
            'ai-edit-transaction-rollback',
            !transactionId || !aiEditTransactionActionAllowed(latest, verification, 'confirm_delete'),
            function() { confirmMindmapDeleteTransaction(transactionId); }
          )
        : makeAiEditTransactionActionButton(
            '保留',
            'ai-edit-transaction-retain',
            !transactionId || !aiEditTransactionActionAllowed(latest, verification, 'retain'),
            function() { retainAiEditTransaction(transactionId); }
          ),
      deleteMode
        ? makeAiEditTransactionActionButton(
            '忽略',
            'ai-edit-transaction-retain',
            !transactionId || !aiEditTransactionActionAllowed(latest, verification, 'dismiss'),
            function() { dismissMindmapDeleteTransaction(transactionId); }
          )
        : makeAiEditTransactionActionButton(
            '回滚',
            'ai-edit-transaction-rollback',
            !transactionId || !aiEditTransactionActionAllowed(latest, verification, 'rollback'),
            function() { rollbackAiEditTransaction(transactionId); }
          ),
      makeAiEditTransactionActionButton(
        '验证',
        'ai-edit-transaction-verify',
        !transactionId || !aiEditTransactionActionAllowed(latest, verification, 'verify'),
        function() { refreshAiEditTransactionVerification(transactionId); }
      ),
      makeAiEditTransactionActionButton(
        '证据',
        'ai-edit-transaction-evidence',
        !transactionId || !aiEditTransactionActionAllowed(latest, verification, 'evidence'),
        function() { showAiEditTransactionEvidence(transactionId); }
      )
    ];
    var nextActions = Array.isArray(verification.nextActions) ? verification.nextActions : [];
    for (var i = 0; i < nextActions.length; i++) {
      var nextAction = nextActions[i] || {};
      if (
        String(nextAction.id || '') === 'request_object_existence_probe' ||
        String(nextAction.action || '') === 'request_mn_object_existence_probe'
      ) {
        var noteIds = Array.isArray(nextAction.noteIds)
          ? nextAction.noteIds
          : (verification.remainingNoteIds || verification.createdNoteIds || latest.createdNoteIds || []);
        nodes.push(
          makeAiEditTransactionActionButton(
            '检查真实对象',
            'ai-edit-transaction-probe',
            !transactionId,
            (function(capturedNoteIds) {
              return function() { requestAiEditObjectExistenceProbe(transactionId, capturedNoteIds); };
            })(noteIds)
          )
        );
      }
    }
    replaceElementChildren(actions, nodes);
  }

  function retainAiEditTransaction(transactionId) {
    transactionId = String(transactionId || '');
    if (!transactionId) return;
    setText('aiEditTransactionSummary', '已发送保留确认：' + transactionId + '。等待 MN4 返回事务结果。');
    bridgeAiEditTransactionWithEvidence('accept_ai_edit_transaction', transactionId);
  }

  function rollbackAiEditTransaction(transactionId) {
    transactionId = String(transactionId || '');
    if (!transactionId) return;
    setText('aiEditTransactionSummary', '正在回滚事务：' + transactionId + '。MN4 会删除本次新增节点并返回残留验证。');
    bridgeAiEditTransactionWithEvidence('reject_ai_edit_transaction', transactionId);
  }

  function confirmMindmapDeleteTransaction(transactionId) {
    transactionId = String(transactionId || '');
    if (!transactionId) return;
    setText('aiEditTransactionSummary', '正在确认删除建议：' + transactionId + '。MN4 只会删除事务列出的目标节点。');
    bridgeAiEditTransactionWithEvidence('confirm_mindmap_delete_transaction', transactionId);
  }

  function dismissMindmapDeleteTransaction(transactionId) {
    transactionId = String(transactionId || '');
    if (!transactionId) return;
    setText('aiEditTransactionSummary', '已请求忽略删除建议：' + transactionId + '。不会删除现有脑图节点。');
    bridgeAiEditTransactionWithEvidence('dismiss_mindmap_delete_transaction', transactionId);
  }

  function bridgeAiEditTransactionWithEvidence(path, transactionId) {
    transactionId = String(transactionId || '');
    if (!transactionId) return;
    postCompanion('ai_edit_transaction_get', {transactionId: transactionId}, function(result) {
      var tx = result && result.ok ? (result.transaction || {}) : {};
      var objectRef = tx.objectRef || {};
      var sourceRef = objectRef.sourceRef || {};
      var payload = {
        transactionId: transactionId,
        createdNoteIds: (tx.createdNoteIds || []).join('|'),
        targetNoteIds: (tx.targetNoteIds || []).join('|'),
        topicid: tx.topicid || '',
        bookmd5: tx.bookmd5 || '',
        draftId: tx.draftId || '',
        mnObjectId: objectRef.objectId || '',
        mnObjectKind: objectRef.kind || '',
        mnObjectTitle: objectRef.title || '',
        mnObjectSourcePage: sourceRef.page === null || sourceRef.page === undefined ? '' : sourceRef.page,
        mnObjectSourceQuote: sourceRef.quote || '',
        mnObjectSourceDocumentTitle: sourceRef.documentTitle || '',
        mnObjectSourcePath: sourceRef.path || ''
      };
      bridge(path, payload);
    }, {showReply: false});
  }

  function refreshAiEditTransactionVerification(transactionId) {
    transactionId = String(transactionId || '');
    if (!transactionId) return;
    setText('aiEditTransactionSummary', '正在刷新事务验证：' + transactionId + '。');
    postCompanion('ai_edit_transaction_verify', {transactionId: transactionId}, function(result) {
      if (!result || !result.ok) {
        addFailureMessage('刷新事务验证失败', result || {});
        return;
      }
      var current = state.aiEditTransactionStatus || {};
      renderAiEditTransactionCenter({
        schema: current.schema || 'codex.mn.aiEditTransactionStatus.v1',
        available: true,
        summary: result.reply || result.message || '已刷新事务验证。',
        latest: result.transaction || current.latest || {},
        verification: result.verification || current.verification || {}
      });
    }, {showReply: false});
  }

  function requestAiEditObjectExistenceProbe(transactionId, noteIds) {
    transactionId = String(transactionId || '');
    if (!transactionId) return;
    noteIds = Array.isArray(noteIds) ? noteIds.filter(function(item) { return !!item; }) : [];
    setText('aiEditTransactionSummary', '正在请求 MN4 检查真实对象：' + transactionId + '。');
    postCompanion('request_mn_object_existence_probe', {
      transactionId: transactionId,
      noteIds: noteIds
    }, function(result) {
      if (!result || !result.ok) {
        addFailureMessage('请求真实对象检查失败', result || {});
        return;
      }
      addMessage('assistant', result.reply || result.message || '已请求 MN4 检查真实对象。');
      refreshAiEditTransactionVerification(transactionId);
    }, {showReply: false});
  }

  function showAiEditTransactionEvidence(transactionId) {
    transactionId = String(transactionId || '');
    if (!transactionId) return;
    postCompanion('ai_edit_transaction_get', {transactionId: transactionId}, function(result) {
      if (!result || !result.ok) {
        addFailureMessage('读取事务证据失败', result || {});
        return;
      }
      var tx = result.transaction || {};
      var diff = tx.mindmapDiffApply || {};
      var verification = diff.verification || {};
      addMessage('assistant',
        '事务证据：' + (tx.transactionId || transactionId) +
        '\n状态：' + (tx.status || '') +
        '\n创建：' + ((tx.createdNoteIds || []).join('、') || '无') +
        '\n应用：' + ((tx.appliedNoteIds || []).join('、') || '无') +
        '\n失败：' + (tx.failedCount || 0) +
        '\n验证：' + (verification.summary || tx.message || '无验证摘要')
      );
    }, {showReply: false});
  }

  function renderAiEditTransactionResidualProof(proof) {
    var container = byId('aiEditTransactionResidualProof');
    if (!container) return;
    proof = proof || {};
    var schema = String(proof.schema || '');
    var status = String(proof.status || 'idle');
    var objects = Array.isArray(proof.objects) ? proof.objects : [];
    var rows = [];
    container.className = 'ai-edit-residual-proof ' + (status === 'pass' ? 'pass' : (status === 'block' ? 'block' : 'pending'));
    if (schema !== 'codex.mn.residualProof.v1' || !objects.length) {
      var empty = document.createElement('div');
      empty.className = 'ai-edit-residual-object empty';
      empty.textContent = proof.summary || '逐对象残留证明：暂无可验证对象。';
      replaceElementChildren(container, [empty]);
      return;
    }
    var title = document.createElement('div');
    title.className = 'ai-edit-residual-title';
    title.textContent =
      '逐对象残留证明：' +
      (proof.remainingCount || 0) + '/' + objects.length + ' 残留' +
      (proof.sourceFields && proof.sourceFields.length ? (' / 来源 ' + proof.sourceFields.join('、')) : '');
    rows.push(title);
    for (var i = 0; i < objects.length && i < 10; i++) {
      var item = objects[i] || {};
      var row = document.createElement('div');
      var residual = !!item.residual;
      row.className = 'ai-edit-residual-object ' + (residual ? 'residual' : 'clear');
      row.setAttribute('data-note-id', String(item.noteId || ''));
      row.setAttribute('data-actual-state', String(item.actualState || ''));
      row.setAttribute('data-expected-state', String(item.expectedState || ''));
      row.setAttribute('data-verification-level', String(item.verificationLevel || ''));
      var state = document.createElement('strong');
      state.textContent = residual ? '残留' : '已处理';
      var body = document.createElement('span');
      body.textContent =
        'noteId ' + (item.noteId || '未知') +
        ' / 期望 ' + (item.expectedState || 'unknown') +
        ' / 实际 ' + (item.actualState || 'unknown') +
        ' / 证据 ' + (item.verificationLevel || 'unknown');
      row.appendChild(state);
      row.appendChild(body);
      rows.push(row);
    }
    if (objects.length > 10) {
      var more = document.createElement('div');
      more.className = 'ai-edit-residual-object empty';
      more.textContent = '还有 ' + (objects.length - 10) + ' 个对象未展开。';
      rows.push(more);
    }
    replaceElementChildren(container, rows);
  }

  function renderAiEditTransactionCenter(status) {
    if (arguments.length) state.aiEditTransactionStatus = status || {};
    status = state.aiEditTransactionStatus || {};
    var panel = byId('aiEditTransactionCenter');
    var notes = byId('aiEditTransactionNotes');
    if (!panel || !notes) return;
    var schema = String(status.schema || 'codex.mn.aiEditTransactionStatus.v1');
    var latest = status.latest || {};
    var verification = status.verification || {};
    if (!status.available) {
      panel.className = 'ai-edit-transaction-center idle';
      panel.setAttribute('data-transaction-state', 'idle');
      setText('aiEditTransactionTitle', '事务中心');
      setText('aiEditTransactionSummary', status.summary || '暂无 AI 编辑事务。');
      var empty = document.createElement('div');
      empty.className = 'ai-edit-transaction-note empty';
      empty.textContent = '接受或拒绝 AI 编辑后，这里会显示回滚状态、残留 noteId 和最近事务摘要。';
      replaceElementChildren(notes, [empty]);
      renderAiEditTransactionResidualProof({});
      renderAiEditTransactionActions({}, {});
      renderMindmapStudioPanel();
      return;
    }
    var verificationStatus = String(verification.status || 'pending');
    var transactionStatus = String(latest.status || verification.transactionStatus || 'unknown');
    var objectRef = latest.objectRef || verification.objectRef || {};
    var mnObjectId = objectRef.objectId || '';
    var className = verificationStatus === 'pass' ? 'pass' : (verificationStatus === 'block' ? 'block' : 'pending');
    panel.className = 'ai-edit-transaction-center ' + className;
    panel.setAttribute('data-transaction-state', transactionStatus);
    panel.setAttribute('data-transaction-id', String(latest.transactionId || verification.transactionId || ''));
    setText(
      'aiEditTransactionTitle',
      '事务中心 / ' + (latest.transactionId || verification.transactionId || '最近事务')
    );
    setText(
      'aiEditTransactionSummary',
      (status.summary || verification.summary || '已读取最近 AI 编辑事务。') +
      ' / schema ' + schema +
      ' / 创建 ' + (verification.createdCount || latest.createdCount || 0) +
      ' / 删除 ' + (verification.deletedCount || latest.deletedCount || 0) +
      ' / 残留 ' + (verification.remainingCount || 0)
    );
    var ids = verification.remainingNoteIds && verification.remainingNoteIds.length
      ? verification.remainingNoteIds
      : latest.createdNoteIds && latest.createdNoteIds.length
      ? latest.createdNoteIds
      : verification.createdNoteIds && verification.createdNoteIds.length
      ? verification.createdNoteIds
      : [];
    var rows = [];
    if (mnObjectId || objectRef.kind || objectRef.title) {
      var objectRow = document.createElement('div');
      objectRow.className = 'ai-edit-transaction-note object-ref';
      objectRow.textContent = '事务对象：' +
        (objectRef.kind || 'object') +
        ' / ' + clip(objectRef.title || mnObjectId, 52) +
        (mnObjectId ? (' / ' + mnObjectId) : '');
      objectRow.setAttribute('data-mn-object-id', String(mnObjectId || ''));
      rows.push(objectRow);
    }
    for (var i = 0; i < ids.length && i < 8; i++) {
      var row = document.createElement('div');
      row.className = 'ai-edit-transaction-note';
      row.textContent = (verification.remainingNoteIds && verification.remainingNoteIds.length ? '残留 noteId：' : '创建 noteId：') + ids[i];
      row.setAttribute('data-note-id', String(ids[i]));
      rows.push(row);
    }
    if (!rows.length) {
      var summary = document.createElement('div');
      summary.className = 'ai-edit-transaction-note empty';
      summary.textContent = '本次事务没有可列出的 noteId。状态：' + transactionStatus;
      rows.push(summary);
    }
    if (ids.length > rows.length) {
      var more = document.createElement('div');
      more.className = 'ai-edit-transaction-note empty';
      more.textContent = '还有 ' + (ids.length - rows.length) + ' 个 noteId 未展开。';
      rows.push(more);
    }
    replaceElementChildren(notes, rows);
    renderAiEditTransactionResidualProof(verification.residualProof || {});
    renderAiEditTransactionActions(latest, verification);
    renderMindmapStudioPanel();
  }

  function renderMindmapTreeCacheStatus(status) {
    if (arguments.length) state.mindmapTreeCache = status || {};
    status = state.mindmapTreeCache || {};
    var bar = byId('mindmapTreeCacheStatus');
    var text = byId('mindmapTreeCacheText');
    if (!bar || !text) return;
    if (!status.available) {
      var pending = String(status.status || '') === 'pending';
      bar.className = 'mindmap-tree-cache-status ' + (pending ? 'pending' : 'idle');
      text.textContent = pending ? '当前脑图树：正在请求读取' : '当前脑图树：未读取';
      renderMindmapTreePreview(status);
      renderMindmapStudioPanel();
      return;
    }
    var nodeCount = status.nodeCount || 0;
    var truncated = status.truncatedCount || 0;
    var title = status.rootTitle || status.selectedNoteTitle || '当前脑图';
    bar.className = truncated ? 'mindmap-tree-cache-status pending' : 'mindmap-tree-cache-status ready';
    text.textContent = '当前脑图树：' + clip(title, 34) + ' / ' + nodeCount + ' 节点' + (truncated ? (' / 截断 ' + truncated) : '');
    renderMindmapTreePreview(status);
    renderMindmapStudioPanel();
  }

  function renderMindmapTreePreview(status) {
    status = status || state.mindmapTreeCache || {};
    var target = byId('mindmapTreePreviewList');
    if (!target) return;
    var preview = status.treePreview && status.treePreview.length ? status.treePreview : [];
    if (!preview.length) {
      var empty = document.createElement('div');
      empty.className = 'workbench-empty';
      empty.textContent = status.available ? '当前脑图树没有可显示节点。' : '点击“读取当前脑图”后显示树预览。';
      replaceElementChildren(target, [empty]);
      return;
    }
    var nodes = [];
    for (var i = 0; i < preview.length && i < 24; i++) {
      var item = preview[i] || {};
      var row = document.createElement('div');
      var depth = Math.max(0, Math.min(2, Number(item.depth || 0)));
      row.className = 'mindmap-tree-preview-node';
      row.setAttribute('data-depth', String(depth));
      row.textContent = Array(depth + 1).join('  ') + (item.title || '未命名节点') + (item.childCount ? (' · ' + item.childCount + ' 子节点') : '');
      if (item.noteId) row.setAttribute('data-note-id', String(item.noteId));
      nodes.push(row);
    }
    if (status.treePreviewTruncated) {
      var more = document.createElement('div');
      more.className = 'workbench-empty';
      more.textContent = '预览已截断，只显示前 ' + nodes.length + ' 个节点。';
      nodes.push(more);
    }
    replaceElementChildren(target, nodes);
  }

  function requestMindmapTreeRead() {
    var button = byId('mindmapTreeRefreshButton');
    if (button) button.disabled = true;
    renderMindmapTreeCacheStatus({
      schema: 'codex.mn.mindmapTreeCache.v1',
      available: false,
      status: 'pending',
      summary: '正在请求 MN4 读取当前脑图树。',
      treePreview: []
    });
    postCompanion('mn_read_tree', {
      mindmapTarget: state.mindmapTarget && state.mindmapTarget.target ? state.mindmapTarget.target : {}
    }, function(result) {
      if (button) button.disabled = false;
      renderControls(result || {});
      if (!result || !result.ok) addFailureMessage('读取当前脑图失败', result);
    }, {showReply: false});
  }

  function agentPlanRefreshKey(extraPrompt) {
    var ctx = state.context || {};
    var target = state.mindmapTarget && state.mindmapTarget.target ? state.mindmapTarget.target : {};
    return [
      currentContextScope(),
      trimText(extraPrompt || '', 180),
      ctx.topicid || ctx.notebookid || '',
      ctx.bookmd5 || ctx.docmd5 || '',
      ctx.documentTitle || '',
      ctx.selectionText || ctx.selectedText || ctx.activeSelectionText || '',
      ctx.selectedNoteId || ctx.noteId || ctx.noteid || '',
      ctx.selectedNoteTitle || '',
      target.mode || '',
      target.label || target.rootTitle || target.selectedNoteTitle || ''
    ].join('|').substring(0, 1600);
  }

  function postCompanionAgentPlan(extra, done) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', 'http://127.0.0.1:48761/marginnote/action', true);
    xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    xhr.onreadystatechange = function() {
      if (xhr.readyState !== 4) return;
      var result = parseCompanionResult(xhr);
      if (done) done(result || {});
    };
    xhr.onerror = function() {
      if (done) done(companionConnectionFailureResult());
    };
    xhr.send(JSON.stringify(companionPayload('agent_plan', extra || {})));
  }

  function formatAgentPlanMessage(operation) {
    operation = operation || state.agentOperation || {};
    var object = operation.object || {};
    var workflow = operation.workflow || {};
    var policy = operation.operationPolicy || {};
    var risk = policy.risk || {};
    var actions = operation.nextActions || [];
    var lines = [
      'Agent 操作计划',
      '对象：' + agentObjectLabel(object.kind) + ' / ' + (object.title || ''),
      '工作流：' + (workflow.title || workflow.id || '未匹配'),
      '写入风险：' + agentRiskLabel(risk.status),
      'Dry-run：' + (risk.dryRunStatus || 'not_available')
    ];
    if (actions.length) {
      lines.push('下一步：' + actions.slice(0, 3).map(function(item) {
        return item.label || item.id || item.action;
      }).join(' / '));
    }
    return lines.join('\n');
  }

  function refreshAgentPlan(manual) {
    if (state.agentPlanInFlight) return;
    var prompt = promptValue() || state.latestAssistantReply || state.lastPromptFromSelection || '';
    var hasAnyContext = !!(
      compactText(prompt) ||
      compactText((state.context || {}).selectionText) ||
      compactText((state.context || {}).selectedNoteTitle) ||
      compactText((state.context || {}).documentTitle) ||
      compactText((state.context || {}).bookmd5 || (state.context || {}).docmd5)
    );
    if (!manual && !hasAnyContext) {
      renderAgentWorkbench(null);
      return;
    }
    var key = agentPlanRefreshKey(prompt);
    if (!manual && key && key === state.agentPlanLastKey) return;
    state.agentPlanLastKey = key;
    state.agentPlanInFlight = true;
    if (manual) {
      var bar = byId('agentWorkbenchBar');
      if (bar) bar.className = 'agent-workbench-bar pending';
      setText('agentWorkbenchLine', 'Agent：正在生成操作计划');
      setText('agentWorkbenchDetail', '正在检查当前对象、工作流、写入风险和确认点。');
    }
    postCompanionAgentPlan({prompt: prompt}, function(result) {
      state.agentPlanInFlight = false;
      if (!result || !result.ok || !result.agentOperation) {
        var bar = byId('agentWorkbenchBar');
        if (bar) bar.className = 'agent-workbench-bar error';
        setText('agentWorkbenchLine', 'Agent：计划刷新失败');
        setText('agentWorkbenchDetail', result && result.message ? result.message : 'Companion 未返回 Agent 操作计划。');
        if (manual) addFailureMessage('Agent 计划失败', result);
        return;
      }
      renderAgentWorkbench(result.agentOperation);
      if (manual) addMessage('assistant', formatAgentPlanMessage(result.agentOperation));
    });
  }

  function scheduleAgentPlanRefresh() {
    if (state.agentPlanRefreshTimer) window.clearTimeout(state.agentPlanRefreshTimer);
    state.agentPlanRefreshTimer = window.setTimeout(function() {
      state.agentPlanRefreshTimer = null;
      refreshAgentPlan(false);
    }, 450);
  }

  function setWebRunLock(active) {
    postCompanionSilent('web_busy_update', {busy: !!active});
  }

  function ackQueuedCommands(ids, done) {
    ids = ids || [];
    if (!ids.length) {
      if (done) done({ok: true});
      return;
    }
    postCompanionPath('/marginnote/ack', 'ack', {ids: ids}, done);
  }

  function ackQueueAndContinue(queueId) {
    if (queueId && state.currentQueueId === queueId) state.currentQueueId = '';
    if (queueId) {
      ackQueuedCommands([queueId], function() {
        refreshQueue();
        drainNextQueuedAction();
      });
    } else {
      refreshQueue();
      drainNextQueuedAction();
    }
  }

  function ackAndSkipQueuedCommand(command, reason) {
    command = command || {};
    var queueId = command._queue_id || '';
    addMessage('assistant', '已跳过异常队列项：' + (reason || '无法执行') + '。');
    ackQueueAndContinue(queueId);
  }

  function deferNativeQueuedCommand(command) {
    command = command || {};
    var nativeAction = command.nativeAction || '';
    if (!nativeAction) return false;
    var labels = {
      highlight_current_selection: '高亮下一次 PDF 选区',
      probe_native_api_capabilities: '刷新 MN 原生能力',
      cache_pdf_from_current_document: '缓存当前 PDF'
    };
    var queueId = command._queue_id || '';
    var dedupeKey = queueId || nativeAction;
    var label = labels[nativeAction] || nativeAction;
    window.CodexPanel.setStatus({text: '等待 MarginNote 原生处理：' + label});
    if (nativeAction === 'cache_pdf_from_current_document') {
      renderPdfCacheBanner({
        state: 'waiting_native',
        label: 'PDF缓存：等待 MN4 缓存',
        detail: '保持当前 PDF 打开，MN4 插件会读取并上传到 Companion 缓存。',
        pending: true,
        queueId: queueId
      });
    }
    if (!state.deferredNativeQueueIds[dedupeKey]) {
      state.deferredNativeQueueIds[dedupeKey] = true;
      addMessage(
        'assistant',
        '等待 MarginNote 原生处理：' + label + '。保持当前 notebook/PDF 打开；MN4 插件原生轮询会执行并 ack 这条命令。'
      );
    }
    window.setTimeout(function() {
      refreshQueue();
      drainNextQueuedAction();
    }, 2500);
    return true;
  }

  function runQueuedCommand(command) {
    command = command || {};
    if (!command._queue_id && !command.rawAction && !command.action && !command.nativeAction) {
      ackAndSkipQueuedCommand(command, '队列缺少动作');
      return;
    }
    if (command.nativeAction) {
      deferNativeQueuedCommand(command);
      return;
    }
    var rawAction = command.rawAction || command.action || '';
    var queueId = command._queue_id || '';
    var prompt = command.prompt || '';
    if (command.contextScope) {
      setContextScope(command.contextScope);
    }
    if (!rawAction) {
      ackAndSkipQueuedCommand(command, '队列缺少动作');
      return;
    }
    if (!isQueueableGoalAction(rawAction) && rawAction !== 'health') {
      ackAndSkipQueuedCommand(command, '无法识别队列动作');
      return;
    }
    if (rawAction === 'goal_run') {
      requestGoalAction(prompt, '[队列执行] 目标', queueId);
      return;
    }
    if (isWriteAction(rawAction)) {
      requestDraftAction(rawAction, prompt, '[队列执行] ' + actionLabel(rawAction), queueId);
      return;
    }
    requestTextAction(rawAction, prompt, '[队列执行] ' + actionLabel(rawAction), queueId);
  }

  function drainNextQueuedAction() {
    if (isActiveRun() || state.drainingQueue) return;
    var ctx = state.context || {};
    var topic = encodeURIComponent(ctx.topicid || ctx.notebookid || '');
    var book = encodeURIComponent(ctx.bookmd5 || ctx.docmd5 || '');
    if (!topic) return;
    state.drainingQueue = true;
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'http://127.0.0.1:48761/marginnote/poll?topicid=' + topic + '&bookmd5=' + book, true);
    xhr.onreadystatechange = function() {
      if (xhr.readyState !== 4) return;
      state.drainingQueue = false;
      var result = null;
      try {
        result = JSON.parse(xhr.responseText || '{}');
      } catch (err) {
        return;
      }
      var command = result.command || null;
      if (!command && result.commands && result.commands.length) command = result.commands[0];
      if (result.blocked === 'web_busy') {
        window.setTimeout(drainNextQueuedAction, 700);
        return;
      }
      if (!command || result.blocked) return;
      runQueuedCommand(command);
    };
    xhr.onerror = function() {
      state.drainingQueue = false;
    };
    xhr.send();
  }

  function requestTextAction(action, prompt, userText, queueId) {
    state.currentQueueId = queueId || '';
    addMessage('user', userText || '[' + action + ']');
    setWebRunLock(true);
    window.CodexPanel.setBusy({busy: true});
    window.CodexPanel.setStatus({text: '正在执行：' + actionLabel(action)});
    var requestId = newRequestId();
    startProgress(action, '正在询问 Codex', 'Web 面板正在直接调用本地 Companion，不再经过 MN4 原生请求层。', requestId);
    postCompanion(action, {prompt: prompt, _web_run_owner: true, _request_id: requestId}, function(result) {
      setWebRunLock(false);
      window.CodexPanel.setBusy({busy: false});
      renderControls(result || {});
      if (!result || !result.ok) {
        finishProgressStage('失败', result && result.message ? result.message : '动作失败。');
        addFailureMessage('队列任务执行失败', result);
        ackQueueAndContinue(queueId);
        return;
      }
      if (result.queued_due_to_web_busy) {
        finishProgressStage('已加入队列', result.message || '上一个任务仍在运行，本次请求已加入队列。');
        if (queueId) {
          ackQueueAndContinue(queueId);
          return;
        }
        refreshQueue();
        return;
      }
      reportActionResponse(action, result || {});
      finishProgressStage('已完成', result.message || result.reply || '动作已完成。');
      ackQueueAndContinue(queueId);
    });
  }

  function promptValue() {
    var input = byId('promptInput');
    return input ? input.value : '';
  }

  function clearPromptInputAfterSend() {
    setValue('promptInput', '');
    releaseTextInputFocus('promptInput');
  }

  function actionLabel(action) {
    var labels = {
      chat: '问 Codex',
      explain_selection: '解释选中',
      generate_card: '生成卡片',
      generate_mindmap: '新建脑图',
      mindmap_diff_preview: '预览脑图 Diff',
      expand_node: '补脑图',
      reorganize_mindmap: '重组脑图',
      generate_full_reading: '完整精读',
      goal_run: '一次性目标',
      diagnose_highlights: '高亮状态',
      request_native_highlight_selection: '高亮下一选区',
      diagnose_permissions: '检查权限',
      open_full_disk_access_settings: '打开权限设置',
      single_document_acceptance_summary: '本文档验收',
      release_acceptance_summary: '发布验收',
      export_annotated_pdf: '导出PDF',
      health: '检查连接'
    };
    return labels[action] || action;
  }

  function isAllowedPromptAction(action) {
    return action === 'chat' ||
      action === 'explain_selection' ||
      action === 'generate_card' ||
      action === 'generate_mindmap' ||
      action === 'expand_node' ||
      action === 'reorganize_mindmap' ||
      action === 'generate_full_reading' ||
      action === 'request_native_highlight_selection';
  }

  function isWriteAction(action) {
    return action === 'generate_card' ||
      action === 'generate_mindmap' ||
      action === 'expand_node' ||
      action === 'reorganize_mindmap' ||
      action === 'generate_full_reading';
  }

  function isQueueableGoalAction(action) {
    return action === 'goal_run' ||
      isAllowedPromptAction(action) ||
      action === 'diagnose_highlights' ||
      action === 'export_annotated_pdf';
  }

  function isMindmapPromptIntent(text) {
    var value = String(text || '').replace(/^\s+|\s+$/g, '');
    var lower = value.toLowerCase();
    if (!/(脑图|mindmap|mind map)/i.test(value)) return false;
    var imperative = /(请|帮我|把|将|给我|直接|需要|我要|生成|创建|做|整理成|转成|补到|补进|补充到|补充进|追加|加到|接到|并入|合并|merge|append)/.test(value) ||
      /^(生成|创建|做|整理成|转成|补到|补进|补充|追加|加到|接到|并入|合并|merge|append)/i.test(value);
    var questionOnly = /(为什么|为何|为啥|怎么回事|什么原因)/.test(value);
    if (questionOnly && !imperative) return false;
    return imperative || /(generate|create|merge|append).*(mindmap|mind map)/i.test(lower);
  }

  function isExpandNodePromptIntent(text) {
    var value = String(text || '').replace(/^\s+|\s+$/g, '');
    return /(展开|扩展|继续展开|补充展开|延展).*(当前节点|这个节点|选中节点|节点|node)/i.test(value) ||
      /(补到|补进|补充到|追加到|加到|接到|并入|合并到).*(当前脑图|现在脑图|这个脑图|选中脑图|当前节点|这个节点|选中节点|脑图节点|mindmap|node)/i.test(value) ||
      /(当前脑图|现在脑图|这个脑图|选中脑图|当前节点|这个节点|选中节点|脑图节点).*(补到|补进|补充|追加|加到|接到|并入|合并到)/i.test(value) ||
      /(expand|extend).*(current\s*)?(node|mindmap node)/i.test(value);
  }

  function isReorganizeMindmapPromptIntent(text) {
    var value = String(text || '').replace(/^\s+|\s+$/g, '');
    return /(重组|重排|重新组织|整理|归类|结构化).*(当前脑图|这个脑图|选中节点|当前节点|脑图|mindmap|node)/i.test(value) ||
      /(reorganize|restructure|regroup).*(mindmap|node)/i.test(value);
  }

  function isCardPromptIntent(text) {
    var value = String(text || '').replace(/^\s+|\s+$/g, '');
    if (!/(卡片|制卡|笔记卡|card)/i.test(value)) return false;
    return /(生成卡片|做卡片|制卡|整理成卡片|转成卡片|生成.*card|create.*card)/i.test(value);
  }

  function isFullReadingPromptIntent(text) {
    var value = String(text || '').replace(/^\s+|\s+$/g, '');
    return /(完整精读|全文精读|整篇精读|深度精读|完整讲解|full reading|full-reading)/i.test(value);
  }

  function isHighlightDiagnosticPromptIntent(text) {
    var value = String(text || '').replace(/^\s+|\s+$/g, '');
    if (!/高亮|highlight/i.test(value)) return false;
    if (/(导出|export|pdf)/i.test(value)) return false;
    return /(高亮状态|检查高亮|诊断高亮|高亮诊断|没有高亮|看不见高亮|为什么.*高亮|高亮.*状态|highlight.*status|diagnose.*highlight|check.*highlight)/i.test(value);
  }

  function isNativeHighlightPromptIntent(text) {
    var value = String(text || '').replace(/^\s+|\s+$/g, '');
    if (!/高亮|下划线|划线|标亮|标注|highlight|underline/i.test(value)) return false;
    if (/(状态|检查|诊断|为什么|看不见|导出|export|pdf)/i.test(value)) return false;
    return /(高亮当前|高亮选区|把.*高亮|给.*高亮|标出原文|画高亮|画下划线|加下划线|划线当前|highlight.*selection|highlight.*current|underline.*selection)/i.test(value);
  }

  function isAnnotatedPdfExportPromptIntent(text) {
    var value = String(text || '').replace(/^\s+|\s+$/g, '');
    return /(导出标注|导出.*pdf|导出.*PDF|标注.*pdf|标注.*PDF|annotated.*pdf|export.*pdf)/i.test(value);
  }

  function routeNaturalLanguageAction(action, prompt) {
    if (action !== 'chat') return action;
    if (isAnnotatedPdfExportPromptIntent(prompt)) return 'export_annotated_pdf';
    if (isNativeHighlightPromptIntent(prompt)) return 'request_native_highlight_selection';
    if (isHighlightDiagnosticPromptIntent(prompt)) return 'diagnose_highlights';
    if (isReorganizeMindmapPromptIntent(prompt)) return 'reorganize_mindmap';
    if (isExpandNodePromptIntent(prompt)) return 'expand_node';
    if (isFullReadingPromptIntent(prompt)) return 'generate_full_reading';
    if (isCardPromptIntent(prompt)) return 'generate_card';
    if (isMindmapPromptIntent(prompt)) return 'generate_mindmap';
    return action;
  }

  function compactText(text) {
    return String(text || '').replace(/^\s+|\s+$/g, '');
  }

  function looksLikePdfMathUnicodeLoss(text) {
    text = String(text || '');
    if (!/[\uD400-\uD7A3]/.test(text)) return false;
    return /[\u0302∇√⋅∣−=+()]/.test(text) ||
      text.indexOf('log') >= 0 ||
      /[A-Za-z0-9][\uD400-\uD7A3]|[\uD400-\uD7A3][A-Za-z0-9]/.test(text);
  }

  function stringFromCodePointSafe(codePoint) {
    if (String.fromCodePoint) return String.fromCodePoint(codePoint);
    var value = codePoint - 0x10000;
    return String.fromCharCode(0xD800 + (value >> 10), 0xDC00 + (value & 1023));
  }

  function codePointChars(text) {
    text = String(text || '');
    var chars = [];
    for (var i = 0; i < text.length; i++) {
      var first = text.charCodeAt(i);
      if (first >= 0xD800 && first <= 0xDBFF && i + 1 < text.length) {
        var second = text.charCodeAt(i + 1);
        if (second >= 0xDC00 && second <= 0xDFFF) {
          chars.push(text.charAt(i) + text.charAt(i + 1));
          i += 1;
          continue;
        }
      }
      chars.push(text.charAt(i));
    }
    return chars;
  }

  function moveLeadingCombiningHat(text) {
    var chars = codePointChars(text);
    var out = [];
    for (var i = 0; i < chars.length; i++) {
      if (chars[i] === '\u0302') {
        var j = i + 1;
        while (j < chars.length && /^\s$/.test(chars[j])) j += 1;
        if (j < chars.length) {
          out.push(chars[j]);
          out.push('\u0302');
          i = j;
          continue;
        }
      }
      out.push(chars[i]);
    }
    return out.join('');
  }

  function repairPdfExtractedMathText(text) {
    text = String(text || '');
    if (!looksLikePdfMathUnicodeLoss(text)) return text;
    var out = '';
    for (var i = 0; i < text.length; i++) {
      var code = text.charCodeAt(i);
      if (code >= 0xD400 && code <= 0xD7A3) {
        out += stringFromCodePointSafe(code + 0x10000);
      } else {
        out += text.charAt(i);
      }
    }
    return moveLeadingCombiningHat(out);
  }

  function repairContextPayload(ctx) {
    var next = {};
    ctx = ctx || {};
    for (var key in ctx) {
      if (!Object.prototype.hasOwnProperty.call(ctx, key)) continue;
      var value = ctx[key];
      if (
        key === 'selectionText' ||
        key === 'selectedText' ||
        key === 'activeSelectionText' ||
        key === 'selectedNoteTitle' ||
        key === 'selectedNoteText' ||
        key === 'prompt'
      ) {
        next[key] = repairPdfExtractedMathText(value);
      } else {
        next[key] = value;
      }
    }
    return next;
  }

  function hasPromptOrSelection(prompt) {
    var ctx = state.context || {};
    return !!(
      compactText(prompt) ||
      compactText(ctx.selectionText) ||
      compactText(ctx.selectedNoteTitle) ||
      compactText(ctx.selectedNoteText) ||
      compactText(state.lastPromptFromSelection)
    );
  }

  function hasPdfSelection() {
    var ctx = state.context || {};
    return !!compactText(ctx.selectionText || ctx.selectedText || ctx.activeSelectionText) ||
      !!compactText(state.lastPromptFromSelection);
  }

  function hasNodeContext(prompt) {
    var ctx = state.context || {};
    return !!(
      compactText(prompt) ||
      compactText(ctx.selectedNoteTitle) ||
      compactText(ctx.selectedNoteText) ||
      compactText(ctx.noteId) ||
      compactText(ctx.noteid)
    );
  }

  function hasDocumentContext() {
    var ctx = state.context || {};
    return !!(
      compactText(ctx.docmd5) ||
      compactText(ctx.bookmd5) ||
      compactText(ctx.pdfPath) ||
      compactText(ctx.documentPath) ||
      compactText(state.lastSourcePdfPath)
    );
  }

  function contextHasSelectedMaterial() {
    var ctx = state.context || {};
    return !!compactText(ctx.selectionText || ctx.selectedText || ctx.activeSelectionText) ||
      !!compactText(ctx.selectedNoteTitle) ||
      !!compactText(ctx.selectedNoteText) ||
      !!compactText(ctx.selectedNoteId || ctx.noteId || ctx.noteid);
  }

  function nativeCapabilityReady(key) {
    var caps = state.nativeApiCapabilities || {};
    var matrix = caps.capabilityMatrix || {};
    var item = matrix[key] || {};
    return !!item.ready;
  }

  function nativeHighlightCapabilityReady() {
    return nativeCapabilityReady('nativeHighlightSelection') ||
      nativeCapabilityReady('selectionPopupHighlight');
  }

  function nativeCapabilityAvailable(key) {
    var caps = state.nativeApiCapabilities || {};
    var matrix = caps.capabilityMatrix || {};
    var item = matrix[key] || {};
    return !!item.available;
  }

  function nativeHighlightCapabilityAvailable() {
    return nativeCapabilityAvailable('nativeHighlightSelection') ||
      nativeCapabilityAvailable('selectionPopupHighlight') ||
      nativeHighlightCapabilityReady();
  }

  function actionUnavailableReason(action, prompt) {
    if (action === 'chat') return '';
    if (action === 'explain_selection' && !hasPromptOrSelection(prompt)) {
      return '先选中内容或输入要求，再点“解释选中”。';
    }
    if (
      (action === 'generate_card' || action === 'generate_mindmap' || action === 'generate_full_reading') &&
      !hasPromptOrSelection(prompt) &&
      !(currentContextScope() !== 'selection' && hasDocumentContext())
    ) {
      return '先选中内容或输入要求，再生成卡片、脑图或精读。';
    }
    if ((action === 'expand_node' || action === 'reorganize_mindmap') && !hasNodeContext(prompt)) {
      return '先选中脑图节点或输入要处理的节点内容。';
    }
    if (action === 'request_native_highlight_selection') {
      if (state.nativeApiCapabilities && state.nativeApiCapabilities.available && !nativeHighlightCapabilityAvailable()) {
        return 'MN4 还没发现可用的原生高亮入口。请先点“刷新MN能力”，或重新打开 Codex 面板。';
      }
    }
    if (action === 'export_annotated_pdf' && !hasDocumentContext()) {
      return '当前没有可导出的文档。请先打开 PDF 并刷新上下文。';
    }
    return '';
  }

  function unavailableHintLabel(reason) {
    var value = String(reason || '');
    if (/脑图节点|节点/.test(value)) return '需节点';
    if (/文档|PDF|pdf/.test(value)) return '需文档';
    if (/MN4|原生高亮|高亮入口|能力/.test(value)) return '需能力';
    if (/选中内容|选中|输入要求|选区/.test(value)) return '需选区';
    return '不可用';
  }

  function updateActionAvailability() {
    var buttons = document.querySelectorAll('button[data-action]');
    var prompt = promptValue ? promptValue() : '';
    for (var i = 0; i < buttons.length; i++) {
      var button = buttons[i];
      var action = button.getAttribute('data-action') || '';
      var defaultTitle = button.getAttribute('data-default-title') || button.getAttribute('title') || actionLabel(action);
      var defaultHint = button.getAttribute('data-default-hint') || button.getAttribute('data-hint') || '';
      if (!button.getAttribute('data-default-title')) {
        button.setAttribute('data-default-title', defaultTitle);
      }
      if (!button.getAttribute('data-default-hint')) {
        button.setAttribute('data-default-hint', defaultHint);
      }
      var unavailable = actionUnavailableReason(action, prompt);
      button.setAttribute('data-action-state', unavailable ? 'needs-context' : 'ready');
      if (unavailable) {
        button.setAttribute('title', defaultTitle + '。不可用：' + unavailable);
        button.setAttribute('data-hint', unavailableHintLabel(unavailable));
        button.setAttribute('data-disabled-reason', unavailable);
        button.setAttribute('aria-disabled', 'true');
      } else {
        button.setAttribute('title', defaultTitle);
        button.setAttribute('data-hint', defaultHint);
        button.removeAttribute('data-disabled-reason');
        button.setAttribute('aria-disabled', 'false');
      }
    }
  }

  function cleanCustomButtons(buttons) {
    var clean = [];
    var pinnedCount = 0;
    buttons = buttons || [];
    for (var i = 0; i < buttons.length && clean.length < 20; i++) {
      var item = buttons[i] || {};
      var title = String(item.title || '').replace(/^\s+|\s+$/g, '').substring(0, 48);
      var action = String(item.action || '');
      var prompt = String(item.prompt || '').replace(/^\s+|\s+$/g, '').substring(0, 3000);
      if (!title || !prompt || !isAllowedPromptAction(action)) continue;
      var showOnMain = !!item.showOnMain && pinnedCount < MAIN_PINNED_BUTTON_LIMIT;
      if (showOnMain) pinnedCount += 1;
      clean.push({title: title, action: action, prompt: prompt, showOnMain: showOnMain});
    }
    return clean;
  }

  function updateReadiness(result) {
    result = result || {};
    if (result.openai_configured !== undefined) state.openaiConfigured = !!result.openai_configured;
    if (result.codex_cli_available !== undefined) state.codexCliAvailable = !!result.codex_cli_available;
    if (result.codex_cli_path !== undefined) state.codexCliPath = String(result.codex_cli_path || '');
    if (result.ai_backend !== undefined) state.aiBackend = String(result.ai_backend || 'auto');
    var settings = result.settings || state.settings || {};
    var backend = settings.aiBackend || state.aiBackend || 'auto';
    state.aiBackend = backend;
    var panel = byId('readinessPanel');
    var line = byId('aiReadinessLine');
    var detail = byId('aiReadinessDetail');
    if (!panel || !line || !detail) return;
    var backendLabels = {
      auto: '自动',
      codex_cli: '本机 Codex CLI',
      openai_api: 'OpenAI API',
      local: '本地工具/诊断'
    };
    var hasRealAi = (backend === 'codex_cli' && state.codexCliAvailable) ||
      (backend === 'openai_api' && state.openaiConfigured) ||
      (backend === 'auto' && (state.codexCliAvailable || state.openaiConfigured));
    if (hasRealAi) {
      panel.className = 'readiness-panel ready';
      line.textContent = '真实 AI 后端已发现';
      detail.textContent =
        'AI 后端：' + (backendLabels[backend] || backend) +
        ' / Codex CLI：' + (state.codexCliAvailable ? '已发现' : '未发现') +
        ' / OpenAI：' + (state.openaiConfigured ? '已配置' : '未配置') +
        ' / 模型：' + (settings.model || state.settings.model || '未设置') +
        ' / 速度：' + (settings.speed || state.settings.speed || '未设置') +
        ' / 代理：' + ((settings.proxyUrl || state.settings.proxyUrl) ? '已配置' : '未配置') +
        ' / 生成仍取决于 CLI 登录、代理和网络';
    } else if (backend === 'local') {
      panel.className = 'readiness-panel warn';
      line.textContent = '本地工具/诊断模式';
      detail.textContent = 'AI 后端：本地工具/诊断。要进行真实 AI 对话，需要可用的 Codex CLI 或 OpenAI API。';
    } else {
      panel.className = 'readiness-panel warn';
      line.textContent = '真实 AI 未配置';
      detail.textContent =
        'AI 后端：' + (backendLabels[backend] || backend) +
        '。未发现可用的本机 Codex CLI，也未配置 OpenAI Key；当前无法进行真实 AI 对话。';
    }
  }

  function renderMnApiStatus(result) {
    result = result || {};
    if (result.mnApi) state.mnApi = result.mnApi || {};
    var settings = result.settings || state.settings || {};
    var info = state.mnApi || {};
    var backend = settings.mnApiBackend || result.mn_api_backend || info.backend || 'auto';
    var configured = info.urlApiConfigured !== undefined ? !!info.urlApiConfigured : !!result.mn_url_api_configured;
    var labels = {
      auto: '自动',
      native: '原生插件',
      url_api: 'URL API'
    };
    setValue('mnApiBackendSelect', backend);
    var line = byId('mnApiStatusLine');
    if (!line) return;
    line.textContent =
      'MN 接口：' + (labels[backend] || backend) +
      ' / URL API：' + (configured ? '已配置' : '未配置') +
      ' / 回调：' + (info.callbackBaseUrl || '默认本机回调');
    if (backend === 'url_api' && !configured) {
      line.className = 'mn-api-status-line warn';
    } else {
      line.className = 'mn-api-status-line ok';
    }
  }

  function renderFileAccess(result) {
    var line = byId('fileAccessLine');
    if (!line) return;
    result = result || {};
    var access = result.fileAccess || {};
    var source = access.sourcePdf || {};
    var cache = access.pdfCache || {};
    var exportDir = access.exportDir || {};
    var status = result.status || '未检查';
    var sourceStatus = source.status || '?';
    var cacheStatus = cache.status || '?';
    var exportStatus = exportDir.status || '?';
    if (source.path) state.lastSourcePdfPath = String(source.path || '');
    line.textContent = '文件访问：' + status + ' / PDF ' + sourceStatus + ' / 缓存 ' + cacheStatus + ' / 导出 ' + exportStatus;
    line.className = /PERMISSION|ERROR/.test(String(status)) ? 'file-access-line error' :
      (String(status) === 'OK' ? 'file-access-line ok' : 'file-access-line warn');
  }

  function renderNativeCapabilities(result) {
    var line = byId('nativeCapabilitiesLine');
    if (!line) return;
    result = result || {};
    var caps = result.nativeApiCapabilities || {};
    if (result.nativeApiCapabilities) state.nativeApiCapabilities = caps;
    var matrix = caps.capabilityMatrix || {};
    if (!caps.available) {
      line.textContent = 'MN 原生能力：等待 MN4 运行时上报';
      line.className = 'native-capabilities-line warn';
      updateActionAvailability();
      return;
    }
    var ready = [];
    var blocked = [];
    for (var key in matrix) {
      if (!Object.prototype.hasOwnProperty.call(matrix, key)) continue;
      var item = matrix[key] || {};
      var label = item.label || key;
      if (item.ready) ready.push(label);
      else if (item.available) blocked.push(label);
    }
    var readyText = ready.length ? ready.slice(0, 3).join('、') : '无';
    var blockedText = blocked.length ? blocked.slice(0, 2).join('、') : '无';
    line.textContent = 'MN 原生能力：可执行 ' + ready.length + '（' + readyText + '） / 受阻 ' + blocked.length + '（' + blockedText + '）';
    line.className = ready.length ? 'native-capabilities-line ok' : 'native-capabilities-line warn';
    updateActionAvailability();
  }

  function releaseBlockerGroupTitle(name) {
    name = String(name || '');
    if (/^(runtime_web_controls|native_api_matrix)$/.test(name)) return 'MN4 运行态';
    if (/^native_visible_highlight$/.test(name)) return '真实功能证据';
    if (/^(release_maintainer_prerequisites|signed_pkg|notarized_pkg)$/.test(name)) return '签名与公证';
    if (/^cross_machine_install$/.test(name)) return '跨机器安装';
    if (/^(unit_tests|syntax_checks|release_zip_smoke|install_dry_run|release_sha256_manifest)$/.test(name)) return '基础包验证';
    return '其他';
  }

  function fallbackReleaseBlockerGroups(blockers) {
    blockers = blockers || [];
    var order = ['基础包验证', 'MN4 运行态', '真实功能证据', '签名与公证', '跨机器安装', '其他'];
    var grouped = {};
    for (var i = 0; i < blockers.length; i++) {
      var item = blockers[i] || {};
      var title = releaseBlockerGroupTitle(item.name || 'unknown');
      if (!grouped[title]) grouped[title] = [];
      grouped[title].push(item);
    }
    var groups = [];
    for (var j = 0; j < order.length; j++) {
      if (grouped[order[j]] && grouped[order[j]].length) {
        groups.push({title: order[j], items: grouped[order[j]]});
      }
    }
    return groups;
  }

  function formatReleaseBlockerGroups(groups, blockers, releasable) {
    blockers = blockers || [];
    groups = groups && groups.length ? groups : fallbackReleaseBlockerGroups(blockers);
    if (!blockers.length && !groups.length) {
      return releasable ? '所有发布 gate 已通过。' : '没有返回阻塞详情，请查看命令行验收输出。';
    }
    var parts = [];
    for (var i = 0; i < groups.length; i++) {
      var group = groups[i] || {};
      var title = group.title || '其他';
      var items = group.items || [];
      if (!items.length) continue;
      parts.push(title);
      for (var j = 0; j < items.length; j++) {
        var item = items[j] || {};
        parts.push('- ' + (item.name || 'unknown') + ': ' + (item.detail || ''));
        var actions = item.nextActions || [];
        for (var k = 0; k < actions.length && k < 2; k++) {
          if (actions[k]) parts.push('  下一步：' + actions[k]);
        }
      }
    }
    return parts.join('\n');
  }

  function formatPermissionSubjects(subjects) {
    subjects = subjects || [];
    if (!subjects.length) return '';
    var parts = ['权限对象'];
    for (var i = 0; i < subjects.length; i++) {
      var item = subjects[i] || {};
      var label = item.label || (i === 0 ? '当前 Companion 进程' : 'Python 可执行文件');
      var line = '- ' + label;
      if (item.pid) line += ' / PID ' + item.pid;
      if (item.launchLabel) line += ' / ' + item.launchLabel;
      if (item.path) line += ' / ' + item.path;
      parts.push(line);
      if (item.note) parts.push('  ' + item.note);
    }
    return parts.join('\n');
  }

  function formatReleaseEvidenceGuide(items) {
    items = items || [];
    if (!items.length) return '';
    var parts = ['证据/发布动作'];
    for (var i = 0; i < items.length; i++) {
      var item = items[i] || {};
      var title = item.title || item.id || '发布动作';
      parts.push('- ' + title);
      if (item.command) parts.push('  命令：' + item.command);
      if (item.outputHint) parts.push('  输出：' + item.outputHint);
      if (item.note) parts.push('  说明：' + item.note);
    }
    return parts.join('\n');
  }

  function copyTextToClipboard(text, label, detail) {
    text = String(text || '');
    label = label || '命令';
    detail = detail || text;

    function report(ok) {
      var prefix = ok ? '已复制命令：' : '无法自动复制命令，请手动复制：';
      addMessage('assistant', prefix + label + '\n\n' + detail);
    }

    function fallbackCopy() {
      var textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.setAttribute('readonly', 'readonly');
      textarea.style.position = 'fixed';
      textarea.style.left = '-9999px';
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      var ok = false;
      try {
        ok = document.execCommand('copy');
      } catch (err) {
        ok = false;
      }
      document.body.removeChild(textarea);
      report(ok);
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function() {
        report(true);
      }).catch(fallbackCopy);
      return;
    }
    fallbackCopy();
  }

  function releaseEvidenceCommandDetail(item) {
    item = item || {};
    var parts = [];
    parts.push('命令：' + (item.command || ''));
    if (item.outputHint) parts.push('输出：' + item.outputHint);
    if (item.note) parts.push('说明：' + item.note);
    return parts.join('\n');
  }

  function runReleaseEvidenceCommand(item) {
    item = item || {};
    var command = String(item.command || '');
    if (!command) {
      addMessage('assistant', item.note || '这个发布动作没有可复制的命令。');
      return;
    }
    copyTextToClipboard(command, item.title || item.id || '发布动作', releaseEvidenceCommandDetail(item));
  }

  function runReleaseRecoveryAction(item) {
    item = item || {};
    if (item.handler === 'openPermissionSettings') {
      openPermissionSettings();
      return;
    }
    if (item.handler === 'refreshNativeCapabilities') {
      refreshNativeCapabilities();
      return;
    }
    if (item.handler === 'collectRuntimeEvidence') {
      collectRuntimeEvidence();
      return;
    }
    if (item.handler === 'restartMarginNote4') {
      restartMarginNote4();
      return;
    }
    if (item.handler === 'checkReleaseAcceptance') {
      checkReleaseAcceptance();
      return;
    }
    if (item.action) {
      executeAction(item.action, item.prompt || '', item.title || actionLabel(item.action));
      return;
    }
    addMessage('assistant', item.description || '这个动作需要在系统或 Finder 中完成。');
  }

  function appendReleaseActionHeading(container, text) {
    var heading = document.createElement('span');
    heading.className = 'release-action-heading';
    heading.textContent = text;
    container.appendChild(heading);
  }

  function renderReleaseRecoveryActions(actions, evidenceGuide) {
    var container = byId('releaseAcceptanceActions');
    if (!container) return;
    actions = actions || [];
    evidenceGuide = evidenceGuide || [];
    container.innerHTML = '';
    if (!actions.length && !evidenceGuide.length) {
      container.className = 'release-acceptance-actions hidden';
      return;
    }
    container.className = 'release-acceptance-actions';
    if (actions.length) appendReleaseActionHeading(container, '面板动作');
    for (var i = 0; i < actions.length; i++) {
      (function(item) {
        item = item || {};
        var button = document.createElement('button');
        button.className = 'small-button release-recovery-button';
        button.type = 'button';
        button.textContent = item.title || item.id || '处理';
        if (item.description) button.title = item.description;
        button.addEventListener('click', function(ev) {
          releaseButtonFocus(ev.currentTarget);
          runReleaseRecoveryAction(item);
        });
        container.appendChild(button);
      })(actions[i]);
    }
    if (evidenceGuide.length) appendReleaseActionHeading(container, '外部命令');
    for (var j = 0; j < evidenceGuide.length; j++) {
      (function(item) {
        item = item || {};
        var button = document.createElement('button');
        button.className = 'small-button release-evidence-button';
        button.type = 'button';
        button.textContent = '复制命令';
        if (item.title) button.textContent = '复制：' + item.title;
        if (item.command) button.title = item.command;
        button.addEventListener('click', function(ev) {
          releaseButtonFocus(ev.currentTarget);
          runReleaseEvidenceCommand(item);
        });
        container.appendChild(button);
      })(evidenceGuide[j]);
    }
  }

  function formatSingleDocumentChecks(report) {
    report = report || {};
    var checks = report.checks || [];
    if (!checks.length) return '还没有检查结果。';
    var lines = [];
    for (var i = 0; i < checks.length && i < 8; i++) {
      var item = checks[i] || {};
      var status = item.status || 'BLOCK';
      var label = item.label || item.id || '检查项';
      var detail = item.detail || '';
      lines.push('- ' + status + ' ' + label + (detail ? '：' + detail : ''));
      if (status !== 'PASS' && item.nextActions && item.nextActions.length) {
        lines.push('  下一步：' + item.nextActions[0]);
      }
    }
    if (checks.length > 8) lines.push('- 另有 ' + (checks.length - 8) + ' 项，查看对话里的完整报告。');
    return lines.join('\n');
  }

  function renderSingleDocumentAcceptance(result) {
    result = result || {};
    var line = byId('singleDocumentAcceptanceLine');
    var detail = byId('singleDocumentAcceptanceDetail');
    if (!line || !detail) return;
    if (!result.singleDocumentAcceptance && result.singleDocumentReady === undefined) {
      line.textContent = '本文档验收：未运行';
      line.className = 'release-acceptance-line warn';
      detail.textContent = '点击“本文档验收”可检查当前 PDF 里按钮和工作流是否真的跑通过。';
      return;
    }
    var ready = !!result.singleDocumentReady;
    var blocked = parseInt(result.singleDocumentBlockerCount || 0, 10);
    var passed = parseInt(result.singleDocumentPassedCount || 0, 10);
    var total = parseInt(result.singleDocumentTotalCount || 0, 10);
    line.textContent = '本文档验收：' + (ready ? 'PASS' : 'BLOCK') + ' / ' + passed + '/' + total + ' / 阻塞 ' + blocked;
    line.className = 'release-acceptance-line ' + (ready ? 'ok' : 'error');
    detail.textContent = formatSingleDocumentChecks(result.singleDocumentAcceptance || {});
  }

  function renderNativeHighlightWizard(result) {
    result = result || {};
    var line = byId('nativeHighlightWizardLine');
    var detail = byId('nativeHighlightWizardDetail');
    var mainPanel = byId('mainNativeHighlightWizardPanel');
    var mainLine = byId('mainNativeHighlightWizardLine');
    var mainDetail = byId('mainNativeHighlightWizardDetail');
    if (!line && !mainLine) return;
    var wizard = result.nativeHighlightWizard || {};
    var lineText = '';
    var detailText = '';
    var stateClass = 'warn';
    var hideMain = false;
    if (!wizard.stage) {
      lineText = '高亮采证：未运行';
      detailText = '点击“高亮采证”后回到 PDF 重新选中一小段文字，插件会尝试 MN4 原生高亮并刷新验收状态。';
      hideMain = true;
    } else {
      var complete = wizard.stage === 'complete';
      var expired = wizard.stage === 'expired';
      var failed = wizard.stage === 'failed' || expired;
      var title = complete ? 'PASS' : wizard.stage;
      stateClass = complete ? 'ok' : (failed ? 'error' : 'warn');
      lineText =
        '高亮采证：' + title +
        ' / 原生高亮 ' + (wizard.visibleHighlightReady ? 'PASS' : 'BLOCK') +
        ' / 选区菜单 ' + (wizard.selectionPopupReady ? 'PASS' : 'BLOCK');
      var blocked = wizard.blockedChecks || [];
      var latest = wizard.latestEvent || {};
      var pieces = [];
      if (wizard.instruction) pieces.push(wizard.instruction);
      if (latest.event) pieces.push('最近事件：' + latest.event);
      if (wizard.latestEventAgeSeconds !== undefined && wizard.latestEventAgeSeconds !== null) {
        pieces.push('等待已超过：' + wizard.latestEventAgeSeconds + ' 秒');
      }
      if (blocked.length) pieces.push('阻塞项：' + blocked.join(', '));
      detailText = pieces.join('\n') || '等待高亮采证状态。';
    }
    if (line) {
      line.textContent = lineText;
      line.className = 'release-acceptance-line ' + stateClass;
    }
    if (detail) detail.textContent = detailText;
    if (mainPanel) mainPanel.className = 'native-highlight-guide' + (hideMain ? ' hidden' : '');
    if (mainLine) {
      mainLine.textContent = lineText;
      mainLine.className = 'native-highlight-guide-line ' + stateClass;
    }
    if (mainDetail) mainDetail.textContent = detailText;
  }

  function renderReleaseAcceptance(result) {
    result = result || {};
    var line = byId('releaseAcceptanceLine');
    var detail = byId('releaseAcceptanceDetail');
    if (!line || !detail) return;
    if (!result.releaseAcceptance && result.releasable === undefined && result.blockerCount === undefined) {
      line.textContent = '发布验收：未运行';
      line.className = 'release-acceptance-line warn';
      detail.textContent = '点击“发布验收”可查看发布 gate 和下一步动作。';
      renderReleaseRecoveryActions([], []);
      return;
    }
    var blockerCount = parseInt(result.blockerCount || 0, 10);
    var releasable = !!result.releasable;
    line.textContent = '发布验收：' + (releasable ? 'PASS' : 'BLOCKED') + ' / 阻塞 ' + blockerCount;
    line.className = 'release-acceptance-line ' + (releasable ? 'ok' : 'error');
    var blockers = result.blockers || [];
    var blockerText = formatReleaseBlockerGroups(result.blockerGroups, blockers, releasable);
    var permissionText = formatPermissionSubjects(result.permissionSubjects || []);
    var evidenceText = formatReleaseEvidenceGuide(result.evidenceGuide || []);
    detail.textContent = [blockerText, permissionText, evidenceText].filter(function(text) {
      return !!text;
    }).join('\n\n');
    renderReleaseRecoveryActions(result.recoveryActions || [], result.evidenceGuide || []);
  }

  function renderMnRuntime(result) {
    var line = byId('mnRuntimeLine');
    var runtime = (result && result.mnRuntime) || {};
    var summary = runtime.summary || 'MN4 运行态：等待 Companion 检查';
    var nextStep = runtime.nextStep || '';
    if (!nextStep && (runtime.staleRuntime || runtime.runtimeHandlerStale)) {
      nextStep = '重新打开 Codex 面板；如果仍旧，重启 MarginNote 4 后再点“刷新MN能力”。';
    }
    renderMnRuntimeNotice(runtime);
    if (!line) return;
    if (!runtime.summary) {
      line.textContent = summary;
      line.className = 'mn-runtime-line warn';
      return;
    }
    line.textContent = 'MN4 运行态：' + summary + (nextStep ? ' ' + nextStep : '');
    if (runtime.ready) {
      line.className = 'mn-runtime-line ok';
    } else if (runtime.staleRuntime || runtime.runtimeHandlerStale) {
      line.className = 'mn-runtime-line error';
    } else {
      line.className = 'mn-runtime-line warn';
    }
  }

  function renderMnRuntimeNotice(runtime) {
    runtime = runtime || {};
    var notice = byId('mnRuntimeNotice');
    var text = byId('mnRuntimeNoticeText');
    if (!notice || !text) return;
    if (runtime.ready || !(runtime.staleRuntime || runtime.runtimeHandlerStale)) {
      notice.className = 'mn-runtime-notice hidden';
      text.textContent = '';
      return;
    }
    var summary = runtime.summary || 'MN4 运行态未刷新。';
    var nextStep = runtime.nextStep || '重新打开 Codex 面板；如果仍旧，重启 MarginNote 4 后再点“刷新MN能力”。';
    notice.className = 'mn-runtime-notice';
    text.textContent = 'MN4 运行态需要刷新：' + summary + ' ' + nextStep;
  }

  function diagnosePermissions() {
    postCompanion('diagnose_permissions', {}, function(result) {
      renderControls(result || {});
      renderFileAccess(result || {});
      if (result && result.status === 'PERMISSION') {
        addMessage('assistant', '文件访问被 macOS 拦截。请在 Full Disk Access 中给 Terminal、Codex 或 Python 授权后重启 Companion。');
      }
    });
  }

  function openPermissionSettings() {
    postCompanion('open_full_disk_access_settings', {}, function(result) {
      if (result && result.reply) addMessage('assistant', result.reply);
    });
  }

  function cacheCurrentPdf() {
    var context = state.context || {};
    var path = state.lastSourcePdfPath || context.pdfPath || context.documentPath || '';
    renderPdfCacheBanner({
      state: 'waiting_native',
      label: 'PDF缓存：等待 MN4 缓存',
      detail: '保持当前 PDF 打开，MN4 插件会读取并上传到 Companion 缓存。',
      pending: true
    });
    postCompanion('request_pdf_cache', {pdfPath: path}, function(result) {
      renderControls(result || {});
      if (result && result.ok) {
        addMessage('assistant', result.reply || '已请求 MN4 插件缓存当前 PDF。');
      } else {
        addFailureMessage('请求缓存 PDF 失败', result);
      }
    });
  }

  function choosePdfCacheFile() {
    var input = byId('pdfCacheFileInput');
    if (!input) {
      addMessage('assistant', '当前面板没有可用的 PDF 文件选择控件。');
      return;
    }
    input.value = '';
    input.click();
  }

  function uploadSelectedPdfCacheFile(ev) {
    var input = ev && ev.currentTarget ? ev.currentTarget : byId('pdfCacheFileInput');
    if (!input || !input.files || !input.files.length) return;
    var file = input.files[0];
    var fileName = file && file.name ? String(file.name) : 'document.pdf';
    if (!/\.pdf$/i.test(fileName) && String(file.type || '') !== 'application/pdf') {
      renderPdfCacheBanner({
        state: 'error',
        label: 'PDF缓存：缓存失败',
        detail: '请选择 PDF 文件。',
        pending: false
      });
      return;
    }
    if (file.size > 80000000) {
      renderPdfCacheBanner({
        state: 'error',
        label: 'PDF缓存：缓存失败',
        detail: 'PDF 超过 80 MB，暂不缓存。',
        pending: false
      });
      return;
    }
    var ctx = state.context || {};
    if (!String(ctx.bookmd5 || ctx.docmd5 || '')) {
      renderPdfCacheBanner({
        state: 'error',
        label: 'PDF缓存：缓存失败',
        detail: '当前还没有 MarginNote 文档标识，请先刷新上下文。',
        pending: false
      });
      return;
    }
    renderPdfCacheBanner({
      state: 'waiting_native',
      label: 'PDF缓存：正在上传',
      detail: '正在读取你选择的 PDF，并写入 Companion 缓存。',
      pending: true
    });
    var reader = new FileReader();
    reader.onload = function() {
      var dataUrl = String(reader.result || '');
      postCompanion('cache_pdf_from_marginnote', {
        source: 'browser_pdf_file_upload',
        fileName: fileName,
        pdfPath: 'browser-file://' + fileName,
        documentPath: 'browser-file://' + fileName,
        pdfBase64: dataUrl
      }, function(result) {
        renderControls(result || {});
        if (result && result.ok) {
          renderPdfCacheBanner(result.pdfCache || {
            state: 'cached',
            label: 'PDF缓存：缓存完成',
            detail: '已通过文件选择写入缓存。',
            pending: false
          });
          addMessage('assistant', result.reply || result.message || 'PDF 缓存完成。');
          return;
        }
        renderPdfCacheBanner({
          state: 'error',
          label: 'PDF缓存：缓存失败',
          detail: result && result.message ? result.message : '文件上传缓存失败。',
          pending: false
        });
        addFailureMessage('选择 PDF 缓存失败', result);
      }, {showReply: false});
    };
    reader.onerror = function() {
      renderPdfCacheBanner({
        state: 'error',
        label: 'PDF缓存：缓存失败',
        detail: 'Web 面板读取所选 PDF 失败。',
        pending: false
      });
    };
    reader.readAsDataURL(file);
  }

  function refreshNativeCapabilities() {
    postCompanion('request_native_capability_probe', {}, function(result) {
      renderControls(result || {});
      if (result && result.ok) {
        addMessage('assistant', '已请求 MN4 插件刷新原生能力；保持当前 notebook 打开，稍后再点“检查权限”或运行 doctor。');
      }
    });
  }

  function collectRuntimeEvidence() {
    postCompanion('collect_mn_runtime_evidence', {waitSeconds: 2}, function(result) {
      renderControls(result || {});
      if (result && result.reply) {
        addMessage('assistant', result.reply);
      } else if (result && result.evidencePath) {
        addMessage('assistant', 'MN4 运行态证据已生成：' + result.evidencePath);
      } else {
        addFailureMessage('运行态采证失败', result);
      }
    });
  }

  function diagnoseHighlights() {
    executeAction('diagnose_highlights', '', '高亮状态');
  }

  function shouldContinueNativeHighlightWizardPolling(result) {
    var wizard = result && result.nativeHighlightWizard ? result.nativeHighlightWizard : {};
    return wizard.stage === 'waiting_selection' || wizard.stage === 'verifying';
  }

  function stopNativeHighlightWizardRefresh() {
    if (!state.nativeHighlightWizardTimer) return;
    window.clearTimeout(state.nativeHighlightWizardTimer);
    state.nativeHighlightWizardTimer = null;
  }

  function scheduleNativeHighlightWizardRefresh() {
    stopNativeHighlightWizardRefresh();
    state.nativeHighlightWizardTimer = window.setTimeout(function() {
      state.nativeHighlightWizardTimer = null;
      refreshNativeHighlightWizard();
    }, 3000);
  }

  function checkSingleDocumentAcceptance() {
    startProgress('single_document_acceptance_summary', '正在检查本文档', 'Companion 正在读取当前 topic/book 的事件、action result 和高亮证据。');
    postCompanion('single_document_acceptance_summary', {}, function(result) {
      finishProgressStage('本文档验收完成', result && result.message ? result.message : '本文档验收已返回。');
      renderSingleDocumentAcceptance(result || {});
      if (result && result.reply) {
        addMessage('assistant', result.reply);
      } else if (!result || !result.ok) {
        addFailureMessage('本文档验收失败', result);
      }
    });
  }

  function refreshNativeHighlightWizard() {
    postCompanion('native_highlight_wizard_status', {}, function(result) {
      renderNativeHighlightWizard(result || {});
      if (!result || !result.ok) addFailureMessage('高亮采证状态刷新失败', result);
      if (result && result.ok && shouldContinueNativeHighlightWizardPolling(result)) {
        scheduleNativeHighlightWizardRefresh();
      } else {
        stopNativeHighlightWizardRefresh();
      }
    });
  }

  function startNativeHighlightWizard() {
    stopNativeHighlightWizardRefresh();
    startProgress('native_highlight_wizard_start', '正在启动高亮采证', 'Companion 正在请求 MN4 进入当前或下一次 PDF 选区高亮流程。');
    postCompanion('native_highlight_wizard_start', {}, function(result) {
      finishProgressStage('高亮采证已启动', result && result.message ? result.message : '请回到 PDF 重新选中文字。');
      renderNativeHighlightWizard(result || {});
      if (result && result.reply) {
        addMessage('assistant', result.reply);
      } else if (!result || !result.ok) {
        addFailureMessage('高亮采证启动失败', result);
      }
      if (result && result.ok && shouldContinueNativeHighlightWizardPolling(result)) {
        scheduleNativeHighlightWizardRefresh();
      }
    });
  }

  function checkReleaseAcceptance() {
    startProgress('release_acceptance_summary', '正在运行发布验收', 'Companion 正在执行 release_acceptance.py --json；这会运行测试、smoke、doctor 和发布 gate。');
    postCompanion('release_acceptance_summary', {}, function(result) {
      finishProgressStage('发布验收完成', result && result.message ? result.message : '验收命令已返回。');
      renderReleaseAcceptance(result || {});
      if (result && result.reply) {
        addMessage('assistant', result.reply);
      } else if (!result || !result.ok) {
        addFailureMessage('发布验收失败', result);
      }
    });
  }

  function restartMarginNote4() {
    var ok = window.confirm(
      '这会请求退出并重新打开 MarginNote 4。请确认当前笔记已保存；重启后需要重新打开 Codex 面板。'
    );
    if (!ok) return;
    postCompanion('restart_marginnote4', {}, function(result) {
      if (result && result.reply) {
        addMessage('assistant', result.reply);
      } else if (result && result.ok) {
        addMessage('assistant', '已请求重启 MarginNote 4。重新打开后请再点“刷新MN能力”。');
      } else {
        addFailureMessage('重启 MN4 失败', result);
      }
    });
  }

  function renderDraft(draft) {
    state.draft = draft || null;
    var panel = byId('draftPanel');
    var summary = byId('draftSummary');
    var editor = byId('draftEditText');
    if (!panel || !summary) return;
    if (!state.draft || !state.draft.id) {
      panel.className = 'draft-panel hidden';
      summary.textContent = '暂无待写入内容。';
      if (editor) editor.value = '';
      return;
    }
    panel.className = 'draft-panel';
    summary.textContent =
      '来源：' + actionLabel(state.draft.original_action || '') + '\n' +
      '卡片：' + (state.draft.card_count || 0) + ' / 脑图：' + (state.draft.has_mindmap ? '有' : '无') + '\n' +
      (state.draft.write_target ? '写入目标：' + state.draft.write_target + '\n' : '') +
      (state.draft.mindmap_title ? '脑图根：' + state.draft.mindmap_title + '\n' : '') +
      (state.draft.reply_preview || '');
    if (editor) editor.value = state.draft.edit_text || state.draft.reply_preview || '';
  }

  function currentDraftEditText() {
    return getValue('draftEditText');
  }

  function draftCreatedCount(draft) {
    draft = draft || {};
    var count = parseInt(draft.createdCount || draft.created_count || draft.card_count || 0, 10);
    if ((!count || count < 1) && draft.has_mindmap) count = 1;
    return count && count > 0 ? count : 0;
  }

  function draftEditOperationMeta(draft) {
    draft = draft || {};
    var lines = [];
    var manifest = draft.operation_manifest || draft.operationManifest || {};
    var dryRun = manifest.dryRun || {};
    if (manifest.operationCount !== undefined) {
      lines.push(
        '操作计划：' + (manifest.operationCount || 0) + ' 项' +
        ' / 卡片 ' + (manifest.createCards || 0) +
        ' / 脑图节点 ' + (manifest.createMindmapNodes || 0)
      );
    }
    if (dryRun.status) lines.push('Dry-run：' + dryRun.status + (dryRun.message ? ' / ' + dryRun.message : ''));
    if (draft.write_target) lines.push('写入目标：' + draft.write_target);
    if (draft.mindmap_title) lines.push('脑图根：' + draft.mindmap_title);
    return lines.join('\n');
  }

  function cardFactoryQualityLines(draft) {
    draft = draft || {};
    var manifest = draft.operation_manifest || draft.operationManifest || {};
    var cardFactory = draft.cardFactory || draft.card_factory || manifest.cardFactory || {};
    var cardQuality = draft.cardQuality || draft.card_quality || manifest.cardQuality || {};
    var lines = [];
    if (cardFactory.schema || cardQuality.schema || cardFactory.cardCount || cardQuality.cardCount) {
      lines.push('卡片工厂：' + (cardFactory.cardCount || cardQuality.cardCount || draft.card_count || 0) + ' 张');
    }
    var typeCounts = cardFactory.typeCounts || cardQuality.typeCounts || {};
    var typeParts = [];
    Object.keys(typeCounts).forEach(function(key) {
      if (typeCounts[key]) typeParts.push(key + ' ' + typeCounts[key]);
    });
    if (typeParts.length) lines.push('卡型：' + typeParts.join(' / '));
    if (cardQuality.missingSourceCount !== undefined) lines.push('缺来源：' + (cardQuality.missingSourceCount || 0));
    if (cardQuality.longCardCount !== undefined) lines.push('长卡：' + (cardQuality.longCardCount || 0));
    if (cardQuality.duplicateTitleCount !== undefined) lines.push('重复标题：' + (cardQuality.duplicateTitleCount || 0));
    return lines;
  }

  function setAiEditOperationBusy(panel, busy) {
    if (!panel) return;
    var buttons = panel.querySelectorAll('button');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].disabled = !!busy;
    }
  }

  function setAiEditOperationStatus(panel, text, mode) {
    if (!panel) return;
    var status = panel.querySelector('.ai-edit-status');
    if (status) status.textContent = text || '';
    panel.setAttribute('data-state', mode || '');
  }

  function renderAiEditVerification(panel, verification) {
    if (!panel) return;
    verification = verification || {};
    var report = panel.querySelector('.ai-edit-verification');
    if (!report) {
      report = document.createElement('div');
      report.className = 'ai-edit-verification';
      panel.appendChild(report);
    }
    var status = String(verification.status || 'pending');
    report.className = 'ai-edit-verification ' + status;
    report.textContent = verification.summary || '回滚验证：未返回验证报告。';
  }

  function refreshAiEditVerification(transactionId, panel) {
    transactionId = String(transactionId || '');
    if (!transactionId || !panel) return;
    renderAiEditVerification(panel, {status: 'pending', summary: '回滚验证：正在核对新增对象和回滚结果...'});
    postCompanion('ai_edit_transaction_verify', {transactionId: transactionId}, function(result) {
      if (!result || !result.ok) {
        renderAiEditVerification(panel, {
          status: 'block',
          summary: '回滚验证：读取失败，' + (result && result.message ? result.message : '未知错误。')
        });
        return;
      }
      renderAiEditVerification(panel, result.verification || {});
    }, {showReply: false});
  }

  function addDraftToReviewQueue(panel, draft) {
    draft = draft || state.draft || {};
    var draftId = draft.id || (panel && panel.getAttribute('data-draft-id')) || '';
    if (!draftId) {
      setAiEditOperationStatus(panel, '没有草稿 ID，不能加入复习队列。', 'error');
      return;
    }
    var objectRef = currentMnObjectRef();
    setAiEditOperationBusy(panel, true);
    setAiEditOperationStatus(panel, '正在加入复习队列...', 'saving');
    postCompanion('review_queue_add', {draftId: draftId, mnObject: objectRef, mnObjectId: objectRef.objectId || ''}, function(result) {
      setAiEditOperationBusy(panel, false);
      if (!result || result.ok === false) {
        setAiEditOperationStatus(panel, '加入复习队列失败：' + (result && result.message ? result.message : '未知错误'), 'error');
        return;
      }
      state.knowledgeWorkspace = Object.assign({}, state.knowledgeWorkspace || {}, {
        reviewQueue: result.reviewQueue || result,
        reviewQueueSummary: result.summary || {},
        reviewItems: result.items || []
      });
      renderKnowledgeWorkspace(state.knowledgeWorkspace);
      setAiEditOperationStatus(panel, result.message || '已加入复习队列。', 'accepted');
    }, {showReply: false});
  }

  function buildAiEditOperationPanel(draft) {
    var panel = document.createElement('section');
    panel.className = 'ai-edit-operation';
    panel.setAttribute('data-draft-id', draft && draft.id ? draft.id : '');
    panel.setAttribute('data-transaction-id', draft && draft.transactionId ? draft.transactionId : '');
    var title = document.createElement('div');
    title.className = 'ai-edit-title';
    title.textContent = 'AI 编辑操作';
    var subtitle = document.createElement('div');
    subtitle.className = 'ai-edit-subtitle';
    subtitle.textContent = 'Created ' + draftCreatedCount(draft) + ' card(s)';
    var metaText = draftEditOperationMeta(draft);
    var meta = document.createElement('div');
    meta.className = 'ai-edit-meta' + (metaText ? '' : ' hidden');
    meta.textContent = metaText;
    var qualityText = cardFactoryQualityLines(draft).join('\n');
    var cardQuality = document.createElement('div');
    cardQuality.className = 'ai-edit-card-quality' + (qualityText ? '' : ' hidden');
    cardQuality.textContent = qualityText;
    var actions = document.createElement('div');
    actions.className = 'ai-edit-actions';
    var accept = document.createElement('button');
    accept.className = 'ai-edit-accept';
    accept.type = 'button';
    accept.textContent = '接受';
    accept.addEventListener('click', function(ev) {
      releaseButtonFocus(ev.currentTarget);
      state.draft = draft || state.draft;
      acceptDraft(panel);
    });
    var reject = document.createElement('button');
    reject.className = 'ai-edit-reject';
    reject.type = 'button';
    reject.textContent = '拒绝';
    reject.addEventListener('click', function(ev) {
      releaseButtonFocus(ev.currentTarget);
      state.draft = draft || state.draft;
      rejectDraft(panel);
    });
    var status = document.createElement('div');
    status.className = 'ai-edit-status';
    status.textContent = '等待确认';
    var secondaryActions = document.createElement('div');
    secondaryActions.className = 'ai-edit-secondary-actions';
    var reviewQueue = document.createElement('button');
    reviewQueue.className = 'small-button ai-edit-review-queue';
    reviewQueue.type = 'button';
    reviewQueue.textContent = '加入复习队列';
    reviewQueue.addEventListener('click', function(ev) {
      releaseButtonFocus(ev.currentTarget);
      addDraftToReviewQueue(panel, draft);
    });
    secondaryActions.appendChild(reviewQueue);
    actions.appendChild(accept);
    actions.appendChild(reject);
    panel.appendChild(title);
    panel.appendChild(subtitle);
    panel.appendChild(meta);
    panel.appendChild(cardQuality);
    panel.appendChild(actions);
    panel.appendChild(secondaryActions);
    panel.appendChild(status);
    return panel;
  }

  function renderAiEditOperation(draft) {
    if (!draft || !draft.id) return;
    state.draft = draft;
    addMessageWithExtra('assistant', '', function(article, body) {
      if (body) body.className = 'message-body empty';
      article.appendChild(buildAiEditOperationPanel(draft));
    });
  }

  function writeDraftForAiEditOperation(draft) {
    if (!draft || !draft.id) {
      addMessage('assistant', '草稿缺少 ID，无法写入脑图。');
      return;
    }
    state.pendingAiEditDrafts = state.pendingAiEditDrafts || {};
    state.pendingAiEditDrafts[draft.id] = draft;
    state.draft = draft;
    window.CodexPanel.setStatus({text: '正在把脑图写入 MarginNote：' + draft.id});
    bridge('write_draft', {id: draft.id, aiEdit: '1'});
  }

  function makePresetButtonItem(button, index) {
    var item = document.createElement('article');
    item.className = 'preset-template-item';
    var copy = document.createElement('div');
    copy.className = 'preset-template-copy';
    var title = document.createElement('div');
    title.className = 'preset-template-title';
    title.textContent = button.title || actionLabel(button.action);
    title.title = (button.prompt || '').substring(0, 500);
    var meta = document.createElement('div');
    meta.className = 'preset-template-meta';
    meta.textContent = actionLabel(button.action);
    copy.appendChild(title);
    copy.appendChild(meta);
    var stageButton = document.createElement('button');
    stageButton.className = 'small-button primary-lite';
    stageButton.type = 'button';
    stageButton.textContent = '填入输入框';
    stageButton.addEventListener('click', function(ev) {
      releaseButtonFocus(ev.currentTarget);
      stageOrExplainPromptAction(button.action, button.prompt, button.title);
    });
    var addButton = document.createElement('button');
    addButton.className = 'small-button';
    addButton.type = 'button';
    addButton.textContent = '添加自定义';
    addButton.addEventListener('click', function(ev) {
      releaseButtonFocus(ev.currentTarget);
      addPresetToCustomButtons(index);
    });
    item.appendChild(copy);
    item.appendChild(stageButton);
    item.appendChild(addButton);
    return item;
  }

  function makePromptButtonItem(button, index, isCustom, isPinnedView) {
    var item = document.createElement('article');
    item.className = 'prompt-button-item' + (isPinnedView ? ' pinned-view' : '');
    var runButton = document.createElement('button');
    runButton.className = isCustom ? 'small-button prompt-run-button' : 'small-button prompt-run-button primary-lite';
    runButton.type = 'button';
    runButton.textContent = button.title || actionLabel(button.action);
    runButton.setAttribute('data-action', button.action);
    runButton.setAttribute('data-default-title', actionLabel(button.action) + '：' + (button.prompt || ''));
    runButton.setAttribute('data-default-hint', '待发送');
    runButton.setAttribute('data-hint', '待发送');
    runButton.addEventListener('click', function(ev) {
      releaseButtonFocus(ev.currentTarget);
      stageOrExplainPromptAction(button.action, button.prompt, button.title);
    });
    var meta = document.createElement('div');
    meta.className = 'prompt-button-meta';
    meta.textContent = actionLabel(button.action);
    item.appendChild(runButton);
    item.appendChild(meta);
    if (isCustom) {
      var pinButton = document.createElement('button');
      pinButton.className = button.showOnMain ? 'small-button danger-lite' : 'small-button';
      pinButton.type = 'button';
      pinButton.textContent = button.showOnMain ? (isPinnedView ? '移出' : '取消置顶') : '置顶';
      pinButton.addEventListener('click', function(ev) {
        releaseButtonFocus(ev.currentTarget);
        toggleCustomButtonPinned(index);
      });
      item.appendChild(pinButton);
      var editButton = document.createElement('button');
      editButton.className = 'small-button';
      editButton.type = 'button';
      editButton.textContent = '编辑';
      editButton.addEventListener('click', function(ev) {
        releaseButtonFocus(ev.currentTarget);
        editCustomButton(index);
      });
      item.appendChild(editButton);
    }
    return item;
  }

  function makeMainPinnedButtonItem(button) {
    var runButton = document.createElement('button');
    runButton.className = 'small-button main-pinned-button';
    runButton.type = 'button';
    runButton.textContent = button.title || actionLabel(button.action);
    runButton.setAttribute('data-action', button.action);
    runButton.setAttribute('data-default-title', actionLabel(button.action) + '：' + (button.prompt || ''));
    runButton.setAttribute('data-default-hint', '待发送');
    runButton.setAttribute('data-hint', '待发送');
    runButton.title = actionLabel(button.action) + '：' + (button.prompt || '');
    runButton.addEventListener('click', function(ev) {
      releaseButtonFocus(ev.currentTarget);
      stageOrExplainPromptAction(button.action, button.prompt, button.title);
    });
    return runButton;
  }

  function renderPresetButtons() {
    var list = byId('presetButtonsList');
    if (!list) return;
    list.innerHTML = '';
    for (var i = 0; i < presetButtons.length; i++) {
      list.appendChild(makePresetButtonItem(presetButtons[i], i));
    }
  }

  function renderMainPinnedButtons() {
    var list = byId('mainPinnedButtonsList');
    var panel = byId('mainPinnedButtonsPanel');
    if (!list) return;
    list.innerHTML = '';
    state.customButtons = cleanCustomButtons(state.customButtons);
    var added = 0;
    for (var i = 0; i < state.customButtons.length && added < MAIN_PINNED_BUTTON_LIMIT; i++) {
      if (!state.customButtons[i].showOnMain) continue;
      list.appendChild(makeMainPinnedButtonItem(state.customButtons[i]));
      added += 1;
    }
    if (panel) panel.className = added ? 'main-pinned-panel' : 'main-pinned-panel hidden';
    renderMainPinnedManager();
    updateActionAvailability();
  }

  function renderMainPinnedManager() {
    var list = byId('mainPinnedManagerList');
    if (!list) return;
    list.innerHTML = '';
    state.customButtons = cleanCustomButtons(state.customButtons);
    var added = 0;
    for (var i = 0; i < state.customButtons.length && added < MAIN_PINNED_BUTTON_LIMIT; i++) {
      if (!state.customButtons[i].showOnMain) continue;
      list.appendChild(makePromptButtonItem(state.customButtons[i], i, true, true));
      added += 1;
    }
    if (!added) {
      var empty = document.createElement('div');
      empty.className = 'empty-row';
      empty.textContent = '还没有主界面按钮。到自定义按钮点“置顶”。';
      list.appendChild(empty);
    }
  }

  function renderCustomButtons() {
    var list = byId('customButtonsList');
    if (!list) return;
    list.innerHTML = '';
    state.customButtons = cleanCustomButtons(state.customButtons);
    if (!state.customButtons.length) {
      var empty = document.createElement('div');
      empty.className = 'empty-row';
      empty.textContent = '暂无自定义按钮';
      list.appendChild(empty);
      return;
    }
    for (var i = 0; i < state.customButtons.length; i++) {
      list.appendChild(makePromptButtonItem(state.customButtons[i], i, true));
    }
  }

  function clearCustomButtonForm() {
    setValue('customButtonIndexInput', '-1');
    setValue('customButtonTitleInput', '');
    setValue('customButtonActionSelect', 'chat');
    setValue('customButtonPromptInput', '');
    setChecked('customButtonShowOnMainInput', false);
  }

  function editCustomButton(index) {
    var button = state.customButtons[index];
    if (!button) return;
    setValue('customButtonIndexInput', String(index));
    setValue('customButtonTitleInput', button.title || '');
    setValue('customButtonActionSelect', button.action || 'chat');
    setValue('customButtonPromptInput', button.prompt || '');
    setChecked('customButtonShowOnMainInput', !!button.showOnMain);
  }

  function newCustomButton() {
    clearCustomButtonForm();
    var titleInput = byId('customButtonTitleInput');
    if (titleInput) titleInput.focus();
  }

  function toggleCustomButtonPinned(index) {
    var buttons = cleanCustomButtons(state.customButtons).slice(0);
    var button = buttons[index];
    if (!button) return;
    if (!button.showOnMain) {
      var pinned = 0;
      for (var i = 0; i < buttons.length; i++) {
        if (buttons[i].showOnMain) pinned += 1;
      }
      if (pinned >= MAIN_PINNED_BUTTON_LIMIT) {
        addMessage('assistant', '主界面最多放 ' + MAIN_PINNED_BUTTON_LIMIT + ' 个按钮。请先移出一个常用按钮。');
        return;
      }
      button.showOnMain = true;
    } else {
      button.showOnMain = false;
    }
    state.customButtons = cleanCustomButtons(buttons);
    persistCustomButtons();
  }

  function addPresetToCustomButtons(index) {
    var preset = presetButtons[index];
    if (!preset) return;
    var buttons = cleanCustomButtons(state.customButtons).slice(0);
    for (var i = 0; i < buttons.length; i++) {
      if (
        buttons[i].title === preset.title &&
        buttons[i].action === preset.action &&
        buttons[i].prompt === preset.prompt
      ) {
        editCustomButton(i);
        switchTab('buttons');
        addMessage('assistant', '这个预设已经在自定义按钮里，已打开编辑状态。');
        return;
      }
    }
    buttons.push({
      title: preset.title,
      action: preset.action,
      prompt: preset.prompt,
      showOnMain: false
    });
    state.customButtons = cleanCustomButtons(buttons);
    persistCustomButtons(function() {
      var addedIndex = Math.max(0, state.customButtons.length - 1);
      editCustomButton(addedIndex);
      addMessage('assistant', '已添加到自定义按钮。勾选“主界面”后才会出现在对话页底部。');
    });
  }

  function persistCustomButtons(done) {
    postCompanion('settings_update', {
      settings: {
        customButtons: state.customButtons
      }
    }, function(result) {
      renderControls(result || {});
      if (done) done(result || {});
    });
  }

  function saveCustomButton() {
    var title = getValue('customButtonTitleInput').replace(/^\s+|\s+$/g, '').substring(0, 48);
    var action = getValue('customButtonActionSelect');
    var prompt = getValue('customButtonPromptInput').replace(/^\s+|\s+$/g, '').substring(0, 3000);
    var showOnMain = getChecked('customButtonShowOnMainInput');
    if (!title || !prompt || !isAllowedPromptAction(action)) {
      addMessage('assistant', '自定义按钮需要名称、动作和 prompt。');
      return;
    }
    var index = parseInt(getValue('customButtonIndexInput') || '-1', 10);
    var buttons = cleanCustomButtons(state.customButtons).slice(0);
    var next = {title: title, action: action, prompt: prompt, showOnMain: showOnMain};
    if (index >= 0 && index < buttons.length) {
      buttons[index] = next;
    } else {
      buttons.push(next);
    }
    state.customButtons = cleanCustomButtons(buttons);
    clearCustomButtonForm();
    persistCustomButtons();
  }

  function deleteCustomButton() {
    var index = parseInt(getValue('customButtonIndexInput') || '-1', 10);
    if (index < 0 || index >= state.customButtons.length) {
      clearCustomButtonForm();
      return;
    }
    state.customButtons.splice(index, 1);
    state.customButtons = cleanCustomButtons(state.customButtons);
    clearCustomButtonForm();
    persistCustomButtons();
  }

  function progressElapsedSeconds() {
    return Math.max(0, Math.floor((Date.now() - state.progressStartedAt) / 1000));
  }

  function progressActiveHint() {
    return '可继续输入；运行中可点停止。';
  }

  function progressFinishedHint() {
    return '可继续输入。';
  }

  function formatProgressText(elapsed, active) {
    var stage = state.progressStage || '准备执行';
    var detail = state.progressDetail || '正在收集当前上下文并准备请求。';
    var running = active !== false;
    return [
      '阶段：' + stage,
      '动作：' + actionLabel(state.progressAction),
      '状态：' + detail,
      '已用：' + elapsed + 's',
      running ? progressActiveHint() : progressFinishedHint()
    ].join('\n');
  }

  function updateProgressText() {
    if (!state.progressBody || !state.progressStartedAt) return;
    state.progressBody.textContent = formatProgressText(progressElapsedSeconds(), true);
  }

  function refreshProgressRunState() {
    if (!state.progressBody || !state.progressStartedAt || state.progressStatusInFlight) return;
    state.progressStatusInFlight = true;
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'http://127.0.0.1:48761/status', true);
    xhr.onreadystatechange = function() {
      if (xhr.readyState !== 4) return;
      state.progressStatusInFlight = false;
      var result = null;
      try {
        result = JSON.parse(xhr.responseText || '{}');
      } catch (err) {
        return;
      }
      var run = result && result.run ? result.run : null;
      if (!run || !(run.active || run.action || run.stage || run.detail)) return;
      var runAction = String(run.action || '');
      if (runAction && state.progressAction && runAction !== state.progressAction) return;
      var runRequestId = String(run.requestId || run.request_id || '');
      if (state.progressRequestId && (!runRequestId || runRequestId !== state.progressRequestId)) return;
      state.progressStage = run.stage || state.progressStage;
      state.progressDetail = run.detail || state.progressDetail;
      state.progressAction = run.action || state.progressAction;
      renderRunState(run);
      if (run.active) updateProgressText();
      else finishProgressStage(state.progressStage, state.progressDetail);
    };
    xhr.onerror = function() {
      state.progressStatusInFlight = false;
    };
    xhr.send();
  }

  function startProgressStatusPolling() {
    stopProgressStatusPolling();
    refreshProgressRunState();
    state.progressStatusTimer = window.setInterval(refreshProgressRunState, 1500);
  }

  function stopProgressStatusPolling() {
    if (state.progressStatusTimer) {
      window.clearInterval(state.progressStatusTimer);
      state.progressStatusTimer = null;
    }
    state.progressStatusInFlight = false;
  }

  function setProgressStage(stage, detail) {
    state.progressStage = stage || state.progressStage;
    state.progressDetail = detail || state.progressDetail;
    updateProgressText();
  }

  function startProgress(action, stage, detail, requestId) {
    finishProgress('');
    state.progressRequestId = requestId || newRequestId();
    state.progressAction = action;
    state.progressStage = stage || '准备执行';
    state.progressDetail = detail || '正在收集当前上下文并准备请求。';
    state.progressStartedAt = Date.now();
    state.progressBody = addMessage('assistant', '');
    updateProgressText();
    state.progressTimer = window.setInterval(updateProgressText, 1000);
    startProgressStatusPolling();
  }

  function finishProgress(text) {
    stopProgressStatusPolling();
    if (state.progressTimer) {
      window.clearInterval(state.progressTimer);
      state.progressTimer = null;
    }
    if (state.progressBody && text) {
      state.progressBody.textContent = text;
    }
    state.progressBody = null;
    state.progressStartedAt = 0;
    state.progressRequestId = '';
    state.progressAction = '';
    state.progressStage = '';
    state.progressDetail = '';
  }

  function finishProgressStage(stage, detail) {
    if (!state.progressBody || !state.progressStartedAt) return;
    state.progressStage = stage || state.progressStage;
    state.progressDetail = detail || state.progressDetail;
    finishProgress(formatProgressText(progressElapsedSeconds(), false));
  }

  function enqueueAction(action, prompt) {
    postCompanionPath('/marginnote/enqueue', action, {
      prompt: prompt,
      _queue_raw: true,
      message: 'queued from web panel'
    }, function(result) {
      if (result && result.ok) {
        addGuideMessage('已自动加入队列：' + actionLabel(action) + '。上一个任务结束后会自动执行。', [
          {title: '停止当前并直接执行', kind: 'stop_then_run', action: action, prompt: prompt, userText: actionLabel(action)},
          {title: '查看队列状态', kind: 'queue_status'}
        ]);
      } else {
        addFailureMessage('入队失败', result);
      }
      refreshQueue();
    });
  }

  function enqueueGoalQueue(items, basePrompt) {
    items = items || [];
    var accepted = 0;
    for (var i = 0; i < items.length; i++) {
      var item = items[i] || {};
      var action = String(item.action || '');
      if (!isQueueableGoalAction(action)) continue;
      accepted += 1;
      postCompanionPath('/marginnote/enqueue', action, {
        prompt: item.prompt || basePrompt || '',
        _queue_raw: true,
        message: 'queued from goal queue: ' + (item.title || action)
      }, function() {
        refreshQueue();
      });
    }
    if (accepted) {
      addMessage('assistant', '目标已自动拆分为 ' + accepted + ' 个后续任务，已加入队列；上一个任务结束后会自动继续。');
    }
    return accepted;
  }

  function goalTextToPayload(goalText) {
    var value = String(goalText || '').replace(/^\s+|\s+$/g, '').substring(0, 3000);
    var lines = value.split(/\r?\n/);
    var cleanLines = [];
    for (var i = 0; i < lines.length; i++) {
      var line = String(lines[i] || '').replace(/^\s+|\s+$/g, '');
      if (line) cleanLines.push(line);
    }
    var title = cleanLines.length ? cleanLines[0] : '';
    title = title.replace(/^\[已排队目标\]\s*/, '').replace(/^目标[:：]\s*/, '');
    var detail = cleanLines.slice(1).join('\n').replace(/^\s+|\s+$/g, '');
    if (!title && value) title = value.substring(0, 160);
    return {title: title.substring(0, 160), detail: detail.substring(0, 3000)};
  }

  function requestGoalAction(goalText, userText, queueId) {
    state.currentQueueId = queueId || '';
    var goal = goalTextToPayload(goalText);
    if (!goal.title && !goal.detail) {
      addMessage('assistant', '队列目标为空，已跳过。');
      ackQueueAndContinue(queueId);
      return;
    }
    addMessage('user', userText || goalUserText(goal));
    setWebRunLock(true);
    window.CodexPanel.setBusy({busy: true});
    window.CodexPanel.setStatus({text: '正在执行目标：' + (goal.title || '未命名目标')});
    var requestId = newRequestId();
    startProgress('goal_run', '正在执行队列目标', '队列中的目标正在作为一次性任务提交给 Companion。', requestId);
    postCompanion('goal_run', {goal: goal, prompt: goalText, _web_run_owner: true, _request_id: requestId}, function(result) {
      setWebRunLock(false);
      window.CodexPanel.setBusy({busy: false});
      renderControls(result || {});
      if (!result || !result.ok) {
        finishProgressStage('失败', result && result.message ? result.message : '目标执行失败。');
        addFailureMessage('目标执行失败', result);
        ackQueueAndContinue(queueId);
        return;
      }
      if (result.queued_due_to_web_busy) {
        finishProgressStage('已加入队列', result.message || '目标已重新加入队列。');
        addMessage('assistant', result.message || '目标已重新加入队列。');
        ackQueueAndContinue(queueId);
        return;
      }
      reportActionResponse('goal_run', result || {});
      finishProgressStage('已完成', result.message || result.reply || '目标已完成。');
      if (enqueueGoalQueue(result.goalQueue, goalUserText(goal))) {
        window.setTimeout(drainNextQueuedAction, 500);
      } else {
        showFollowUpGuides('chat', goalUserText(goal));
      }
      ackQueueAndContinue(queueId);
    });
  }

  function requestDraftAction(action, prompt, userText, queueId) {
    state.currentQueueId = queueId || '';
    if (!ensureMindmapTargetReady(action)) {
      ackQueueAndContinue(queueId);
      return;
    }
    addMessage('user', userText || '[' + action + ']');
    renderDraft(null);
    setWebRunLock(true);
    window.CodexPanel.setBusy({busy: true});
    window.CodexPanel.setStatus({text: '正在生成草稿：' + actionLabel(action)});
    var requestId = newRequestId();
    startProgress(action, '正在生成草稿', '正在把当前上下文发送给 Companion，并等待卡片/脑图草稿。', requestId);
    postCompanion(action, {prompt: prompt, _web_run_owner: true, _request_id: requestId}, function(result) {
      if (!result || !result.ok) {
        setWebRunLock(false);
        window.CodexPanel.setBusy({busy: false});
        finishProgressStage('失败', result && result.message ? result.message : '草稿生成失败。');
        addFailureMessage('草稿生成失败', result);
        ackQueueAndContinue(queueId);
        return;
      }
      if (result.queued_due_to_web_busy) {
        setWebRunLock(false);
        window.CodexPanel.setBusy({busy: false});
        finishProgressStage('已加入队列', result.message || '已加入队列，上一个任务结束后会自动执行。');
        addMessage('assistant', result.message || '已加入队列，上一个任务结束后会自动执行。');
        if (queueId) {
          ackQueueAndContinue(queueId);
          return;
        }
        refreshQueue();
        return;
      }
      if (!result.cards && !result.mindmap) {
        setWebRunLock(false);
        window.CodexPanel.setBusy({busy: false});
        finishProgressStage('未生成脑图', result.message || '没有可写入的卡片或脑图。');
        addMessage('assistant', '没有可写入的卡片或脑图。');
        ackQueueAndContinue(queueId);
        return;
      }
      reportActionResponse(action, result || {});
      setProgressStage('正在保存草稿', '卡片/脑图内容已生成，正在保存到本地草稿确认区。');
      postCompanionPath('/marginnote/draft', 'draft_save', {
        originalAction: action,
        draft: result,
        writeTarget: result.writeTarget || (result.mindmap && result.mindmap.writeTarget) || (state.mindmapTarget && state.mindmapTarget.target) || {}
      }, function(saved) {
        setWebRunLock(false);
        window.CodexPanel.setBusy({busy: false});
        if (saved && saved.ok && saved.draft) {
          renderDraft(saved.draft);
          writeDraftForAiEditOperation(saved.draft);
          finishProgressStage('已发送写入', '草稿已保存并发送给 MarginNote 写入。');
          ackQueueAndContinue(queueId);
        } else {
          finishProgressStage('失败', saved && saved.message ? saved.message : '草稿保存失败。');
          addFailureMessage('草稿保存失败', saved);
          ackQueueAndContinue(queueId);
        }
      });
    }, {showReply: false});
  }

  function stagePromptAction(action, prompt, label) {
    var stagedPrompt = String(prompt || '');
    state.stagedAction = String(action || 'chat');
    state.stagedPrompt = stagedPrompt;
    state.stagedLabel = String(label || actionLabel(state.stagedAction));
    setValue('promptInput', stagedPrompt);
    switchTab('chat');
    switchProductMode('chat');
    renderStagedActionLine();
    updateActionAvailability();
    updateRunToggleButton();
    window.CodexPanel.setStatus({text: '待发送：' + state.stagedLabel + ' / ' + actionLabel(state.stagedAction)});
  }

  function stageOrExplainPromptAction(action, prompt, label) {
    var stagedPrompt = String(prompt || '');
    var stagedAction = String(action || 'chat');
    var unavailable = actionUnavailableReason(stagedAction, stagedPrompt);
    if (unavailable) {
      addMessage('assistant', unavailable);
      updateActionAvailability();
      return false;
    }
    stagePromptAction(stagedAction, stagedPrompt, label);
    return true;
  }

  function runStagedAction() {
    sendAction('chat');
  }

  function clearStagedPrompt() {
    state.stagedAction = '';
    state.stagedPrompt = '';
    state.stagedLabel = '';
    renderStagedActionLine();
  }

  function renderStagedActionLine() {
    var line = byId('stagedActionLine');
    var text = byId('stagedActionText');
    if (!line) return;
    if (!state.stagedAction) {
      line.className = 'staged-action-line hidden';
      if (text) text.textContent = '';
      return;
    }
    line.className = 'staged-action-line';
    if (text) {
      text.textContent =
        '待发送：' + (state.stagedLabel || actionLabel(state.stagedAction)) +
        ' / ' + actionLabel(state.stagedAction) +
        '。可先改输入框，再点发送或立即执行。';
    }
  }

  function runPromptAction(action, prompt, label) {
    executeAction(action, prompt || '', label || actionLabel(action));
  }

  function executeAction(action, prompt, userText) {
    prompt = prompt || '';
    userText = userText || prompt || state.lastPromptFromSelection || '';
    var unavailable = actionUnavailableReason(action, prompt);
    if (unavailable) {
      addMessage('assistant', unavailable);
      updateActionAvailability();
      return false;
    }
    if (isActiveRun()) {
      addMessage('user', '[已排队] ' + (userText || actionLabel(action)));
      window.CodexPanel.setStatus({text: '当前任务运行中，已把“' + actionLabel(action) + '”加入队列'});
      enqueueAction(action, prompt);
      return true;
    }
    if (action === 'request_native_highlight_selection') {
      startNativeHighlightWizard();
      return true;
    }
    if (isWriteAction(action)) {
      requestDraftAction(action, prompt, userText || '[' + action + '] 当前内容');
      return true;
    }
    if (action === 'chat' || action === 'explain_selection') {
      requestTextAction(action, prompt, userText || '[' + action + ']');
      return true;
    }
    requestTextAction(action, prompt, '[' + action + '] ' + (userText || '当前内容'));
    return true;
  }

  function sendAction(action) {
    var prompt = repairPdfExtractedMathText(promptValue());
    var useSelectionFallback = currentContextScope() !== 'document';
    var naturalText = prompt || (useSelectionFallback ? state.lastPromptFromSelection : '') || '';
    var chatPrompt = prompt || (useSelectionFallback ? state.lastPromptFromSelection : '') || '';
    if (executeAction('chat', chatPrompt, naturalText || '问 AI') !== false) {
      clearPromptInputAfterSend();
      clearStagedPrompt();
    }
  }

  function normalizePdfCacheState(cache) {
    cache = cache || {};
    var raw = String(cache.state || cache.status || 'unknown').toLowerCase();
    if (raw === 'ok') return 'cached';
    if (raw === 'permission') return 'permission';
    if (raw === 'error') return 'error';
    if (raw === 'warn' || raw === 'warning') return 'warning';
    if (raw === 'waiting_native' || raw === 'pending' || raw === 'caching') return 'waiting_native';
    if (raw === 'missing') return 'missing';
    return raw || 'unknown';
  }

  function renderPdfCacheStatusFromText(text) {
    var value = String(text || '').replace(/^\s+|\s+$/g, '');
    if (!value) return;
    if (!/(PDF\s*缓存|PDF缓存|当前 PDF|可缓存的 PDF|读取当前 PDF|上传当前 PDF)/i.test(value)) return;
    if (/PDF 缓存失败|失败|错误|无法|不能|没有可缓存|读取失败|文件为空|超过|转码失败|未返回有效|not found|error|permission|denied/i.test(value)) {
      renderPdfCacheBanner({
        state: 'error',
        label: 'PDF 缓存失败',
        detail: value,
        pending: false
      });
      return;
    }
    if (/PDF 缓存完成|完成|已缓存|缓存到 Companion|已提交|已由 MarginNote|已就绪/i.test(value)) {
      renderPdfCacheBanner({
        state: 'cached',
        label: 'PDF 缓存完成',
        detail: value,
        pending: false
      });
      return;
    }
    if (/正在读取当前 PDF|正在上传当前 PDF 缓存|等待|缓存当前 PDF|保持.*PDF.*缓存|上传缓存/i.test(value)) {
      renderPdfCacheBanner({
        state: 'waiting_native',
        label: 'PDF缓存：缓存中',
        detail: value,
        pending: true
      });
    }
  }

  function renderPdfCacheBanner(cache) {
    if (cache) state.pdfCache = cache;
    cache = state.pdfCache || {};
    var banner = byId('pdfCacheBanner');
    var text = byId('pdfCacheBannerText');
    if (!banner || !text) return;
    var pdfState = normalizePdfCacheState(cache);
    if (!pdfState || pdfState === 'unknown' || pdfState === 'missing') {
      banner.className = 'pdf-cache-banner idle';
      var idleLabel = cache.label || (pdfState === 'missing' ? 'PDF缓存：尚未缓存' : 'PDF缓存：等待当前文档');
      var idleDetail = cache.detail || (pdfState === 'missing' ? '当前文档还没有缓存副本。' : '打开或刷新当前文档后会自动更新状态。');
      text.textContent = idleDetail ? idleLabel + '：' + idleDetail : idleLabel;
      return;
    }
    var label = cache.label || 'PDF缓存';
    var detail = cache.detail || '';
    if (pdfState === 'waiting_native' && !detail) {
      detail = '保持当前 PDF 打开，MN4 插件正在上传缓存。';
    } else if (pdfState === 'cached' && !detail) {
      detail = '缓存完成，全文读取已就绪。';
    } else if (pdfState === 'permission' && !detail) {
      detail = '后台读取受限，等待 MN4 插件上传缓存。';
    }
    if (pdfState === 'waiting_native' && /等待 MN4 缓存/.test(label)) label = 'PDF缓存：缓存中';
    if (pdfState === 'cached' && /已就绪/.test(label)) label = 'PDF缓存：缓存完成';
    if ((pdfState === 'permission' || pdfState === 'error') && !/缓存失败|权限受限|读取异常/.test(label)) {
      label = 'PDF缓存：缓存失败';
    }
    var className = 'pdf-cache-banner ';
    if (pdfState === 'waiting_native' || pdfState === 'warning') {
      className += 'waiting';
    } else if (pdfState === 'cached') {
      className += 'cached';
    } else if (pdfState === 'permission') {
      className += 'permission';
    } else {
      className += 'error';
    }
    banner.className = className;
    text.textContent = detail ? label + '：' + detail : label;
  }

  function normalizeMindmapTargetState(targetState) {
    targetState = targetState || {};
    return String(targetState.state || targetState.status || 'unknown').toLowerCase();
  }

  function selectedMindmapTargetValue(target) {
    target = target || {};
    var mode = String(target.mode || '');
    return mode === 'merge_children_into_selected_node' ? 'selected_node' : (mode || 'document_root');
  }

  function renderMindmapTargetBar(targetState) {
    if (targetState) state.mindmapTarget = targetState;
    targetState = state.mindmapTarget || {};
    var bar = byId('mindmapTargetBar');
    var select = byId('mindmapTargetSelect');
    if (!bar || !select) return;
    var status = normalizeMindmapTargetState(targetState);
    if (!status || status === 'unknown') status = 'suggested';
    var options = targetState.options || [];
    var target = targetState.target || {};
    var selectedValue = selectedMindmapTargetValue(target);
    select.innerHTML = '';
    if (!options.length) {
      var empty = document.createElement('option');
      empty.value = '';
      empty.textContent = targetState.label || '目标脑图：未识别文档';
      select.appendChild(empty);
      select.disabled = true;
    } else {
      select.disabled = false;
      for (var i = 0; i < options.length; i++) {
        var item = options[i] || {};
        var option = document.createElement('option');
        option.value = String(item.value || '');
        option.textContent = item.label || item.value || '目标脑图';
        if (option.value === selectedValue) option.selected = true;
        select.appendChild(option);
      }
    }
    var label = targetState.label || (target.rootTitle ? ('文档脑图：' + target.rootTitle) : '目标脑图');
    select.title = (targetState.detail ? targetState.detail + '\n' : '') + label;
    bar.className = 'mindmap-target-bar ' + status;
    scheduleAgentPlanRefresh();
  }

  function refreshMindmapTarget() {
    postCompanion('mindmap_target_status', {}, function(result) {
      if (result && result.mindmapTarget) renderMindmapTargetBar(result.mindmapTarget);
      else renderMindmapTargetBar({state: 'error', label: result && result.message ? result.message : '目标脑图：刷新失败', target: {}, options: []});
    }, {showReply: false});
  }

  function updateMindmapTargetFromSelect(value) {
    if (!value) return;
    postCompanion('mindmap_target_update', {targetMode: value}, function(result) {
      renderControls(result || {});
      if (!result || !result.ok) addFailureMessage('设置目标脑图失败', result);
    }, {showReply: false});
  }

  function ensureMindmapTargetReady(action) {
    if (action !== 'generate_mindmap' && action !== 'generate_full_reading') return true;
    var targetState = state.mindmapTarget || {};
    var status = normalizeMindmapTargetState(targetState);
    if (status === 'blocked' || status === 'error') {
      var message = targetState.label || '目标脑图不可用：请先刷新 MarginNote 上下文或在顶部选择目标脑图。';
      addMessage('assistant', message);
      refreshMindmapTarget();
      return false;
    }
    return true;
  }

  function renderControls(result) {
    result = result || {};
    state.settings = result.settings || state.settings || {};
    if (result.pluginVersion) state.pluginVersion = String(result.pluginVersion || '');
    state.customButtons = cleanCustomButtons(state.settings.customButtons || state.customButtons || []);
    state.goal = result.goalOneShot ? {} : (result.goal || state.goal || {});
    state.files = result.files || state.files || [];
    state.queue = result.queue || state.queue || {pending: 0};
    renderPdfCacheBanner(result.pdfCache || (state.queue && state.queue.pdfCache));
    if (result.mindmapTarget) renderMindmapTargetBar(result.mindmapTarget);
    if (result.agentOperation) renderAgentWorkbench(result.agentOperation);
    if (result.mindmapTreeCache) renderMindmapTreeCacheStatus(result.mindmapTreeCache);
    if (result.mindmapDiff) renderMindmapDiffWorkbench(result);
    if (result.mindmapDiffApply) renderMindmapDiffApplyStatus(result.mindmapDiffApply);
    if (result.aiEditTransactionStatus) renderAiEditTransactionCenter(result.aiEditTransactionStatus);
    if (result.notebookWorkspace) renderNotebookWorkspace(result.notebookWorkspace);
    if (result.knowledgeWorkspace || result.knowledgeIndex || result.knowledgeIndexStatus) {
      renderKnowledgeWorkspace(result.knowledgeWorkspace || result.knowledgeIndex || result.knowledgeIndexStatus);
    }
    if (result.workflowWorkspace || result.workflowRuns || result.workflowStatus) {
      renderWorkflowWorkspace(result.workflowWorkspace || result.workflowStatus || result);
    }
    renderWorkbenchPanels();
    updateReadiness(result);
    setValue('aiBackendSelect', state.settings.aiBackend || state.aiBackend || 'auto');
    setValue('permissionSelect', state.settings.permission || 'notes');
    renderMnApiStatus(result);
    renderWorkflowWorkspace();
    setValue('modelInput', state.settings.model || 'gpt-5.5');
    setValue('speedSelect', state.settings.speed || 'fast');
    setValue('proxyUrlInput', state.settings.proxyUrl || '');
    setValue('codexCliPathInput', state.settings.codexCliPath || state.codexCliPath || '');
    setValue('defaultContextScopeSelect', state.settings.defaultContextScope || 'auto');
    setValue('githubRepoInput', state.settings.githubRepo || (state.update && state.update.repo) || 'LiuWhale/marginnote-assistant');
    renderFileSearchRoots(state.settings);
    if (!state.contextScopeInitialized) {
      state.contextScopeInitialized = true;
      setContextScope(state.settings.defaultContextScope || 'auto');
    }
    setValue('goalTitleInput', state.goal.title || '');
    setValue('goalDetailInput', state.goal.detail || '');
    var pending = state.queue && state.queue.pending !== undefined ? state.queue.pending : 0;
    var fileCount = state.files ? state.files.length : 0;
    renderRunState(result.run || (state.queue && state.queue.run));
    setBusyButtons(isActiveRun());
    setText('queueBadge', pending + ' pending / ' + fileCount + ' files');
    updateRunToggleButton();
    renderGoalStatus();
    if (result.fileAccess) renderFileAccess(result);
    renderMnRuntime(result);
    renderNativeCapabilities(result);
    renderUpdateStatus(result);
    if (result.logs) renderDiagnosticLogs(result);
    renderSettingsContextMeta(state.context || {});
    if (result.nativeHighlightWizard) renderNativeHighlightWizard(result);
    if (result.releaseAcceptance || result.releasable !== undefined || result.blockerCount !== undefined) {
      renderReleaseAcceptance(result);
    }
    renderMainPinnedButtons();
    renderCustomButtons();
    updateActionAvailability();
    if (!state.busy && pending > 0) {
      window.setTimeout(drainNextQueuedAction, 300);
    }
  }

  function renderRunState(run) {
    run = run || {};
    state.runActive = !!run.active;
    var line = byId('runStateLine');
    if (!line) return;
    var stage = String(run.stage || (run.active ? '正在执行' : '空闲'));
    var detail = String(run.detail || (run.active ? '任务正在运行。' : '没有正在运行的任务。'));
    var action = run.action ? actionLabel(String(run.action)) : '任务';
    var elapsed = run.elapsed_seconds !== undefined ? parseInt(run.elapsed_seconds || 0, 10) : 0;
    var prefix = run.active ? '运行中' : '最近';
    if (!run.action && !run.active) {
      line.textContent = '运行：空闲';
      line.className = 'run-state-line';
      setBusyButtons(isActiveRun());
      updateRunToggleButton();
      return;
    }
    line.textContent = prefix + '：' + action + ' / ' + stage + ' / ' + detail + ' / ' + elapsed + 's';
    line.className = 'run-state-line' + (run.active ? ' active' : '');
    setBusyButtons(isActiveRun());
    updateRunToggleButton();
  }

  function renderGoalStatus() {
    var line = byId('goalStatusLine');
    if (!line) return;
    var goal = state.goal || {};
    var title = String(goal.title || '').replace(/^\s+|\s+$/g, '');
    var detail = String(goal.detail || '').replace(/^\s+|\s+$/g, '');
    if (!title && !detail) {
      line.textContent = '当前目标：未设置';
      line.className = 'goal-status-line empty';
      return;
    }
    line.textContent = '当前目标：' + clip(title || detail, 38);
    line.className = 'goal-status-line active';
  }

  function parseFileSearchRootsInput() {
    var raw = getValue('fileSearchRootsInput');
    var seen = {};
    var roots = [];
    var lines = String(raw || '').split(/\r?\n/);
    for (var i = 0; i < lines.length; i++) {
      var value = lines[i].replace(/^\s+|\s+$/g, '');
      if (!value || seen[value]) continue;
      seen[value] = true;
      roots.push(value);
      if (roots.length >= 40) break;
    }
    return roots;
  }

  function renderFileSearchRoots(settings) {
    settings = settings || state.settings || {};
    var roots = settings.fileSearchRoots || [];
    if (!roots || !roots.length) roots = [];
    setValue('fileSearchRootsInput', roots.join('\n'));
    setText(
      'fileSearchRootsStatusLine',
      roots.length ? ('已配置 ' + roots.length + ' 个文件路径') : '未配置额外文件路径'
    );
  }

  function saveFileSearchRoots() {
    postCompanion('settings_update', {
      settings: {
        fileSearchRoots: parseFileSearchRootsInput()
      }
    }, function(result) {
      renderControls(result || {});
      if (!result || !result.ok) addFailureMessage('保存文件路径失败', result);
    }, {showReply: false});
  }

  function renderDiagnosticLogs(result) {
    result = result || {};
    var logs = result.logs || state.diagnosticLogs || [];
    state.diagnosticLogs = logs;
    var pathText = result.logPath ? (' / ' + result.logPath) : '';
    setText('logsStatusLine', '诊断日志：最近 ' + logs.length + ' 条' + pathText);
    var list = byId('logsList');
    if (!list) return;
    list.innerHTML = '';
    if (!logs.length) {
      var empty = document.createElement('div');
      empty.className = 'diagnostic-log-empty';
      empty.textContent = '暂无诊断日志';
      list.appendChild(empty);
      return;
    }
    for (var i = logs.length - 1; i >= 0; i--) {
      var item = logs[i] || {};
      var row = document.createElement('div');
      row.className = 'diagnostic-log-item';
      var meta = document.createElement('div');
      meta.className = 'diagnostic-log-meta';
      meta.textContent = [
        item.ts || 'no-ts',
        item.level || 'info',
        item.event || 'event',
        item.requestId ? ('#' + item.requestId) : ''
      ].filter(Boolean).join(' / ');
      var message = document.createElement('div');
      message.className = 'diagnostic-log-message';
      message.textContent = item.message || '';
      row.appendChild(meta);
      row.appendChild(message);
      list.appendChild(row);
    }
  }

  function refreshDiagnosticLogs() {
    postCompanion('logs_recent', {limit: 80}, function(result) {
      renderDiagnosticLogs(result || {});
      if (!result || !result.ok) addFailureMessage('读取诊断日志失败', result);
    }, {showReply: false});
  }

  function clearDiagnosticLogs() {
    if (window.confirm && !window.confirm('确认清空诊断日志？')) return;
    postCompanion('logs_clear', {}, function(result) {
      renderDiagnosticLogs(result || {logs: []});
      if (!result || !result.ok) addFailureMessage('清空诊断日志失败', result);
    }, {showReply: false});
  }

  function refreshSettings() {
    postCompanion('settings_get', {}, function(result) {
      renderControls(result || {});
      if (!state.updateAutoChecked) {
        state.updateAutoChecked = true;
        window.setTimeout(function() {
          checkForUpdates(true);
        }, 800);
      }
    }, {showReply: false});
  }

  function saveSettings() {
    var openaiApiKey = getValue('openaiApiKeyInput');
    var mnUrlApiSecret = getValue('mnUrlApiSecretInput');
    postCompanion('settings_update', {
      settings: {
        aiBackend: getValue('aiBackendSelect'),
        mnApiBackend: getValue('mnApiBackendSelect'),
        permission: getValue('permissionSelect'),
        model: getValue('modelInput'),
        speed: getValue('speedSelect'),
        codexCliPath: getValue('codexCliPathInput'),
        proxyUrl: getValue('proxyUrlInput'),
        defaultContextScope: getValue('defaultContextScopeSelect'),
        githubRepo: getValue('githubRepoInput'),
        fileSearchRoots: parseFileSearchRootsInput(),
        customButtons: state.customButtons,
        openaiApiKey: openaiApiKey,
        mnUrlApiSecret: mnUrlApiSecret
      }
    }, function(result) {
      if (openaiApiKey) setValue('openaiApiKeyInput', '');
      if (mnUrlApiSecret) setValue('mnUrlApiSecretInput', '');
      renderControls(result || {});
      setContextScope((result && result.settings && result.settings.defaultContextScope) || getValue('defaultContextScopeSelect') || 'auto');
    });
  }

  function clearOpenAIKey() {
    if (window.confirm && !window.confirm('确认清除本机保存的 OpenAI Key？')) return;
    setValue('openaiApiKeyInput', '');
    postCompanion('settings_update', {
      settings: {
        clearOpenAIKey: true
      }
    }, function(result) {
      renderControls(result || {});
      if (!result || !result.ok) addFailureMessage('清除 OpenAI Key 失败', result);
    });
  }

  function clearMnUrlApiSecret() {
    if (window.confirm && !window.confirm('确认清除本机保存的 URL API Secret？')) return;
    setValue('mnUrlApiSecretInput', '');
    postCompanion('settings_update', {
      settings: {
        clearMnUrlApiSecret: true
      }
    }, function(result) {
      renderControls(result || {});
      if (!result || !result.ok) addFailureMessage('清除 URL API Secret 失败', result);
    });
  }

  function probeAiBackend() {
    postCompanion('ai_backend_probe', {}, function(result) {
      renderControls(result || {});
      if (!result || !result.ok) addFailureMessage('AI 后端试连失败', result);
    });
  }

  function checkHealth() {
    postCompanion('health', {}, function(result) {
      renderControls(result || {});
      if (result && result.ok) {
        addMessage('assistant', result.reply || result.message || 'Companion 连接正常。');
      } else {
        addFailureMessage('连接检查失败', result);
      }
    });
  }

  function renderUpdateStatus(result) {
    result = result || {};
    if (result.pluginVersion) state.pluginVersion = String(result.pluginVersion || '');
    if (result.update) state.update = result.update || {};
    var update = state.update || {};
    var settings = result.settings || state.settings || {};
    var repo = settings.githubRepo || update.repo || 'LiuWhale/marginnote-assistant';
    setValue('githubRepoInput', repo);
    var current = update.currentVersion || state.pluginVersion || '0.4.1';
    var latest = update.latestVersion || '未检查';
    var status = String(update.state || 'unknown');
    var message = update.message || '尚未检查更新。';
    setText('updateVersionLine', '当前：' + current + ' / 最新：' + latest);
    var line = byId('updateStatusLine');
    if (line) {
      if (update.available) {
        line.textContent = '更新：发现新版本 ' + latest;
        line.className = 'update-status-line available';
      } else if (status === 'error' || update.ok === false) {
        line.textContent = '更新：检查失败';
        line.className = 'update-status-line error';
      } else if (status === 'installing') {
        line.textContent = '更新：正在安装';
        line.className = 'update-status-line available';
      } else if (status === 'ready') {
        line.textContent = '更新：已下载待安装';
        line.className = 'update-status-line available';
      } else if (status === 'current') {
        line.textContent = '更新：已是最新';
        line.className = 'update-status-line';
      } else {
        line.textContent = '更新：尚未检查';
        line.className = 'update-status-line';
      }
    }
    setText('updateStatusDetail', message);
    var installButton = byId('updateInstallButton');
    if (installButton) {
      installButton.disabled = false;
      installButton.textContent = '打开下载页';
    }
    var notice = byId('updateNotice');
    if (notice) {
      notice.className = update.available ? 'update-notice' : 'update-notice hidden';
    }
    setText('updateNoticeText', update.available ? ('发现插件更新：v' + latest) : '');
  }

  function openUpdateSettings() {
    openConfigPage();
    var section = byId('updateSection');
    if (section && section.scrollIntoView) section.scrollIntoView({block: 'start'});
  }

  function checkForUpdates(silent) {
    var button = byId('updateCheckButton');
    if (button) {
      button.disabled = true;
      button.textContent = '检查中...';
    }
    setText('updateStatusLine', '更新：正在检查');
    setText('updateStatusDetail', '正在检查 GitHub Release...');
    postCompanion('update_check', {
      githubRepo: getValue('githubRepoInput')
    }, function(result) {
      if (button) {
        button.disabled = false;
        button.textContent = '检查更新';
      }
      renderControls(result || {});
      if (!result || !result.ok) {
        if (!silent) addFailureMessage('检查更新失败', result);
        return;
      }
      if (!silent) addMessage('assistant', result.message || '已检查更新。');
    }, {showReply: false});
  }

  function installUpdate() {
    var update = state.update || {};
    var repo = getValue('githubRepoInput') || update.repo || 'LiuWhale/marginnote-assistant';
    var fallback = 'https://github.com/' + repo.replace(/^\/+|\/+$/g, '') + '/releases';
    var url = update.releaseUrl || update.downloadUrl || fallback;
    addMessage('assistant', '正在打开下载页面：' + url);
    postCompanion('open_url', {url: url}, function(result) {
      if (result && result.ok) {
        addMessage('assistant', result.message || '已打开下载页面。');
        return;
      }
      bridge('open_url', {url: url});
      addFailureMessage('Companion 打开下载页失败，已尝试交给 MN4 打开', result);
    }, {showReply: false});
  }

  function trimText(text, limit) {
    var value = String(text || '').replace(/^\s+|\s+$/g, '');
    return limit && value.length > limit ? value.substring(0, limit) : value;
  }

  function goalInputValue() {
    var title = trimText(getValue('goalTitleInput'), 160);
    var detail = trimText(getValue('goalDetailInput'), 3000);
    if (!title && promptValue()) {
      title = trimText(promptValue(), 160);
    }
    return {title: title, detail: detail};
  }

  function goalUserText(goal) {
    var parts = ['目标：' + (goal.title || '未命名目标')];
    if (goal.detail) parts.push(goal.detail);
    return parts.join('\n\n');
  }

  function setGoalPanelVisible(visible) {
    var panel = byId('goalPanel');
    if (!panel) return;
    panel.className = 'goal-panel' + (visible ? '' : ' hidden');
    var button = byId('goalToggleButton');
    if (button) {
      button.className = 'goal-toggle-button' + (visible ? ' active' : '');
      button.setAttribute('aria-expanded', visible ? 'true' : 'false');
    }
    if (visible && byId('goalTitleInput')) {
      window.setTimeout(function() { byId('goalTitleInput').focus(); }, 0);
    }
  }

  function toggleGoalPanel() {
    var panel = byId('goalPanel');
    var hidden = !panel || panel.className.indexOf('hidden') >= 0;
    setGoalPanelVisible(hidden);
  }

  function runGoalWithValue(goal) {
    if (!goal.title && !goal.detail) {
      addMessage('assistant', '先输入一个目标。');
      setGoalPanelVisible(true);
      return;
    }
    clearPromptInputAfterSend();
    if (isActiveRun()) {
      addMessage('user', '[已排队目标] ' + (goal.title || '未命名目标'));
      enqueueAction('goal_run', goalUserText(goal));
      return;
    }
    addMessage('user', goalUserText(goal));
    setWebRunLock(true);
    window.CodexPanel.setBusy({busy: true});
    window.CodexPanel.setStatus({text: '正在执行目标：' + (goal.title || '未命名目标')});
    var requestId = newRequestId();
    startProgress('goal_run', '已提交目标', 'Companion 正在把目标作为一次性任务执行。', requestId);
    postCompanion('goal_run', {goal: goal, _web_run_owner: true, _request_id: requestId}, function(result) {
      setWebRunLock(false);
      window.CodexPanel.setBusy({busy: false});
      renderControls(result || {});
      if (!result || !result.ok) {
        finishProgressStage('失败', result && result.message ? result.message : '目标执行失败。');
        addFailureMessage('目标执行失败', result);
        return;
      }
      if (result.queued_due_to_web_busy) {
        finishProgressStage('已加入队列', result.message || '目标已加入队列。');
        addMessage('assistant', result.message || '目标已加入队列。');
        refreshQueue();
        return;
      }
      reportActionResponse('goal_run', result || {});
      finishProgressStage('已完成', result.message || result.reply || '目标已完成。');
      if (enqueueGoalQueue(result.goalQueue, goalUserText(goal))) {
        window.setTimeout(drainNextQueuedAction, 500);
      } else {
        showFollowUpGuides('chat', goalUserText(goal));
        drainNextQueuedAction();
      }
    });
  }

  function runGoal() {
    var goal = {
      title: goalInputValue().title,
      detail: goalInputValue().detail
    };
    runGoalWithValue(goal);
  }

  function refreshQueue() {
    postCompanion('queue_status', {}, function(result) {
      renderControls(result || {queue: {pending: 0}});
    });
  }

  function queuePumpTick() {
    if (isActiveRun() || state.drainingQueue) return;
    var ctx = state.context || {};
    if (!(ctx.topicid || ctx.notebookid)) return;
    var xhr = new XMLHttpRequest();
    xhr.open('POST', 'http://127.0.0.1:48761/marginnote/action', true);
    xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    xhr.onreadystatechange = function() {
      if (xhr.readyState !== 4) return;
      var result = null;
      try {
        result = JSON.parse(xhr.responseText || '{}');
      } catch (err) {
        return;
      }
      if (result && result.queue) {
        renderControls(result || {});
        if (!isActiveRun() && result.queue.pending > 0) {
          drainNextQueuedAction();
        }
      }
    };
    xhr.send(JSON.stringify(companionPayload('queue_status', {})));
  }

  function startQueuePump() {
    if (state.queuePumpTimer) return;
    state.queuePumpTimer = window.setInterval(queuePumpTick, 3000);
    window.setTimeout(queuePumpTick, 600);
  }

  function startContextAutoRefresh() {
    if (state.contextAutoRefreshTimer) return;
    state.contextAutoRefreshTimer = window.setInterval(function() {
      if (isActiveRun()) return;
      if (isTextInputActive()) return;
      bridge('context', {reason: 'auto-refresh'});
    }, 5000);
  }

  function refreshHistory() {
    postCompanion('history_list', {}, function(result) {
      renderHistoryItems(result.history || []);
    });
  }

  function clearHistory() {
    postCompanion('history_clear', {}, function() {
      renderHistoryItems([]);
    });
  }

  function stopCurrent() {
    var queueId = state.currentQueueId || '';
    setWebRunLock(false);
    state.runActive = false;
    finishProgressStage('已停止', '已请求终止当前生成；不会继续写入当前队列项。');
    window.CodexPanel.setBusy({busy: false});
    postCompanion('stop_current', {queue_id: queueId}, function(result) {
      state.currentQueueId = '';
      renderControls(result || {queue: state.queue});
      refreshQueue();
    });
  }

  function writeAcceptedDraft(draftId, panel) {
    bridge('write_draft', {id: draftId});
    renderDraft(null);
    if (panel) {
      if (panel.className && panel.className.indexOf('mindmap-diff-operation') !== -1) {
        setMindmapDiffStatus(panel, '已接受，写入请求已发送。', 'accepted');
        setMindmapDiffBusy(panel, true);
      } else if (panel.className && panel.className.indexOf('operation-plan-panel') !== -1) {
        setOperationPlanStatus(panel, '已接受，写入请求已发送。', 'accepted');
        setOperationPlanBusy(panel, true);
      } else {
        setAiEditOperationStatus(panel, '已接受，写入请求已发送。', 'accepted');
        setAiEditOperationBusy(panel, true);
      }
    } else {
      addMessage('assistant', '已发送写入请求：' + draftId);
    }
  }

  function currentAiEditTransactionId(panel) {
    if (panel) {
      var panelId = panel.getAttribute('data-transaction-id') || '';
      if (panelId) return panelId;
    }
    return state.draft && state.draft.transactionId ? state.draft.transactionId : '';
  }

  function acceptDraft(panel) {
    if (!state.draft || !state.draft.id) {
      addMessage('assistant', '没有待写入草稿。');
      return;
    }
    var transactionId = currentAiEditTransactionId(panel);
    if (transactionId) {
      setAiEditOperationBusy(panel, true);
      setAiEditOperationStatus(panel, '已接受，保留本次新增内容。', 'accepted');
      bridge('accept_ai_edit_transaction', {transactionId: transactionId});
      return;
    }
    var draftId = state.draft.id;
    var editor = byId('draftEditText');
    var editText = editor ? currentDraftEditText() : '';
    if (!editor || !String(editText || '').replace(/^\s+|\s+$/g, '')) {
      writeAcceptedDraft(draftId, panel);
      return;
    }
    setAiEditOperationBusy(panel, true);
    setAiEditOperationStatus(panel, '正在保存编辑...', 'saving');
    postCompanion('draft_update', {id: draftId, editText: editText}, function(result) {
      if (!result || !result.ok) {
        setAiEditOperationBusy(panel, false);
        setAiEditOperationStatus(panel, result && result.message ? result.message : '草稿编辑保存失败。', 'error');
        addFailureMessage('草稿编辑保存失败', result);
        return;
      }
      writeAcceptedDraft(draftId, panel);
    });
  }

  function rejectDraft(panel) {
    var transactionId = currentAiEditTransactionId(panel);
    if (transactionId) {
      setAiEditOperationBusy(panel, true);
      setAiEditOperationStatus(panel, '正在删除本次新增内容...', 'rejected');
      bridge('reject_ai_edit_transaction', {transactionId: transactionId});
      return;
    }
    var draftId = state.draft && state.draft.id ? state.draft.id : '';
    if (state.draft && state.draft.id) {
      postCompanion('draft_delete', {id: state.draft.id}, function() {});
    }
    renderDraft(null);
    if (panel) {
      setAiEditOperationBusy(panel, true);
      setAiEditOperationStatus(panel, draftId ? '已拒绝并丢弃草稿。' : '已拒绝。', 'rejected');
    } else {
      addMessage('assistant', '已丢弃草稿。');
    }
  }

  function runToggle() {
    if (isActiveRun()) {
      stopCurrent();
      return;
    }
    var pending = state.queue && state.queue.pending !== undefined ? parseInt(state.queue.pending || 0, 10) : 0;
    if (pending > 0) {
      drainNextQueuedAction();
      return;
    }
    refreshQueue();
    addMessage('assistant', '当前没有 pending 任务。发送请使用输入框右侧的“发送”，动作请点击下方对应按钮。');
  }

  function uploadFromInputs() {
    var fileEl = byId('fileInput');
    var filePath = getValue('filePathInput');
    if (fileEl && fileEl.files && fileEl.files.length) {
      var file = fileEl.files[0];
      if (file.size > 200000) {
        window.CodexPanel.setStatus({text: 'Web 面板上传文本上限为 200 KB；请改用文件路径。'});
        return;
      }
      var reader = new FileReader();
      reader.onload = function() {
        postCompanion('upload_file', {
          fileName: file.name,
          fileContent: String(reader.result || '')
        }, renderControls);
      };
      reader.onerror = function() {
        window.CodexPanel.setStatus({text: '读取文件失败'});
      };
      reader.readAsText(file);
      return;
    }
    postCompanion('upload_file', {filePath: filePath, fileName: filePath.split('/').pop()}, renderControls);
  }

  function openConfigPage() {
    closeConversationHistory();
    var page = byId('configPage');
    if (page) page.className = 'config-page';
    renderSettingsContextMeta(state.context || {});
    refreshDiagnosticLogs();
  }

  function closeConfigPage() {
    var page = byId('configPage');
    if (page) page.className = 'config-page hidden';
  }

  function renderContextPreview() {
    var parts = [];
    if (state.context.selectionText) parts.push(state.context.selectionText);
    if (state.context.selectedNoteTitle) parts.push('节点：' + state.context.selectedNoteTitle);
    if (state.context.selectedNoteText) parts.push(state.context.selectedNoteText);
    var preview = parts.join('\n\n').trim();
    state.lastPromptFromSelection = preview;
    if (currentContextScope() === 'document' && hasDocumentContext()) {
      setText('selectionPreview', '将使用当前 PDF 全文检索。你仍然可以输入具体问题来缩小范围。');
      return;
    }
    if (currentContextScope() === 'selection' && !preview) {
      setText('selectionPreview', '当前选择“选区”，但还没有 PDF 选区或 MN 节点。');
      return;
    }
    setText('selectionPreview', preview || '在 MN4 中选中内容，或直接输入问题。');
  }

  function renderSettingsContextMeta(ctx) {
    ctx = ctx || state.context || {};
    var topic = ctx.topicid || ctx.notebookid || '未识别 notebook';
    var doc = ctx.documentTitle || ctx.docmd5 || ctx.bookmd5 || ctx.pdfPath || ctx.documentPath || '未识别文档';
    var sources = [];
    if (compactText(ctx.selectionText || ctx.selectedText || ctx.activeSelectionText)) sources.push('PDF 选区');
    if (compactText(ctx.selectedNoteTitle) || compactText(ctx.selectedNoteText) || compactText(ctx.selectedNoteId || ctx.noteId || ctx.noteid)) {
      sources.push('脑图节点');
    }
    if (compactText(ctx.docmd5) || compactText(ctx.bookmd5) || compactText(ctx.documentTitle) || compactText(ctx.pdfPath)) {
      sources.push('当前文档');
    }
    setText('settingsNotebookLine', topic);
    setText('settingsDocumentLine', doc);
    setText(
      'settingsContextScopeLine',
      '策略：' + currentContextScope() + ' / 可见：' + (sources.length ? sources.join(' / ') : '未选择上下文')
    );
  }

  function autoRequestPdfCacheForCurrentContext() {
    var ctx = state.context || {};
    var topicid = String(ctx.topicid || ctx.notebookid || '');
    var bookmd5 = String(ctx.bookmd5 || ctx.docmd5 || '');
    var docKey = String(bookmd5 || ctx.documentTitle || ctx.pdfPath || ctx.documentPath || '');
    if (!topicid || !bookmd5 || !docKey) return;
    if (state.autoPdfCacheRequestedKey === docKey) return;
    var cacheState = normalizePdfCacheState(state.pdfCache);
    if (cacheState === 'cached' || cacheState === 'waiting_native') return;
    state.autoPdfCacheRequestedKey = docKey;
    renderPdfCacheBanner({
      state: 'waiting_native',
      label: 'PDF缓存：缓存中',
      detail: '已自动请求缓存当前文档；保持该 PDF 在 MarginNote 中打开。',
      pending: true
    });
    postCompanion('request_pdf_cache', {auto: true}, function(result) {
      renderControls(result || {});
      if (!result || !result.ok) {
        renderPdfCacheBanner({
          state: 'error',
          label: 'PDF 缓存失败',
          detail: result && result.message ? result.message : '自动缓存请求失败。',
          pending: false
        });
      }
    }, {showReply: false});
  }

  function renderContext(ctx) {
    state.context = repairContextPayload(ctx || {});
    var docKey = String(
      state.context.bookmd5 ||
      state.context.docmd5 ||
      state.context.documentTitle ||
      state.context.pdfPath ||
      state.context.documentPath ||
      ''
    );
    if (docKey && state.contextDocumentKey && docKey !== state.contextDocumentKey) {
      state.pdfCache = {state: 'unknown'};
      renderPdfCacheBanner(state.pdfCache);
    }
    if (docKey) state.contextDocumentKey = docKey;
    renderContextSourceLine(state.context);
    var connected = state.context.topicid || state.context.notebookid || state.context.docmd5 || state.context.bookmd5;
    setText('contextLine', connected ? '已连接 MarginNote 上下文' : '等待 MarginNote 上下文');
    renderSettingsContextMeta(state.context);

    renderContextPreview();
    renderWorkbenchPanels();
    autoRequestPdfCacheForCurrentContext();
    refreshMindmapTarget();
    scheduleAgentPlanRefresh();
    updateActionAvailability();
  }

  function renderContextSourceLine(ctx) {
    ctx = ctx || state.context || {};
    var line = byId('contextSourceLine');
    if (!line) return;

    var selectedSources = [];
    if (compactText(ctx.selectionText || ctx.selectedText || ctx.activeSelectionText)) {
      selectedSources.push('PDF 选区');
    }
    if (
      compactText(ctx.selectedNoteTitle) ||
      compactText(ctx.selectedNoteText) ||
      compactText(ctx.selectedNoteId || ctx.noteId || ctx.noteid)
    ) {
      selectedSources.push('脑图节点');
    }
    var hasDocument = !!(
      compactText(ctx.docmd5) ||
      compactText(ctx.bookmd5) ||
      compactText(ctx.documentTitle) ||
      compactText(ctx.documentPath) ||
      compactText(ctx.pdfPath) ||
      compactText(state.lastSourcePdfPath)
    );
    var scope = currentContextScope();
    if (scope === 'selection') {
      if (!selectedSources.length) {
        line.textContent = 'AI 将使用：选区/节点（当前未选中）';
        line.setAttribute('data-context-state', 'empty');
        return;
      }
      line.textContent = 'AI 将使用：' + selectedSources.join(' / ');
      line.setAttribute('data-context-state', 'ready');
      return;
    }
    if (scope === 'document') {
      line.textContent = hasDocument ? 'AI 将使用：当前文档全文检索' : 'AI 将使用：全文检索（当前未识别 PDF）';
      line.setAttribute('data-context-state', hasDocument ? 'ready' : 'empty');
      return;
    }
    var sources = selectedSources.slice();
    if (hasDocument) {
      sources.push('当前文档');
    }

    if (!sources.length) {
      line.textContent = 'AI 可见：未选择上下文';
      line.setAttribute('data-context-state', 'empty');
      return;
    }
    line.textContent = 'AI 将自动使用：' + sources.join(' / ') + '（有选区优先，否则全文）';
    line.setAttribute('data-context-state', 'ready');
  }

  window.CodexPanel = {
    setContext: function(ctx) {
      renderContext(ctx || {});
    },
    setPrompt: function(payload) {
      var text = payload && payload.text ? repairPdfExtractedMathText(payload.text) : '';
      state.lastPromptFromSelection = text;
      state.context = state.context || {};
      if (text) {
        state.context.selectionText = text;
      } else {
        delete state.context.selectionText;
        delete state.context.selectedText;
        delete state.context.activeSelectionText;
      }
      renderContextSourceLine(state.context);
      renderContextPreview();
      renderSettingsContextMeta(state.context);
      scheduleAgentPlanRefresh();
      updateActionAvailability();
    },
    setStatus: function(payload) {
      var text = payload && payload.text ? String(payload.text) : '';
      var pill = byId('statusPill');
      if (!pill) return;
      renderPdfCacheStatusFromText(text);
      pill.textContent = text || 'Companion: 127.0.0.1:48761';
      pill.className = 'status-pill ' + (state.busy ? 'busy' : 'idle');
      if (/失败|错误|未运行|不可用|not found|error/i.test(text)) {
        pill.className = 'status-pill error';
      }
    },
    setReply: function(payload) {
      var text = payload && payload.text ? String(payload.text) : '';
      if (text) {
        addAssistantReplyWithActions(text);
        if (state.pendingGuideAction) {
          showFollowUpGuides(state.pendingGuideAction, state.pendingGuidePrompt);
          state.pendingGuideAction = '';
          state.pendingGuidePrompt = '';
        }
      }
    },
    setAiEditOperationReady: function(payload) {
      payload = payload || {};
      var draftId = payload.draftId || payload.id || '';
      var draft = draftId && state.pendingAiEditDrafts ? state.pendingAiEditDrafts[draftId] : null;
      draft = draft || {};
      for (var key in payload) {
        if (Object.prototype.hasOwnProperty.call(payload, key)) draft[key] = payload[key];
      }
      if (!draft.id) draft.id = draftId;
      if (draftId && state.pendingAiEditDrafts) delete state.pendingAiEditDrafts[draftId];
      renderAiEditOperation(draft);
    },
    setAiEditOperationResult: function(payload) {
      payload = payload || {};
      var transactionId = payload.transactionId || '';
      var panels = document.querySelectorAll('.ai-edit-operation');
      for (var i = 0; i < panels.length; i++) {
        if (transactionId && panels[i].getAttribute('data-transaction-id') !== transactionId) continue;
        setAiEditOperationBusy(panels[i], true);
        if (payload.action === 'reject') {
          setAiEditOperationStatus(
            panels[i],
            payload.ok ? '已拒绝，已删除本次新增内容。' : (payload.message || '拒绝失败，请手动撤销。'),
            payload.ok ? 'rejected' : 'error'
          );
        } else {
          setAiEditOperationStatus(panels[i], '已接受，保留本次新增内容。', 'accepted');
        }
        refreshAiEditVerification(transactionId, panels[i]);
      }
    },
    setBusy: function(payload) {
      state.busy = !!(payload && payload.busy);
      setBusyButtons(isActiveRun());
      updateRunToggleButton();
      if (!isActiveRun()) {
        finishProgressStage('已收到结果', 'MN4 插件已结束动作，正在等待最终文字输出显示。');
      }
      var pill = byId('statusPill');
      if (pill) {
        pill.className = 'status-pill ' + (state.busy ? 'busy' : 'idle');
      }
    }
  };

  // The native bridge invokes these by fully-qualified name.
  window.CodexPanel.setAiEditOperationReady = window.CodexPanel.setAiEditOperationReady;
  window.CodexPanel.setAiEditOperationResult = window.CodexPanel.setAiEditOperationResult;

  function bind() {
    var buttons = document.querySelectorAll('button[data-action]');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener('click', function(ev) {
        releaseButtonFocus(ev.currentTarget);
        var disabledReason = ev.currentTarget.getAttribute('data-disabled-reason') || '';
        if (disabledReason) {
          ev.preventDefault();
          addMessage('assistant', disabledReason);
          updateActionAvailability();
          return;
        }
        sendAction(ev.currentTarget.getAttribute('data-action'));
      });
    }
    var scopeButtons = document.querySelectorAll('button[data-context-scope]');
    for (var s = 0; s < scopeButtons.length; s++) {
      scopeButtons[s].addEventListener('click', function(ev) {
        releaseButtonFocus(ev.currentTarget);
        setContextScope(ev.currentTarget.getAttribute('data-context-scope'));
      });
    }
    var defaultScopeSelect = byId('defaultContextScopeSelect');
    if (defaultScopeSelect) {
      defaultScopeSelect.addEventListener('change', function(ev) {
        setContextScope(ev.currentTarget.value);
      });
    }
    var tabButtons = document.querySelectorAll('.tab-button');
    for (var t = 0; t < tabButtons.length; t++) {
      tabButtons[t].addEventListener('click', function(ev) {
        releaseButtonFocus(ev.currentTarget);
        switchTab(ev.currentTarget.getAttribute('data-tab'));
      });
    }
    var workbenchTabs = document.querySelectorAll('.workbench-tab');
    for (var w = 0; w < workbenchTabs.length; w++) {
      workbenchTabs[w].addEventListener('click', function(ev) {
        releaseButtonFocus(ev.currentTarget);
        switchWorkbenchPane(ev.currentTarget.getAttribute('data-workbench-pane'));
      });
    }
    var workspaceNavCards = document.querySelectorAll('.workspace-nav-card');
    for (var n = 0; n < workspaceNavCards.length; n++) {
      workspaceNavCards[n].addEventListener('click', function(ev) {
        releaseButtonFocus(ev.currentTarget);
        switchWorkspaceSurface(ev.currentTarget.getAttribute('data-workspace-surface'));
      });
    }
    bindButton('chatModeButton', function() {
      switchProductMode('chat');
    });
    bindButton('agentWorkspaceModeButton', function() {
      switchProductMode('workspace');
    });
    bindButton('closeButton', function() {
      bridge('close', {});
    });
    bindButton('settingsButton', openConfigPage);
    bindButton('newConversationButton', newConversation);
    bindButton('conversationHistoryButton', openConversationHistory);
    bindButton('conversationHistoryCloseButton', closeConversationHistory);
    bindButton('notebookWorkspaceRefreshButton', function() {
      refreshNotebookWorkspace(true);
    });
    bindButton('conversationHistoryAllButton', function() {
      state.conversationHistoryScope = 'document';
      refreshConversationHistory();
    });
    bindButton('conversationHistoryObjectButton', function() {
      state.conversationHistoryScope = 'object';
      refreshConversationHistory();
    });
    bindButton('objectBrowserRefreshButton', function() {
      refreshObjectBrowser(true);
    });
    bindButton('objectBrowserFilterButton', function() {
      refreshObjectBrowser(true);
    });
    bindButton('objectRegistryScanButton', requestObjectRegistryScan);
    bindButton('objectGraphRefreshButton', function() {
      refreshObjectGraph(true);
    });
    bindButton('objectGraphRelationAddButton', openObjectGraphRelationEditor);
    bindButton('objectGraphRelationSaveButton', saveObjectGraphRelation);
    bindButton('objectGraphRelationCancelButton', closeObjectGraphRelationEditor);
    bindButton('objectActivityRefreshButton', function() {
      refreshObjectActivity(true);
    });
    bindButton('operationLedgerRefreshButton', function() {
      refreshOperationLedger(true);
    });
    bindButton('operationLedgerFilterButton', function() {
      refreshOperationLedger(true);
    });
    bindButton('operationLedgerDetailCloseButton', closeOperationLedgerDetail);
    bindButton('workflowRunInspectorCloseButton', closeWorkflowRunInspector);
    bindButton('configBackButton', closeConfigPage);
    bindButton('contextButton', function() {
      bridge('context', {});
    });
    bindButton('stopButton', stopCurrent);
    bindButton('saveSettingsButton', saveSettings);
    bindButton('saveFileSearchRootsButton', saveFileSearchRoots);
    bindButton('clearOpenAIKeyButton', clearOpenAIKey);
    bindButton('clearMnUrlApiSecretButton', clearMnUrlApiSecret);
    bindButton('aiBackendProbeButton', probeAiBackend);
    bindButton('healthCheckButton', checkHealth);
    bindButton('permissionDiagnoseButton', diagnosePermissions);
    bindButton('cacheCurrentPdfButton', cacheCurrentPdf);
    bindButton('pdfCacheFileButton', choosePdfCacheFile);
    bindButton('pdfCacheFileBannerButton', choosePdfCacheFile);
    bindButton('mindmapTargetRefreshButton', refreshMindmapTarget);
    bindButton('mindmapTreeRefreshButton', requestMindmapTreeRead);
    bindButton('mindmapStudioReadTreeButton', requestMindmapTreeRead);
    bindButton('mindmapStudioPreviewDiffButton', previewMindmapDiffFromStudio);
    bindButton('mindmapStudioApplySelectedButton', applyMindmapStudioSelectedDiff);
    bindButton('mindmapStudioVerifyButton', verifyMindmapStudioTransaction);
    bindButton('mindmapStudioRollbackButton', rollbackMindmapStudioTransaction);
    bindButton('agentPlanRefreshButton', function() {
      refreshAgentPlan(true);
    });
    bindButton('knowledgeWorkspaceSearchButton', function() {
      searchKnowledgeWorkspace('');
    });
    bindButton('runtimeEvidenceButton', collectRuntimeEvidence);
    bindButton('nativeCapabilitiesRefreshButton', refreshNativeCapabilities);
    bindButton('updateCheckButton', function() {
      checkForUpdates(false);
    });
    bindButton('updateInstallButton', installUpdate);
    bindButton('logsRefreshButton', refreshDiagnosticLogs);
    bindButton('logsClearButton', clearDiagnosticLogs);
    bindButton('updateNoticeOpenSettingsButton', openUpdateSettings);
    bindButton('settingsHighlightStatusButton', diagnoseHighlights);
    bindButton('nativeHighlightWizardButton', startNativeHighlightWizard);
    bindButton('singleDocumentAcceptanceButton', checkSingleDocumentAcceptance);
    bindButton('releaseAcceptanceButton', checkReleaseAcceptance);
    bindButton('openPermissionSettingsButton', openPermissionSettings);
    bindButton('mnRuntimeNoticeRefreshButton', refreshNativeCapabilities);
    bindButton('mnRuntimeNoticeSettingsButton', function() {
      openConfigPage();
    });
    bindButton('goalToggleButton', toggleGoalPanel);
    bindButton('runGoalButton', runGoal);
    bindButton('runStagedActionButton', runStagedAction);
    bindButton('clearStagedActionButton', function() {
      clearStagedPrompt();
      updateActionAvailability();
      updateRunToggleButton();
      window.CodexPanel.setStatus({text: '已改为普通问 Codex'});
    });
    bindButton('newCustomButtonButton', newCustomButton);
    bindButton('saveCustomButtonButton', saveCustomButton);
    bindButton('deleteCustomButtonButton', deleteCustomButton);
    bindButton('uploadButton', uploadFromInputs);
    bindButton('runToggleButton', runToggle);
    bindButton('draftAcceptButton', acceptDraft);
    bindButton('draftRejectButton', rejectDraft);
    bindButton('historyButton', refreshHistory);
    bindButton('clearHistoryButton', clearHistory);
    var pdfCacheFileInput = byId('pdfCacheFileInput');
    if (pdfCacheFileInput) {
      pdfCacheFileInput.addEventListener('change', uploadSelectedPdfCacheFile);
    }
    var mindmapTargetSelect = byId('mindmapTargetSelect');
    if (mindmapTargetSelect) {
      mindmapTargetSelect.addEventListener('change', function(ev) {
        updateMindmapTargetFromSelect(ev.currentTarget.value);
      });
    }
    var knowledgeSearchInput = byId('knowledgeWorkspaceSearchInput');
    if (knowledgeSearchInput) {
      knowledgeSearchInput.addEventListener('keydown', function(ev) {
        if (ev.isComposing || ev.keyCode === 229) return;
        if (ev.keyCode === 13) {
          ev.preventDefault();
          searchKnowledgeWorkspace('');
        }
      });
    }
    var objectBrowserTypeFilterSelect = byId('objectBrowserTypeFilterSelect');
    if (objectBrowserTypeFilterSelect) {
      objectBrowserTypeFilterSelect.addEventListener('change', function() {
        refreshObjectBrowser(true);
      });
    }
    var objectBrowserFilterInputs = [
      byId('objectBrowserKindFilterInput'),
      byId('objectBrowserSearchInput')
    ];
    for (var f = 0; f < objectBrowserFilterInputs.length; f++) {
      if (!objectBrowserFilterInputs[f]) continue;
      objectBrowserFilterInputs[f].addEventListener('keydown', function(ev) {
        if (ev.isComposing || ev.keyCode === 229) return;
        if (ev.keyCode === 13) {
          ev.preventDefault();
          refreshObjectBrowser(true);
        }
      });
    }
    var operationLedgerTypeFilterSelect = byId('operationLedgerTypeFilterSelect');
    if (operationLedgerTypeFilterSelect) {
      operationLedgerTypeFilterSelect.addEventListener('change', function() {
        refreshOperationLedger(true);
      });
    }
    var operationLedgerFilterInputs = [
      byId('operationLedgerStatusFilterInput'),
      byId('operationLedgerSearchInput')
    ];
    for (var lf = 0; lf < operationLedgerFilterInputs.length; lf++) {
      if (!operationLedgerFilterInputs[lf]) continue;
      operationLedgerFilterInputs[lf].addEventListener('keydown', function(ev) {
        if (ev.isComposing || ev.keyCode === 229) return;
        if (ev.keyCode === 13) {
          ev.preventDefault();
          refreshOperationLedger(true);
        }
      });
    }
    byId('promptInput').addEventListener('keydown', function(ev) {
      if (ev.isComposing || ev.keyCode === 229) return;
      if (ev.keyCode === 13 && !ev.shiftKey) {
        ev.preventDefault();
        sendAction('chat');
      }
    });
    byId('promptInput').addEventListener('input', function() {
      updateActionAvailability();
      updateRunToggleButton();
      scheduleAgentPlanRefresh();
    });
    updateRunToggleButton();
    updateReadiness({});
    renderContextScopeButtons();
    renderContextSourceLine(state.context);
    renderContextPreview();
    renderMindmapTargetBar(state.mindmapTarget);
    renderMindmapTreeCacheStatus(state.mindmapTreeCache);
    renderMindmapDiffWorkbench();
    renderMindmapStudioPanel();
    renderAiEditTransactionCenter(state.aiEditTransactionStatus);
    renderAgentWorkbench(null);
    renderNotebookWorkspace(state.notebookWorkspace);
    renderWorkbenchPanels();
    renderObjectBrowser();
    renderOperationLedgerDetail();
    renderKnowledgeWorkspace();
    renderWorkflowWorkspace();
    switchProductMode(state.activeProductMode);
    renderSettingsContextMeta(state.context);
    renderPresetButtons();
    renderMainPinnedButtons();
    renderMainPinnedManager();
    renderCustomButtons();
    renderDraft(null);
    renderStagedActionLine();
    bridge('context', {});
    refreshNotebookWorkspace(false);
    window.setTimeout(reportControlsReady, 80);
    refreshSettings();
    startQueuePump();
    startContextAutoRefresh();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
})();
