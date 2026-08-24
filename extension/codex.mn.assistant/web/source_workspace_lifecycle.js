(function(root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.SourceWorkspaceLifecycle = api;
})(typeof window !== 'undefined' ? window : globalThis, function() {
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
    staleConversationCleanupPayload: staleConversationCleanupPayload
  };
});
