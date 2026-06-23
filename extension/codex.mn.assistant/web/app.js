(function() {
  var state = {
    busy: false,
    runActive: false,
    context: {},
    contextScope: 'auto',
    contextScopeInitialized: false,
    lastPromptFromSelection: '',
    settings: {},
    customButtons: [],
    goal: {},
    files: [],
    queue: {pending: 0},
    openaiConfigured: false,
    codexCliAvailable: false,
    codexCliPath: '',
    aiBackend: 'auto',
    draft: null,
    pendingAiEditDrafts: {},
    progressTimer: null,
    progressStatusTimer: null,
    progressStatusInFlight: false,
    progressBody: null,
    progressStartedAt: 0,
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
    deferredNativeQueueIds: {}
  };
  var MAIN_PINNED_BUTTON_LIMIT = 4;
  var requiredControlIds = [
    'aiChatShell',
    'settingsButton',
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
    'statusPill',
    'contextLine',
    'readinessPanel'
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

  function setChecked(id, checked) {
    var el = byId(id);
    if (el) el.checked = !!checked;
  }

  function getChecked(id) {
    var el = byId(id);
    return !!(el && el.checked);
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
      article.appendChild(buildReplyMindmapControls(replyText));
    });
  }

  function latestChatTranscript() {
    var history = byId('liveHistory');
    if (!history) return state.latestAssistantReply || '';
    var messages = history.querySelectorAll('.message');
    var parts = [];
    for (var i = 0; i < messages.length; i++) {
      var roleEl = messages[i].querySelector('.message-role');
      var bodyEl = messages[i].querySelector('.message-body');
      var body = bodyEl ? String(bodyEl.textContent || '').replace(/^\s+|\s+$/g, '') : '';
      if (!body) continue;
      var role = roleEl ? String(roleEl.textContent || '').replace(/^\s+|\s+$/g, '') : 'Codex';
      parts.push(role + '：\n' + body);
    }
    return parts.join('\n\n---\n\n') || state.latestAssistantReply || '';
  }

  function buildReplyMindmapPrompt(kind, replyText) {
    var answer = String(replyText || state.latestAssistantReply || '').replace(/^\s+|\s+$/g, '');
    var transcript = latestChatTranscript();
    var outlineRule = '输出必须是 Markdown 层级大纲：## 一级主题、### 二级主题、#### 三级细节点。覆盖全文章节或回答中的完整逻辑链；长文尽量形成 18-30 个二级主题、40-80 个三级细节点；每个节点标题不超过 28 个汉字，说明不超过 80 个汉字；不要把整段回答塞进一张卡；末尾用“覆盖统计：...”说明覆盖章节、二级主题和三级细节点数量。';
    if (kind === 'conversation') {
      return '[conversation_to_mindmap] 根据上面的对话创建一个结构化的脑图分支（使用markdown大纲格式，并保留问答关系和双向同步线索）。' +
        '\n' + outlineRule + '\n\n上面的对话：\n' + transcript;
    }
    if (kind === 'card_tree') {
      return '[create_card_tree] 根据上面的回答创建一个结构化的卡片树（使用markdown大纲格式）。' +
        '\n' + outlineRule + '\n\n上面的回答：\n' + answer;
    }
    return '[answer_to_mindmap] 根据上面的回答创建一个结构化的脑图分支（使用markdown大纲格式）。' +
      '\n' + outlineRule + '\n\n上面的回答：\n' + answer;
  }

  function runReplyMindmapAction(kind, replyText) {
    var labels = {
      answer: '回答添加到脑图',
      conversation: '对话添加到脑图（双向同步）',
      card_tree: '在脑图中创建卡片树'
    };
    var prompt = buildReplyMindmapPrompt(kind, replyText);
    executeAction('generate_mindmap', prompt, labels[kind] || '添加到脑图');
  }

  function buildReplyMindmapControls(replyText) {
    var wrapper = document.createElement('div');
    wrapper.className = 'reply-mindmap-actions';
    var trigger = document.createElement('button');
    trigger.className = 'small-button reply-mindmap-trigger';
    trigger.type = 'button';
    trigger.textContent = '添加到脑图';
    trigger.setAttribute('aria-expanded', 'false');
    var menu = document.createElement('div');
    menu.className = 'reply-mindmap-menu hidden';
    var items = [
      {kind: 'answer', title: '回答添加到脑图'},
      {kind: 'conversation', title: '对话添加到脑图（双向同步）'},
      {kind: 'card_tree', title: '在脑图中创建卡片树'}
    ];
    trigger.addEventListener('click', function(ev) {
      releaseButtonFocus(ev.currentTarget);
      var hidden = menu.className.indexOf('hidden') >= 0;
      menu.className = hidden ? 'reply-mindmap-menu' : 'reply-mindmap-menu hidden';
      trigger.setAttribute('aria-expanded', hidden ? 'true' : 'false');
    });
    for (var i = 0; i < items.length; i++) {
      (function(item) {
        var button = document.createElement('button');
        button.className = 'reply-mindmap-menu-item';
        button.type = 'button';
        button.textContent = item.title;
        button.addEventListener('click', function(ev) {
          releaseButtonFocus(ev.currentTarget);
          menu.className = 'reply-mindmap-menu hidden';
          trigger.setAttribute('aria-expanded', 'false');
          runReplyMindmapAction(item.kind, replyText);
        });
        menu.appendChild(button);
      })(items[i]);
    }
    wrapper.appendChild(trigger);
    wrapper.appendChild(menu);
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
    payload.action = action;
    payload.source = payload.source || 'marginnote4-web-panel';
    payload.contextScope = currentContextScope();
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
    addMessage('user', userText || '[' + action + ']');
    setWebRunLock(true);
    window.CodexPanel.setBusy({busy: true});
    window.CodexPanel.setStatus({text: '正在执行：' + actionLabel(action)});
    startProgress(action, '正在询问 Codex', 'Web 面板正在直接调用本地 Companion，不再经过 MN4 原生请求层。');
    postCompanion(action, {prompt: prompt, _web_run_owner: true}, function(result) {
      setWebRunLock(false);
      window.CodexPanel.setBusy({busy: false});
      renderControls(result || {});
      if (!result || !result.ok) {
        addFailureMessage('队列任务执行失败', result);
        ackQueueAndContinue(queueId);
        return;
      }
      if (result.queued_due_to_web_busy) {
        if (queueId) {
          ackQueueAndContinue(queueId);
          return;
        }
        refreshQueue();
        return;
      }
      reportActionResponse(action, result || {});
      ackQueueAndContinue(queueId);
    });
  }

  function promptValue() {
    var input = byId('promptInput');
    return input ? input.value : '';
  }

  function clearPromptInputAfterSend() {
    setValue('promptInput', '');
  }

  function actionLabel(action) {
    var labels = {
      chat: '问 Codex',
      explain_selection: '解释选中',
      generate_card: '生成卡片',
      generate_mindmap: '新建脑图',
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
      line.textContent = '真实 AI 已配置';
      detail.textContent =
        'AI 后端：' + (backendLabels[backend] || backend) +
        ' / Codex CLI：' + (state.codexCliAvailable ? '已发现' : '未发现') +
        ' / OpenAI：' + (state.openaiConfigured ? '已配置' : '未配置') +
        ' / 模型：' + (settings.model || state.settings.model || '未设置') +
        ' / 速度：' + (settings.speed || state.settings.speed || '未设置') +
        ' / 代理：' + ((settings.proxyUrl || state.settings.proxyUrl) ? '已配置' : '未配置');
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
    if (!path) {
      addMessage('assistant', '先点“检查权限”或刷新上下文，让 Companion 知道当前 PDF 路径。');
      return;
    }
    bridge('upload_pdf', {path: path});
    addMessage('assistant', '已请求 MarginNote 上传当前 PDF 缓存；完成后再点“检查权限”或导出 PDF。');
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
    if (draft.write_target) lines.push('写入目标：' + draft.write_target);
    if (draft.mindmap_title) lines.push('脑图根：' + draft.mindmap_title);
    return lines.join('\n');
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
    actions.appendChild(accept);
    actions.appendChild(reject);
    panel.appendChild(title);
    panel.appendChild(subtitle);
    panel.appendChild(meta);
    panel.appendChild(actions);
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

  function formatProgressText(elapsed) {
    var stage = state.progressStage || '准备执行';
    var detail = state.progressDetail || '正在收集当前上下文并准备请求。';
    return [
      '阶段：' + stage,
      '动作：' + actionLabel(state.progressAction),
      '状态：' + detail,
      '已用：' + elapsed + 's',
      '可继续输入；运行中可点停止。'
    ].join('\n');
  }

  function updateProgressText() {
    if (!state.progressBody || !state.progressStartedAt) return;
    state.progressBody.textContent = formatProgressText(progressElapsedSeconds());
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
      state.progressStage = run.stage || state.progressStage;
      state.progressDetail = run.detail || state.progressDetail;
      state.progressAction = run.action || state.progressAction;
      renderRunState(run);
      updateProgressText();
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

  function startProgress(action, stage, detail) {
    finishProgress('');
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
    state.progressAction = '';
    state.progressStage = '';
    state.progressDetail = '';
  }

  function finishProgressStage(stage, detail) {
    if (!state.progressBody || !state.progressStartedAt) return;
    state.progressStage = stage || state.progressStage;
    state.progressDetail = detail || state.progressDetail;
    finishProgress(formatProgressText(progressElapsedSeconds()));
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
    startProgress('goal_run', '正在执行队列目标', '队列中的目标正在作为一次性任务提交给 Companion。');
    postCompanion('goal_run', {goal: goal, prompt: goalText, _web_run_owner: true}, function(result) {
      setWebRunLock(false);
      window.CodexPanel.setBusy({busy: false});
      renderControls(result || {});
      if (!result || !result.ok) {
        addFailureMessage('目标执行失败', result);
        ackQueueAndContinue(queueId);
        return;
      }
      if (result.queued_due_to_web_busy) {
        addMessage('assistant', result.message || '目标已重新加入队列。');
        ackQueueAndContinue(queueId);
        return;
      }
      reportActionResponse('goal_run', result || {});
      if (enqueueGoalQueue(result.goalQueue, goalUserText(goal))) {
        window.setTimeout(drainNextQueuedAction, 500);
      } else {
        showFollowUpGuides('chat', goalUserText(goal));
      }
      ackQueueAndContinue(queueId);
    });
  }

  function requestDraftAction(action, prompt, userText, queueId) {
    addMessage('user', userText || '[' + action + ']');
    renderDraft(null);
    setWebRunLock(true);
    window.CodexPanel.setBusy({busy: true});
    window.CodexPanel.setStatus({text: '正在生成草稿：' + actionLabel(action)});
    startProgress(action, '正在生成草稿', '正在把当前上下文发送给 Companion，并等待卡片/脑图草稿。');
    postCompanion(action, {prompt: prompt, _web_run_owner: true}, function(result) {
      if (!result || !result.ok) {
        setWebRunLock(false);
        window.CodexPanel.setBusy({busy: false});
        addFailureMessage('草稿生成失败', result);
        ackQueueAndContinue(queueId);
        return;
      }
      if (result.queued_due_to_web_busy) {
        setWebRunLock(false);
        window.CodexPanel.setBusy({busy: false});
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
        addMessage('assistant', '没有可写入的卡片或脑图。');
        ackQueueAndContinue(queueId);
        return;
      }
      reportActionResponse(action, result || {});
      setProgressStage('正在保存草稿', '卡片/脑图内容已生成，正在保存到本地草稿确认区。');
      postCompanionPath('/marginnote/draft', 'draft_save', {
        originalAction: action,
        draft: result
      }, function(saved) {
        setWebRunLock(false);
        window.CodexPanel.setBusy({busy: false});
        if (saved && saved.ok && saved.draft) {
          renderDraft(saved.draft);
          writeDraftForAiEditOperation(saved.draft);
          ackQueueAndContinue(queueId);
        } else {
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

  function renderControls(result) {
    result = result || {};
    state.settings = result.settings || state.settings || {};
    state.customButtons = cleanCustomButtons(state.settings.customButtons || state.customButtons || []);
    state.goal = result.goalOneShot ? {} : (result.goal || state.goal || {});
    state.files = result.files || state.files || [];
    state.queue = result.queue || state.queue || {pending: 0};
    updateReadiness(result);
    setValue('aiBackendSelect', state.settings.aiBackend || state.aiBackend || 'auto');
    setValue('permissionSelect', state.settings.permission || 'notes');
    setValue('modelInput', state.settings.model || 'gpt-5.5');
    setValue('speedSelect', state.settings.speed || 'fast');
    setValue('proxyUrlInput', state.settings.proxyUrl || '');
    setValue('codexCliPathInput', state.settings.codexCliPath || state.codexCliPath || '');
    setValue('defaultContextScopeSelect', state.settings.defaultContextScope || 'auto');
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

  function refreshSettings() {
    postCompanion('settings_get', {}, renderControls);
  }

  function saveSettings() {
    var openaiApiKey = getValue('openaiApiKeyInput');
    postCompanion('settings_update', {
      settings: {
        aiBackend: getValue('aiBackendSelect'),
        permission: getValue('permissionSelect'),
        model: getValue('modelInput'),
        speed: getValue('speedSelect'),
        codexCliPath: getValue('codexCliPathInput'),
        proxyUrl: getValue('proxyUrlInput'),
        defaultContextScope: getValue('defaultContextScopeSelect'),
        customButtons: state.customButtons,
        openaiApiKey: openaiApiKey
      }
    }, function(result) {
      if (openaiApiKey) setValue('openaiApiKeyInput', '');
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
    startProgress('goal_run', '已提交目标', 'Companion 正在把目标作为一次性任务执行。');
    postCompanion('goal_run', {goal: goal, _web_run_owner: true}, function(result) {
      setWebRunLock(false);
      window.CodexPanel.setBusy({busy: false});
      renderControls(result || {});
      if (!result || !result.ok) {
        addFailureMessage('目标执行失败', result);
        return;
      }
      if (result.queued_due_to_web_busy) {
        addMessage('assistant', result.message || '目标已加入队列。');
        refreshQueue();
        return;
      }
      reportActionResponse('goal_run', result || {});
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
      bridge('context', {reason: 'auto-refresh'});
    }, 1800);
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
    setWebRunLock(false);
    window.CodexPanel.setBusy({busy: false});
    postCompanion('stop_current', {}, function(result) {
      renderControls({queue: result.queue || state.queue});
    });
  }

  function writeAcceptedDraft(draftId, panel) {
    bridge('write_draft', {id: draftId});
    renderDraft(null);
    if (panel) {
      setAiEditOperationStatus(panel, '已接受，写入请求已发送。', 'accepted');
      setAiEditOperationBusy(panel, true);
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
    var page = byId('configPage');
    if (page) page.className = 'config-page';
    renderSettingsContextMeta(state.context || {});
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

  function renderContext(ctx) {
    state.context = repairContextPayload(ctx || {});
    renderContextSourceLine(state.context);
    var connected = state.context.topicid || state.context.notebookid || state.context.docmd5 || state.context.bookmd5;
    setText('contextLine', connected ? '已连接 MarginNote 上下文' : '等待 MarginNote 上下文');
    renderSettingsContextMeta(state.context);

    renderContextPreview();
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
      updateActionAvailability();
    },
    setStatus: function(payload) {
      var text = payload && payload.text ? String(payload.text) : '';
      var pill = byId('statusPill');
      if (!pill) return;
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
    bindButton('closeButton', function() {
      bridge('close', {});
    });
    bindButton('settingsButton', openConfigPage);
    bindButton('configBackButton', closeConfigPage);
    bindButton('contextButton', function() {
      bridge('context', {});
    });
    bindButton('stopButton', stopCurrent);
    bindButton('saveSettingsButton', saveSettings);
    bindButton('clearOpenAIKeyButton', clearOpenAIKey);
    bindButton('aiBackendProbeButton', probeAiBackend);
    bindButton('healthCheckButton', checkHealth);
    bindButton('permissionDiagnoseButton', diagnosePermissions);
    bindButton('cacheCurrentPdfButton', cacheCurrentPdf);
    bindButton('runtimeEvidenceButton', collectRuntimeEvidence);
    bindButton('nativeCapabilitiesRefreshButton', refreshNativeCapabilities);
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
    });
    updateRunToggleButton();
    updateReadiness({});
    renderContextScopeButtons();
    renderContextSourceLine(state.context);
    renderContextPreview();
    renderSettingsContextMeta(state.context);
    renderPresetButtons();
    renderMainPinnedButtons();
    renderMainPinnedManager();
    renderCustomButtons();
    renderDraft(null);
    renderStagedActionLine();
    bridge('context', {});
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
