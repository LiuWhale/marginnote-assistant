function codexJsonForEval(payload) {
  try {
    return JSON.stringify(payload || {});
  } catch (err) {
    return '{}';
  }
}

function codexSafeString(value) {
  if (value === null || value === undefined) return '';
  return String(value);
}

function codexUrlString(url) {
  if (!url) return '';
  try {
    if (url.absoluteString) {
      return String(typeof url.absoluteString === 'function' ? url.absoluteString() : url.absoluteString);
    }
  } catch (err) {}
  return String(url || '');
}

function codexParseQuery(urlString) {
  var out = {};
  var index = urlString.indexOf('?');
  if (index < 0) return out;
  var query = urlString.substring(index + 1);
  var hashIndex = query.indexOf('#');
  if (hashIndex >= 0) query = query.substring(0, hashIndex);
  var parts = query.split('&');
  for (var i = 0; i < parts.length; i++) {
    if (!parts[i]) continue;
    var eq = parts[i].indexOf('=');
    if (eq < 0) continue;
    var key = parts[i].substring(0, eq);
    var value = parts[i].substring(eq + 1).replace(/\+/g, ' ');
    try {
      out[decodeURIComponent(key)] = decodeURIComponent(value);
    } catch (err) {
      out[key] = value;
    }
  }
  return out;
}

var CodexPanelMinWidth = 390;
var CodexPanelMinHeight = 520;
var CodexPanelDefaultWidth = 540;
var CodexPanelDefaultHeight = 680;
var CodexPanelWidthKey = 'codex_mn_assistant_panel_width';
var CodexPanelHeightKey = 'codex_mn_assistant_panel_height';
var CodexPanelXKey = 'codex_mn_assistant_panel_x';
var CodexPanelYKey = 'codex_mn_assistant_panel_y';

function codexClampNumber(value, minValue, maxValue) {
  var numberValue = Number(value);
  if (isNaN(numberValue)) numberValue = minValue;
  return Math.max(minValue, Math.min(maxValue, numberValue));
}

function codexSavedNumber(key, fallback) {
  try {
    var value = NSUserDefaults.standardUserDefaults().objectForKey(key);
    var numberValue = Number(value);
    if (!isNaN(numberValue) && numberValue > 0) return numberValue;
  } catch (err) {}
  return fallback;
}

function codexSavedOptionalNumber(key) {
  try {
    var value = NSUserDefaults.standardUserDefaults().objectForKey(key);
    var numberValue = Number(value);
    if (!isNaN(numberValue)) return numberValue;
  } catch (err) {}
  return null;
}

var CodexWebPanelController = JSB.defineClass('CodexWebPanelController : UIViewController <UIWebViewDelegate>', {
  viewDidLoad: function() {
    self.panelLoaded = false;
    self.lastPromptValue = '';
    self.lastStatusValue = '正在加载 Codex Companion...';
    self.lastReplyValue = '';
    self.busyValue = false;
    self._isResizing = false;
    self._isMoving = false;

    self.view.backgroundColor = UIColor.clearColor();
    self.view.layer.shadowOffset = {width: 0, height: 3};
    self.view.layer.shadowRadius = 10;
    self.view.layer.shadowOpacity = 0.26;
    self.view.layer.shadowColor = UIColor.blackColor();
    self.view.layer.masksToBounds = false;

    var bounds = self.view.bounds;
    var width = bounds.width > 0 ? bounds.width : codexSavedNumber(CodexPanelWidthKey, CodexPanelDefaultWidth);
    var height = bounds.height > 0 ? bounds.height : codexSavedNumber(CodexPanelHeightKey, CodexPanelDefaultHeight);
    width = Math.max(CodexPanelMinWidth, width);
    height = Math.max(CodexPanelMinHeight, height);
    self.preferredPanelWidth = width;
    self.preferredPanelHeight = height;

    self.containerView = new UIView({x: 0, y: 0, width: width, height: height});
    self.containerView.backgroundColor = UIColor.whiteColor();
    self.containerView.layer.cornerRadius = 12;
    self.containerView.layer.masksToBounds = true;
    self.containerView.layer.borderWidth = 0.5;
    self.containerView.layer.borderColor = UIColor.lightGrayColor().colorWithAlphaComponent(0.35);
    self.containerView.autoresizingMask = (1 << 1 | 1 << 4);
    self.view.addSubview(self.containerView);

    self.titleBar = new UIView({x: 0, y: 0, width: width, height: 32});
    self.titleBar.backgroundColor = UIColor.colorWithWhiteAlpha(0.965, 1);
    self.titleBar.autoresizingMask = (1 << 1);
    self.titleBar.userInteractionEnabled = true;
    self.containerView.addSubview(self.titleBar);

    self.titleLabel = new UILabel({x: 14, y: 0, width: width - 130, height: 32});
    self.titleLabel.text = 'Codex Companion';
    self.titleLabel.font = UIFont.boldSystemFontOfSize(13);
    self.titleLabel.textColor = UIColor.darkGrayColor();
    self.titleLabel.autoresizingMask = (1 << 1);
    self.titleBar.addSubview(self.titleLabel);

    self.shrinkButton = UIButton.buttonWithType(0);
    self.shrinkButton.frame = {x: width - 108, y: 0, width: 34, height: 32};
    self.shrinkButton.autoresizingMask = (1 << 0);
    self.shrinkButton.setTitleForState('-', 0);
    self.shrinkButton.setTitleColorForState(UIColor.grayColor(), 0);
    self.shrinkButton.titleLabel.font = UIFont.boldSystemFontOfSize(17);
    self.shrinkButton.addTargetActionForControlEvents(self, 'zoomOut:', 1 << 6);
    self.titleBar.addSubview(self.shrinkButton);

    self.expandButton = UIButton.buttonWithType(0);
    self.expandButton.frame = {x: width - 73, y: 0, width: 34, height: 32};
    self.expandButton.autoresizingMask = (1 << 0);
    self.expandButton.setTitleForState('+', 0);
    self.expandButton.setTitleColorForState(UIColor.grayColor(), 0);
    self.expandButton.titleLabel.font = UIFont.boldSystemFontOfSize(17);
    self.expandButton.addTargetActionForControlEvents(self, 'zoomIn:', 1 << 6);
    self.titleBar.addSubview(self.expandButton);

    self.closeButton = UIButton.buttonWithType(0);
    self.closeButton.frame = {x: width - 38, y: 0, width: 34, height: 32};
    self.closeButton.autoresizingMask = (1 << 0);
    self.closeButton.setTitleForState('x', 0);
    self.closeButton.setTitleColorForState(UIColor.grayColor(), 0);
    self.closeButton.titleLabel.font = UIFont.boldSystemFontOfSize(15);
    self.closeButton.addTargetActionForControlEvents(self, 'closeWindow:', 1 << 6);
    self.titleBar.addSubview(self.closeButton);

    var webFrame = {x: 0, y: 32, width: width, height: Math.max(100, height - 32)};
    self.webView = new UIWebView(webFrame);
    self.webView.backgroundColor = UIColor.whiteColor();
    self.webView.scalesPageToFit = false;
    self.webView.autoresizingMask = (1 << 1 | 1 << 4);
    self.webView.delegate = self;
    self.containerView.addSubview(self.webView);

    self.resizeHandle = new UIView({x: width - 38, y: height - 38, width: 38, height: 38});
    self.resizeHandle.backgroundColor = UIColor.clearColor();
    self.resizeHandle.userInteractionEnabled = true;
    self.resizeHandle.autoresizingMask = (1 << 0 | 1 << 3);
    var resizeLabel = new UILabel({x: 12, y: 12, width: 22, height: 22});
    resizeLabel.text = '↘';
    resizeLabel.font = UIFont.boldSystemFontOfSize(16);
    resizeLabel.textColor = UIColor.lightGrayColor();
    self.resizeHandle.addSubview(resizeLabel);
    self.containerView.addSubview(self.resizeHandle);

    var resizePan = new UIPanGestureRecognizer(self, 'handleResize:');
    self.resizeHandle.addGestureRecognizer(resizePan);
    var movePan = new UIPanGestureRecognizer(self, 'handleMove:');
    self.titleBar.addGestureRecognizer(movePan);

    self.loadInitialPage();
  },

  closeWindow: function(sender) {
    if (self.addon && self.addon.hidePanel) self.addon.hidePanel();
  },

  zoomOut: function(sender) {
    self.resizePanelBy(-80, -80, 'zoomOut');
  },

  zoomIn: function(sender) {
    self.resizePanelBy(80, 80, 'zoomIn');
  },

  handleMove: function(gesture) {
    if (!self.view || !self.view.superview) return;
    if (gesture.state === 1) {
      self._isMoving = true;
      self._moveStartLocation = gesture.locationInView(self.view.superview);
      self._moveStartFrame = self.view.frame;
      return;
    }
    if (gesture.state === 3 || gesture.state === 4) {
      self._isMoving = false;
      self.savePanelOrigin();
      if (self.addon && self.addon.postEvent) {
        self.addon.postEvent('panelMoveFinished', {
          x: self.view.frame.x,
          y: self.view.frame.y,
          width: self.view.frame.width,
          height: self.view.frame.height
        });
      }
      self._moveStartLocation = null;
      self._moveStartFrame = null;
      return;
    }
    if (gesture.state !== 2 || !self._moveStartLocation || !self._moveStartFrame) return;
    var location = gesture.locationInView(self.view.superview);
    var dx = location.x - self._moveStartLocation.x;
    var dy = location.y - self._moveStartLocation.y;
    var parent = self.view.superview.bounds;
    var frame = self._moveStartFrame;
    var x = codexClampNumber(frame.x + dx, 8, Math.max(8, parent.width - frame.width - 8));
    var y = codexClampNumber(frame.y + dy, 8, Math.max(8, parent.height - frame.height - 8));
    self.view.frame = {x: x, y: y, width: frame.width, height: frame.height};
  },

  handleResize: function(gesture) {
    if (!self.view || !self.view.superview) return;
    if (gesture.state === 1) {
      self._isResizing = true;
      self._resizeStartLocation = gesture.locationInView(self.view.superview);
      self._resizeStartFrame = self.view.frame;
      return;
    }
    if (gesture.state === 3 || gesture.state === 4) {
      self._isResizing = false;
      self.savePanelSize();
      self.savePanelOrigin();
      if (self.addon && self.addon.postEvent) {
        self.addon.postEvent('panelResizeFinished', {
          width: self.preferredPanelWidth,
          height: self.preferredPanelHeight,
          minWidth: CodexPanelMinWidth,
          minHeight: CodexPanelMinHeight
        });
      }
      self._resizeStartLocation = null;
      self._resizeStartFrame = null;
      return;
    }
    if (gesture.state !== 2 || !self._resizeStartLocation || !self._resizeStartFrame) return;
    var location = gesture.locationInView(self.view.superview);
    var dx = location.x - self._resizeStartLocation.x;
    var dy = location.y - self._resizeStartLocation.y;
    var parent = self.view.superview.bounds;
    var maxWidth = Math.max(CodexPanelMinWidth, parent.width - 16);
    var maxHeight = Math.max(CodexPanelMinHeight, parent.height - 16);
    var width = codexClampNumber(self._resizeStartFrame.width + dx, CodexPanelMinWidth, maxWidth);
    var height = codexClampNumber(self._resizeStartFrame.height + dy, CodexPanelMinHeight, maxHeight);
    var x = self._resizeStartFrame.x;
    var y = self._resizeStartFrame.y;
    if (x + width > parent.width - 8) x = parent.width - width - 8;
    if (y + height > parent.height - 8) y = parent.height - height - 8;
    x = Math.max(8, x);
    y = Math.max(8, y);
    self.preferredPanelWidth = width;
    self.preferredPanelHeight = height;
    self.view.frame = {x: x, y: y, width: width, height: height};
    self.syncPanelFrames(width, height);
  },

  webViewDidFinishLoad: function(webView) {
    UIApplication.sharedApplication().networkActivityIndicatorVisible = false;
    self.panelLoaded = true;
    self.injectCurrentState();
    if (self.addon && self.addon.postEvent) self.addon.postEvent('webPanelLoaded', {ok: true});
  },

  webViewDidStartLoad: function(webView) {
    UIApplication.sharedApplication().networkActivityIndicatorVisible = true;
  },

  webViewDidFailLoadWithError: function(webView, error) {
    UIApplication.sharedApplication().networkActivityIndicatorVisible = false;
    var message = codexSafeString(error && error.localizedDescription ? error.localizedDescription : error);
    self.panelLoaded = false;
    self.loadErrorPage(message);
    if (self.addon && self.addon.postEvent) self.addon.postEvent('webPanelLoadFailed', {message: message});
  },

  webViewShouldStartLoadWithRequestNavigationType: function(webView, request, navigationType) {
    var url = null;
    try {
      url = request.URL ? request.URL() : request.URL;
    } catch (err) {
      url = null;
    }
    var raw = codexUrlString(url);
    var scheme = '';
    try {
      scheme = codexSafeString(url.scheme || '').toLowerCase();
    } catch (err2) {
      scheme = raw.split(':')[0].toLowerCase();
    }
    if (scheme !== 'codexpaper') return true;
    return self.handleBridgeUrl(raw);
  }
});

CodexWebPanelController.prototype.panelMinimumSize = function() {
  return {width: CodexPanelMinWidth, height: CodexPanelMinHeight};
};

CodexWebPanelController.prototype.panelPreferredSize = function() {
  var width = Number(this.preferredPanelWidth || CodexPanelDefaultWidth);
  var height = Number(this.preferredPanelHeight || CodexPanelDefaultHeight);
  if (isNaN(width)) width = CodexPanelDefaultWidth;
  if (isNaN(height)) height = CodexPanelDefaultHeight;
  return {
    width: Math.max(CodexPanelMinWidth, width),
    height: Math.max(CodexPanelMinHeight, height)
  };
};

CodexWebPanelController.prototype.isResizingPanel = function() {
  return !!this._isResizing;
};

CodexWebPanelController.prototype.isMovingPanel = function() {
  return !!this._isMoving;
};

CodexWebPanelController.prototype.savePanelSize = function() {
  var size = this.panelPreferredSize();
  this.preferredPanelWidth = size.width;
  this.preferredPanelHeight = size.height;
  try {
    var defaults = NSUserDefaults.standardUserDefaults();
    defaults.setObjectForKey(size.width, CodexPanelWidthKey);
    defaults.setObjectForKey(size.height, CodexPanelHeightKey);
    if (defaults.synchronize) defaults.synchronize();
  } catch (err) {}
};

CodexWebPanelController.prototype.savePanelOrigin = function() {
  if (!this.view || !this.view.frame) return;
  try {
    var defaults = NSUserDefaults.standardUserDefaults();
    defaults.setObjectForKey(this.view.frame.x, CodexPanelXKey);
    defaults.setObjectForKey(this.view.frame.y, CodexPanelYKey);
    if (defaults.synchronize) defaults.synchronize();
  } catch (err) {}
};

CodexWebPanelController.prototype.panelPreferredOrigin = function(bounds, width, height) {
  var fallbackX = bounds.width - width - 24;
  var fallbackY = bounds.height - height - 32;
  var savedX = codexSavedOptionalNumber(CodexPanelXKey);
  var savedY = codexSavedOptionalNumber(CodexPanelYKey);
  var x = savedX === null ? fallbackX : savedX;
  var y = savedY === null ? fallbackY : savedY;
  return {
    x: codexClampNumber(x, 8, Math.max(8, bounds.width - width - 8)),
    y: codexClampNumber(y, 8, Math.max(8, bounds.height - height - 8))
  };
};

CodexWebPanelController.prototype.resizePanelBy = function(deltaWidth, deltaHeight, reason) {
  if (!this.view || !this.view.superview) return;
  var parent = this.view.superview.bounds;
  var current = this.view.frame;
  var width = codexClampNumber(current.width + deltaWidth, CodexPanelMinWidth, Math.max(CodexPanelMinWidth, parent.width - 16));
  var height = codexClampNumber(current.height + deltaHeight, CodexPanelMinHeight, Math.max(CodexPanelMinHeight, parent.height - 16));
  var x = codexClampNumber(current.x, 8, Math.max(8, parent.width - width - 8));
  var y = codexClampNumber(current.y, 8, Math.max(8, parent.height - height - 8));
  this.preferredPanelWidth = width;
  this.preferredPanelHeight = height;
  this.view.frame = {x: x, y: y, width: width, height: height};
  this.syncPanelFrames(width, height);
  this.savePanelSize();
  this.savePanelOrigin();
  if (this.addon && this.addon.postEvent) {
    this.addon.postEvent('panelZoomButton', {
      reason: reason || '',
      width: width,
      height: height,
      minWidth: CodexPanelMinWidth,
      minHeight: CodexPanelMinHeight
    });
  }
};

CodexWebPanelController.prototype.syncPanelFrames = function(width, height) {
  width = Math.max(CodexPanelMinWidth, Number(width || this.preferredPanelWidth || CodexPanelDefaultWidth));
  height = Math.max(CodexPanelMinHeight, Number(height || this.preferredPanelHeight || CodexPanelDefaultHeight));
  this.preferredPanelWidth = width;
  this.preferredPanelHeight = height;
  if (this.containerView) this.containerView.frame = {x: 0, y: 0, width: width, height: height};
  if (this.titleBar) this.titleBar.frame = {x: 0, y: 0, width: width, height: 32};
  if (this.titleLabel) this.titleLabel.frame = {x: 14, y: 0, width: Math.max(120, width - 130), height: 32};
  if (this.shrinkButton) this.shrinkButton.frame = {x: width - 108, y: 0, width: 34, height: 32};
  if (this.expandButton) this.expandButton.frame = {x: width - 73, y: 0, width: 34, height: 32};
  if (this.closeButton) this.closeButton.frame = {x: width - 38, y: 0, width: 34, height: 32};
  if (this.webView) this.webView.frame = {x: 0, y: 32, width: width, height: Math.max(100, height - 32)};
  if (this.resizeHandle) this.resizeHandle.frame = {x: width - 38, y: height - 38, width: 38, height: 38};
};

CodexWebPanelController.prototype.loadInitialPage = function() {
  var path = this.mainPath ? this.mainPath + '/web/index.html' : '';
  if (!path) {
    this.loadErrorPage('mainPath not found');
    return;
  }
  try {
    var request = NSMutableURLRequest.requestWithURL(NSURL.fileURLWithPath(path));
    request.setCachePolicy(1);
    this.webView.loadRequest(request);
  } catch (err) {
    this.loadErrorPage(String(err));
  }
};

CodexWebPanelController.prototype.loadErrorPage = function(message) {
  var text = codexSafeString(message).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  var html = '<html><body style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;margin:20px;color:#334155;">' +
    '<h3>Codex Companion</h3><p>Web 面板加载失败。</p><pre style="white-space:pre-wrap;">' + text + '</pre>' +
    '<p>旧版按钮面板仍可作为兜底。</p></body></html>';
  try {
    this.webView.loadHTMLStringBaseURL(html, null);
  } catch (err) {}
};

CodexWebPanelController.prototype.handleBridgeUrl = function(raw) {
  var params = codexParseQuery(raw);
  var lower = raw.toLowerCase();
  if (lower.indexOf('codexpaper://close') === 0) {
    if (this.addon && this.addon.hidePanel) this.addon.hidePanel();
    return false;
  }
  if (lower.indexOf('codexpaper://context') === 0) {
    this.sendContextToWeb();
    return false;
  }
  if (lower.indexOf('codexpaper://event') === 0) {
    var eventName = params.name || 'webEvent';
    if (this.addon && this.addon.postEvent) this.addon.postEvent(eventName, params);
    return false;
  }
  if (lower.indexOf('codexpaper://reject_ai_edit_transaction') === 0) {
    var rejectTransactionId = params.transactionId || params.id || '';
    if (this.addon && this.addon.rejectAiEditTransaction) this.addon.rejectAiEditTransaction(rejectTransactionId, params);
    return false;
  }
  if (lower.indexOf('codexpaper://accept_ai_edit_transaction') === 0) {
    var acceptTransactionId = params.transactionId || params.id || '';
    if (this.addon && this.addon.acceptAiEditTransaction) this.addon.acceptAiEditTransaction(acceptTransactionId, params);
    return false;
  }
  if (lower.indexOf('codexpaper://confirm_mindmap_delete_transaction') === 0) {
    var confirmDeleteTransactionId = params.transactionId || params.id || '';
    if (this.addon && this.addon.confirmMindmapDeleteTransaction) this.addon.confirmMindmapDeleteTransaction(confirmDeleteTransactionId, params);
    return false;
  }
  if (lower.indexOf('codexpaper://dismiss_mindmap_delete_transaction') === 0) {
    var dismissDeleteTransactionId = params.transactionId || params.id || '';
    if (this.addon && this.addon.dismissMindmapDeleteTransaction) this.addon.dismissMindmapDeleteTransaction(dismissDeleteTransactionId, params);
    return false;
  }
  if (lower.indexOf('codexpaper://ai_edit') === 0) {
    var editAction = params.action || '';
    var transactionId = params.transactionId || params.id || '';
    if (editAction === 'reject' && this.addon && this.addon.rejectAiEditTransaction) {
      this.addon.rejectAiEditTransaction(transactionId, params);
    } else if (editAction === 'accept' && this.addon && this.addon.acceptAiEditTransaction) {
      this.addon.acceptAiEditTransaction(transactionId, params);
    }
    return false;
  }
  if (lower.indexOf('codexpaper://write_draft') === 0) {
    var draftId = params.id || params.draftId || '';
    this.setStatus('正在写入草稿：' + draftId);
    if (this.addon && this.addon.writeDraft) this.addon.writeDraft(draftId, {aiEditOperation: params.aiEdit === '1'});
    return false;
  }
  if (lower.indexOf('codexpaper://upload_pdf') === 0) {
    var pdfPath = params.path || params.pdfPath || '';
    this.setStatus('正在缓存当前 PDF...');
    if (this.addon && this.addon.uploadPdfToCompanion) this.addon.uploadPdfToCompanion(pdfPath);
    return false;
  }
  if (lower.indexOf('codexpaper://open_url') === 0) {
    var openUrl = params.url || '';
    if (/^https?:\/\//i.test(openUrl)) {
      try {
        UIApplication.sharedApplication().openURL(NSURL.URLWithString(openUrl));
      } catch (err) {
        this.setStatus('无法打开链接：' + openUrl);
      }
    }
    return false;
  }
  if (lower.indexOf('codexpaper://action') === 0) {
    var action = params.name || params.action || 'chat';
    var prompt = params.prompt || '';
    this.lastPromptValue = prompt;
    this.setBusy(true);
    this.setStatus('正在执行：' + action);
    if (this.addon && this.addon.sendPanelAction) this.addon.sendPanelAction(action, prompt);
    return false;
  }
  return false;
};

CodexWebPanelController.prototype.evaluatePanel = function(js) {
  if (!this.webView) return;
  try {
    this.webView.evaluateJavaScript(String(js), function(ret) {});
  } catch (err) {}
};

CodexWebPanelController.prototype.callPanel = function(method, payload) {
  if (!this.panelLoaded) return;
  var json = codexJsonForEval(payload || {});
  this.evaluatePanel(
    '(function(){ if(window.CodexPanel && window.CodexPanel.' + method + ') {' +
    'window.CodexPanel.' + method + '(' + json + '); } })();'
  );
};

CodexWebPanelController.prototype.injectCurrentState = function() {
  this.sendContextToWeb();
  this.setPromptText(this.lastPromptValue);
  this.setStatus(this.lastStatusValue);
  if (this.lastReplyValue) this.setReply(this.lastReplyValue);
  this.setBusy(this.busyValue);
};

CodexWebPanelController.prototype.sendContextToWeb = function() {
  var context = {};
  try {
    if (this.addon && this.addon.resolveContext) context = this.addon.resolveContext('context', this.lastPromptValue || '');
  } catch (err) {
    context = {error: String(err || '')};
  }
  context.panel = 'webview';
  context.companionUrl = 'http://127.0.0.1:48761';
  this.callPanel('setContext', context);
};

CodexWebPanelController.prototype.promptText = function() {
  return this.lastPromptValue ? String(this.lastPromptValue) : '';
};

CodexWebPanelController.prototype.setPromptText = function(text) {
  this.lastPromptValue = text ? String(text) : '';
  this.callPanel('setPrompt', {text: this.lastPromptValue});
};

CodexWebPanelController.prototype.setStatus = function(text) {
  this.lastStatusValue = text ? String(text) : '';
  this.callPanel('setStatus', {text: this.lastStatusValue});
};

CodexWebPanelController.prototype.setReply = function(text) {
  this.lastReplyValue = text ? String(text) : '';
  this.callPanel('setReply', {text: this.lastReplyValue});
};

CodexWebPanelController.prototype.setAiEditOperationReady = function(payload) {
  this.callPanel('setAiEditOperationReady', payload || {});
};

CodexWebPanelController.prototype.setAiEditOperationResult = function(payload) {
  this.callPanel('setAiEditOperationResult', payload || {});
};

CodexWebPanelController.prototype.setBusy = function(value) {
  this.busyValue = !!value;
  this.callPanel('setBusy', {busy: this.busyValue});
};
