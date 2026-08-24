(function(root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.SourceWorkspaceLifecycle = api;
})(typeof window !== 'undefined' ? window : globalThis, function() {
  function shouldAttachImplicitMnObject(action) {
    action = String(action || '');
    return action !== 'conversation_new' && action.indexOf('source_workspace_') !== 0;
  }

  function documentContextReadyForAutomaticSwitch(ctx, docKey) {
    ctx = ctx || {};
    return !!(
      String(docKey || '') &&
      String(ctx.topicid || ctx.notebookid || '') &&
      String(ctx.bookmd5 || ctx.docmd5 || '')
    );
  }

  function queuedSessionRouting(command, activeConversation) {
    command = command || {};
    activeConversation = activeConversation || {};
    var conversationId = String(command.conversationId || '');
    var sessionId = String(command.sessionId || '');
    if (!conversationId && !sessionId) return 'active';
    if (!conversationId || !sessionId) return 'invalid';
    return (
      conversationId === String(activeConversation.conversationId || '') &&
      sessionId === String(activeConversation.sessionId || '')
    ) ? 'active' : 'background';
  }

  function queuedExecutionDisposition(command, runtime) {
    command = command || {};
    runtime = runtime || {};
    if (command._queue_completed_ack_pending === true) return 'ack_only';
    if (
      queuedConfirmationMatchesActiveSession(runtime.pendingQueuedWriteConfirmation, runtime) &&
      queuedWriteCommandMatchesConfirmation(command, runtime.pendingQueuedWriteConfirmation)
    ) {
      return 'confirmation_pending';
    }
    return 'execute';
  }

  function queueRuntimeCanStart(runtime) {
    runtime = runtime || {};
    return !!(
      String(runtime.conversationId || '') &&
      String(runtime.sessionId || '') &&
      String(runtime.sessionEpoch || '') &&
      String(runtime.contextDocumentKey || '')
    );
  }

  function queuedWriteCommandMatchesConfirmation(command, confirmation) {
    command = command || {};
    confirmation = confirmation || {};
    var action = String(command.rawAction || command.action || '');
    var isWriteAction = action === 'generate_card' ||
      action === 'generate_mindmap' ||
      action === 'generate_full_reading' ||
      action === 'expand_node' ||
      action === 'reorganize_mindmap';
    return !!(
      isWriteAction &&
      String(command.sessionId || '') &&
      String(command.sessionEpoch || '') &&
      String(command.contextDocumentKey || '') &&
      String(command.sessionId || '') === String(confirmation.sessionId || '') &&
      String(command.sessionEpoch || '') === String(confirmation.sessionEpoch || '') &&
      String(command.contextDocumentKey || '') === String(confirmation.contextDocumentKey || '')
    );
  }

  function queuedConfirmationMatchesActiveSession(confirmation, activeConversation) {
    confirmation = confirmation || {};
    activeConversation = activeConversation || {};
    var sessionId = String(confirmation.sessionId || '');
    var sessionEpoch = String(confirmation.sessionEpoch || '');
    var contextDocumentKey = String(confirmation.contextDocumentKey || '');
    return !!(
      sessionId &&
      sessionEpoch &&
      contextDocumentKey &&
      sessionId === String(activeConversation.sessionId || '') &&
      sessionEpoch === String(activeConversation.sessionEpoch || '') &&
      contextDocumentKey === String(activeConversation.contextDocumentKey || '')
    );
  }

  function queuedDraftBindingMatchesActiveSession(draft, activeConversation) {
    draft = draft || {};
    if (!String(draft.queueId || '')) return true;
    var confirmation = draft.queueConfirmation || {};
    return queuedConfirmationMatchesActiveSession(confirmation, activeConversation || {});
  }

  function queuedResultFailureReason(command, result, routing) {
    command = command || {};
    result = result || {};
    var blocked = String(result.blocked || '');
    if (routing === 'invalid') return 'session_binding_mismatch';
    if (
      result.tombstoned === true ||
      blocked.indexOf('tombstone') !== -1 ||
      blocked === 'session_deleted'
    ) return 'session_tombstoned';
    if (
      blocked.indexOf('session_epoch') !== -1 ||
      blocked.indexOf('session_binding') !== -1 ||
      blocked === 'session_ownership_mismatch'
    ) return 'session_binding_mismatch';
    if (
      result.sessionEpoch && command.sessionEpoch &&
      String(result.sessionEpoch) !== String(command.sessionEpoch)
    ) return 'session_binding_mismatch';
    if (result.ok !== true || result.queued_due_to_web_busy) return 'result_failed';
    return '';
  }

  function handleQueuedResult(options) {
    options = options || {};
    var command = options.command || {};
    var result = options.result || {};
    var action = String(command.rawAction || command.action || options.action || '');
    var routing = queuedSessionRouting(command, options.activeConversation || {});
    var hasCompleteBinding = !!(
      String(command.conversationId || '') &&
      String(command.sessionId || '') &&
      String(command.sessionEpoch || '')
    );
    if (!hasCompleteBinding) routing = 'invalid';
    if (
      routing === 'active' &&
      String(command.sessionEpoch || '') !== String((options.activeConversation || {}).sessionEpoch || '')
    ) routing = 'invalid';

    function defer(reason, failedResult) {
      var detail = {
        status: 'deferred',
        reason: reason || 'result_failed',
        retryable: true,
        routing: routing,
        action: action,
        queueId: String(command._queue_id || ''),
        result: failedResult || result
      };
      if (options.onDeferred) options.onDeferred(detail);
      return detail;
    }

    function acknowledge() {
      if (options.onAck) options.onAck(result);
      return {status: 'acked', routing: routing, action: action};
    }

    var failureReason = queuedResultFailureReason(command, result, routing);
    if (failureReason) return defer(failureReason, result);

    var writeAction = options.isWriteAction ? !!options.isWriteAction(action) : false;
    if (writeAction && routing !== 'active') return defer('inactive_write', result);

    if (writeAction) {
      if (!options.onActiveWrite) return defer('write_confirmation_unavailable', result);
      var settled = false;
      var disposition = {status: 'routing_write', routing: routing, action: action};
      try {
        options.onActiveWrite(result, function(writeResult) {
          if (settled) return;
          settled = true;
          if (!writeResult || writeResult.ok !== true) {
            defer(queuedResultFailureReason(command, writeResult || {}, routing) || 'result_failed', writeResult || {});
            return;
          }
          acknowledge();
        });
      } catch (err) {
        settled = true;
        return defer('result_failed', {ok: false, message: String(err && err.message || err)});
      }
      return disposition;
    }

    try {
      if (routing === 'active') {
        if (options.onActiveChat) options.onActiveChat(result);
      } else if (options.onInactiveChat) {
        options.onInactiveChat(result);
      }
    } catch (err) {
      return defer('result_failed', {ok: false, message: String(err && err.message || err)});
    }
    return acknowledge();
  }

  function createHandle(kind, epoch, meta) {
    return {
      kind: kind,
      epoch: epoch,
      phase: 'pending',
      meta: Object.assign({}, meta || {})
    };
  }

  function createController() {
    var migrationEpoch = 0;
    var uploadEpoch = 0;
    var activeMigration = null;
    var activeUpload = null;

    function beginMigration(meta) {
      var superseded = activeMigration;
      migrationEpoch += 1;
      activeMigration = createHandle('migration', migrationEpoch, meta);
      return {handle: activeMigration, superseded: superseded};
    }

    function isMigrationCurrent(handle) {
      return !!handle && activeMigration === handle && handle.epoch === migrationEpoch;
    }

    function startMigration(handle) {
      if (!isMigrationCurrent(handle)) return false;
      handle.phase = 'in_flight';
      return true;
    }

    function updateMigration(handle, patch) {
      if (!isMigrationCurrent(handle)) return false;
      Object.assign(handle.meta, patch || {});
      return true;
    }

    function finishMigration(handle) {
      if (!isMigrationCurrent(handle)) return false;
      handle.phase = 'finished';
      activeMigration = null;
      return true;
    }

    function cancelMigration(reason) {
      var canceled = activeMigration;
      migrationEpoch += 1;
      activeMigration = null;
      if (canceled) {
        canceled.phase = 'canceled';
        canceled.cancelReason = String(reason || 'canceled');
      }
      return canceled;
    }

    function beginUpload(meta) {
      var superseded = activeUpload;
      uploadEpoch += 1;
      activeUpload = createHandle('upload', uploadEpoch, meta);
      activeUpload.phase = 'in_flight';
      return {handle: activeUpload, superseded: superseded};
    }

    function isUploadCurrent(handle) {
      return !!handle && activeUpload === handle && handle.epoch === uploadEpoch;
    }

    function updateUpload(handle, patch) {
      if (!isUploadCurrent(handle)) return false;
      Object.assign(handle.meta, patch || {});
      return true;
    }

    function finishUpload(handle) {
      if (!isUploadCurrent(handle)) return false;
      handle.phase = 'finished';
      activeUpload = null;
      return true;
    }

    function cancelUpload(reason) {
      var canceled = activeUpload;
      uploadEpoch += 1;
      activeUpload = null;
      if (canceled) {
        canceled.phase = 'canceled';
        canceled.cancelReason = String(reason || 'canceled');
      }
      return canceled;
    }

    function isSourceMutationAllowed(handle) {
      if (activeMigration && !isMigrationCurrent(handle)) return false;
      if (activeUpload && !isUploadCurrent(handle)) return false;
      return true;
    }

    return {
      beginMigration: beginMigration,
      isMigrationCurrent: isMigrationCurrent,
      startMigration: startMigration,
      updateMigration: updateMigration,
      finishMigration: finishMigration,
      cancelMigration: cancelMigration,
      isMigrationActive: function() { return !!activeMigration; },
      isMigrationInFlight: function() { return !!activeMigration && activeMigration.phase === 'in_flight'; },
      beginUpload: beginUpload,
      isUploadCurrent: isUploadCurrent,
      updateUpload: updateUpload,
      finishUpload: finishUpload,
      cancelUpload: cancelUpload,
      isUploadActive: function() { return !!activeUpload; },
      isSourceMutationAllowed: isSourceMutationAllowed,
      areSourceControlsLocked: function() { return !!activeMigration || !!activeUpload; },
      isGenerationBlocked: function() { return !!activeMigration; }
    };
  }

  function staleConversationCleanupPayload(conversation, ownershipPayload) {
    var cleanup = {};
    var ownership = ownershipPayload || {};
    for (var key in ownership) {
      if (Object.prototype.hasOwnProperty.call(ownership, key)) cleanup[key] = ownership[key];
    }
    cleanup.action = 'conversation_delete';
    cleanup.conversationId = String((conversation || {}).conversationId || '');
    cleanup.sessionId = String((conversation || {}).sessionId || '');
    delete cleanup.sourceWorkspaceRevision;
    return cleanup;
  }

  return {
    createController: createController,
    documentContextReadyForAutomaticSwitch: documentContextReadyForAutomaticSwitch,
    handleQueuedResult: handleQueuedResult,
    queueRuntimeCanStart: queueRuntimeCanStart,
    queuedDraftBindingMatchesActiveSession: queuedDraftBindingMatchesActiveSession,
    queuedExecutionDisposition: queuedExecutionDisposition,
    queuedConfirmationMatchesActiveSession: queuedConfirmationMatchesActiveSession,
    queuedWriteCommandMatchesConfirmation: queuedWriteCommandMatchesConfirmation,
    queuedSessionRouting: queuedSessionRouting,
    shouldAttachImplicitMnObject: shouldAttachImplicitMnObject,
    staleConversationCleanupPayload: staleConversationCleanupPayload
  };
});
