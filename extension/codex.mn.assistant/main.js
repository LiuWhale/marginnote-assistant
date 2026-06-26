JSB.newAddon = function(mainPath) {
  JSB.require('CodexPanelController');
  JSB.require('CodexWebPanelController');

  var CompanionURL = 'http://127.0.0.1:48761/marginnote/action';
  var DraftURL = 'http://127.0.0.1:48761/marginnote/draft?id=';
  var PluginVersion = '0.4.28';
  var CompanionActionTimeout = 900;
  var CodexMarkerPrefix = '<!--codex-paper-companion:';
  var NativeHandlerFeatures = [
    'native-highlight-arm-next-selection-default',
    'native-highlight-prefer-next-selection-v1',
    'native-highlight-command-prepared',
    'selection-popup-diagnostics-v1',
    'native-highlight-selection-poll-v1',
    'selection-popup-scene-observer-v1',
    'selection-popup-notebook-rebind-v1',
    'native-highlight-selection-text-resolver-v1',
    'context-refresh-clears-stale-selection-v1',
    'ai-edit-transaction-rollback-v1',
    'ai-edit-undo-rollback-v2',
    'native-mindmap-read-tree-request-v1',
    'native-mn-object-registry-scan-v1',
    'native-mindmap-diff-apply-create-v1',
    'native-mindmap-delete-suggestion-confirm-v1'
  ];

  function isNil(value) {
    return value === null || value === undefined || (typeof NSNull !== 'undefined' && value instanceof NSNull);
  }

  function safeString(value) {
    if (isNil(value)) return '';
    return String(value);
  }

  function looksLikePdfMathUnicodeLoss(text) {
    text = safeString(text);
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
    text = safeString(text);
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
    text = safeString(text);
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

  function companionErrorDescription(error) {
    if (!error) return '';
    var parts = [];
    try {
      if (typeof error.localizedDescription === 'function') parts.push(String(error.localizedDescription()));
    } catch (err) {}
    try {
      if (typeof error.localizedFailureReason === 'function') parts.push(String(error.localizedFailureReason()));
    } catch (err2) {}
    try {
      if (typeof error.code === 'function') parts.push('code=' + String(error.code()));
      else if (error.code !== undefined) parts.push('code=' + String(error.code));
    } catch (err3) {}
    var fallback = safeString(error);
    if (fallback) parts.push(fallback);
    var joined = parts.join(' ');
    return joined.length > 500 ? joined.substring(0, 500) + '...' : joined;
  }

  function companionRequestErrorMessage(error, timeoutSeconds) {
    var detail = companionErrorDescription(error);
    var lower = detail.toLowerCase();
    if (lower.indexOf('timed out') >= 0 || lower.indexOf('timeout') >= 0 || lower.indexOf('-1001') >= 0) {
      return 'Codex Companion 请求超时：本地服务 127.0.0.1:48761 已收到请求，但模型任务超过 ' + Math.round(timeoutSeconds / 60) + ' 分钟未返回。请稍后查看结果，或停止后重试；也可以在设置页的“运行态采证”生成诊断 JSON。';
    }
    if (lower.indexOf('could not connect') >= 0 ||
        lower.indexOf('connection refused') >= 0 ||
        lower.indexOf('not connect') >= 0 ||
        lower.indexOf('refused') >= 0 ||
        lower.indexOf('-1004') >= 0) {
      return 'Codex Companion 未运行或端口不可达：无法连接 127.0.0.1:48761。请先启动本地 Companion 服务；若状态栏仍显示已连接，请在设置页的“运行态采证”生成诊断 JSON。';
    }
    if (!detail) {
      return 'Codex Companion 请求失败：没有收到系统错误详情。请检查本地服务 127.0.0.1:48761，并在设置页的“运行态采证”生成诊断 JSON。';
    }
    return 'Codex Companion 请求失败：' + detail + '。请检查本地服务 127.0.0.1:48761，必要时在设置页的“运行态采证”生成诊断 JSON。';
  }

  function countOf(list) {
    if (!list) return 0;
    if (list.length !== undefined) return list.length;
    if (typeof list.count === 'function') return list.count();
    if (list.count !== undefined) return list.count;
    return 0;
  }

  function objectAt(list, index) {
    if (!list) return null;
    try {
      if (typeof list.objectAtIndex === 'function') return list.objectAtIndex(index);
    } catch (err) {}
    return list[index];
  }

  function valueOf(obj, key) {
    if (!obj) return null;
    try {
      if (obj[key] !== undefined) return isNil(obj[key]) ? null : obj[key];
    } catch (err) {}
    try {
      if (typeof obj.objectForKey === 'function') {
        var value = obj.objectForKey(key);
        return isNil(value) ? null : value;
      }
    } catch (err2) {}
    return null;
  }

  function notificationValueOf(obj, key) {
    if (!obj) return null;
    try {
      var direct = obj[key];
      if (typeof direct === 'function') {
        var called = direct.call(obj);
        return isNil(called) ? null : called;
      }
      if (!isNil(direct)) return direct;
    } catch (err) {}
    try {
      if (typeof obj.objectForKey === 'function') {
        var keyed = obj.objectForKey(key);
        return isNil(keyed) ? null : keyed;
      }
    } catch (err2) {}
    return null;
  }

  function notificationUserInfo(sender) {
    var info = notificationValueOf(sender, 'userInfo');
    if (info) return info;
    var object = notificationValueOf(sender, 'object');
    return notificationValueOf(object, 'userInfo');
  }

  function notificationDocumentController(sender, userInfo) {
    var controller = notificationValueOf(userInfo, 'documentController');
    if (controller) return controller;
    controller = notificationValueOf(sender, 'documentController');
    if (controller) return controller;
    var object = notificationValueOf(sender, 'object');
    return notificationValueOf(object, 'documentController');
  }

  function selectionTextFromDocumentController(documentController) {
    if (!documentController) return '';
    var keys = [
      'selectionText',
      'selectedText',
      'selectionString',
      'selectedString',
      'selectedTextString',
      'currentSelectionText'
    ];
    for (var i = 0; i < keys.length; i++) {
      var key = keys[i];
      try {
        var direct = documentController[key];
        if (typeof direct === 'function') direct = direct.call(documentController);
        var directText = safeString(direct);
        if (directText) return repairPdfExtractedMathText(directText);
      } catch (err) {}
      try {
        var keyed = valueOf(documentController, key);
        if (typeof keyed === 'function') keyed = keyed.call(documentController);
        var keyedText = safeString(keyed);
        if (keyedText) return repairPdfExtractedMathText(keyedText);
      } catch (err2) {}
    }
    return '';
  }

  function firstStringValue(obj, keys) {
    if (!obj) return '';
    for (var i = 0; i < keys.length; i++) {
      var value = valueOf(obj, keys[i]);
      var text = safeString(value);
      if (text) return text;
    }
    return '';
  }

  function escapeMarkerText(text) {
    return String(text || '').replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/</g, '\\u003c').replace(/>/g, '\\u003e');
  }

  function metadataComment(codexId) {
    if (!codexId) return '';
    return CodexMarkerPrefix + '{"codexId":"' + escapeMarkerText(codexId) + '"}-->';
  }

  function textFromComment(comment) {
    if (!comment) return '';
    var parts = [];
    var keys = ['text', 'html', 'markdown', 'noteText'];
    for (var i = 0; i < keys.length; i++) {
      try {
        var value = comment[keys[i]];
        if (typeof value === 'function') value = value.call(comment);
        if (!isNil(value)) parts.push(String(value));
      } catch (err) {}
    }
    return parts.join('\n');
  }

  function allTextFromNote(note) {
    if (!note) return '';
    var parts = [];
    try {
      if (note.allNoteText) parts.push(String(note.allNoteText()));
    } catch (err) {}
    try {
      var comments = note.comments;
      var total = countOf(comments);
      for (var i = 0; i < total; i++) parts.push(textFromComment(objectAt(comments, i)));
    } catch (err2) {}
    return parts.join('\n');
  }

  function noteHasCodexId(note, codexId) {
    if (!note || !codexId) return false;
    var raw = allTextFromNote(note);
    return raw.indexOf(CodexMarkerPrefix) >= 0 && raw.indexOf(String(codexId)) >= 0;
  }

  function scanNotesDeep(notes, visitor, stats, depth) {
    if (!notes || depth > 24) return null;
    var total = countOf(notes);
    for (var i = 0; i < total; i++) {
      var note = objectAt(notes, i);
      if (!note) continue;
      if (stats) stats.scanned += 1;
      var matched = visitor(note);
      if (matched) return matched;
      if (stats && stats.scanned > 5000) return null;
      var childKeys = ['childNotes', 'children', 'notes'];
      for (var j = 0; j < childKeys.length; j++) {
        var children = valueOf(note, childKeys[j]);
        if (!children || children === notes) continue;
        var found = scanNotesDeep(children, visitor, stats, depth + 1);
        if (found) return found;
      }
    }
    return null;
  }

  function findExistingCodexNote(notebook, codexId, title, stats) {
    if (!notebook || !codexId) return null;
    if (!stats) stats = {};
    if (stats.scanned === undefined) stats.scanned = 0;
    if (stats.markerMatches === undefined) stats.markerMatches = 0;
    if (stats.titleMatches === undefined) stats.titleMatches = 0;
    return scanNotesDeep(notebook.notes, function(note) {
      if (noteHasCodexId(note, codexId)) {
        stats.markerMatches += 1;
        return note;
      }
      return null;
    }, stats, 0);
  }

  function md5FromDocumentObject(doc) {
    return firstStringValue(doc, [
      'md5Long',
      'md5long',
      'md5',
      'bookMd5',
      'bookmd5',
      'docMd5',
      'docmd5',
      'documentMd5',
      'documentmd5',
      'identifier'
    ]);
  }

  function documentTitleFromDocumentObject(doc) {
    var direct = firstStringValue(doc, [
      'documentTitle',
      'title',
      'name',
      'fileName',
      'filename',
      'bookTitle',
      'bookName',
      'ZFILE',
      'ZBOOKURL'
    ]);
    if (direct) return direct;
    var path = pdfPathFromDocumentObject(doc);
    if (path) {
      var parts = path.split('/');
      return parts.length ? parts[parts.length - 1] : path;
    }
    var nestedKeys = ['document', 'currentDocument', 'book', 'currentBook', 'file', 'source'];
    for (var i = 0; i < nestedKeys.length; i++) {
      var item = valueOf(doc, nestedKeys[i]);
      direct = firstStringValue(item, [
        'documentTitle',
        'title',
        'name',
        'fileName',
        'filename',
        'bookTitle',
        'bookName',
        'ZFILE',
        'ZBOOKURL'
      ]);
      if (direct) return direct;
    }
    return '';
  }

  function pdfPathFromDocumentObject(doc) {
    var direct = firstStringValue(doc, [
      'pdfPath',
      'PDFPath',
      'filePath',
      'filepath',
      'localPath',
      'path',
      'documentPath',
      'sourcePath',
      'fullPath',
      'fileURL',
      'fileUrl',
      'url',
      'URL'
    ]);
    if (direct) return direct;
    var nestedKeys = ['document', 'currentDocument', 'book', 'currentBook', 'file', 'source'];
    for (var i = 0; i < nestedKeys.length; i++) {
      var item = valueOf(doc, nestedKeys[i]);
      direct = firstStringValue(item, [
        'pdfPath',
        'filePath',
        'localPath',
        'path',
        'documentPath',
        'fullPath',
        'fileURL',
        'url'
      ]);
      if (direct) return direct;
    }
    return '';
  }

  function documentTitleFromNotebookObject(notebook) {
    var direct = firstStringValue(notebook, [
      'documentTitle',
      'title',
      'name',
      'fileName',
      'filename',
      'bookTitle',
      'bookName',
      'ZFILE',
      'ZBOOKURL'
    ]);
    if (direct) return direct;
    try {
      if (notebook && notebook.documents && countOf(notebook.documents) > 0) {
        return documentTitleFromDocumentObject(objectAt(notebook.documents, 0));
      }
    } catch (err) {}
    var path = pdfPathFromNotebookObject(notebook);
    if (path) {
      var parts = path.split('/');
      return parts.length ? parts[parts.length - 1] : path;
    }
    return '';
  }

  function md5FromNotebookObject(notebook) {
    var direct = firstStringValue(notebook, [
      'mainDocMd5',
      'mainDocmd5',
      'mainDocumentMd5',
      'bookMd5',
      'bookmd5',
      'docMd5',
      'docmd5',
      'md5Long',
      'md5long',
      'md5'
    ]);
    if (direct) return direct;
    try {
      if (notebook && notebook.documents && countOf(notebook.documents) > 0) {
        return md5FromDocumentObject(objectAt(notebook.documents, 0));
      }
    } catch (err) {}
    return '';
  }

  function pdfPathFromNotebookObject(notebook) {
    var direct = firstStringValue(notebook, [
      'pdfPath',
      'PDFPath',
      'filePath',
      'filepath',
      'localPath',
      'path',
      'documentPath',
      'sourcePath',
      'fullPath',
      'fileURL',
      'url',
      'URL'
    ]);
    if (direct) return direct;
    try {
      if (notebook && notebook.documents && countOf(notebook.documents) > 0) {
        return pdfPathFromDocumentObject(objectAt(notebook.documents, 0));
      }
    } catch (err) {}
    return '';
  }

  function md5FromNotebookController(nc) {
    var direct = firstStringValue(nc, [
      'bookMd5',
      'bookmd5',
      'docMd5',
      'docmd5',
      'currentDocMd5',
      'currentDocumentMd5',
      'mainDocMd5',
      'mainDocumentMd5'
    ]);
    if (direct) return direct;
    var objectKeys = ['notebook', 'topic', 'document', 'currentDocument', 'book', 'currentBook'];
    for (var i = 0; i < objectKeys.length; i++) {
      var item = valueOf(nc, objectKeys[i]);
      direct = md5FromNotebookObject(item) || md5FromDocumentObject(item);
      if (direct) return direct;
    }
    return '';
  }

  function documentTitleFromNotebookController(nc) {
    var direct = firstStringValue(nc, [
      'documentTitle',
      'currentDocumentTitle',
      'fileName',
      'filename',
      'bookTitle',
      'bookName',
      'title',
      'name'
    ]);
    if (direct) return direct;
    var objectKeys = ['documentController', 'docController', 'notebook', 'topic', 'document', 'currentDocument', 'book', 'currentBook'];
    for (var i = 0; i < objectKeys.length; i++) {
      var item = valueOf(nc, objectKeys[i]);
      direct = documentTitleFromNotebookObject(item) || documentTitleFromDocumentObject(item);
      if (direct) return direct;
    }
    return '';
  }

  function pdfPathFromNotebookController(nc) {
    var direct = firstStringValue(nc, [
      'pdfPath',
      'PDFPath',
      'filePath',
      'filepath',
      'localPath',
      'path',
      'documentPath',
      'currentDocumentPath',
      'sourcePath',
      'fullPath',
      'fileURL',
      'url',
      'URL'
    ]);
    if (direct) return direct;
    var objectKeys = ['documentController', 'docController', 'notebook', 'topic', 'document', 'currentDocument', 'book', 'currentBook'];
    for (var i = 0; i < objectKeys.length; i++) {
      var item = valueOf(nc, objectKeys[i]);
      direct = pdfPathFromNotebookObject(item) || pdfPathFromDocumentObject(item);
      if (direct) return direct;
    }
    return '';
  }

  function md5FromDatabaseTopic(topicId) {
    if (!topicId) return '';
    try {
      var notebook = Database.sharedInstance().getNotebookById(String(topicId));
      return md5FromNotebookObject(notebook);
    } catch (err) {
      return '';
    }
  }

  function documentTitleFromDatabaseTopic(topicId) {
    if (!topicId) return '';
    try {
      var notebook = Database.sharedInstance().getNotebookById(String(topicId));
      return documentTitleFromNotebookObject(notebook);
    } catch (err) {
      return '';
    }
  }

  function pdfPathFromDatabaseTopic(topicId) {
    if (!topicId) return '';
    try {
      var notebook = Database.sharedInstance().getNotebookById(String(topicId));
      return pdfPathFromNotebookObject(notebook);
    } catch (err) {
      return '';
    }
  }

  function parseJSONData(data) {
    if (!data) return null;
    try {
      return NSJSONSerialization.JSONObjectWithDataOptions(data, 1);
    } catch (err) {}
    try {
      var raw = rawStringFromData(data);
      if (raw && raw.length) return JSON.parse(raw);
    } catch (err2) {}
    return null;
  }

  function rawStringFromData(data) {
    if (!data) return '';
    try {
      if (typeof data.base64Encoding === 'function') {
        var decoded = decodeBase64Utf8(String(data.base64Encoding()));
        if (decoded && decoded.length) return decoded;
      }
    } catch (err2) {}
    try {
      if (typeof data.length === 'function' && data.length() === 0) return '';
    } catch (err3) {}
    return '';
  }

  function previewData(data) {
    var raw = rawStringFromData(data);
    if (!raw) return '';
    return raw.length > 500 ? raw.substring(0, 500) + '...' : raw;
  }

  function decodeBase64Utf8(input) {
    var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
    var bytes = [];
    var i = 0;
    input = String(input || '').replace(/[^A-Za-z0-9+/=]/g, '');
    while (i < input.length) {
      var enc1 = chars.indexOf(input.charAt(i++));
      var enc2 = chars.indexOf(input.charAt(i++));
      var enc3 = chars.indexOf(input.charAt(i++));
      var enc4 = chars.indexOf(input.charAt(i++));
      if (enc1 < 0 || enc2 < 0) break;
      var chr1 = (enc1 << 2) | (enc2 >> 4);
      var chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
      var chr3 = ((enc3 & 3) << 6) | enc4;
      bytes.push(chr1 & 255);
      if (enc3 !== 64 && enc3 >= 0) bytes.push(chr2 & 255);
      if (enc4 !== 64 && enc4 >= 0) bytes.push(chr3 & 255);
    }
    return decodeUtf8Bytes(bytes);
  }

  function decodeUtf8Bytes(bytes) {
    var out = '';
    for (var i = 0; i < bytes.length;) {
      var c = bytes[i++];
      if (c < 128) {
        out += String.fromCharCode(c);
      } else if (c >= 192 && c < 224 && i < bytes.length) {
        out += String.fromCharCode(((c & 31) << 6) | (bytes[i++] & 63));
      } else if (c >= 224 && c < 240 && i + 1 < bytes.length) {
        out += String.fromCharCode(((c & 15) << 12) | ((bytes[i++] & 63) << 6) | (bytes[i++] & 63));
      } else if (c >= 240 && i + 2 < bytes.length) {
        var codepoint = ((c & 7) << 18) | ((bytes[i++] & 63) << 12) | ((bytes[i++] & 63) << 6) | (bytes[i++] & 63);
        codepoint -= 0x10000;
        out += String.fromCharCode(0xD800 + (codepoint >> 10), 0xDC00 + (codepoint & 1023));
      }
    }
    return out;
  }

  function postJSON(url, payload, timeout, callback) {
    var request = NSMutableURLRequest.requestWithURL(NSURL.URLWithString(url));
    request.setHTTPMethod('POST');
    request.setTimeoutInterval(timeout || 5);
    request.setAllHTTPHeaderFields({'Content-Type': 'application/json', 'Accept': 'application/json'});
    request.setHTTPBody(NSJSONSerialization.dataWithJSONObjectOptions(payload, 1));
    NSURLConnection.sendAsynchronousRequestQueueCompletionHandler(request, NSOperationQueue.mainQueue(), function(response, data, error) {
      if (callback) callback(response, data, error);
    });
  }

  function createPanelController(addon) {
    try {
      if (typeof CodexWebPanelController !== 'undefined') {
        var webPanel = CodexWebPanelController.new();
        webPanel.panelKind = 'webview';
        webPanel.mainPath = mainPath;
        webPanel.addon = addon;
        webPanel.addonWindow = addon.window;
        return webPanel;
      }
    } catch (err) {
      try {
        addon.postEvent('webPanelCreateFailed', {message: safeString(err)});
      } catch (ignored) {}
    }
    var legacyPanel = CodexPanelController.new();
    legacyPanel.panelKind = 'legacy';
    legacyPanel.addon = addon;
    legacyPanel.addonWindow = addon.window;
    return legacyPanel;
  }

  function toArray(list) {
    var out = [];
    var count = countOf(list);
    for (var i = 0; i < count; i++) {
      var item = objectAt(list, i);
      if (item) out.push(item);
    }
    return out;
  }

  var NativeHighlightMethodCandidates = [
    'AppendHighlight',
    'appendHighlight',
    'addHighlight',
    'createHighlight',
    'highlightSelection',
    'highlightFromSelection',
    'TextHighlightTool',
    'textHighlightTool',
    'UpdateAnnotationOfNotes',
    'updateAnnotationOfNotes',
    'importPdfAnnotations'
  ];
  var NativeExportMethodCandidates = [
    'ExportHighlightedPages',
    'exportHighlightedPages',
    'exportAnnotatedPDF',
    'exportAnnotatedPdf',
    'exportPDF',
    'exportPdf',
    'exportPdfWithAnnotations',
    'exportPDFWithAnnotations',
    'importPdfAnnotations'
  ];

  function selectorVariants(name) {
    return [name, name + ':', name + '::', name + ':::'];
  }

  function objectRespondsToMethod(obj, name) {
    if (!obj || !name) return false;
    try {
      if (typeof obj[name] === 'function') return true;
      if (obj[name] !== undefined && obj[name] !== null) return true;
    } catch (err) {}
    try {
      if (typeof obj.respondsToSelector === 'function') {
        var variants = selectorVariants(name);
        for (var i = 0; i < variants.length; i++) {
          try {
            if (obj.respondsToSelector(variants[i])) return true;
          } catch (ignored) {}
        }
      }
    } catch (err2) {}
    return false;
  }

  function noteIdentifier(note) {
    return safeString(valueOf(note, 'noteId') || valueOf(note, 'id') || valueOf(note, 'noteid'));
  }

  function findNoteById(notebook, noteId) {
    noteId = safeString(noteId);
    if (!notebook || !noteId) return null;
    return scanNotesDeep(notebook.notes, function(note) {
      return noteIdentifier(note) === noteId ? note : null;
    }, {scanned: 0}, 0);
  }

  function refreshAiEditNotebook(ctx) {
    if (!ctx || !ctx.topicId) return ctx;
    try {
      var notebook = Database.sharedInstance().getNotebookById(String(ctx.topicId));
      if (notebook) ctx.notebook = notebook;
    } catch (err) {}
    return ctx;
  }

  function aiEditDatabases() {
    var out = [];
    function add(label, db) {
      if (!db) return;
      for (var i = 0; i < out.length; i++) {
        if (out[i].object === db) return;
      }
      out.push({label: label, object: db});
    }
    try {
      if (typeof Database !== 'undefined' && Database.sharedInstance) add('Database', Database.sharedInstance());
    } catch (err) {}
    try {
      if (typeof MbModelTool !== 'undefined' && MbModelTool.sharedInstance) add('MbModelTool', MbModelTool.sharedInstance());
    } catch (err2) {}
    return out;
  }

  function aiEditDatabase() {
    var dbs = aiEditDatabases();
    return dbs.length ? dbs[0].object : null;
  }

  function callAiEditMethodValue(obj, method, args) {
    if (!obj || !method || !objectRespondsToMethod(obj, method)) return null;
    var callables = callableMethodVariants(obj, method);
    args = args || [];
    for (var i = 0; i < callables.length; i++) {
      try {
        return {ok: true, method: callables[i], value: obj[callables[i]].apply(obj, args)};
      } catch (err) {}
    }
    return null;
  }

  function databaseNoteById(noteId) {
    noteId = safeString(noteId);
    if (!noteId) return null;
    var dbs = aiEditDatabases();
    for (var i = 0; i < dbs.length; i++) {
      var db = dbs[i].object;
      var result = callAiEditMethodValue(db, 'getNoteById', [noteId]) ||
        callAiEditMethodValue(db, 'getNoteFromId', [noteId]);
      if (result && !isNil(result.value)) return result.value;
    }
    return null;
  }

  function markAiEditDatabaseChanged(topicId) {
    topicId = safeString(topicId);
    var dbs = aiEditDatabases();
    for (var i = 0; i < dbs.length; i++) {
      var db = dbs[i].object;
      if (topicId) {
        callAiEditMethodValue(db, 'setNotebookSyncDirty', [topicId]);
        callAiEditMethodValue(db, 'setTopicDirty', [topicId]);
      }
      callAiEditMethodValue(db, 'savedb', []);
    }
  }

  function resolveAiEditNoteById(ctx, noteId) {
    noteId = safeString(noteId);
    if (!noteId) return null;
    var note = ctx ? findNoteById(ctx.notebook, noteId) : null;
    if (note) return note;
    if (ctx) {
      refreshAiEditNotebook(ctx);
      note = findNoteById(ctx.notebook, noteId);
      if (note) return note;
    }
    return databaseNoteById(noteId);
  }

  function verifyAiEditNoteDeleted(noteId, ctx) {
    noteId = safeString(noteId);
    if (!noteId) return false;
    if (databaseNoteById(noteId)) return false;
    if (!ctx) return true;
    refreshAiEditNotebook(ctx);
    return !findNoteById(ctx.notebook, noteId);
  }

  function callableMethodVariants(obj, method) {
    var out = [];
    if (!obj || !method) return out;
    var variants = selectorVariants(method);
    for (var i = 0; i < variants.length; i++) {
      try {
        if (typeof obj[variants[i]] === 'function') out.push(variants[i]);
      } catch (err) {}
    }
    return out;
  }

  function tryCallAiEditMethod(obj, method, argsList) {
    if (!obj || !method || !objectRespondsToMethod(obj, method)) return null;
    argsList = argsList || [[]];
    for (var i = 0; i < argsList.length; i++) {
      var result = callAiEditMethodValue(obj, method, argsList[i]);
      if (result && result.ok) {
        return {ok: true, method: result.method};
      }
    }
    return null;
  }

  function attemptVerifiedAiEditDelete(label, obj, methods, argsList, noteId, ctx) {
    if (!obj) return null;
    var lastFailure = null;
    for (var i = 0; i < methods.length; i++) {
      var call = tryCallAiEditMethod(obj, methods[i], argsList);
      if (!call || !call.ok) continue;
      var methodName = label + '.' + call.method;
      if (verifyAiEditNoteDeleted(noteId, ctx)) {
        return {ok: true, method: methodName, noteId: noteId};
      }
      lastFailure = {ok: false, method: methodName, reason: 'still-exists-after-delete', noteId: noteId};
    }
    return lastFailure;
  }

  function deleteNoteForAiEdit(note, ctx, noteId) {
    noteId = safeString(noteId || noteIdentifier(note));
    if (!noteId) return {ok: false, method: '', reason: 'missing-note-id'};
    if (!note) note = resolveAiEditNoteById(ctx, noteId);
    if (!note && verifyAiEditNoteDeleted(noteId, ctx)) {
      return {ok: true, method: 'already-deleted', noteId: noteId};
    }
    var databaseDeleteMethods = ['deleteBookNoteTree', 'deleteBookNote', 'removeNote', 'deleteNote', 'removeNotebookNote', 'deleteNotebookNote', 'deleteObject', 'removeObject'];
    var argsList = [[noteId]];
    if (note) {
      argsList.push([note]);
      argsList.push([note, noteId]);
    }
    var dbs = aiEditDatabases();
    var lastFailure = null;
    for (var i = 0; i < dbs.length; i++) {
      var result = attemptVerifiedAiEditDelete('database.' + dbs[i].label, dbs[i].object, databaseDeleteMethods, argsList, noteId, ctx);
      if (result && result.ok) return result;
      if (result) lastFailure = result;
    }
    if (verifyAiEditNoteDeleted(noteId, ctx)) {
      return {ok: true, method: 'deleted-by-related-node', noteId: noteId};
    }
    if (lastFailure) return lastFailure;
    return {ok: false, method: 'database', reason: 'database-delete-unavailable', noteId: noteId};
  }

  function pruneAiEditDeleteFailures(failed, ctx) {
    var remaining = [];
    for (var i = 0; i < failed.length; i++) {
      var item = failed[i];
      if (!verifyAiEditNoteDeleted(item.noteId, ctx)) remaining.push(item);
    }
    return remaining;
  }

  function remainingAiEditNoteIds(noteIds, ctx) {
    var ids = toArray(noteIds);
    var remaining = [];
    for (var i = 0; i < ids.length; i++) {
      var noteId = safeString(ids[i]);
      if (noteId && !verifyAiEditNoteDeleted(noteId, ctx)) remaining.push(noteId);
    }
    return remaining;
  }

  function rollbackAiEditTransactionWithUndo(transaction, ctx) {
    var ids = transaction ? transaction.createdNoteIds : [];
    var before = remainingAiEditNoteIds(ids, ctx);
    var topicId = ctx ? ctx.topicId : safeString(transaction ? transaction.topicid : '');
    if (!before.length) {
      return {ok: true, method: 'undo-already-deleted', deleted: countOf(ids), remaining: [], reason: ''};
    }
    var manager = null;
    try {
      manager = UndoManager.sharedInstance();
    } catch (err) {}
    if (!manager || !objectRespondsToMethod(manager, 'undo')) {
      return {ok: false, method: 'undo', deleted: 0, remaining: before, reason: 'undo-unavailable'};
    }
    var canUndo = true;
    try {
      if (typeof manager.canUndo === 'function') canUndo = !!manager.canUndo();
      else if (!isNil(manager.canUndo)) canUndo = !!manager.canUndo;
    } catch (canUndoErr) {}
    if (!canUndo) {
      return {ok: false, method: 'undo', deleted: 0, remaining: before, reason: 'undo-stack-empty'};
    }
    try {
      UndoManager.sharedInstance().undo();
    } catch (undoErr) {
      return {ok: false, method: 'undo', deleted: 0, remaining: before, reason: 'undo-threw:' + safeString(undoErr)};
    }
    markAiEditDatabaseChanged(topicId);
    try {
      if (ctx && ctx.topicId) Application.sharedInstance().refreshAfterDBChanged(ctx.topicId);
    } catch (refreshErr) {}
    var after = remainingAiEditNoteIds(ids, ctx);
    return {
      ok: after.length === 0,
      method: 'undo',
      deleted: before.length - after.length,
      remaining: after,
      reason: after.length ? 'created-notes-still-exist-after-undo' : ''
    };
  }

  function aiEditFallbackContext(topicId) {
    topicId = safeString(topicId);
    if (!topicId) return null;
    try {
      var notebook = Database.sharedInstance().getNotebookById(topicId);
      if (!notebook) return null;
      return {controller: null, notebook: notebook, document: null, topicId: topicId};
    } catch (err) {
      return null;
    }
  }

  function probeCandidateMethods(label, obj, methods, found) {
    var hits = [];
    if (!obj) return hits;
    for (var i = 0; i < methods.length; i++) {
      var method = methods[i];
      if (objectRespondsToMethod(obj, method)) {
        var full = label + '.' + method;
        hits.push(full);
        found.push(full);
      }
    }
    return hits;
  }

  function probeTargetObject(label, obj, highlightMethods, exportMethods, foundHighlight, foundExport) {
    return {
      label: label,
      exists: !!obj,
      highlightMethods: probeCandidateMethods(label, obj, highlightMethods, foundHighlight),
      exportMethods: probeCandidateMethods(label, obj, exportMethods, foundExport)
    };
  }

  function documentControllerCandidates(addon, controller, nc) {
    var candidates = [];
    var seenLabels = {};
    function add(label, obj) {
      if (!label || seenLabels[label]) return;
      seenLabels[label] = true;
      candidates.push({label: label, object: obj || null});
    }
    function addStableControllerPaths(prefix, obj) {
      if (!obj) return;
      add(prefix + '.currentDocumentController', valueOf(obj, 'currentDocumentController'));
      add(prefix + '.readerController', valueOf(obj, 'readerController'));
      add(prefix + '.readerViewController', valueOf(obj, 'readerViewController'));
      add(prefix + '.pdfController', valueOf(obj, 'pdfController'));
      add(prefix + '.pdfViewController', valueOf(obj, 'pdfViewController'));

      var readerController = valueOf(obj, 'readerController');
      var readerViewController = valueOf(obj, 'readerViewController');
      var pdfController = valueOf(obj, 'pdfController');
      var pdfViewController = valueOf(obj, 'pdfViewController');
      add(prefix + '.readerController.documentController', valueOf(readerController, 'documentController'));
      add(prefix + '.readerController.docController', valueOf(readerController, 'docController'));
      add(prefix + '.readerController.currentDocumentController', valueOf(readerController, 'currentDocumentController'));
      add(prefix + '.readerViewController.documentController', valueOf(readerViewController, 'documentController'));
      add(prefix + '.readerViewController.docController', valueOf(readerViewController, 'docController'));
      add(prefix + '.readerViewController.currentDocumentController', valueOf(readerViewController, 'currentDocumentController'));
      add(prefix + '.pdfController.documentController', valueOf(pdfController, 'documentController'));
      add(prefix + '.pdfController.docController', valueOf(pdfController, 'docController'));
      add(prefix + '.pdfController.currentDocumentController', valueOf(pdfController, 'currentDocumentController'));
      add(prefix + '.pdfViewController.documentController', valueOf(pdfViewController, 'documentController'));
      add(prefix + '.pdfViewController.docController', valueOf(pdfViewController, 'docController'));
      add(prefix + '.pdfViewController.currentDocumentController', valueOf(pdfViewController, 'currentDocumentController'));
    }
    function addControllerAliases(prefix, obj) {
      if (!obj) return;
      var directKeys = [
        'documentController',
        'docController',
        'currentDocumentController',
        'readerController',
        'readerViewController',
        'reader',
        'readerView',
        'readerVC',
        'pdfController',
        'pdfViewController',
        'pdfReader',
        'pdfReaderController',
        'pdfDocumentController',
        'documentViewController',
        'docViewController',
        'pdfView'
      ];
      for (var i = 0; i < directKeys.length; i++) {
        add(prefix + '.' + directKeys[i], valueOf(obj, directKeys[i]));
      }
      var nestedKeys = [
        'readerController',
        'readerViewController',
        'reader',
        'readerView',
        'readerVC',
        'pdfController',
        'pdfViewController',
        'pdfReader',
        'pdfReaderController',
        'pdfDocumentController',
        'documentViewController',
        'docViewController',
        'pdfView'
      ];
      var nestedControllerKeys = ['documentController', 'docController', 'currentDocumentController'];
      for (var n = 0; n < nestedKeys.length; n++) {
        var nested = valueOf(obj, nestedKeys[n]);
        for (var c = 0; c < nestedControllerKeys.length; c++) {
          add(prefix + '.' + nestedKeys[n] + '.' + nestedControllerKeys[c], valueOf(nested, nestedControllerKeys[c]));
        }
      }
    }
    var lastDocumentController = addon ? addon.lastDocumentController : null;
    add('selectionDocumentController', lastDocumentController);
    add('lastDocumentController', lastDocumentController);
    add('documentController',
      valueOf(controller, 'documentController') ||
      valueOf(controller, 'docController') ||
      valueOf(nc, 'documentController') ||
      valueOf(nc, 'docController'));
    add('studyController.currentDocumentController', valueOf(controller, 'currentDocumentController'));
    add('studyController.readerController', valueOf(controller, 'readerController'));
    add('studyController.pdfController', valueOf(controller, 'pdfController'));
    add('studyController.pdfViewController', valueOf(controller, 'pdfViewController'));
    add('notebookController.currentDocumentController', valueOf(nc, 'currentDocumentController'));
    add('notebookController.readerController', valueOf(nc, 'readerController'));
    add('notebookController.pdfController', valueOf(nc, 'pdfController'));
    add('notebookController.pdfViewController', valueOf(nc, 'pdfViewController'));
    addStableControllerPaths('studyController', controller);
    addStableControllerPaths('notebookController', nc);
    addControllerAliases('studyController', controller);
    addControllerAliases('notebookController', nc);
    var controllerDocument = valueOf(controller, 'currentDocument') || valueOf(controller, 'document') || valueOf(controller, 'currentDoc') || valueOf(controller, 'doc');
    var notebookDocument = valueOf(nc, 'currentDocument') || valueOf(nc, 'document') || valueOf(nc, 'currentDoc') || valueOf(nc, 'doc');
    add('studyController.currentDocument.documentController', valueOf(controllerDocument, 'documentController'));
    add('studyController.currentDocument.docController', valueOf(controllerDocument, 'docController'));
    add('notebookController.currentDocument.documentController', valueOf(notebookDocument, 'documentController'));
    add('notebookController.currentDocument.docController', valueOf(notebookDocument, 'docController'));
    return candidates;
  }

  function resolveDocumentController(addon, controller, nc) {
    var candidates = documentControllerCandidates(addon, controller, nc);
    var labels = [];
    var firstObject = null;
    var firstLabel = '';
    for (var i = 0; i < candidates.length; i++) {
      var candidate = candidates[i];
      labels.push(candidate.label);
      if (!candidate.object) continue;
      if (!firstObject) {
        firstObject = candidate.object;
        firstLabel = candidate.label;
      }
      if (objectRespondsToMethod(candidate.object, 'highlightFromSelection')) {
        return {
          controller: candidate.object,
          label: candidate.label,
          labels: labels,
          candidates: candidates
        };
      }
    }
    return {
      controller: firstObject,
      label: firstLabel,
      labels: labels,
      candidates: candidates
    };
  }

  function targetExists(targets, label) {
    for (var i = 0; i < targets.length; i++) {
      if (targets[i] && targets[i].label === label && targets[i].exists) return true;
    }
    return false;
  }

  function targetLabelIndicatesDocumentController(targets) {
    var markers = [
      'documentcontroller',
      'doccontroller',
      'currentdocumentcontroller',
      'readercontroller',
      'readerviewcontroller',
      'pdfcontroller',
      'pdfviewcontroller',
      'pdfreader',
      'pdfdocumentcontroller',
      'documentviewcontroller',
      'docviewcontroller',
      'pdfview'
    ];
    for (var i = 0; i < targets.length; i++) {
      var target = targets[i];
      if (!target || !target.exists || !target.label) continue;
      var label = String(target.label).toLowerCase();
      if (label === 'selectiondocumentcontroller' || label === 'documentcontroller') return true;
      if (label === 'studycontroller.readercontroller') return true;
      for (var j = 0; j < markers.length; j++) {
        if (label.indexOf(markers[j]) >= 0) return true;
      }
    }
    return false;
  }

  function invokeHighlightFromSelection(docController) {
    var selectorVerified = objectRespondsToMethod(docController, 'highlightFromSelection');
    try {
      return {
        ok: true,
        highlight: docController.highlightFromSelection(),
        selectorVerified: selectorVerified,
        attemptedUnverifiedSelector: !selectorVerified
      };
    } catch (err) {
      return {
        ok: false,
        error: err,
        selectorVerified: selectorVerified,
        attemptedUnverifiedSelector: !selectorVerified
      };
    }
  }

  function hasMethodHit(methods, needle) {
    needle = String(needle || '').toLowerCase();
    for (var i = 0; i < methods.length; i++) {
      if (String(methods[i] || '').toLowerCase().indexOf(needle) >= 0) return true;
    }
    return false;
  }

  function nativeCapabilityMatrix(targets, foundHighlight, foundExport, activeSelectionLength, context) {
    var selectionControllerExists =
      targetExists(targets, 'selectionDocumentController') ||
      targetExists(targets, 'documentController') ||
      hasMethodHit(foundHighlight, 'selectionDocumentController.') ||
      hasMethodHit(foundHighlight, 'documentController.') ||
      hasMethodHit(foundHighlight, 'currentDocumentController.') ||
      hasMethodHit(foundHighlight, 'readerController.') ||
      hasMethodHit(foundHighlight, 'readerViewController.') ||
      hasMethodHit(foundHighlight, 'pdfController.') ||
      hasMethodHit(foundHighlight, 'pdfViewController.') ||
      targetLabelIndicatesDocumentController(targets);
    var hasHighlightSelector = hasMethodHit(foundHighlight, 'highlightFromSelection') || foundHighlight.length > 0;
    var canAttemptUnverifiedHighlightCall = !!(selectionControllerExists && !hasHighlightSelector);
    var canCreateNote = false;
    try {
      canCreateNote = typeof Note !== 'undefined' &&
        typeof Note.createWithTitleNotebookDocument === 'function';
    } catch (noteErr) {
      canCreateNote = false;
    }
    var canGroupUndo = false;
    try {
      canGroupUndo = typeof UndoManager !== 'undefined' &&
        !!UndoManager.sharedInstance().undoGrouping;
    } catch (undoErr) {
      canGroupUndo = false;
    }
    var app = null;
    try {
      app = Application.sharedInstance();
    } catch (appErr) {
      app = null;
    }
    var canRefreshAfterDBChanged = objectRespondsToMethod(app, 'refreshAfterDBChanged');
    var canInstallSelectionPopupMenu = false;
    try {
      canInstallSelectionPopupMenu = typeof PopupMenu !== 'undefined' &&
        typeof PopupMenuItem !== 'undefined';
    } catch (popupErr) {
      canInstallSelectionPopupMenu = false;
    }
    var hasPdfPath = !!(context && (context.pdfPath || context.documentPath));
    var hasDocumentIdentity = !!(hasPdfPath || (context && (context.documentTitle || context.documentFileName || context.sourceFileName)));
    var canUpdateMindmapNode = canCreateNote;
    var canMergeMindmapNode = canCreateNote;
    var canMoveMindmapNode = canCreateNote;
    var canDeleteMindmapNode = false;
    var highlightBlocked = '';
    var highlightNext = '点击“高亮选区”，MN4 会调用 documentController.highlightFromSelection().';
    if (!selectionControllerExists) {
      highlightBlocked = 'missing-document-controller';
      highlightNext = '先打开 PDF 文档并让 MN4 面板刷新上下文。';
    } else if (!hasHighlightSelector && !canAttemptUnverifiedHighlightCall) {
      highlightBlocked = 'missing-highlight-selector';
      highlightNext = '当前 MN4 运行时未暴露可调用的选区高亮 selector。';
    } else if (!activeSelectionLength) {
      highlightBlocked = 'missing-active-pdf-selection';
      highlightNext = canAttemptUnverifiedHighlightCall ?
        '已发现 PDF 控制器但 selector 不可枚举；先在 PDF 里选中文本，再点击“高亮选区”尝试官方 highlightFromSelection。' :
        '先在 PDF 里选中文本，再点击“高亮选区”。';
    } else if (canAttemptUnverifiedHighlightCall) {
      highlightBlocked = '';
      highlightNext = '已发现 PDF 控制器但 selector 不可枚举；点击“高亮选区”会尝试官方 highlightFromSelection 并记录结果。';
    }
    var highlightEvidence = foundHighlight.slice ? foundHighlight.slice(0) : [];
    if (canAttemptUnverifiedHighlightCall) highlightEvidence.push('unverified-highlightFromSelection-call');
    return {
      nativeHighlightSelection: {
        label: '原生高亮当前 PDF 选区',
        available: !!(selectionControllerExists && (hasHighlightSelector || canAttemptUnverifiedHighlightCall)),
        ready: !!(selectionControllerExists && (hasHighlightSelector || canAttemptUnverifiedHighlightCall) && activeSelectionLength),
        entryAction: 'request_native_highlight_selection',
        nativeAction: 'highlight_current_selection',
        blockedReason: highlightBlocked,
        nextStep: highlightNext,
        evidence: highlightEvidence
      },
      selectionPopupHighlight: {
        label: 'PDF 选区弹出菜单高亮入口',
        available: canInstallSelectionPopupMenu,
        ready: !!(canInstallSelectionPopupMenu && activeSelectionLength),
        entryAction: 'request_native_highlight_selection',
        blockedReason: canInstallSelectionPopupMenu && activeSelectionLength ? '' : 'needs-selection-popup',
        nextStep: '在 PDF 中选中文本后，从弹出菜单点“Codex 高亮选区”。',
        evidence: canInstallSelectionPopupMenu ? ['PopupMenu.currentMenu', 'PopupMenuItem'] : []
      },
      nativeCards: {
        label: '创建 MN 原生卡片',
        available: canCreateNote,
        ready: canCreateNote,
        entryAction: 'draft_accept',
        nativeAction: 'createCards',
        blockedReason: canCreateNote ? '' : 'unverified-note-api',
        nextStep: '生成卡片草稿后点“写入 MarginNote”。',
        evidence: canCreateNote ? ['Note.createWithTitleNotebookDocument'] : []
      },
      nativeMindmap: {
        label: '创建或合并 MN 原生脑图节点',
        available: canCreateNote,
        ready: canCreateNote,
        entryAction: 'draft_accept',
        nativeAction: 'createMindmap',
        blockedReason: canCreateNote ? '' : 'unverified-note-api',
        nextStep: '生成脑图草稿后点“写入 MarginNote”；合并会追加到当前选中节点下。',
        evidence: canCreateNote ? ['Note.createWithTitleNotebookDocument', 'addChild'] : []
      },
      nativeMindmapUpdate: {
        label: '更新 MN 原生脑图节点',
        available: canUpdateMindmapNode,
        ready: canUpdateMindmapNode,
        entryAction: 'request_mindmap_diff_apply',
        nativeAction: 'apply_mindmap_diff_operations',
        blockedReason: canUpdateMindmapNode ? '' : 'unverified-note-update-api',
        nextStep: '局部 Diff 可通过 noteTitle 与 appendMarkdownComment 更新现有节点。',
        evidence: canUpdateMindmapNode ? ['noteTitle', 'appendMarkdownComment'] : []
      },
      nativeMindmapMerge: {
        label: '合并 MN 原生脑图节点',
        available: canMergeMindmapNode,
        ready: canMergeMindmapNode,
        entryAction: 'request_mindmap_diff_apply',
        nativeAction: 'apply_mindmap_diff_operations',
        blockedReason: canMergeMindmapNode ? '' : 'unverified-note-merge-api',
        nextStep: '局部 Diff 可把重复节点内容追加到现有节点正文中。',
        evidence: canMergeMindmapNode ? ['appendMarkdownComment'] : []
      },
      nativeMindmapMove: {
        label: '移动 MN 原生脑图节点',
        available: canMoveMindmapNode,
        ready: canMoveMindmapNode,
        entryAction: 'request_mindmap_diff_apply',
        nativeAction: 'apply_mindmap_diff_operations',
        blockedReason: canMoveMindmapNode ? '' : 'unverified-note-move-api',
        nextStep: '局部 Diff 可通过 addChild 把现有节点挂到新父节点下。',
        evidence: canMoveMindmapNode ? ['addChild'] : []
      },
      nativeMindmapDelete: {
        label: '删除 MN 原生脑图节点',
        available: canDeleteMindmapNode,
        ready: canDeleteMindmapNode,
        entryAction: 'request_mindmap_diff_apply',
        nativeAction: 'apply_mindmap_diff_operations',
        blockedReason: canDeleteMindmapNode ? '' : 'unverified-note-delete-api',
        nextStep: '删除类 diff 仍只做建议；必须额外确认并通过事务验证后才能执行。',
        evidence: []
      },
      undoGroupedWrites: {
        label: 'MN Undo 分组写入',
        available: canGroupUndo,
        ready: canGroupUndo,
        entryAction: 'draft_accept',
        blockedReason: canGroupUndo ? '' : 'unverified-undo-manager',
        nextStep: '写入卡片/脑图时由 UndoManager 分组，便于撤销。',
        evidence: canGroupUndo ? ['UndoManager.sharedInstance().undoGrouping'] : []
      },
      refreshAfterWrite: {
        label: '写入后刷新 MN 视图',
        available: canRefreshAfterDBChanged,
        ready: canRefreshAfterDBChanged,
        entryAction: 'draft_accept',
        blockedReason: canRefreshAfterDBChanged ? '' : 'unverified-refresh-api',
        nextStep: '写入后刷新当前 topic，让新节点立即显示。',
        evidence: canRefreshAfterDBChanged ? ['Application.sharedInstance().refreshAfterDBChanged'] : []
      },
      cacheCurrentPdf: {
        label: '由 MN 插件进程缓存当前 PDF',
        available: true,
        ready: hasDocumentIdentity,
        entryAction: 'request_pdf_cache',
        nativeAction: 'cache_pdf_from_current_document',
        blockedReason: hasDocumentIdentity ? '' : 'needs-current-pdf-identity',
        nextStep: '打开目标 PDF 后点击“缓存PDF”，由 MN4 插件进程读取文件并上传给 Companion。',
        evidence: hasPdfPath ? ['resolveContext.pdfPath'] : (hasDocumentIdentity ? ['resolveContext.documentTitle'] : [])
      },
      annotatedPdfExport: {
        label: '导出带标注 PDF 副本',
        available: true,
        ready: !!(foundExport.length || hasPdfPath),
        entryAction: 'export_annotated_pdf',
        blockedReason: foundExport.length || hasPdfPath ? '' : 'needs-pdf-cache-or-path',
        nextStep: '先缓存 PDF 或让 MN4 payload 带上 pdfPath；导出只写副本，不覆盖原 PDF。',
        evidence: foundExport.length ? foundExport : (hasPdfPath ? ['cached/pdfPath'] : [])
      }
    };
  }

  var CodexAssistantAddon = JSB.defineClass('CodexAssistantAddon : JSExtension', {
    sceneWillConnect: function() {
      self.currentNotebookId = '';
      self.currentDocMd5 = '';
      self.lastSelectionText = '';
      self.lastDocumentController = null;
      self.nativeHighlightNextSelectionArmed = false;
      self.nativeHighlightNextSelectionReason = '';
      self.nativeHighlightNextSelectionText = '';
      self.nativeHighlightNextSelectionPollTimer = null;
      self.nativeHighlightNextSelectionPollStartedAt = 0;
      self.selectionPopupObserverRegistered = false;
      self.companionBusy = false;
      self.panel = createPanelController(self);
      self.registerSelectionPopupObserver('sceneWillConnect');
      NSTimer.scheduledTimerWithTimeInterval(0.3, false, function() {
        if (self.postEvent) self.postEvent('sceneWillConnect', {});
      });
    },

    sceneDidDisconnect: function() {
      self.stopNativeHighlightSelectionPoll();
      self.unregisterSelectionPopupObserver('sceneDidDisconnect');
      self.hidePanel();
    },

    notebookWillOpen: function(notebookid) {
      self.currentNotebookId = safeString(notebookid);
      self.registerSelectionPopupObserver('notebookWillOpen', true);
      self.postEvent('notebookWillOpen', {notebookid: safeString(notebookid)});
      self.startCommandPolling();
      NSTimer.scheduledTimerWithTimeInterval(0.8, false, function() {
        try {
          self.showPanel();
          self.postEvent('panelAutoShown', {reason: 'notebookWillOpen'});
        } catch (err) {
          self.postEvent('panelAutoShowFailed', {message: safeString(err)});
        }
      });
    },

    notebookWillClose: function(notebookid) {
      self.unregisterSelectionPopupObserver('notebookWillClose');
      self.stopCommandPolling();
      self.hidePanel();
    },

    documentDidOpen: function(docmd5) {
      self.currentDocMd5 = safeString(docmd5);
      self.postEvent('documentDidOpen', {docmd5: safeString(docmd5)});
    },

    documentWillClose: function(docmd5) {
      self.currentDocMd5 = '';
    },

    controllerWillLayoutSubviews: function(controller) {
      if (controller == Application.sharedInstance().studyController(self.window)) self.layoutPanel();
    },

    queryAddonCommandStatus: function() {
      var controller = Application.sharedInstance().studyController(self.window);
      if (controller && controller.studyMode < 3) {
        return {image: 'codex.png', object: self, selector: 'togglePanel:', checked: !!(self.panel && self.panel.view && self.panel.view.window)};
      }
      return null;
    },

    onPopupMenuOnSelection: function(sender) {
      var popupUserInfo = notificationUserInfo(sender);
      var documentController = notificationDocumentController(sender, popupUserInfo);
      var text = selectionTextFromDocumentController(documentController);
      self.postEvent('selectionPopupHighlightNotificationObserved', {
        hasSender: !!sender,
        hasUserInfo: !!popupUserInfo,
        hasDocumentController: !!documentController,
        selectionLength: text.length,
        armed: !!self.nativeHighlightNextSelectionArmed
      });
      var senderInWindow = false;
      var windowFilterError = '';
      try {
        senderInWindow = !!Application.sharedInstance().checkNotifySenderInWindow(sender, self.window);
      } catch (windowErr) {
        windowFilterError = safeString(windowErr);
      }
      if (!senderInWindow) {
        self.postEvent('selectionPopupHighlightNotificationSkipped', {
          reason: 'outside-window',
          hasSender: !!sender,
          hasUserInfo: !!popupUserInfo,
          hasDocumentController: !!documentController,
          selectionLength: text.length,
          armed: !!self.nativeHighlightNextSelectionArmed,
          error: windowFilterError
        });
        return;
      }
      if (documentController) self.lastDocumentController = documentController;
      if (text && text.length) {
        self.lastSelectionText = String(text);
        if (self.panel && self.panel.view && self.panel.view.window) self.panel.setPromptText(self.lastSelectionText);
        if (self.panel && self.panel.sendContextToWeb) self.panel.sendContextToWeb();
      }
      self.appendSelectionPopupMenuActions(sender, documentController);
      if (self.consumeArmedNativeHighlightSelection(documentController, text)) return;
    },

    togglePanel: function(sender) {
      if (self.panel && self.panel.view && self.panel.view.window) self.hidePanel();
      else self.showPanel();
      Application.sharedInstance().studyController(self.window).refreshAddonCommands();
    },

    sendPanelAction: function(action, prompt) {
      self.callCompanion(action, prompt);
    }
  }, {
    addonDidConnect: function() {},
    addonWillDisconnect: function() {},
    applicationWillEnterForeground: function() {},
    applicationDidEnterBackground: function() {},
    applicationDidReceiveLocalNotification: function(notify) {}
  });

  CodexAssistantAddon.prototype.registerSelectionPopupObserver = function(source, force) {
    if (this.selectionPopupObserverRegistered && !force) return;
    if (this.selectionPopupObserverRegistered && force) {
      try {
        NSNotificationCenter.defaultCenter().removeObserverName(self, 'PopupMenuOnSelection');
        this.postEvent('selectionPopupHighlightObserverRebinding', {
          source: safeString(source),
          notificationName: 'PopupMenuOnSelection'
        });
      } catch (rebindErr) {
        this.postEvent('selectionPopupHighlightObserverRebindFailed', {
          source: safeString(source),
          notificationName: 'PopupMenuOnSelection',
          error: safeString(rebindErr)
        });
      }
      this.selectionPopupObserverRegistered = false;
    }
    try {
      NSNotificationCenter.defaultCenter().addObserverSelectorName(self, 'onPopupMenuOnSelection:', 'PopupMenuOnSelection');
      this.selectionPopupObserverRegistered = true;
      this.postEvent('selectionPopupHighlightObserverRegistered', {
        source: safeString(source),
        notificationName: 'PopupMenuOnSelection',
        force: !!force
      });
    } catch (err) {
      this.selectionPopupObserverRegistered = false;
      this.postEvent('selectionPopupHighlightObserverFailed', {
        source: safeString(source),
        notificationName: 'PopupMenuOnSelection',
        error: safeString(err)
      });
    }
  };

  CodexAssistantAddon.prototype.unregisterSelectionPopupObserver = function(source) {
    if (!this.selectionPopupObserverRegistered) return;
    try {
      NSNotificationCenter.defaultCenter().removeObserverName(self, 'PopupMenuOnSelection');
      this.postEvent('selectionPopupHighlightObserverUnregistered', {
        source: safeString(source),
        notificationName: 'PopupMenuOnSelection'
      });
    } catch (err) {
      this.postEvent('selectionPopupHighlightObserverUnregisterFailed', {
        source: safeString(source),
        notificationName: 'PopupMenuOnSelection',
        error: safeString(err)
      });
    }
    this.selectionPopupObserverRegistered = false;
  };

  CodexAssistantAddon.prototype.currentSelectionText = function() {
    var controller = this.getStudyController();
    var nc = controller ? controller.notebookController : null;
    var docResolution = resolveDocumentController(this, controller, nc);
    var text = '';
    try {
      text = selectionTextFromDocumentController(docResolution.controller);
    } catch (err) {
      text = '';
    }
    if (text && docResolution.controller) this.lastDocumentController = docResolution.controller;
    return safeString(text);
  };

  CodexAssistantAddon.prototype.showPanel = function() {
    var controller = Application.sharedInstance().studyController(this.window);
    if (!controller) return;
    if (!this.panel) this.panel = createPanelController(this);
    controller.view.addSubview(this.panel.view);
    this.layoutPanel();
    if (this.lastSelectionText) this.panel.setPromptText(this.lastSelectionText);
    if (this.panel.sendContextToWeb) this.panel.sendContextToWeb();
    this.postEvent('panelShownState', {
      panelKind: this.panel.panelKind || 'unknown',
      isWebPanel: this.panel.panelKind === 'webview',
      hasPromptView: !!this.panel.promptView,
      hasReplyView: !!this.panel.replyView,
      hasPromptLabel: !!this.panel.promptLabel,
      hasReplyLabel: !!this.panel.replyLabel,
      hasChatButton: !!this.panel.chatButton,
      hasFullButton: !!this.panel.fullButton,
      hasCardButton: !!this.panel.cardButton,
      hasMapButton: !!this.panel.mapButton,
      hasHighlightButton: !!this.panel.hlButton,
      hasHealthButton: !!this.panel.healthButton
    });
    this.probeNativeApiCapabilities();
    NSUserDefaults.standardUserDefaults().setObjectForKey(true, 'codex_mn_assistant_panel_on');
    NSTimer.scheduledTimerWithTimeInterval(0.2, false, function() {
      controller.becomeFirstResponder();
    });
  };

  CodexAssistantAddon.prototype.hidePanel = function() {
    if (this.panel && this.panel.view && this.panel.view.window) this.panel.view.removeFromSuperview();
    NSUserDefaults.standardUserDefaults().setObjectForKey(false, 'codex_mn_assistant_panel_on');
  };

  CodexAssistantAddon.prototype.reloadWebPanel = function() {
    var addon = this;
    this.postEvent('webPanelReloadRequested', {
      panelKind: this.panel && this.panel.panelKind ? this.panel.panelKind : 'unknown'
    });
    try {
      this.hidePanel();
      addon.panel = null;
    } catch (err) {
      this.postEvent('webPanelReloadHideFailed', {message: safeString(err)});
    }
    NSTimer.scheduledTimerWithTimeInterval(0.35, false, function() {
      try {
        addon.showPanel();
        addon.postEvent('webPanelReloadFinished', {
          panelKind: addon.panel && addon.panel.panelKind ? addon.panel.panelKind : 'unknown'
        });
      } catch (err2) {
        addon.postEvent('webPanelReloadFailed', {message: safeString(err2)});
      }
    });
  };

  CodexAssistantAddon.prototype.layoutPanel = function() {
    if (!this.panel || !this.panel.view || !this.panel.view.superview) return;
    if (this.panel.isResizingPanel && this.panel.isResizingPanel()) return;
    if (this.panel.isMovingPanel && this.panel.isMovingPanel()) return;
    var bounds = Application.sharedInstance().studyController(this.window).view.bounds;
    var isWebPanel = this.panel.panelKind === 'webview';
    var minimumSize = isWebPanel && this.panel.panelMinimumSize ? this.panel.panelMinimumSize() : {width: 380, height: 500};
    var preferredSize = isWebPanel && this.panel.panelPreferredSize ? this.panel.panelPreferredSize() : {width: 430, height: 560};
    var maxWidth = Math.max(minimumSize.width, bounds.width - 40);
    var maxHeight = Math.max(minimumSize.height, bounds.height - 60);
    var width = isWebPanel ?
      Math.min(maxWidth, Math.max(minimumSize.width, preferredSize.width || 540)) :
      Math.min(430, Math.max(minimumSize.width, bounds.width - 40));
    var height = isWebPanel ?
      Math.min(maxHeight, Math.max(minimumSize.height, preferredSize.height || 680)) :
      Math.min(560, Math.max(minimumSize.height, bounds.height - 60));
    var origin = isWebPanel && this.panel.panelPreferredOrigin ?
      this.panel.panelPreferredOrigin(bounds, width, height) :
      {x: bounds.width - width - 24, y: bounds.height - height - 32};
    this.panel.view.frame = {x: origin.x, y: origin.y, width: width, height: height};
    if (isWebPanel && this.panel.syncPanelFrames) this.panel.syncPanelFrames(width, height);
  };

  CodexAssistantAddon.prototype.getStudyController = function() {
    return Application.sharedInstance().studyController(this.window);
  };

  CodexAssistantAddon.prototype.getSelectedNote = function() {
    var controller = this.getStudyController();
    if (!controller || !controller.notebookController) return null;
    var nc = controller.notebookController;
    var mindmap = nc.mindmapView || nc.mindMapView || nc.noteMindMap;
    if (!mindmap || !mindmap.selViewLst) return null;
    var first = objectAt(mindmap.selViewLst, 0);
    if (!first) return null;
    var note = first.note !== undefined ? first.note : first;
    note = note && note.note !== undefined ? note.note : note;
    return note && note.noteId ? note : null;
  };

  CodexAssistantAddon.prototype.probeNativeApiCapabilities = function() {
    var controller = this.getStudyController();
    var nc = controller ? controller.notebookController : null;
    var foundHighlight = [];
    var foundExport = [];
    var docResolution = resolveDocumentController(this, controller, nc);
    var selectionDocumentController = docResolution.controller;
    var database = null;
    try {
      database = Database.sharedInstance();
    } catch (err2) {
      database = null;
    }
    var app = null;
    try {
      app = Application.sharedInstance();
    } catch (err3) {
      app = null;
    }
    var targets = [
      probeTargetObject('studyController', controller, NativeHighlightMethodCandidates, NativeExportMethodCandidates, foundHighlight, foundExport),
      probeTargetObject('notebookController', nc, NativeHighlightMethodCandidates, NativeExportMethodCandidates, foundHighlight, foundExport)
    ];
    for (var dc = 0; dc < docResolution.candidates.length; dc++) {
      var candidate = docResolution.candidates[dc];
      targets.push(probeTargetObject(candidate.label, candidate.object, NativeHighlightMethodCandidates, NativeExportMethodCandidates, foundHighlight, foundExport));
    }
    targets = targets.concat([
      probeTargetObject('selectedNote', this.getSelectedNote(), NativeHighlightMethodCandidates, NativeExportMethodCandidates, foundHighlight, foundExport),
      probeTargetObject('Database', database, NativeHighlightMethodCandidates, NativeExportMethodCandidates, foundHighlight, foundExport),
      probeTargetObject('Application', app, NativeHighlightMethodCandidates, NativeExportMethodCandidates, foundHighlight, foundExport)
    ]);
    var activeSelectionText = '';
    try {
      activeSelectionText = safeString(valueOf(selectionDocumentController, 'selectionText'));
    } catch (selectionProbeErr) {
      activeSelectionText = '';
    }
    if (!activeSelectionText) activeSelectionText = this.lastSelectionText || '';
    var context = {};
    try {
      context = this.resolveContext('native_api_probe', '');
    } catch (contextErr) {
      context = {};
    }
    var candidateMethods = foundHighlight.concat(foundExport);
    var capabilityMatrix = nativeCapabilityMatrix(targets, foundHighlight, foundExport, activeSelectionText.length, context);
    this.postEvent('nativeApiCapabilities', {
      targetCount: targets.length,
      targets: targets,
      candidateMethods: candidateMethods,
      documentControllerCandidates: docResolution.labels,
      selectedDocumentControllerLabel: docResolution.label,
      hasNativeHighlightCandidate: !!(foundHighlight.length > 0 || capabilityMatrix.nativeHighlightSelection.available),
      hasAnnotatedExportCandidate: foundExport.length > 0,
      activeSelectionLength: activeSelectionText.length,
      canCreateNote: capabilityMatrix.nativeCards.available,
      canGroupUndo: capabilityMatrix.undoGroupedWrites.available,
      canRefreshAfterDBChanged: capabilityMatrix.refreshAfterWrite.available,
      canInstallSelectionPopupMenu: capabilityMatrix.selectionPopupHighlight.available,
      canUpdateMindmapNode: capabilityMatrix.nativeMindmapUpdate.available,
      canMergeMindmapNode: capabilityMatrix.nativeMindmapMerge.available,
      canMoveMindmapNode: capabilityMatrix.nativeMindmapMove.available,
      canDeleteMindmapNode: capabilityMatrix.nativeMindmapDelete.available,
      hasPdfPath: capabilityMatrix.cacheCurrentPdf.ready,
      handlerFeatures: NativeHandlerFeatures,
      capabilityMatrix: capabilityMatrix,
      message: candidateMethods.length ? 'found candidate selectors' : (
        capabilityMatrix.nativeHighlightSelection.available ? 'found unverified documentController highlight attempt path' : 'no candidate selectors found'
      )
    });
  };

  CodexAssistantAddon.prototype.resolveContext = function(action, prompt) {
    var defaults = NSUserDefaults.standardUserDefaults();
    var controller = this.getStudyController();
    var nc = controller ? controller.notebookController : null;
    var topicId = nc && nc.topicId ? safeString(nc.topicId) : safeString(defaults.objectForKey('mindbooks_lasttopicid'));
    var notebookId = nc && nc.notebookId ? safeString(nc.notebookId) : this.currentNotebookId;
    var bookMd5 = safeString(this.currentDocMd5) ||
      md5FromNotebookController(nc) ||
      md5FromDatabaseTopic(topicId) ||
      safeString(defaults.objectForKey('mindbooks_lastbookmd5'));
    var pdfPath = pdfPathFromNotebookController(nc) ||
      pdfPathFromDatabaseTopic(topicId) ||
      safeString(defaults.objectForKey('mindbooks_lastpdfpath')) ||
      safeString(defaults.objectForKey('mindbooks_lastbookpath'));
    var documentTitle = documentTitleFromNotebookController(nc) ||
      documentTitleFromDatabaseTopic(topicId) ||
      safeString(defaults.objectForKey('mindbooks_lastbooktitle')) ||
      safeString(defaults.objectForKey('mindbooks_lastbookname'));
    var selectedNote = this.getSelectedNote();
    var selectedNoteText = '';
    var selectedNoteTitle = '';
    var selectedNoteId = '';
    try {
      if (selectedNote) {
        selectedNoteId = safeString(selectedNote.noteId);
        selectedNoteTitle = safeString(selectedNote.noteTitle);
        if (selectedNote.allNoteText) selectedNoteText = safeString(selectedNote.allNoteText());
      }
    } catch (err) {
      selectedNoteText = '';
    }
    var liveSelectionText = this.currentSelectionText();
    var selectionText = this.lastSelectionText || '';
    if (liveSelectionText) {
      selectionText = liveSelectionText;
      this.lastSelectionText = liveSelectionText;
    } else if (action === 'context') {
      selectionText = '';
      this.lastSelectionText = '';
    }
    return {
      action: action,
      prompt: safeString(prompt),
      selectionText: selectionText,
      selectedNoteId: selectedNoteId,
      selectedNoteTitle: selectedNoteTitle,
      selectedNoteText: selectedNoteText,
      topicid: topicId,
      notebookid: notebookId || topicId,
      docmd5: bookMd5,
      bookmd5: bookMd5,
      pdfPath: pdfPath,
      documentPath: pdfPath,
      documentTitle: documentTitle,
      documentFileName: documentTitle,
      sourceFileName: documentTitle,
      source: 'marginnote4-plugin',
      pluginVersion: PluginVersion
    };
  };

  CodexAssistantAddon.prototype.callCompanion = function(action, prompt, ackIds) {
    if (this.companionBusy) {
      this.postEvent('callCompanionSkippedBusy', {action: safeString(action)});
      return;
    }
    this.companionBusy = true;
    var app = Application.sharedInstance();
    var controller = this.getStudyController();
    var view = controller ? controller.view : this.window;
    if (this.panel) this.panel.setStatus('正在调用本地 Codex Companion...');
    if (this.panel && this.panel.setBusy) this.panel.setBusy(true);
    if (this.panel && this.panel.sendContextToWeb) this.panel.sendContextToWeb();

    var payload = this.resolveContext(action, prompt);
    var request = NSMutableURLRequest.requestWithURL(NSURL.URLWithString(CompanionURL));
    request.setHTTPMethod('POST');
    request.setTimeoutInterval(CompanionActionTimeout);
    request.setAllHTTPHeaderFields({'Content-Type': 'application/json', 'Accept': 'application/json'});
    request.setHTTPBody(NSJSONSerialization.dataWithJSONObjectOptions(payload, 1));

    var addon = this;
    NSURLConnection.sendAsynchronousRequestQueueCompletionHandler(request, NSOperationQueue.mainQueue(), function(response, data, error) {
      if (error) {
        addon.companionBusy = false;
        var detail = companionErrorDescription(error);
        var msg = companionRequestErrorMessage(error, CompanionActionTimeout);
        addon.postEvent('callCompanionRequestFailed', {
          action: safeString(action),
          timeout: CompanionActionTimeout,
          error: detail,
          message: msg
        });
        if (addon.panel) addon.panel.setStatus(msg);
        if (addon.panel && addon.panel.setBusy) addon.panel.setBusy(false);
        if (addon.panel && addon.panel.setReply) addon.panel.setReply(msg);
        app.showHUD(msg, view, 4);
        return;
      }
      var json = parseJSONData(data);
      if (!json) {
        addon.companionBusy = false;
        if (addon.panel) addon.panel.setStatus(previewData(data) || 'Companion 返回为空');
        if (addon.panel && addon.panel.setBusy) addon.panel.setBusy(false);
        return;
      }
      addon.handleCompanionResponse(json, action);
      if (ackIds && ackIds.length) addon.ackCommands(ackIds);
      addon.companionBusy = false;
    });
  };

  CodexAssistantAddon.prototype.postEvent = function(name, extra) {
    var payload;
    try {
      payload = this.resolveContext('event', '');
    } catch (err) {
      payload = {action: 'event', source: 'marginnote4-plugin', pluginVersion: PluginVersion};
    }
    payload.event = safeString(name);
    payload.extra = extra || {};
    postJSON('http://127.0.0.1:48761/marginnote/event', payload, 5);
  };

  CodexAssistantAddon.prototype.uploadPdfToCompanion = function(pdfPath, pdfPathCandidates) {
    var controller = this.getStudyController();
    var view = controller ? controller.view : this.window;
    var ctx = this.resolveContext('cache_pdf_from_marginnote', '');
    var candidates = [];
    function addCandidate(path) {
      path = safeString(path);
      if (!path) return;
      for (var i = 0; i < candidates.length; i++) {
        if (candidates[i] === path) return;
      }
      candidates.push(path);
    }
    addCandidate(pdfPath);
    var extraPaths = toArray(pdfPathCandidates);
    for (var p = 0; p < extraPaths.length; p++) addCandidate(extraPaths[p]);
    addCandidate(ctx.pdfPath);
    addCandidate(ctx.documentPath);
    if (!candidates.length) {
      var missingPath = '当前文档没有可缓存的 PDF 路径。请先打开 PDF 并刷新上下文。';
      if (this.panel) this.panel.setStatus(missingPath);
      Application.sharedInstance().showHUD(missingPath, view, 3);
      this.postEvent('pdfCacheUploadFailed', {reason: 'missing-path'});
      return;
    }
    try {
      var pdfPathValue = '';
      var data = null;
      var length = 0;
      for (var c = 0; c < candidates.length; c++) {
        var candidate = candidates[c];
        this.postEvent('pdfCacheUploadStarted', {path: candidate, candidateIndex: c});
        if (this.panel) this.panel.setStatus('正在读取当前 PDF...');
        try {
          data = NSData.dataWithContentsOfFile(candidate);
        } catch (readErr) {
          this.postEvent('pdfCacheUploadCandidateFailed', {
            reason: 'read-exception',
            path: candidate,
            candidateIndex: c,
            error: safeString(readErr)
          });
          data = null;
        }
        try {
          length = typeof data.length === 'function' ? Number(data.length()) : Number(data.length || 0);
        } catch (lengthErr) {
          length = 0;
        }
        if (data && length) {
          pdfPathValue = candidate;
          break;
        }
        this.postEvent('pdfCacheUploadCandidateFailed', {reason: 'read-empty', path: candidate, candidateIndex: c});
      }
      if (!pdfPathValue) {
        var emptyMessage = 'PDF 读取失败或文件为空：' + candidates.join(' | ');
        if (this.panel) this.panel.setStatus(emptyMessage);
        Application.sharedInstance().showHUD(emptyMessage, view, 3);
        this.postEvent('pdfCacheUploadFailed', {reason: 'read-empty', candidates: candidates});
        return;
      }
      if (length > 80000000) {
        var tooLargeMessage = 'PDF 超过 80MB，暂不自动缓存。';
        if (this.panel) this.panel.setStatus(tooLargeMessage);
        Application.sharedInstance().showHUD(tooLargeMessage, view, 3);
        this.postEvent('pdfCacheUploadFailed', {reason: 'too-large', path: pdfPathValue, size: length});
        return;
      }
      var encoded = '';
      if (typeof data.base64Encoding === 'function') encoded = String(data.base64Encoding());
      else if (typeof data.base64EncodedStringWithOptions === 'function') encoded = String(data.base64EncodedStringWithOptions(0));
      if (!encoded) {
        var encodeMessage = 'PDF 转码失败，无法上传缓存。';
        if (this.panel) this.panel.setStatus(encodeMessage);
        Application.sharedInstance().showHUD(encodeMessage, view, 3);
        this.postEvent('pdfCacheUploadFailed', {reason: 'base64-empty', path: pdfPathValue, size: length});
        return;
      }
      var parts = pdfPathValue.split('/');
      ctx.action = 'cache_pdf_from_marginnote';
      ctx.pdfPath = pdfPathValue;
      ctx.documentPath = pdfPathValue;
      ctx.fileName = parts.length ? parts[parts.length - 1] : 'document.pdf';
      ctx.pdfBase64 = encoded;
      if (this.panel) this.panel.setStatus('正在上传当前 PDF 缓存...');
      var addon = this;
      postJSON(CompanionURL, ctx, 30, function(response, responseData, error) {
        if (!isNil(error)) {
          var failMessage = companionRequestErrorMessage(error, 30);
          if (addon.panel) addon.panel.setStatus(failMessage);
          Application.sharedInstance().showHUD(failMessage, view, 4);
          addon.postEvent('pdfCacheUploadFailed', {
            reason: 'request-failed',
            path: pdfPathValue,
            size: length,
            error: companionErrorDescription(error)
          });
          return;
        }
        var json = parseJSONData(responseData);
        var ok = json ? valueOf(json, 'ok') !== false : false;
        var message = json ? safeString(valueOf(json, 'reply') || valueOf(json, 'message')) : 'PDF 缓存已提交。';
        if (!message) message = ok ? 'PDF 缓存完成。' : 'PDF 缓存请求未返回有效结果。';
        if (addon.panel) addon.panel.setStatus(message);
        Application.sharedInstance().showHUD(message, view, ok ? 3 : 4);
        addon.postEvent(ok ? 'pdfCacheUploadPosted' : 'pdfCacheUploadFailed', {
          reason: ok ? 'posted' : 'response-not-ok',
          path: pdfPathValue,
          size: length,
          message: message
        });
      });
    } catch (err) {
      var errText = 'PDF 缓存失败：' + safeString(err);
      if (this.panel) this.panel.setStatus(errText);
      Application.sharedInstance().showHUD(errText, view, 4);
      this.postEvent('pdfCacheUploadFailed', {reason: 'exception', candidates: candidates, error: safeString(err)});
    }
  };

  CodexAssistantAddon.prototype.appendSelectionPopupMenuActions = function(sender, documentController) {
    var selectionText = '';
    try {
      selectionText = selectionTextFromDocumentController(documentController);
    } catch (selectionErr) {
      selectionText = this.lastSelectionText || '';
    }
    if (!selectionText) {
      this.postEvent('selectionPopupHighlightMenuSkipped', {
        reason: 'missing-selection-text',
        hasSender: !!sender,
        hasDocumentController: !!documentController,
        hasLastSelectionText: !!this.lastSelectionText
      });
      return;
    }
    try {
      if (documentController) this.lastDocumentController = documentController;
      var currentMenu = PopupMenu.currentMenu();
      if (!currentMenu) {
        this.postEvent('selectionPopupHighlightMenuSkipped', {reason: 'missing-popup-menu', selectionLength: selectionText.length});
        return;
      }
      var items = toArray(valueOf(currentMenu, 'items'));
      for (var i = 0; i < items.length; i++) {
        if (safeString(valueOf(items[i], 'title')) === 'Codex 高亮选区') {
          this.postEvent('selectionPopupHighlightMenuInstalled', {alreadyInstalled: true, selectionLength: selectionText.length});
          return;
        }
      }
      var item = this.createSelectionPopupHighlightItem();
      if (!item) {
        this.postEvent('selectionPopupHighlightMenuFailed', {reason: 'item-create-failed', selectionLength: selectionText.length});
        return;
      }
      items.push(item);
      currentMenu.items = items;
      if (typeof currentMenu.updateWithTargetRect === 'function') {
        try {
          currentMenu.updateWithTargetRect(currentMenu.targetWinRect);
        } catch (updateErr) {}
      }
      this.postEvent('selectionPopupHighlightMenuInstalled', {alreadyInstalled: false, selectionLength: selectionText.length});
    } catch (err) {
      this.postEvent('selectionPopupHighlightMenuFailed', {reason: 'exception', error: safeString(err), selectionLength: selectionText.length});
    }
  };

  CodexAssistantAddon.prototype.createSelectionPopupHighlightItem = function() {
    var selector = 'highlightCurrentSelectionFromMenu:';
    try {
      if (PopupMenuItem && typeof PopupMenuItem.itemWithTitleTargetAction === 'function') {
        return PopupMenuItem.itemWithTitleTargetAction('Codex 高亮选区', this, selector);
      }
    } catch (err1) {}
    try {
      if (PopupMenuItem && typeof PopupMenuItem.itemWithTitleAction === 'function') {
        return PopupMenuItem.itemWithTitleAction('Codex 高亮选区', selector);
      }
    } catch (err2) {}
    try {
      if (PopupMenuItem && PopupMenuItem.alloc) {
        var item = PopupMenuItem.alloc();
        if (item && typeof item.initWithTitleTargetAction === 'function') {
          return item.initWithTitleTargetAction('Codex 高亮选区', this, selector);
        }
        if (item && typeof item.initWithTitleAction === 'function') {
          return item.initWithTitleAction('Codex 高亮选区', selector);
        }
      }
    } catch (err3) {}
    try {
      if (typeof UIMenuItem !== 'undefined' && UIMenuItem.alloc) {
        return UIMenuItem.alloc().initWithTitleEvent('Codex 高亮选区', selector);
      }
    } catch (err4) {}
    return null;
  };

  CodexAssistantAddon.prototype.highlightCurrentSelectionFromMenu = function(sender) {
    this.postEvent('selectionPopupHighlightMenuAction', {});
    this.highlightCurrentSelection({
      nativeAction: 'highlight_current_selection',
      selectionText: this.lastSelectionText || '',
      source: 'selection-popup-menu',
      allowCachedSelectionText: true
    });
  };

  CodexAssistantAddon.prototype.startNativeHighlightSelectionPoll = function() {
    this.stopNativeHighlightSelectionPoll();
    var addon = this;
    this.nativeHighlightNextSelectionPollStartedAt = new Date().getTime();
    this.postEvent('nativeHighlightNextSelectionPollStarted', {
      reason: this.nativeHighlightNextSelectionReason || '',
      timeoutSeconds: 90,
      intervalSeconds: 0.75
    });
    this.nativeHighlightNextSelectionPollTimer = NSTimer.scheduledTimerWithTimeInterval(0.75, true, function(timer) {
      if (!addon.nativeHighlightNextSelectionArmed) {
        addon.stopNativeHighlightSelectionPoll();
        return;
      }
      var elapsedMs = new Date().getTime() - (addon.nativeHighlightNextSelectionPollStartedAt || 0);
      if (elapsedMs > 90000) {
        addon.nativeHighlightNextSelectionArmed = false;
        addon.stopNativeHighlightSelectionPoll();
        addon.postEvent('nativeHighlightNextSelectionPollExpired', {
          reason: addon.nativeHighlightNextSelectionReason || '',
          elapsedSeconds: Math.round(elapsedMs / 1000)
        });
        addon.nativeHighlightNextSelectionReason = '';
        addon.nativeHighlightNextSelectionText = '';
        return;
      }
      var controller = addon.getStudyController();
      var nc = controller ? controller.notebookController : null;
      var docResolution = resolveDocumentController(addon, controller, nc);
      var docController = docResolution.controller;
      var text = selectionTextFromDocumentController(docController);
      if (!text) return;
      addon.postEvent('nativeHighlightNextSelectionPollObserved', {
        selectionLength: text.length,
        selectedDocumentControllerLabel: docResolution.label,
        elapsedSeconds: Math.round(elapsedMs / 1000)
      });
      addon.consumeArmedNativeHighlightSelection(docController, text);
    });
  };

  CodexAssistantAddon.prototype.stopNativeHighlightSelectionPoll = function() {
    if (this.nativeHighlightNextSelectionPollTimer) {
      try {
        this.nativeHighlightNextSelectionPollTimer.invalidate();
      } catch (err) {}
      this.nativeHighlightNextSelectionPollTimer = null;
    }
  };

  CodexAssistantAddon.prototype.armNativeHighlightNextSelection = function(reason, requestedText) {
    var controller = this.getStudyController();
    var view = controller ? controller.view : this.window;
    var message = '已开启下一次 PDF 选区自动高亮。请回到原文中重新选中一小段文字。';
    this.nativeHighlightNextSelectionArmed = true;
    this.nativeHighlightNextSelectionReason = safeString(reason);
    this.nativeHighlightNextSelectionText = safeString(requestedText);
    if (this.panel) this.panel.setStatus(message);
    Application.sharedInstance().showHUD(message, view, 4);
    this.postEvent('nativeHighlightNextSelectionArmed', {
      reason: safeString(reason),
      requestedSelectionLength: safeString(requestedText).length
    });
    this.startNativeHighlightSelectionPoll();
  };

  CodexAssistantAddon.prototype.consumeArmedNativeHighlightSelection = function(documentController, selectionText) {
    if (!this.nativeHighlightNextSelectionArmed) return false;
    var text = safeString(selectionText || this.lastSelectionText || this.nativeHighlightNextSelectionText || '');
    this.stopNativeHighlightSelectionPoll();
    this.nativeHighlightNextSelectionArmed = false;
    if (documentController) this.lastDocumentController = documentController;
    this.postEvent('nativeHighlightNextSelectionConsumed', {
      reason: this.nativeHighlightNextSelectionReason || '',
      selectionLength: text.length
    });
    this.highlightCurrentSelection({
      nativeAction: 'highlight_current_selection',
      selectionText: text,
      source: 'armed-next-selection',
      allowCachedSelectionText: true
    });
    this.nativeHighlightNextSelectionReason = '';
    this.nativeHighlightNextSelectionText = '';
    return true;
  };

  CodexAssistantAddon.prototype.highlightCurrentSelection = function(command) {
    var controller = this.getStudyController();
    var view = controller ? controller.view : this.window;
    var nc = controller ? controller.notebookController : null;
    var docResolution = resolveDocumentController(this, controller, nc);
    var docController = docResolution.controller;
    var requestedText = safeString(valueOf(command, 'selectionText'));
    var selectionText = '';
    try {
      selectionText = selectionTextFromDocumentController(docController);
    } catch (selectionErr) {
      selectionText = '';
    }
    var allowCachedSelectionText = !!valueOf(command, 'allowCachedSelectionText');
      var preferNextSelection = !!valueOf(command, 'preferNextSelection');
      var shouldArmNextSelection = !!valueOf(command, 'armIfMissingSelection') ||
        safeString(valueOf(command, 'nativeAction')) === 'highlight_current_selection' ||
        safeString(valueOf(command, 'source')) === 'native-queue';
    var usedCachedSelectionText = false;
    var selectionTextSource = selectionText ? 'document-controller' : '';
    if (!selectionText && allowCachedSelectionText && requestedText) {
      selectionText = requestedText;
      usedCachedSelectionText = true;
      selectionTextSource = 'cached-selection';
    }
      if (preferNextSelection && shouldArmNextSelection && !selectionText) {
        this.armNativeHighlightNextSelection('prefer-next-selection', requestedText);
        return;
      }
      if (!docController) {
      if (shouldArmNextSelection) {
        this.armNativeHighlightNextSelection('missing-document-controller', requestedText);
        return;
      }
      var noController = '没有拿到当前 PDF 选区控制器。请先在 PDF 中选中文本，再执行原生高亮。';
      if (this.panel) this.panel.setStatus(noController);
      Application.sharedInstance().showHUD(noController, view, 3);
      this.postEvent('nativeHighlightSelectionFailed', {
        reason: 'missing-document-controller',
        requestedSelectionLength: requestedText.length,
        candidateLabels: docResolution.labels,
        candidateCount: docResolution.labels.length,
        selectedDocumentControllerLabel: docResolution.label
      });
      return;
    }
    if (!selectionText) {
      if (shouldArmNextSelection) {
        this.armNativeHighlightNextSelection('missing-selection', requestedText);
        return;
      }
      var noSelection = '当前没有有效 PDF 选区。请先选中文本，再执行原生高亮。';
      if (this.panel) this.panel.setStatus(noSelection);
      Application.sharedInstance().showHUD(noSelection, view, 3);
      this.postEvent('nativeHighlightSelectionFailed', {
        reason: 'missing-selection',
        requestedSelectionLength: requestedText.length,
        usedCachedSelectionText: usedCachedSelectionText,
        selectionTextSource: selectionTextSource,
        candidateLabels: docResolution.labels,
        candidateCount: docResolution.labels.length,
        selectedDocumentControllerLabel: docResolution.label
      });
      return;
    }
    var highlightResult = invokeHighlightFromSelection(docController);
    if (highlightResult.ok) {
      var highlight = highlightResult.highlight;
      var message = '已调用 MarginNote 原生 highlightFromSelection 创建当前选区高亮。';
      if (this.panel) this.panel.setStatus(message);
      Application.sharedInstance().showHUD(message, view, 3);
      try {
        var ctx = this.resolveContext('native_highlight', '');
        if (ctx.topicid) Application.sharedInstance().refreshAfterDBChanged(ctx.topicid);
      } catch (refreshErr) {}
      this.postEvent('nativeHighlightSelectionPosted', {
        selectionLength: selectionText.length,
        requestedSelectionLength: requestedText.length,
        highlightReturned: !!highlight,
        usedCachedSelectionText: usedCachedSelectionText,
        selectionTextSource: selectionTextSource,
        selectorVerified: !!highlightResult.selectorVerified,
        attemptedUnverifiedSelector: !!highlightResult.attemptedUnverifiedSelector,
        selectedDocumentControllerLabel: docResolution.label
      });
    } else {
      var errText = '原生高亮当前选区失败：' + safeString(highlightResult.error);
      if (this.panel) this.panel.setStatus(errText);
      Application.sharedInstance().showHUD(errText, view, 4);
      this.postEvent('nativeHighlightSelectionFailed', {
        reason: 'exception',
        selectionLength: selectionText.length,
        requestedSelectionLength: requestedText.length,
        usedCachedSelectionText: usedCachedSelectionText,
        selectionTextSource: selectionTextSource,
        selectorVerified: !!highlightResult.selectorVerified,
        attemptedUnverifiedSelector: !!highlightResult.attemptedUnverifiedSelector,
        candidateLabels: docResolution.labels,
        candidateCount: docResolution.labels.length,
        selectedDocumentControllerLabel: docResolution.label,
        error: safeString(highlightResult.error)
      });
    }
  };

  CodexAssistantAddon.prototype.startCommandPolling = function() {
    this.stopCommandPolling();
    this.pollDebugSent = false;
    var addon = this;
    this.commandTimer = NSTimer.scheduledTimerWithTimeInterval(2.0, true, function(timer) {
      addon.pollCommands();
    });
    this.pollCommands();
  };

  CodexAssistantAddon.prototype.stopCommandPolling = function() {
    if (this.commandTimer) {
      this.commandTimer.invalidate();
      this.commandTimer = null;
    }
  };

  CodexAssistantAddon.prototype.pollCommands = function() {
    if (this.companionBusy) return;
    var ctx = this.resolveContext('poll', '');
    var topic = encodeURIComponent(ctx.topicid || ctx.notebookid || '');
    var book = encodeURIComponent(ctx.bookmd5 || ctx.docmd5 || '');
    if (!topic) return;
    var url = 'http://127.0.0.1:48761/marginnote/poll?topicid=' + topic + '&bookmd5=' + book;
    var addon = this;
    try {
      var data = NSData.dataWithContentsOfURL(NSURL.URLWithString(url));
      var raw = rawStringFromData(data);
      if (!addon.pollDebugSent) {
        addon.pollDebugSent = true;
        addon.postEvent('pollCallback', {
          mode: 'sync',
          hasData: data ? true : false,
          rawLength: raw ? raw.length : 0,
          rawPrefix: raw ? raw.substring(0, 160) : ''
        });
      }
      if (raw && raw.indexOf('"pending": 0') < 0 && raw.indexOf('"pending":0') < 0) {
        addon.postEvent('pollRawCommand', {length: raw.length, prefix: raw.substring(0, 220)});
      }
      var json = parseJSONData(data);
      if (!json) {
        addon.postEvent('pollParseFailed', {hasData: data ? true : false, rawLength: raw ? raw.length : 0});
        return;
      }
      var singleCommand = valueOf(json, 'command');
      if (singleCommand) {
        var queueIdSingle = valueOf(singleCommand, '_queue_id');
        var rawActionSingle = valueOf(singleCommand, 'rawAction');
        if (rawActionSingle) {
          addon.postEvent('rawQueueDeferredToWebView', {
            action: safeString(rawActionSingle),
            mode: 'single',
            queueId: queueIdSingle ? String(queueIdSingle) : ''
          });
          return;
        }
        if (addon.handleNativeQueueCommand(singleCommand)) {
          if (queueIdSingle) addon.ackCommands([String(queueIdSingle)]);
          return;
        }
        addon.postEvent('commandsReceived', {count: 1, mode: 'single-sync'});
        var handledSingle = addon.handleCompanionResponse(singleCommand, 'queued');
        if (queueIdSingle && handledSingle !== false) addon.ackCommands([String(queueIdSingle)]);
        return;
      }
      var commandList = valueOf(json, 'commands');
      var pendingValue = valueOf(json, 'pending');
      if (!commandList) {
        if (pendingValue && Number(pendingValue) > 0) addon.postEvent('pollMissingCommands', {pending: Number(pendingValue)});
        return;
      }
      var commands = toArray(commandList);
      if (commands.length) addon.postEvent('commandsReceived', {count: commands.length, mode: 'array-sync'});
      var ackIds = [];
      for (var i = 0; i < commands.length; i++) {
        var queueId = valueOf(commands[i], '_queue_id');
        var rawAction = valueOf(commands[i], 'rawAction');
        if (rawAction) {
          addon.postEvent('rawQueueDeferredToWebView', {
            action: safeString(rawAction),
            mode: 'array',
            queueId: queueId ? String(queueId) : ''
          });
          break;
        }
        if (addon.handleNativeQueueCommand(commands[i])) {
          if (queueId) ackIds.push(String(queueId));
          continue;
        }
        var handled = addon.handleCompanionResponse(commands[i], 'queued');
        if (queueId && handled !== false) ackIds.push(String(queueId));
      }
      if (ackIds.length) addon.ackCommands(ackIds);
    } catch (err) {
      try { addon.postEvent('pollException', {message: safeString(err)}); } catch (ignored) {}
    }
  };

  CodexAssistantAddon.prototype.serializeMindmapNode = function(note, depth, maxDepth, stats) {
    if (!note || depth > maxDepth) return null;
    stats = stats || {nodes: 0, truncated: 0};
    stats.nodes += 1;
    var title = safeString(valueOf(note, 'noteTitle') || valueOf(note, 'title') || valueOf(note, 'name') || noteIdentifier(note) || '未命名节点');
    var body = '';
    try {
      body = allTextFromNote(note);
    } catch (bodyErr) {
      body = '';
    }
    var node = {
      noteId: noteIdentifier(note),
      title: title,
      body: body ? String(body).substring(0, 1200) : '',
      children: []
    };
    var children = valueOf(note, 'childNotes') || valueOf(note, 'children') || valueOf(note, 'notes');
    var total = countOf(children);
    if (depth >= maxDepth && total > 0) {
      stats.truncated += total;
      return node;
    }
    for (var i = 0; i < total && i < 80; i++) {
      var child = objectAt(children, i);
      var childTree = this.serializeMindmapNode(child, depth + 1, maxDepth, stats);
      if (childTree) node.children.push(childTree);
    }
    if (total > 80) stats.truncated += total - 80;
    return node;
  };

  CodexAssistantAddon.prototype.readMindmapTree = function(command) {
    var ctx = this.resolveNotebookAndDocument();
    var requestedNoteId = safeString(valueOf(command, 'selectedNoteId') || '');
    var requestedTitle = safeString(valueOf(command, 'selectedNoteTitle') || '');
    var note = null;
    if (ctx && requestedNoteId) note = findNoteById(ctx.notebook, requestedNoteId);
    if (!note) note = this.getSelectedNote();
    var noteId = noteIdentifier(note);
    this.postEvent('mindmapTreeReadRequested', {
      nativeAction: 'read_mindmap_tree',
      requestedNoteId: requestedNoteId,
      requestedTitle: requestedTitle,
      resolvedNoteId: noteId,
      source: safeString(valueOf(command, 'source') || 'native-queue')
    });
    if (!ctx || !note) {
      this.postEvent('mindmapTreeReadUnavailable', {
        nativeAction: 'read_mindmap_tree',
        reason: ctx ? 'missing-selected-note' : (this.lastResolveError || 'missing-context'),
        requestedNoteId: requestedNoteId,
        requestedTitle: requestedTitle
      });
      return;
    }
    var stats = {nodes: 0, truncated: 0};
    var tree = this.serializeMindmapNode(note, 0, 4, stats);
    this.postEvent('mindmapTreeReadFinished', {
      nativeAction: 'read_mindmap_tree',
      selectedNoteId: noteId,
      selectedNoteTitle: safeString(valueOf(note, 'noteTitle') || requestedTitle),
      nodeCount: stats.nodes,
      truncatedCount: stats.truncated,
      currentMindmap: tree
    });
  };

  CodexAssistantAddon.prototype.serializeMnObjectForRegistry = function(note, parentNoteId, nodePath, documentTitle) {
    if (!note) return null;
    var noteId = noteIdentifier(note);
    if (!noteId) return null;
    var title = safeString(valueOf(note, 'noteTitle') || valueOf(note, 'title') || valueOf(note, 'name') || noteId);
    var body = '';
    try {
      body = allTextFromNote(note);
    } catch (bodyErr) {
      body = '';
    }
    return {
      objectId: 'mnobj:note:' + noteId,
      kind: 'mindmap_node',
      title: title || noteId,
      summary: body ? body.substring(0, 240) : '',
      evidenceType: 'native_object_scan',
      sourceRef: {
        noteId: noteId,
        parentNoteId: safeString(parentNoteId),
        nodePath: safeString(nodePath),
        documentTitle: safeString(documentTitle)
      }
    };
  };

  CodexAssistantAddon.prototype.scanMnObjects = function(command) {
    var ctx = this.resolveNotebookAndDocument();
    var limit = parseInt(valueOf(command, 'limit') || 200, 10);
    if (!limit || limit < 1) limit = 200;
    if (limit > 1000) limit = 1000;
    this.postEvent('mnObjectRegistryScanRequested', {
      nativeAction: 'scan_mn_objects',
      limit: limit,
      source: safeString(valueOf(command, 'source') || 'native-queue')
    });
    if (!ctx) {
      this.postEvent('mnObjectRegistryScanFinished', {
        nativeAction: 'scan_mn_objects',
        ok: false,
        reason: this.lastResolveError || 'missing-context',
        objects: [],
        objectCount: 0,
        truncatedCount: 0
      });
      return;
    }
    var objects = [];
    var truncated = 0;
    var documentTitle = documentTitleFromDocumentObject(ctx.document) || documentTitleFromNotebookObject(ctx.notebook);
    var addon = this;

    function scanList(notes, parentNoteId, path, depth) {
      if (!notes || depth > 24) return;
      var total = countOf(notes);
      for (var i = 0; i < total; i++) {
        var note = objectAt(notes, i);
        if (!note) continue;
        var notePath = path ? (path + '.' + (i + 1)) : String(i + 1);
        if (objects.length >= limit) {
          truncated += total - i;
          break;
        }
        var objectRef = addon.serializeMnObjectForRegistry(note, parentNoteId, notePath, documentTitle);
        if (objectRef) objects.push(objectRef);
        var noteId = noteIdentifier(note);
        var children = valueOf(note, 'childNotes') || valueOf(note, 'children') || valueOf(note, 'notes');
        if (children && children !== notes) scanList(children, noteId, notePath, depth + 1);
      }
    }

    scanList(ctx.notebook.notes, '', '', 0);
    this.postEvent('mnObjectRegistryScanFinished', {
      nativeAction: 'scan_mn_objects',
      ok: true,
      scanId: String(new Date().getTime()),
      evidenceType: 'native_object_scan',
      objectCount: objects.length,
      truncatedCount: truncated,
      objects: objects,
      topicid: ctx.topicId
    });
  };

  CodexAssistantAddon.prototype.applyMindmapDiffOperations = function(command) {
    var ctx = this.resolveNotebookAndDocument();
    var plan = valueOf(command, 'mindmapDiffOperationPlan') || {};
    var operations = toArray(valueOf(plan, 'operations'));
    var transactionId = safeString(valueOf(command, 'transactionId') || valueOf(plan, 'transactionId') || '');
    var draftId = safeString(valueOf(command, 'draftId') || valueOf(command, 'id') || '');
    var selected = this.getSelectedNote();
    var createdByPath = {};
    var created = [];
    var failed = [];
    var addon = this;
    var previousActiveAiEditTransaction = this.activeAiEditTransaction || null;
    var mindmapDiffTransaction = transactionId ? {
      transactionId: transactionId,
      draftId: draftId,
      topicid: '',
      objectRef: aiEditObjectRefFromDraft(command),
      createdNotes: [],
      createdNoteIds: [],
      createdNoteIdsMap: {},
      startedAt: String(new Date().getTime())
    } : null;
    if (mindmapDiffTransaction) this.activeAiEditTransaction = mindmapDiffTransaction;

    this.postEvent('mindmapDiffApplyRequested', {
      nativeAction: 'apply_mindmap_diff_operations',
      transactionId: transactionId,
      draftId: draftId,
      operationCount: operations.length,
      source: safeString(valueOf(command, 'source') || 'native-queue')
    });

    if (!ctx) {
      this.activeAiEditTransaction = previousActiveAiEditTransaction;
      this.postEvent('mindmapDiffApplyFinished', {
        nativeAction: 'apply_mindmap_diff_operations',
        transactionId: transactionId,
        draftId: draftId,
        appliedCount: 0,
        failedCount: operations.length,
        reason: this.lastResolveError || 'missing-context'
      });
      return;
    }

    function parentPathOf(path) {
      path = safeString(path);
      var index = path.lastIndexOf('.');
      return index > 0 ? path.substring(0, index) : '';
    }

    function createOperationNode(operation) {
      var title = safeString(valueOf(operation, 'title') || 'Codex 节点');
      var proposedPath = safeString(valueOf(operation, 'proposedPath') || '');
      var parent = createdByPath[parentPathOf(proposedPath)] || selected;
      var note = Note.createWithTitleNotebookDocument(title, ctx.notebook, ctx.document);
      if (!note) return null;
      if (parent) parent.addChild(note);
      appendOperationComment(note, operation, 'create');
      if (proposedPath) createdByPath[proposedPath] = note;
      created.push(note);
      addon.recordAiEditCreatedNote(note);
      return note;
    }

    function operationBody(operation) {
      return safeString(valueOf(operation, 'bodyPreview') || valueOf(operation, 'shortBody') || valueOf(operation, 'body') || '');
    }

    function appendOperationComment(note, operation, label) {
      if (!note || !note.appendMarkdownComment) return false;
      var body = operationBody(operation);
      var proposedRef = valueOf(operation, 'proposedRef') || {};
      var codexId = safeString(valueOf(proposedRef, 'codexId') || valueOf(operation, 'codexId') || '');
      var marker = metadataComment(codexId);
      var sourceText = sourceTextForOperation(operation);
      var chunks = [];
      if (marker) chunks.push(marker);
      if (label) chunks.push('**Codex ' + label + '**');
      if (body) chunks.push(body);
      if (sourceText) chunks.push('Source: ' + sourceText);
      if (!chunks.length) return false;
      note.appendMarkdownComment(chunks.join('\n\n'));
      return true;
    }

    function resolveOperationCurrentNote(operation) {
      var currentRef = valueOf(operation, 'currentRef') || {};
      var noteId = safeString(
        valueOf(currentRef, 'noteId') ||
        valueOf(operation, 'currentNoteId') ||
        valueOf(operation, 'noteId') ||
        ''
      );
      if (!noteId) return null;
      return findNoteById(ctx.notebook, noteId);
    }

    function resolveOperationTargetParent(operation) {
      var targetParentRef = valueOf(operation, 'targetParentRef') || valueOf(operation, 'parentRef') || {};
      var parentNoteId = safeString(
        valueOf(targetParentRef, 'noteId') ||
        valueOf(operation, 'targetParentNoteId') ||
        valueOf(operation, 'parentNoteId') ||
        ''
      );
      if (parentNoteId) return findNoteById(ctx.notebook, parentNoteId);
      var proposedPath = safeString(valueOf(operation, 'proposedPath') || '');
      var parentFromCreated = createdByPath[parentPathOf(proposedPath)];
      if (parentFromCreated) return parentFromCreated;
      return selected;
    }

    function setOperationNodeTitle(note, title) {
      title = safeString(title);
      if (!note || !title) return false;
      try {
        note.noteTitle = title;
        return true;
      } catch (err) {}
      try {
        note.title = title;
        return true;
      } catch (err2) {}
      try {
        if (note.setTitle) {
          note.setTitle(title);
          return true;
        }
      } catch (err3) {}
      try {
        if (note.setNoteTitle) {
          note.setNoteTitle(title);
          return true;
        }
      } catch (err4) {}
      return false;
    }

    function updateOperationNode(operation) {
      var note = resolveOperationCurrentNote(operation);
      if (!note) return {ok: false, reason: 'missing-current-note'};
      var title = safeString(valueOf(operation, 'title') || '');
      var titleUpdated = title ? setOperationNodeTitle(note, title) : false;
      var commentAdded = appendOperationComment(note, operation, 'update');
      return {
        ok: titleUpdated || commentAdded,
        reason: titleUpdated || commentAdded ? '' : 'nothing-to-update',
        noteId: noteIdentifier(note),
        method: titleUpdated ? 'note-title-comment' : 'note-comment'
      };
    }

    function mergeOperationNode(operation) {
      var note = resolveOperationCurrentNote(operation);
      if (!note) return {ok: false, reason: 'missing-current-note'};
      var commentAdded = appendOperationComment(note, operation, 'merge');
      return {
        ok: commentAdded,
        reason: commentAdded ? '' : 'nothing-to-merge',
        noteId: noteIdentifier(note),
        method: 'merge-comment'
      };
    }

    function moveOperationNode(operation) {
      var note = resolveOperationCurrentNote(operation);
      if (!note) return {ok: false, reason: 'missing-current-note'};
      var parent = resolveOperationTargetParent(operation);
      if (!parent) return {ok: false, reason: 'missing-target-parent', noteId: noteIdentifier(note)};
      var noteId = noteIdentifier(note);
      var parentId = noteIdentifier(parent);
      if (noteId && parentId && noteId === parentId) {
        return {ok: false, reason: 'target-parent-is-current-note', noteId: noteId};
      }
      try {
        parent.addChild(note);
        return {ok: true, noteId: noteId, targetParentNoteId: parentId, method: 'add-child'};
      } catch (err) {
        return {ok: false, reason: 'move-failed:' + safeString(err), noteId: noteId, targetParentNoteId: parentId};
      }
    }

    function recordApplied(operation, result, applied) {
      applied.push({
        opId: safeString(valueOf(operation, 'opId')),
        op: safeString(valueOf(operation, 'op')),
        mutation: safeString(valueOf(operation, 'mutation')),
        noteId: result.noteId || '',
        targetParentNoteId: result.targetParentNoteId || '',
        method: result.method || ''
      });
    }

    function recordFailure(operation, result) {
      failed.push({
        opId: safeString(valueOf(operation, 'opId')),
        op: safeString(valueOf(operation, 'op')),
        mutation: safeString(valueOf(operation, 'mutation')),
        noteId: result && result.noteId ? result.noteId : '',
        targetParentNoteId: result && result.targetParentNoteId ? result.targetParentNoteId : '',
        reason: result && result.reason ? result.reason : 'operation-failed'
      });
    }

    function parentNoteIdFor(noteId) {
      noteId = safeString(noteId);
      if (!noteId || !ctx.notebook) return '';
      function scan(notes, parentId, depth) {
        if (!notes || depth > 24) return '';
        var total = countOf(notes);
        for (var i = 0; i < total; i++) {
          var note = objectAt(notes, i);
          if (!note) continue;
          var currentId = noteIdentifier(note);
          if (currentId === noteId) return parentId || '';
          var children = valueOf(note, 'childNotes') || valueOf(note, 'children') || valueOf(note, 'notes');
          var found = scan(children, currentId, depth + 1);
          if (found) return found;
        }
        return '';
      }
      return scan(ctx.notebook.notes, '', 0);
    }

    function sourceTextForOperation(operation) {
      var source = valueOf(operation, 'source') || {};
      if (typeof source === 'string') return safeString(source);
      return safeString(
        valueOf(source, 'quote') ||
        valueOf(source, 'text') ||
        valueOf(source, 'page') ||
        valueOf(source, 'label') ||
        ''
      );
    }

    function textContainsExpected(actual, expected) {
      actual = safeString(actual);
      expected = safeString(expected);
      if (!expected) return true;
      if (actual.indexOf(expected) >= 0) return true;
      var clipped = expected.length > 120 ? expected.substring(0, 120) : expected;
      return clipped ? actual.indexOf(clipped) >= 0 : true;
    }

    function verifyAppliedMindmapDiffOperation(operation, applied) {
      operation = operation || {};
      applied = applied || {};
      var noteId = safeString(applied.noteId || '');
      var note = noteId ? findNoteById(ctx.notebook, noteId) : null;
      var expectedTitle = safeString(valueOf(operation, 'title') || '');
      var actualTitle = note ? safeString(valueOf(note, 'noteTitle') || valueOf(note, 'title') || valueOf(note, 'name') || '') : '';
      var targetParentRef = valueOf(operation, 'targetParentRef') || valueOf(operation, 'parentRef') || {};
      var expectedParentNoteId = safeString(
        applied.targetParentNoteId ||
        valueOf(targetParentRef, 'noteId') ||
        valueOf(operation, 'targetParentNoteId') ||
        valueOf(operation, 'parentNoteId') ||
        ''
      );
      var actualParentNoteId = note ? parentNoteIdFor(noteId) : '';
      var titleMatches = !expectedTitle || expectedTitle === actualTitle;
      var parentMatches = !expectedParentNoteId || expectedParentNoteId === actualParentNoteId;
      var expectedBody = operationBody(operation);
      var expectedSourceText = sourceTextForOperation(operation);
      var actualCommentText = note ? allTextFromNote(note) : '';
      var bodyMatches = textContainsExpected(actualCommentText, expectedBody);
      var sourceMatches = textContainsExpected(actualCommentText, expectedSourceText);
      var commentMatches = bodyMatches && sourceMatches;
      var ok = !!note && titleMatches && parentMatches && commentMatches;
      return {
        opId: safeString(valueOf(operation, 'opId') || applied.opId || ''),
        op: safeString(valueOf(operation, 'op') || applied.op || ''),
        mutation: safeString(valueOf(operation, 'mutation') || applied.mutation || ''),
        noteId: noteId,
        exists: !!note,
        ok: ok,
        expectedTitle: expectedTitle,
        actualTitle: actualTitle,
        titleMatches: titleMatches,
        expectedParentNoteId: expectedParentNoteId,
        actualParentNoteId: actualParentNoteId,
        parentMatches: parentMatches,
        expectedBody: expectedBody,
        bodyMatches: bodyMatches,
        commentMatches: commentMatches,
        expectedSourceText: expectedSourceText,
        sourceMatches: sourceMatches,
        actualCommentText: actualCommentText ? actualCommentText.substring(0, 1200) : '',
        method: safeString(applied.method || '')
      };
    }

    function buildMindmapDiffApplyVerification(operationsList, appliedList, failedList) {
      var byOpId = {};
      for (var i = 0; i < operationsList.length; i++) {
        var operation = operationsList[i] || {};
        byOpId[safeString(valueOf(operation, 'opId'))] = operation;
      }
      var operationVerification = [];
      var verifiedCount = 0;
      var failedVerificationCount = 0;
      for (var j = 0; j < appliedList.length; j++) {
        var applied = appliedList[j] || {};
        var original = byOpId[safeString(applied.opId)] || {};
        var verified = verifyAppliedMindmapDiffOperation(original, applied);
        operationVerification.push(verified);
        if (verified.ok) verifiedCount += 1;
        else failedVerificationCount += 1;
      }
      failedVerificationCount += failedList.length;
      return {
        schema: 'codex.mn.mindmapDiffApplyVerification.v1',
        status: failedVerificationCount ? 'block' : 'pass',
        summary: '脑图 Diff 验证：通过 ' + verifiedCount + '，失败 ' + failedVerificationCount + '。',
        operationCount: operationsList.length,
        appliedCount: appliedList.length,
        failedCount: failedList.length,
        verifiedCount: verifiedCount,
        failedVerificationCount: failedVerificationCount,
        operationVerification: operationVerification,
        failures: failedList
      };
    }

    var appliedOperations = [];
    UndoManager.sharedInstance().undoGrouping('Codex Apply Mindmap Diff', ctx.topicId, function() {
      for (var i = 0; i < operations.length; i++) {
        var operation = operations[i];
        var op = safeString(valueOf(operation, 'op'));
        var mutation = safeString(valueOf(operation, 'mutation'));
        if (op === 'create_mindmap_node' || mutation === 'create') {
          var note = createOperationNode(operation);
          if (!note) {
            recordFailure(operation, {reason: 'note-create-failed'});
          } else {
            recordApplied(operation, {
              noteId: noteIdentifier(note),
              method: 'create-note'
            }, appliedOperations);
          }
          continue;
        }
        var result = null;
        if (op === 'update_mindmap_node' || mutation === 'update') result = updateOperationNode(operation);
        else if (op === 'merge_mindmap_node' || mutation === 'merge') result = mergeOperationNode(operation);
        else if (op === 'move_mindmap_node' || mutation === 'move') result = moveOperationNode(operation);
        else if (op === 'suggest_delete_mindmap_node' || mutation === 'delete_suggest' || mutation === 'delete') {
          result = {ok: false, reason: 'delete-suggestion-not-applied'};
        } else {
          result = {ok: false, reason: 'unknown-operation'};
        }
        if (result && result.ok) recordApplied(operation, result, appliedOperations);
        else recordFailure(operation, result);
      }
    });

    Application.sharedInstance().refreshAfterDBChanged(ctx.topicId);
    var verification = buildMindmapDiffApplyVerification(operations, appliedOperations, failed);
    if (mindmapDiffTransaction) {
      mindmapDiffTransaction.topicid = ctx.topicId;
      if (!mindmapDiffTransaction.createdNoteIds.length) {
        mindmapDiffTransaction.createdNoteIds = created.map(function(note) { return noteIdentifier(note); });
      }
      mindmapDiffTransaction.createdNotes = created;
      for (var createdIndex = 0; createdIndex < mindmapDiffTransaction.createdNoteIds.length; createdIndex++) {
        var createdId = mindmapDiffTransaction.createdNoteIds[createdIndex];
        if (createdId) mindmapDiffTransaction.createdNoteIdsMap[createdId] = true;
      }
      this.aiEditTransactions = this.aiEditTransactions || {};
      this.aiEditTransactions[transactionId] = mindmapDiffTransaction;
      this.activeAiEditTransaction = previousActiveAiEditTransaction;
    }
    this.postEvent('mindmapDiffApplyFinished', {
      nativeAction: 'apply_mindmap_diff_operations',
      transactionId: transactionId,
      draftId: draftId,
      appliedCount: appliedOperations.length,
      failedCount: failed.length,
      createdNoteIds: created.map(function(note) { return noteIdentifier(note); }),
      appliedOperations: appliedOperations,
      failures: failed,
      verification: verification,
      topicid: ctx.topicId
    });
    if (created.length && ctx.controller.focusNoteInMindMapById) {
      var noteId = noteIdentifier(created[0]);
      NSTimer.scheduledTimerWithTimeInterval(0.3, false, function() {
        ctx.controller.focusNoteInMindMapById(noteId);
      });
    }
  };

  CodexAssistantAddon.prototype.handleNativeQueueCommand = function(command) {
    var nativeAction = safeString(valueOf(command, 'nativeAction'));
    if (!nativeAction) return false;
    this.postEvent('nativeQueueCommandReceived', {nativeAction: nativeAction});
    this.postEvent('pdfCacheCommandReceived', {nativeAction: nativeAction});
    if (nativeAction === 'cache_pdf_from_current_document') {
      this.uploadPdfToCompanion(
        safeString(valueOf(command, 'pdfPath') || valueOf(command, 'documentPath') || ''),
        toArray(valueOf(command, 'pdfPathCandidates'))
      );
      return true;
    }
    if (nativeAction === 'highlight_current_selection') {
      var highlightCommand = {
        nativeAction: nativeAction,
        selectionText: safeString(valueOf(command, 'selectionText') || this.lastSelectionText || ''),
        source: safeString(valueOf(command, 'source') || 'native-queue'),
        allowCachedSelectionText: !!valueOf(command, 'allowCachedSelectionText')
      };
      highlightCommand.allowCachedSelectionText = true;
      highlightCommand.armIfMissingSelection = true;
      highlightCommand.preferNextSelection = !!valueOf(command, 'preferNextSelection');
      if (!highlightCommand.selectionText && this.lastSelectionText) highlightCommand.selectionText = this.lastSelectionText;
      this.postEvent('nativeHighlightCommandPrepared', {
        nativeAction: nativeAction,
        source: highlightCommand.source,
        armIfMissingSelection: highlightCommand.armIfMissingSelection,
        preferNextSelection: highlightCommand.preferNextSelection,
        selectionLength: highlightCommand.selectionText.length
      });
      this.highlightCurrentSelection(highlightCommand);
      return true;
    }
    if (nativeAction === 'probe_native_api_capabilities') {
      this.postEvent('nativeApiCapabilityProbeRequested', {
        nativeAction: nativeAction,
        requestedAt: safeString(valueOf(command, 'requested_at'))
      });
      this.probeNativeApiCapabilities();
      return true;
    }
    if (nativeAction === 'reload_web_panel') {
      this.reloadWebPanel();
      return true;
    }
    if (nativeAction === 'write_draft') {
      var draftId = safeString(valueOf(command, 'draftId') || valueOf(command, 'id') || '');
      this.postEvent('nativeDraftWriteCommandPrepared', {
        nativeAction: nativeAction,
        draftId: draftId,
        source: safeString(valueOf(command, 'source') || 'native-queue')
      });
      if (!!valueOf(command, 'aiEditOperation') || valueOf(command, 'aiEdit') === '1') {
        this.writeDraft(draftId, {aiEditOperation: true});
      } else {
        this.writeDraft(draftId);
      }
      return true;
    }
    if (nativeAction === 'read_mindmap_tree') {
      this.readMindmapTree(command);
      return true;
    }
    if (nativeAction === 'scan_mn_objects') {
      this.scanMnObjects(command);
      return true;
    }
    if (nativeAction === 'apply_mindmap_diff_operations') {
      this.applyMindmapDiffOperations(command);
      return true;
    }
    this.postEvent('nativeQueueCommandUnknown', {nativeAction: nativeAction});
    return true;
  };

  CodexAssistantAddon.prototype.ackCommands = function(ids) {
    var ctx = this.resolveContext('ack', '');
    postJSON('http://127.0.0.1:48761/marginnote/ack', {
      topicid: ctx.topicid || ctx.notebookid || '',
      bookmd5: ctx.bookmd5 || ctx.docmd5 || '',
      ids: ids
    }, 5);
    this.postEvent('commandsAcked', {count: ids.length});
  };

  function aiEditObjectRefFromDraft(json) {
    var mnObject = valueOf(json, 'mnObject') || {};
    var sourceRef = valueOf(mnObject, 'sourceRef') || {};
    var objectRef = {
      objectId: safeString(valueOf(mnObject, 'objectId')),
      kind: safeString(valueOf(mnObject, 'kind')),
      title: safeString(valueOf(mnObject, 'title')),
      sourceRef: {
        page: valueOf(sourceRef, 'page'),
        quote: safeString(valueOf(sourceRef, 'quote')),
        documentTitle: safeString(valueOf(sourceRef, 'documentTitle')),
        path: safeString(valueOf(sourceRef, 'path'))
      }
    };
    return objectRef;
  }

  function aiEditObjectRefFromBridgeParams(params) {
    params = params || {};
    return {
      objectId: safeString(valueOf(params, 'mnObjectId')),
      kind: safeString(valueOf(params, 'mnObjectKind')),
      title: safeString(valueOf(params, 'mnObjectTitle')),
      sourceRef: {
        page: valueOf(params, 'mnObjectSourcePage'),
        quote: safeString(valueOf(params, 'mnObjectSourceQuote')),
        documentTitle: safeString(valueOf(params, 'mnObjectSourceDocumentTitle')),
        path: safeString(valueOf(params, 'mnObjectSourcePath'))
      }
    };
  }

  function aiEditCreatedNoteIdsFromBridgeParams(params) {
    params = params || {};
    var createdNoteIdsString = safeString(valueOf(params, 'createdNoteIds'));
    var parts = createdNoteIdsString.split('|');
    var out = [];
    var seen = {};
    for (var i = 0; i < parts.length; i++) {
      var noteId = safeString(parts[i]);
      if (!noteId || seen[noteId]) continue;
      seen[noteId] = true;
      out.push(noteId);
    }
    return out;
  }

  function mindmapDeleteTargetNoteIdsFromBridgeParams(params) {
    params = params || {};
    var targetNoteIdsString = safeString(valueOf(params, 'targetNoteIds'));
    var parts = targetNoteIdsString.split('|');
    var out = [];
    var seen = {};
    for (var i = 0; i < parts.length; i++) {
      var noteId = safeString(parts[i]);
      if (!noteId || seen[noteId]) continue;
      seen[noteId] = true;
      out.push(noteId);
    }
    return out;
  }

  function fallbackAiEditTransactionFromBridge(transactionId, fallback) {
    transactionId = safeString(transactionId);
    fallback = fallback || {};
    var createdNoteIds = aiEditCreatedNoteIdsFromBridgeParams(fallback);
    if (!transactionId || !createdNoteIds.length) return null;
    var createdNoteIdsMap = {};
    for (var i = 0; i < createdNoteIds.length; i++) {
      createdNoteIdsMap[createdNoteIds[i]] = true;
    }
    return {
      transactionId: transactionId,
      draftId: safeString(valueOf(fallback, 'draftId') || valueOf(fallback, 'id')),
      topicid: safeString(valueOf(fallback, 'topicid')),
      objectRef: aiEditObjectRefFromBridgeParams(fallback),
      createdNotes: [],
      createdNoteIds: createdNoteIds,
      createdNoteIdsMap: createdNoteIdsMap,
      startedAt: String(new Date().getTime())
    };
  }

  function copyAiEditObjectRefFields(payload, objectRef) {
    objectRef = objectRef || {};
    payload.objectRef = objectRef;
    payload.mnObjectId = safeString(valueOf(objectRef, 'objectId'));
    payload.mnObjectKind = safeString(valueOf(objectRef, 'kind'));
    payload.mnObjectTitle = safeString(valueOf(objectRef, 'title'));
    payload.mnObjectSourceRef = valueOf(objectRef, 'sourceRef') || {};
    return payload;
  }

  CodexAssistantAddon.prototype.beginAiEditTransaction = function(draftId, json) {
    var now = String(new Date().getTime());
    var objectRef = aiEditObjectRefFromDraft(json);
    var transaction = {
      transactionId: 'ai-edit-' + now + '-' + String(Math.random()).substring(2, 8),
      draftId: safeString(draftId),
      topicid: '',
      objectRef: objectRef,
      createdNotes: [],
      createdNoteIds: [],
      createdNoteIdsMap: {},
      startedAt: now
    };
    try {
      var ctx = this.resolveNotebookAndDocument();
      transaction.topicid = ctx ? ctx.topicId : '';
    } catch (ctxErr) {}
    this.activeAiEditTransaction = transaction;
    this.aiEditTransactions = this.aiEditTransactions || {};
    this.postEvent('aiEditTransactionStarted', copyAiEditObjectRefFields({
      transactionId: transaction.transactionId,
      draftId: transaction.draftId,
      topicid: transaction.topicid,
      hasMindmap: valueOf(json, 'mindmap') ? true : false,
      cards: countOf(valueOf(json, 'cards'))
    }, objectRef));
    return transaction;
  };

  CodexAssistantAddon.prototype.recordAiEditCreatedNote = function(note) {
    var transaction = this.activeAiEditTransaction;
    if (!transaction || !note) return;
    var noteId = noteIdentifier(note);
    if (!noteId || transaction.createdNoteIdsMap[noteId]) return;
    transaction.createdNoteIdsMap[noteId] = true;
    transaction.createdNoteIds.push(noteId);
    transaction.createdNotes.push(note);
  };

  CodexAssistantAddon.prototype.finishAiEditTransaction = function(json) {
    var transaction = this.activeAiEditTransaction;
    if (!transaction) return null;
    this.activeAiEditTransaction = null;
    this.aiEditTransactions = this.aiEditTransactions || {};
    this.aiEditTransactions[transaction.transactionId] = transaction;
    var draftSummary = valueOf(json, 'draft') || {};
    var mindmap = valueOf(json, 'mindmap') || {};
    var payload = {
      id: transaction.draftId,
      draftId: transaction.draftId,
      transactionId: transaction.transactionId,
      createdCount: transaction.createdNoteIds.length,
      createdNoteIds: transaction.createdNoteIds,
      card_count: countOf(valueOf(json, 'cards')),
      has_mindmap: mindmap ? true : false,
      mindmap_title: safeString(valueOf(draftSummary, 'mindmap_title') || valueOf(mindmap, 'title')),
      write_target: safeString(valueOf(draftSummary, 'write_target')),
      topicid: transaction.topicid
    };
    copyAiEditObjectRefFields(payload, transaction.objectRef);
    this.postEvent('aiEditOperationReady', payload);
    if (this.panel && this.panel.setAiEditOperationReady) this.panel.setAiEditOperationReady(payload);
    return payload;
  };

  CodexAssistantAddon.prototype.acceptAiEditTransaction = function(transactionId, fallback) {
    transactionId = safeString(transactionId);
    fallback = fallback || {};
    var acceptedObjectRef = this.aiEditTransactions && this.aiEditTransactions[transactionId]
      ? this.aiEditTransactions[transactionId].objectRef
      : aiEditObjectRefFromBridgeParams(fallback);
    if (this.aiEditTransactions && this.aiEditTransactions[transactionId]) {
      delete this.aiEditTransactions[transactionId];
    }
    var payload = copyAiEditObjectRefFields({ok: true, action: 'accept', transactionId: transactionId, message: '已保留本次 AI 编辑结果。'}, acceptedObjectRef);
    this.postEvent('aiEditTransactionAccepted', payload);
    if (this.panel && this.panel.setAiEditOperationResult) this.panel.setAiEditOperationResult(payload);
    return payload;
  };

  CodexAssistantAddon.prototype.rejectAiEditTransaction = function(transactionId, fallback) {
    transactionId = safeString(transactionId);
    fallback = fallback || {};
    var transaction = this.aiEditTransactions ? this.aiEditTransactions[transactionId] : null;
    if (!transaction) {
      transaction = fallbackAiEditTransactionFromBridge(transactionId, fallback);
      if (transaction) {
        this.aiEditTransactions = this.aiEditTransactions || {};
        this.aiEditTransactions[transactionId] = transaction;
      }
    }
    if (!transaction) {
      var missing = {ok: false, action: 'reject', transactionId: transactionId, message: '未找到可撤销的 AI 编辑事务。'};
      this.postEvent('aiEditTransactionRejected', missing);
      if (this.panel && this.panel.setAiEditOperationResult) this.panel.setAiEditOperationResult(missing);
      return missing;
    }
    var ctx = this.resolveNotebookAndDocument() || aiEditFallbackContext(transaction.topicid);
    var deleted = 0;
    var failed = [];
    var undoRollback = rollbackAiEditTransactionWithUndo(transaction, ctx);
    this.postEvent('aiEditUndoRollbackAttempted', {
      transactionId: transactionId,
      ok: undoRollback.ok,
      method: undoRollback.method,
      deleted: undoRollback.deleted,
      remaining: countOf(undoRollback.remaining),
      reason: undoRollback.reason || ''
    });
    deleted = undoRollback.deleted || 0;
    if (!undoRollback.ok) {
      var remainingIds = countOf(undoRollback.remaining) ? undoRollback.remaining : transaction.createdNoteIds;
      UndoManager.sharedInstance().undoGrouping('Codex Reject AI Edit', ctx ? ctx.topicId : transaction.topicid, function() {
        for (var i = remainingIds.length - 1; i >= 0; i--) {
          var noteId = remainingIds[i];
          var note = resolveAiEditNoteById(ctx, noteId);
          var result = deleteNoteForAiEdit(note, ctx, noteId);
          if (result && result.ok) deleted += 1;
          else failed.push({
            noteId: noteId,
            method: result ? result.method : '',
            reason: result ? result.reason : 'unknown'
          });
        }
      });
    }
    markAiEditDatabaseChanged(ctx ? ctx.topicId : transaction.topicid);
    if (ctx && ctx.topicId) Application.sharedInstance().refreshAfterDBChanged(ctx.topicId);
    var originalFailed = failed.length;
    if (failed.length && ctx) failed = pruneAiEditDeleteFailures(failed, ctx);
    deleted += originalFailed - failed.length;
    var ok = failed.length === 0;
    if (ok && this.aiEditTransactions) delete this.aiEditTransactions[transactionId];
    var payload = {
      ok: ok,
      action: 'reject',
      transactionId: transactionId,
      deleted: deleted,
      failed: failed.length,
      message: ok ? '已删除本次新增内容。' : '部分新增内容删除失败，请手动撤销。',
      failures: failed,
      undoRollback: {
        ok: undoRollback.ok,
        method: undoRollback.method,
        deleted: undoRollback.deleted,
        remaining: countOf(undoRollback.remaining),
        reason: undoRollback.reason || ''
      }
    };
    copyAiEditObjectRefFields(payload, transaction.objectRef);
    this.postEvent('aiEditTransactionRejected', payload);
    if (this.panel && this.panel.setAiEditOperationResult) this.panel.setAiEditOperationResult(payload);
    return payload;
  };

  CodexAssistantAddon.prototype.confirmMindmapDeleteTransaction = function(transactionId, fallback) {
    transactionId = safeString(transactionId);
    fallback = fallback || {};
    var targetNoteIds = mindmapDeleteTargetNoteIdsFromBridgeParams(fallback);
    var ctx = this.resolveNotebookAndDocument() || aiEditFallbackContext(safeString(valueOf(fallback, 'topicid')));
    var deleted = 0;
    var failed = [];
    UndoManager.sharedInstance().undoGrouping('Codex Confirm Mindmap Delete', ctx ? ctx.topicId : safeString(valueOf(fallback, 'topicid')), function() {
      for (var i = targetNoteIds.length - 1; i >= 0; i--) {
        var noteId = targetNoteIds[i];
        var note = resolveAiEditNoteById(ctx, noteId);
        var result = deleteNoteForAiEdit(note, ctx, noteId);
        if (result && result.ok) deleted += 1;
        else failed.push({
          noteId: noteId,
          method: result ? result.method : '',
          reason: result ? result.reason : 'unknown'
        });
      }
    });
    markAiEditDatabaseChanged(ctx ? ctx.topicId : safeString(valueOf(fallback, 'topicid')));
    if (ctx && ctx.topicId) Application.sharedInstance().refreshAfterDBChanged(ctx.topicId);
    if (failed.length && ctx) {
      var originalFailed = failed.length;
      failed = pruneAiEditDeleteFailures(failed, ctx);
      deleted += originalFailed - failed.length;
    }
    var ok = failed.length === 0;
    var payload = {
      ok: ok,
      action: 'confirm_delete',
      transactionId: transactionId,
      targetNoteIds: targetNoteIds,
      deleted: deleted,
      failed: failed.length,
      failures: failed,
      message: ok ? '已删除确认的脑图节点。' : '部分确认删除的脑图节点删除失败。'
    };
    this.postEvent('mindmapDeleteSuggestionConfirmed', payload);
    if (this.panel && this.panel.setAiEditOperationResult) this.panel.setAiEditOperationResult(payload);
    return payload;
  };

  CodexAssistantAddon.prototype.dismissMindmapDeleteTransaction = function(transactionId, fallback) {
    transactionId = safeString(transactionId);
    fallback = fallback || {};
    var targetNoteIds = mindmapDeleteTargetNoteIdsFromBridgeParams(fallback);
    var payload = {
      ok: true,
      action: 'dismiss_delete',
      transactionId: transactionId,
      targetNoteIds: targetNoteIds,
      message: '已忽略本次脑图删除建议。'
    };
    this.postEvent('mindmapDeleteSuggestionDismissed', payload);
    if (this.panel && this.panel.setAiEditOperationResult) this.panel.setAiEditOperationResult(payload);
    return payload;
  };

  CodexAssistantAddon.prototype.writeDraft = function(draftId, options) {
    options = options || {};
    draftId = safeString(draftId);
    var controller = this.getStudyController();
    var view = controller ? controller.view : this.window;
    if (!draftId) {
      var missing = '草稿 ID 为空，无法写入。';
      if (this.panel) this.panel.setStatus(missing);
      Application.sharedInstance().showHUD(missing, view, 3);
      this.postEvent('draftWriteFailed', {reason: 'missing-id'});
      return;
    }
    try {
      var url = DraftURL + encodeURIComponent(draftId);
      var data = NSData.dataWithContentsOfURL(NSURL.URLWithString(url));
      var json = parseJSONData(data);
      if (!json || valueOf(json, 'ok') === false) {
        var message = json ? safeString(valueOf(json, 'message')) : '草稿读取失败。';
        if (this.panel) this.panel.setStatus(message);
        Application.sharedInstance().showHUD(message, view, 3);
        this.postEvent('draftWriteFailed', {id: draftId, reason: message || 'load-failed'});
        return;
      }
      var operationManifest = valueOf(json, 'operationManifest') || {};
      var dryRun = valueOf(operationManifest, 'dryRun') || {};
      var dryRunStatus = safeString(valueOf(dryRun, 'status'));
      if (dryRunStatus === 'blocked') {
        var dryRunMessage = safeString(valueOf(dryRun, 'message')) || 'Operation dry-run blocked this write.';
        var blockedMessage = '草稿写入已阻断：' + dryRunMessage;
        if (this.panel) this.panel.setStatus(blockedMessage);
        Application.sharedInstance().showHUD(blockedMessage, view, 4);
        this.postEvent('draftWriteFailed', {
          id: draftId,
          reason: 'operation-dry-run-blocked',
          dryRunStatus: dryRunStatus,
          dryRunMessage: dryRunMessage
        });
        return;
      }
      this.postEvent('draftWritten', {
        id: draftId,
        cards: countOf(valueOf(json, 'cards')),
        hasMindmap: valueOf(json, 'mindmap') ? true : false
      });
      if (options.aiEditOperation) this.beginAiEditTransaction(draftId, json);
      this.handleCompanionResponse(json, 'write_draft');
      if (options.aiEditOperation) this.finishAiEditTransaction(json);
    } catch (err) {
      this.activeAiEditTransaction = null;
      var errText = '草稿写入失败：' + safeString(err);
      if (this.panel) this.panel.setStatus(errText);
      Application.sharedInstance().showHUD(errText, view, 4);
      this.postEvent('draftWriteFailed', {id: draftId, reason: safeString(err)});
    }
  };

  CodexAssistantAddon.prototype.handleCompanionResponse = function(json, action) {
    var messageValue = valueOf(json, 'message');
    var okValue = valueOf(json, 'ok');
    var replyValue = valueOf(json, 'reply');
    var cardsValue = valueOf(json, 'cards');
    var mindmapValue = valueOf(json, 'mindmap');
    var message = messageValue ? String(messageValue) : (okValue ? '完成' : '失败');
    if (this.panel) this.panel.setStatus(message);
    if (this.panel && this.panel.setBusy) this.panel.setBusy(false);
    if (this.panel && replyValue) this.panel.setReply(String(replyValue));
    this.postEvent('handleResponse', {
      action: safeString(action),
      message: message,
      cards: countOf(cardsValue),
      hasMindmap: mindmapValue ? true : false
    });
    var controller = this.getStudyController();
    var view = controller ? controller.view : this.window;
    Application.sharedInstance().showHUD(message, view, 3);
    if (cardsValue && countOf(cardsValue) > 0) this.createCards(cardsValue);
    if (mindmapValue) this.createMindmap(mindmapValue);
    return true;
  };

  CodexAssistantAddon.prototype.resolveNotebookAndDocument = function() {
    this.lastResolveError = '';
    var controller = this.getStudyController();
    if (!controller || !controller.notebookController) {
      this.lastResolveError = 'no-study-controller-or-notebook-controller';
      return null;
    }
    var topicId = controller.notebookController.topicId || controller.notebookController.notebookId || this.currentNotebookId;
    if (!topicId) {
      this.lastResolveError = 'no-topic-id';
      return null;
    }
    var db = Database.sharedInstance();
    var notebook = db.getNotebookById(String(topicId));
    if (!notebook) {
      this.lastResolveError = 'notebook-not-found:' + String(topicId);
      return null;
    }
    var document = null;
    if (notebook.documents && countOf(notebook.documents) > 0) document = objectAt(notebook.documents, 0);
    else if (notebook.mainDocMd5) document = db.getDocumentById(notebook.mainDocMd5);
    if (!document) {
      this.lastResolveError = 'document-not-found';
      return null;
    }
    return {controller: controller, notebook: notebook, document: document, topicId: String(topicId)};
  };

  CodexAssistantAddon.prototype.createCards = function(cards) {
    var ctx = this.resolveNotebookAndDocument();
    if (!ctx) {
      this.postEvent('createCardsFailed', {reason: this.lastResolveError || 'unknown'});
      return;
    }
    var addon = this;
    var parent = this.getSelectedNote();
    var created = [];
    var skipped = [];
    var arr = toArray(cards);
    var dedupeStats = {scanned: 0, markerMatches: 0, titleMatches: 0};
    UndoManager.sharedInstance().undoGrouping('Codex Create Cards', ctx.topicId, function() {
      for (var i = 0; i < arr.length; i++) {
        var item = arr[i];
        var titleValue = valueOf(item, 'title');
        var bodyValue = valueOf(item, 'body');
        var codexIdValue = valueOf(item, 'codexId');
        var title = titleValue ? String(titleValue) : 'Codex 卡片';
        var body = bodyValue ? String(bodyValue) : '';
        var codexId = codexIdValue ? String(codexIdValue) : '';
        if (codexId && findExistingCodexNote(ctx.notebook, codexId, title, dedupeStats)) {
          skipped.push(codexId);
          continue;
        }
        var note = Note.createWithTitleNotebookDocument(title, ctx.notebook, ctx.document);
        if (note) {
          if (parent) parent.addChild(note);
          if (note.appendMarkdownComment) {
            var marker = metadataComment(codexId);
            note.appendMarkdownComment(marker ? marker + '\n\n' + body : body);
          }
          created.push(note);
          addon.recordAiEditCreatedNote(note);
        }
      }
    });
    Application.sharedInstance().refreshAfterDBChanged(ctx.topicId);
    this.postEvent('createCardsFinished', {
      requested: arr.length,
      created: created.length,
      skipped: skipped.length,
      topicid: ctx.topicId,
      dedupeScanned: dedupeStats.scanned,
      markerMatches: dedupeStats.markerMatches,
      titleMatches: dedupeStats.titleMatches
    });
    if (created.length && ctx.controller.focusNoteInMindMapById) {
      var noteId = created[0].noteId;
      NSTimer.scheduledTimerWithTimeInterval(0.3, false, function() {
        ctx.controller.focusNoteInMindMapById(noteId);
      });
    }
  };

  CodexAssistantAddon.prototype.createMindmap = function(tree) {
    var ctx = this.resolveNotebookAndDocument();
    if (!ctx || !tree) {
      this.postEvent('createMindmapFailed', {reason: this.lastResolveError || 'missing-tree'});
      return;
    }
    var addon = this;
    var selected = this.getSelectedNote();
    var rootNote = null;
    var rootTitleValue = valueOf(tree, 'title');
    var rootCodexIdValue = valueOf(tree, 'codexId');
    var rootTitle = rootTitleValue ? String(rootTitleValue) : 'Codex 节点';
    var rootCodexId = rootCodexIdValue ? String(rootCodexIdValue) : '';
    var writeTarget = valueOf(tree, 'writeTarget') || {};
    var targetMode = String(valueOf(writeTarget, 'mode') || '');
    var targetSelectedNoteId = String(valueOf(writeTarget, 'selectedNoteId') || '');
    var wantsMergeIntoSelected = !!valueOf(tree, 'mergeIntoSelected') || targetMode === 'merge_children_into_selected_node';
    var wantsDocumentRoot = targetMode === 'document_root';
    if (wantsMergeIntoSelected && selected && targetSelectedNoteId && noteIdentifier(selected) !== targetSelectedNoteId) {
      var mismatchMessage = '目标脑图节点已变化，请重新选择目标脑图后再生成。';
      if (this.panel) this.panel.setStatus(mismatchMessage);
      try {
        Application.sharedInstance().showHUD(mismatchMessage, ctx.controller ? ctx.controller.view : this.window, 3);
      } catch (mismatchHudErr) {}
      this.postEvent('createMindmapFailed', {
        reason: 'selected-node-target-mismatch',
        expectedNoteId: targetSelectedNoteId,
        actualNoteId: noteIdentifier(selected),
        title: rootTitle,
        topicid: ctx.topicId,
        requestedMode: 'mergeIntoSelected'
      });
      return;
    }
    if (wantsMergeIntoSelected && !selected) {
      var missingSelected = '请先在脑图中选中一个节点，再执行合并/补到当前脑图。';
      if (this.panel) this.panel.setStatus(missingSelected);
      try {
        Application.sharedInstance().showHUD(missingSelected, ctx.controller ? ctx.controller.view : this.window, 3);
      } catch (hudErr) {}
      this.postEvent('createMindmapFailed', {
        reason: 'missing-selected-node-for-merge',
        title: rootTitle,
        topicid: ctx.topicId,
        requestedMode: 'mergeIntoSelected'
      });
      return;
    }
    var mergeIntoSelected = wantsMergeIntoSelected && !!selected;
    var createdNodes = [];
    var rootDedupeStats = {scanned: 0, markerMatches: 0, titleMatches: 0};
    var existingRoot = rootCodexId ? findExistingCodexNote(ctx.notebook, rootCodexId, rootTitle, rootDedupeStats) : null;

    function makeNode(node, parent) {
      if (!node) return null;
      var titleValue = valueOf(node, 'title');
      var bodyValue = valueOf(node, 'body');
      var childrenValue = valueOf(node, 'children');
      var codexIdValue = valueOf(node, 'codexId');
      var title = titleValue ? String(titleValue) : 'Codex 节点';
      var body = bodyValue ? String(bodyValue) : '';
      var codexId = codexIdValue ? String(codexIdValue) : '';
      var note = Note.createWithTitleNotebookDocument(title, ctx.notebook, ctx.document);
      if (!note) return null;
      if (parent) parent.addChild(note);
      if (note.appendMarkdownComment) {
        var marker = metadataComment(codexId);
        note.appendMarkdownComment(marker ? marker + '\n\n' + body : body);
      }
      createdNodes.push(note);
      addon.recordAiEditCreatedNote(note);
      var children = toArray(childrenValue);
      for (var i = 0; i < children.length; i++) makeNode(children[i], note);
      return note;
    }

    function mergeChildrenIntoSelected() {
      var children = toArray(valueOf(tree, 'children'));
      for (var i = 0; i < children.length; i++) {
        var child = makeNode(children[i], selected);
        if (!rootNote && child) rootNote = child;
      }
    }

    function appendChildrenToDocumentRoot(documentRoot) {
      var children = toArray(valueOf(tree, 'children'));
      for (var i = 0; i < children.length; i++) {
        var child = makeNode(children[i], documentRoot);
        if (!rootNote && child) rootNote = child;
      }
      if (!rootNote) rootNote = documentRoot;
    }

    var mergeIntoDocumentRoot = wantsDocumentRoot && !!existingRoot;
    UndoManager.sharedInstance().undoGrouping('Codex Create Mindmap', ctx.topicId, function() {
      if (mergeIntoSelected) mergeChildrenIntoSelected();
      else if (mergeIntoDocumentRoot) appendChildrenToDocumentRoot(existingRoot);
      else if (wantsDocumentRoot) rootNote = makeNode(tree, null);
      else rootNote = makeNode(tree, selected);
    });
    Application.sharedInstance().refreshAfterDBChanged(ctx.topicId);
    this.postEvent('createMindmapFinished', {
      created: rootNote ? true : false,
      createdCount: createdNodes.length,
      topicid: ctx.topicId,
      mode: mergeIntoSelected ? 'mergeIntoSelected' : (mergeIntoDocumentRoot ? 'mergeIntoDocumentRoot' : 'createRoot')
    });
    if (rootNote && ctx.controller.focusNoteInMindMapById) {
      NSTimer.scheduledTimerWithTimeInterval(0.3, false, function() {
        ctx.controller.focusNoteInMindMapById(rootNote.noteId);
      });
    }
  };

  return CodexAssistantAddon;
};
