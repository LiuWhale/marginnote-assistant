const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const lifecycle = require('../extension/codex.mn.assistant/web/source_workspace_lifecycle.js');

const appSource = fs.readFileSync(
  path.join(__dirname, '../extension/codex.mn.assistant/web/app.js'),
  'utf8',
);

function loadAppFunction(name, nextName, dependencies) {
  const startMarker = `  function ${name}(`;
  const endMarker = `\n  function ${nextName}`;
  const start = appSource.indexOf(startMarker);
  const end = appSource.indexOf(endMarker, start);
  assert.notEqual(start, -1, `${name} must exist in app.js`);
  assert.notEqual(end, -1, `${name} must end before ${nextName}`);
  const functionSource = appSource.slice(start, end);
  const names = Object.keys(dependencies);
  const factory = new Function(
    ...names,
    functionSource + `\nreturn ${name};`,
  );
  return factory(...names.map((dependency) => dependencies[dependency]));
}

function loadCompanionPayload(state) {
  return loadAppFunction('companionPayload', 'parseCompanionResult', {
    state,
    sourceWorkspaceSelectionIds: () => {
      if (state.sourceWorkspaceSelection) {
        return Object.keys(state.sourceWorkspaceSelection).filter(
          (sourceId) => state.sourceWorkspaceSelection[sourceId],
        );
      }
      return (state.testSourceIds || []).slice();
    },
    currentContextScope: () => state.testContextScope || 'document',
    window: {SourceWorkspaceLifecycle: lifecycle},
  });
}

function payloadState(overrides) {
  return Object.assign({
    context: {
      topicid: 'TOPIC-HILTON',
      bookmd5: 'BOOK-HILTON',
      contextDocumentKey: 'TOPIC-HILTON|BOOK-HILTON|/papers/hilton.pdf',
      documentTitle: 'Hilton.pdf',
    },
    conversationId: 'CONV-LEE',
    sessionId: 'SESSION-LEE',
    sessionEpoch: '11111111111111111111111111111111',
    testSourceIds: ['upload:one', 'upload:two', 'upload:three'],
    followCurrentDocument: false,
    sourceWorkspace: {revision: 'REV-LEE'},
    agentOperation: {
      mnObject: {
        objectId: 'mnobj:lee:stale',
        kind: 'mindmap_node',
        title: 'Lee stale node',
      },
    },
    mindmapTarget: null,
    testContextScope: 'document',
  }, overrides || {});
}

const appIsWriteAction = loadAppFunction('isWriteAction', 'isQueueableGoalAction', {});

test('automatic switch readiness accepts stable identity without title or path metadata', () => {
  const context = {
    topicid: 'TOPIC-HILTON',
    bookmd5: 'BOOK-HILTON',
    documentTitle: '',
    documentFileName: '',
    pdfPath: '',
    documentPath: '',
  };

  assert.equal(
    lifecycle.documentContextReadyForAutomaticSwitch?.(
      context,
      'TOPIC-HILTON|BOOK-HILTON',
    ),
    true,
  );
});

test('automatic switch readiness rejects context without a topic or notebook identity', () => {
  assert.equal(
    lifecycle.documentContextReadyForAutomaticSwitch?.(
      {bookmd5: 'BOOK-HILTON'},
      'TOPIC-HILTON|BOOK-HILTON',
    ),
    false,
  );
});

test('automatic switch readiness rejects context without a book or document identity', () => {
  assert.equal(
    lifecycle.documentContextReadyForAutomaticSwitch?.(
      {topicid: 'TOPIC-HILTON'},
      'TOPIC-HILTON|BOOK-HILTON',
    ),
    false,
  );
});

test('automatic switch readiness rejects an empty document key', () => {
  assert.equal(
    lifecycle.documentContextReadyForAutomaticSwitch?.(
      {topicid: 'TOPIC-HILTON', bookmd5: 'BOOK-HILTON'},
      '',
    ),
    false,
  );
});

test('migration superseded before conversation callback stays blocked by newer epoch', () => {
  const controller = lifecycle.createController();
  const first = controller.beginMigration({contextDocumentKey: 'transient'}).handle;
  controller.startMigration(first);
  const secondResult = controller.beginMigration({contextDocumentKey: 'stable'});
  const second = secondResult.handle;

  assert.equal(controller.isMigrationCurrent(first), false);
  assert.equal(controller.isMigrationCurrent(second), true);
  assert.equal(controller.finishMigration(first), false);
  assert.equal(controller.isGenerationBlocked(), true);
  assert.equal(controller.finishMigration(second), true);
  assert.equal(controller.isGenerationBlocked(), false);
});

test('stale conversation cleanup keeps exact original ownership context', () => {
  const ownership = {
    action: 'conversation_new',
    topicid: 'TOPIC-A',
    bookmd5: 'BOOK-A',
    contextDocumentKey: 'TOPIC-A|BOOK-A|/a.pdf',
    documentTitle: 'A.pdf',
    mnObject: {objectId: 'mnobj:a'},
    sourceIds: ['upload:one'],
    followCurrentDocument: false,
  };
  const cleanup = lifecycle.staleConversationCleanupPayload(
    {conversationId: 'CONV-A', sessionId: 'SESSION-A'},
    ownership,
  );

  assert.equal(cleanup.action, 'conversation_delete');
  assert.equal(cleanup.conversationId, 'CONV-A');
  assert.equal(cleanup.sessionId, 'SESSION-A');
  assert.equal(cleanup.topicid, ownership.topicid);
  assert.equal(cleanup.bookmd5, ownership.bookmd5);
  assert.equal(cleanup.contextDocumentKey, ownership.contextDocumentKey);
  assert.deepEqual(cleanup.mnObject, ownership.mnObject);
});

test('upload cancellation preserves successes and requires unfinished files to retry', () => {
  const controller = lifecycle.createController();
  const upload = controller.beginUpload({successfulUploadIds: [], total: 3}).handle;
  upload.meta.successfulUploadIds.push('upload:one');

  const canceled = controller.cancelUpload('document-switch');

  assert.deepEqual(canceled.meta.successfulUploadIds, ['upload:one']);
  assert.equal(controller.isUploadCurrent(upload), false);
  assert.equal(controller.isUploadActive(), false);
  assert.equal(controller.finishUpload(upload), false);
});

test('older upload callback cannot unlock a newer upload lifecycle', () => {
  const controller = lifecycle.createController();
  const first = controller.beginUpload({successfulUploadIds: []}).handle;
  const second = controller.beginUpload({successfulUploadIds: []}).handle;

  assert.equal(controller.finishUpload(first), false);
  assert.equal(controller.isUploadCurrent(second), true);
  assert.equal(controller.isUploadActive(), true);
  assert.equal(controller.finishUpload(second), true);
  assert.equal(controller.isUploadActive(), false);
});

test('active upload locks conflicting source controls but permits its own finalization handle', () => {
  const controller = lifecycle.createController();
  const upload = controller.beginUpload({successfulUploadIds: []}).handle;

  assert.equal(controller.areSourceControlsLocked(), true);
  assert.equal(controller.isSourceMutationAllowed(null), false);
  assert.equal(controller.isSourceMutationAllowed(upload), true);

  controller.finishUpload(upload);
  assert.equal(controller.areSourceControlsLocked(), false);
  assert.equal(controller.isSourceMutationAllowed(null), true);
});

test('clear cancellation preserves upload successes and makes stale reselection callback inert', () => {
  const controller = lifecycle.createController();
  const upload = controller.beginUpload({successfulUploadIds: ['upload:one']}).handle;

  const canceled = controller.cancelUpload('clear');

  assert.deepEqual(canceled.meta.successfulUploadIds, ['upload:one']);
  assert.equal(controller.isUploadCurrent(upload), false);
  assert.equal(controller.updateUpload(upload, {autoSelect: true}), false);
  assert.equal(controller.areSourceControlsLocked(), false);
});

test('generation gate remains active for the full migration lifecycle', () => {
  const controller = lifecycle.createController();
  const migration = controller.beginMigration({contextDocumentKey: 'stable'}).handle;

  assert.equal(controller.isGenerationBlocked(), true);
  controller.startMigration(migration);
  assert.equal(controller.isGenerationBlocked(), true);
  controller.finishMigration(migration);
  assert.equal(controller.isGenerationBlocked(), false);
});

test('implicit object predicate excludes every document-scoped source action', () => {
  for (const action of [
    'conversation_new',
    'source_workspace_get',
    'source_workspace_update',
    'source_workspace_validate',
    'source_workspace_clear',
  ]) {
    assert.equal(
      lifecycle.shouldAttachImplicitMnObject(action),
      false,
      `${action} must remain document-scoped`,
    );
  }

  for (const action of ['generate_card', 'generate_mindmap', 'object_graph']) {
    assert.equal(
      lifecycle.shouldAttachImplicitMnObject(action),
      true,
      `${action} must retain implicit object ownership`,
    );
  }
});

test('app payload keeps explicit object ownership but skips stale implicit ownership', () => {
  const state = payloadState();
  const companionPayload = loadCompanionPayload(state);

  const manualConversation = companionPayload('conversation_new', {});
  const automaticConversation = companionPayload('conversation_new', {
    automaticDocumentSwitch: true,
    sourceIds: state.testSourceIds,
    followCurrentDocument: false,
    sourceWorkspaceRevision: '',
  });
  assert.equal(Object.hasOwn(manualConversation, 'mnObject'), false);
  assert.equal(Object.hasOwn(automaticConversation, 'mnObject'), false);

  for (const action of [
    'source_workspace_get',
    'source_workspace_update',
    'source_workspace_validate',
    'source_workspace_clear',
  ]) {
    const payload = companionPayload(action, {conversationId: 'CONV-HILTON'});
    assert.equal(Object.hasOwn(payload, 'mnObject'), false, action);
  }

  const explicitObject = {objectId: 'mnobj:hilton:explicit', kind: 'mindmap_node'};
  const explicitPayload = companionPayload('source_workspace_update', {
    conversationId: 'CONV-HILTON',
    mnObject: explicitObject,
  });
  assert.deepEqual(explicitPayload.mnObject, explicitObject);

  for (const action of ['generate_card', 'generate_mindmap', 'object_graph']) {
    const payload = companionPayload(action, {});
    assert.deepEqual(payload.mnObject, state.agentOperation.mnObject, action);
  }
});

test('app payload never copies the Web action token into action JSON', () => {
  const state = payloadState({
    context: Object.assign({}, payloadState().context, {
      webActionToken: 'sensitive-install-token',
    }),
  });
  const companionPayload = loadCompanionPayload(state);

  const payload = companionPayload('chat', {prompt: 'hello'});

  assert.equal(Object.hasOwn(payload, 'webActionToken'), false);
  assert.equal(JSON.stringify(payload).includes('sensitive-install-token'), false);
});

test('explicit queued conversation never inherits the currently active session', () => {
  const state = payloadState({conversationId: 'CONV-B', sessionId: 'SESSION-B'});
  const companionPayload = loadCompanionPayload(state);

  const unbound = companionPayload('chat', {conversationId: 'CONV-A'});
  const bound = companionPayload('chat', {
    conversationId: 'CONV-A',
    sessionId: 'SESSION-A',
  });

  assert.equal(Object.hasOwn(unbound, 'sessionId'), false);
  assert.equal(bound.sessionId, 'SESSION-A');
});

test('queued A result stays background after the active session switches to B', () => {
  assert.equal(
    lifecycle.queuedSessionRouting(
      {conversationId: 'CONV-A', sessionId: 'SESSION-A'},
      {conversationId: 'CONV-B', sessionId: 'SESSION-B'},
    ),
    'background',
  );
  assert.equal(
    lifecycle.queuedSessionRouting(
      {conversationId: 'CONV-A', sessionId: 'SESSION-A'},
      {conversationId: 'CONV-A', sessionId: 'SESSION-A'},
    ),
    'active',
  );
});

test('completed queue records are ack-only even while a write confirmation blocks execution', () => {
  assert.equal(
    lifecycle.queuedExecutionDisposition(
      {_queue_id: 'QUEUE-DONE', _queue_completed_ack_pending: true},
      {pendingQueuedWriteConfirmation: {queueId: 'QUEUE-WRITE'}},
    ),
    'ack_only',
  );
  assert.equal(
    lifecycle.queuedExecutionDisposition(
      {_queue_id: 'QUEUE-NEXT', rawAction: 'generate_card'},
      {pendingQueuedWriteConfirmation: {queueId: 'QUEUE-WRITE'}},
    ),
    'confirmation_pending',
  );
  assert.equal(
    lifecycle.queuedExecutionDisposition(
      {_queue_id: 'QUEUE-NEXT', rawAction: 'chat'},
      {},
    ),
    'execute',
  );
});

function queueResultHarness(overrides) {
  const events = [];
  let finishWrite = null;
  const options = Object.assign({
    command: {
      _queue_id: 'QUEUE-A',
      rawAction: 'chat',
      conversationId: 'CONV-A',
      sessionId: 'SESSION-A',
      sessionEpoch: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    },
    result: {ok: true, reply: 'saved'},
    activeConversation: {
      conversationId: 'CONV-A',
      sessionId: 'SESSION-A',
      sessionEpoch: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    },
    isWriteAction: appIsWriteAction,
    onActiveChat: () => events.push('active-chat'),
    onInactiveChat: () => events.push('inactive-chat'),
    onActiveWrite: (_result, done) => {
      events.push('active-write');
      finishWrite = done;
    },
    onDeferred: (detail) => events.push(['deferred', detail]),
    onAck: () => events.push('ack'),
  }, overrides || {});
  const disposition = lifecycle.handleQueuedResult(options);
  return {events, disposition, finishWrite: () => finishWrite};
}

test('failed queued result remains deferred and retryable without acknowledgement', () => {
  const run = queueResultHarness({result: {ok: false, message: 'model failed'}});

  assert.equal(run.disposition.status, 'deferred');
  assert.equal(run.disposition.retryable, true);
  assert.deepEqual(run.events.map((item) => Array.isArray(item) ? item[0] : item), ['deferred']);
  assert.equal(run.events[0][1].retryable, true);
  assert.equal(run.events[0][1].reason, 'result_failed');
});

test('active-session chat renders through the active handler before acknowledgement', () => {
  const run = queueResultHarness({});

  assert.equal(run.disposition.status, 'acked');
  assert.deepEqual(run.events, ['active-chat', 'ack']);
});

test('inactive-session chat persists without active rendering before acknowledgement', () => {
  const run = queueResultHarness({
    activeConversation: {
      conversationId: 'CONV-B',
      sessionId: 'SESSION-B',
      sessionEpoch: 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
    },
  });

  assert.equal(run.disposition.status, 'acked');
  assert.deepEqual(run.events, ['inactive-chat', 'ack']);
});

test('inactive-session write remains deferred without execution or acknowledgement', () => {
  for (const action of [
    'generate_card',
    'generate_mindmap',
    'generate_full_reading',
    'expand_node',
    'reorganize_mindmap',
  ]) {
    const run = queueResultHarness({
      command: {
        _queue_id: `QUEUE-${action}`,
        rawAction: action,
        conversationId: 'CONV-A',
        sessionId: 'SESSION-A',
        sessionEpoch: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
      },
      activeConversation: {
        conversationId: 'CONV-B',
        sessionId: 'SESSION-B',
        sessionEpoch: 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
      },
    });

    assert.equal(run.disposition.status, 'deferred', action);
    assert.equal(run.disposition.reason, 'inactive_write', action);
    assert.deepEqual(run.events.map((item) => Array.isArray(item) ? item[0] : item), ['deferred'], action);
    assert.equal(run.finishWrite(), null, action);
  }
});

test('active-session write acknowledges only after draft confirmation routing succeeds', () => {
  const run = queueResultHarness({
    command: {
      _queue_id: 'QUEUE-WRITE',
      rawAction: 'generate_card',
      conversationId: 'CONV-A',
      sessionId: 'SESSION-A',
      sessionEpoch: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    },
  });

  assert.equal(run.disposition.status, 'routing_write');
  assert.deepEqual(run.events, ['active-write']);
  run.finishWrite()({ok: true});
  assert.deepEqual(run.events, ['active-write', 'ack']);
});

test('session epoch mismatch and tombstone results defer without acknowledgement', () => {
  const mismatched = queueResultHarness({
    activeConversation: {
      conversationId: 'CONV-A',
      sessionId: 'SESSION-A',
      sessionEpoch: 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
    },
  });
  const tombstoned = queueResultHarness({
    result: {ok: true, tombstoned: true, reply: 'must not render'},
  });

  assert.equal(mismatched.disposition.reason, 'session_binding_mismatch');
  assert.equal(tombstoned.disposition.reason, 'session_tombstoned');
  assert.deepEqual(mismatched.events.map((item) => Array.isArray(item) ? item[0] : item), ['deferred']);
  assert.deepEqual(tombstoned.events.map((item) => Array.isArray(item) ? item[0] : item), ['deferred']);
});

test('ack failure preserves completed-ack-pending and never pumps execution', () => {
  const state = {
    currentQueueId: 'QUEUE-A',
    completedAckPendingQueueIds: {'QUEUE-A': true},
  };
  const events = [];
  const ackQueueAndContinue = loadAppFunction('ackQueueAndContinue', 'ackAndSkipQueuedCommand', {
    state,
    ackQueuedCommands: (_ids, done) => done({ok: false, message: 'disk busy'}),
    refreshQueue: () => events.push('refresh'),
    drainNextQueuedAction: () => events.push('drain'),
    window: {CodexPanel: {setStatus: () => events.push('status')}},
  });

  ackQueueAndContinue('QUEUE-A');

  assert.equal(state.completedAckPendingQueueIds['QUEUE-A'], true);
  assert.deepEqual(events, ['status']);
});

test('ack success clears completed marker before queue refresh and drain', () => {
  const state = {
    currentQueueId: 'QUEUE-A',
    completedAckPendingQueueIds: {'QUEUE-A': true},
  };
  const events = [];
  const ackQueueAndContinue = loadAppFunction('ackQueueAndContinue', 'ackAndSkipQueuedCommand', {
    state,
    ackQueuedCommands: (_ids, done) => done({ok: true, removed: 1}),
    refreshQueue: () => events.push('refresh'),
    drainNextQueuedAction: () => events.push('drain'),
    window: {CodexPanel: {setStatus: () => events.push('status')}},
  });

  ackQueueAndContinue('QUEUE-A');

  assert.equal(Object.hasOwn(state.completedAckPendingQueueIds, 'QUEUE-A'), false);
  assert.deepEqual(events, ['refresh', 'drain']);
});

test('empty queued goal is failed through shared policy without acknowledgement', () => {
  const policyCalls = [];
  const state = {currentQueueId: ''};
  const requestGoalAction = loadAppFunction('requestGoalAction', 'requestDraftAction', {
    state,
    generationLifecycleUnavailableReason: () => '',
    deferQueuedGenerationForLifecycle: () => assert.fail('lifecycle is available'),
    addMessage: () => {},
    goalTextToPayload: () => ({title: '', detail: ''}),
    applyQueuedResultPolicy: (command, result) => policyCalls.push({command, result}),
    ackQueueAndContinue: () => assert.fail('empty goal must not be acknowledged'),
  });

  requestGoalAction('', '[queue goal]', 'QUEUE-GOAL', {
    conversationId: 'CONV-A',
    sessionId: 'SESSION-A',
    sessionEpoch: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
  });

  assert.equal(policyCalls.length, 1);
  assert.equal(policyCalls[0].command._queue_id, 'QUEUE-GOAL');
  assert.equal(policyCalls[0].command.rawAction, 'goal_run');
  assert.equal(policyCalls[0].result.ok, false);
  assert.equal(policyCalls[0].result.blocked, 'empty_queued_goal');
});

test('draft persistence failure defers with the draft response instead of generation success', () => {
  const generationResult = {ok: true, cards: [{title: 'A'}]};
  const draftFailure = {ok: false, message: 'draft disk failed'};
  let deferredResult = null;
  const applyQueuedResultPolicy = loadAppFunction('applyQueuedResultPolicy', 'saveQueuedWriteForConfirmation', {
    state: {
      conversationId: 'CONV-A',
      sessionId: 'SESSION-A',
      sessionEpoch: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
      contextDocumentKey: 'DOC-A',
      completedAckPendingQueueIds: {},
    },
    window: {
      SourceWorkspaceLifecycle: {
        handleQueuedResult: (options) => options.onDeferred({
          status: 'deferred',
          reason: 'result_failed',
          routing: 'active',
          result: draftFailure,
        }),
      },
    },
    isWriteAction: () => true,
    deferQueuedResult: (_command, result) => { deferredResult = result; },
    persistCompletedQueuedResult: () => assert.fail('failed draft must not persist completion'),
  });

  applyQueuedResultPolicy({_queue_id: 'QUEUE-WRITE'}, generationResult, {});

  assert.equal(deferredResult, draftFailure);
});

test('queued write confirmation resolves only for its bound draft or transaction', () => {
  const state = {
    pendingQueuedWriteConfirmation: {
      queueId: 'QUEUE-WRITE',
      draftId: 'DRAFT-1',
      transactionId: 'TX-1',
    },
  };
  const drains = [];
  const resolveQueuedWriteConfirmation = loadAppFunction(
    'resolveQueuedWriteConfirmation',
    'writeAcceptedDraft',
    {
      state,
      drainNextQueuedAction: () => drains.push('drain'),
    },
  );

  assert.equal(resolveQueuedWriteConfirmation({draftId: 'OTHER'}), false);
  assert.ok(state.pendingQueuedWriteConfirmation);
  assert.equal(resolveQueuedWriteConfirmation({transactionId: 'TX-1'}), true);
  assert.equal(state.pendingQueuedWriteConfirmation, null);
  assert.deepEqual(drains, ['drain']);
});

test('runQueuedCommand persists A through exact background payload after switching to B', () => {
  const state = payloadState({
    conversationId: 'CONV-B',
    sessionId: 'SESSION-B',
    sessionEpoch: 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
  });
  const companionPayload = loadCompanionPayload(state);
  const exactPayloads = [];
  const acked = [];
  const runQueuedCommand = loadAppFunction('runQueuedCommand', 'drainNextQueuedAction', {
    state,
    window: {SourceWorkspaceLifecycle: lifecycle},
    generationLifecycleUnavailableReason: () => '',
    ackAndSkipQueuedCommand: () => assert.fail('valid bound command must not be skipped'),
    deferNativeQueuedCommand: () => assert.fail('generation command is not native'),
    setContextScope: () => {},
    isQueueableGoalAction: () => true,
    isWriteAction: () => false,
    companionPayload,
    newRequestId: () => 'REQUEST-A',
    postCompanionExactPayload: (payload, done) => {
      exactPayloads.push(payload);
      done({ok: true, reply: 'saved in A'});
    },
    applyQueuedResultPolicy: (command, result, effects) => lifecycle.handleQueuedResult({
      command,
      result,
      activeConversation: state,
      isWriteAction: () => false,
      onActiveChat: effects && effects.onActiveChat,
      onInactiveChat: effects && effects.onInactiveChat,
      onDeferred: () => assert.fail('successful background chat must not defer'),
      onAck: () => acked.push(command._queue_id),
    }),
    ackQueueAndContinue: (queueId) => acked.push(queueId),
    requestGoalAction: () => assert.fail('background result must bypass active rendering path'),
    requestDraftAction: () => assert.fail('background result must bypass active rendering path'),
    requestTextAction: () => assert.fail('background result must bypass active rendering path'),
  });

  runQueuedCommand({
    _queue_id: 'QUEUE-A',
    rawAction: 'chat',
    prompt: 'queued for A',
    conversationId: 'CONV-A',
    sessionId: 'SESSION-A',
    sessionEpoch: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    sourceIds: ['upload:one'],
    sourceWorkspaceRevision: 'REV-A',
  });

  assert.equal(exactPayloads.length, 1);
  assert.equal(exactPayloads[0].conversationId, 'CONV-A');
  assert.equal(exactPayloads[0].sessionId, 'SESSION-A');
  assert.equal(exactPayloads[0].prompt, 'queued for A');
  assert.deepEqual(acked, ['QUEUE-A']);
});

test('stable automatic switch persists three sources and rebuilds in the new document scope', () => {
  const sourceIds = ['upload:one', 'upload:two', 'upload:three'];
  const state = payloadState({testSourceIds: sourceIds.slice()});
  const companionPayload = loadCompanionPayload(state);
  const requests = [];
  let persistedConversation = null;

  function handleCompanion(request) {
    requests.push(JSON.parse(JSON.stringify(request)));
    assert.equal(request.topicid, 'TOPIC-HILTON');
    assert.equal(request.bookmd5, 'BOOK-HILTON');
    assert.equal(request.contextDocumentKey, 'TOPIC-HILTON|BOOK-HILTON|/papers/hilton.pdf');
    assert.equal(Object.hasOwn(request, 'mnObject'), false, request.action);
    assert.equal(Object.hasOwn(request, 'mnObjectId'), false, request.action);

    if (request.action === 'conversation_new') {
      persistedConversation = {
        conversationId: 'CONV-HILTON',
        sessionId: 'SESSION-HILTON',
        topicid: request.topicid,
        bookmd5: request.bookmd5,
        contextDocumentKey: request.contextDocumentKey,
        sourceIds: request.sourceIds.slice(),
        followCurrentDocument: request.followCurrentDocument,
        sourceWorkspaceRevision: '',
      };
      return {ok: true, conversation: persistedConversation};
    }

    assert.ok(persistedConversation, 'conversation must be persisted before source actions');
    assert.equal(request.conversationId, persistedConversation.conversationId);
    assert.equal(request.sessionId, persistedConversation.sessionId);
    if (request.action === 'source_workspace_update') {
      persistedConversation.sourceIds = request.sourceIds.slice();
      persistedConversation.followCurrentDocument = request.followCurrentDocument;
      persistedConversation.sourceWorkspaceRevision = 'REV-HILTON';
      return {ok: true, workspace: {revision: 'REV-HILTON'}};
    }
    if (request.action === 'source_workspace_validate') {
      assert.equal(request.sourceWorkspaceRevision, 'REV-HILTON');
      assert.deepEqual(request.sourceIds, sourceIds);
      return {ok: true, workspace: {ok: true, revision: 'REV-HILTON'}};
    }
    return {ok: true, workspace: {revision: persistedConversation.sourceWorkspaceRevision}};
  }

  const controller = lifecycle.createController();
  const migrationMeta = {
    contextDocumentKey: state.context.contextDocumentKey,
    sourceIds: sourceIds.slice(),
    followCurrentDocument: false,
    currentDocumentIds: ['marginnote:lee'],
  };
  const migrationHandle = controller.beginMigration(migrationMeta).handle;
  const pending = Object.assign({}, migrationMeta, {lifecycleHandle: migrationHandle});
  state.pendingDocumentSwitch = pending;
  state.contextDocumentKey = state.context.contextDocumentKey;

  const completeAutomaticDocumentSwitch = loadAppFunction(
    'completeAutomaticDocumentSwitch',
    'renderContext',
    {
      state,
      sourceWorkspaceLifecycle: controller,
      documentContextReadyForAutomaticSwitch: () => true,
      sourceWorkspaceSelectionMap: (ids) => Object.fromEntries(ids.map((id) => [id, true])),
      resetConversationForDocumentChange: () => {
        state.conversationId = '';
        state.sessionId = '';
      },
      syncSourceWorkspaceLifecycleFlags: () => {},
      updateActionAvailability: () => {},
      requestNewConversation: (done, extra) => {
        const result = handleCompanion(companionPayload('conversation_new', extra));
        done(result, requests[requests.length - 1]);
      },
      cleanupStaleConversation: () => {
        assert.fail('stable migration must not clean up its new conversation');
      },
      setSourceWorkspaceStatus: (tone, message) => {
        assert.fail(`stable migration failed: ${tone} ${message}`);
      },
      addFailureMessage: (message) => {
        assert.fail(`stable migration failed: ${message}`);
      },
      initializeNewConversationState: (conversation) => {
        state.conversationId = conversation.conversationId;
        state.sessionId = conversation.sessionId;
        state.sourceWorkspaceSelection = Object.fromEntries(
          conversation.sourceIds.map((id) => [id, true]),
        );
        state.followCurrentDocument = conversation.followCurrentDocument;
        state.sourceWorkspace.revision = conversation.sourceWorkspaceRevision;
      },
      refreshSourceWorkspace: (selectCurrentByDefault, options) => {
        assert.equal(selectCurrentByDefault, false);
        handleCompanion(companionPayload('source_workspace_get', {
          conversationId: state.conversationId,
        }));
        options.after({ok: true});
      },
      currentDocumentSourceCandidate: () => {
        assert.fail('follow=false must not add the current document');
      },
      saveSourceWorkspaceSelection: (closeAfterSave, done) => {
        assert.equal(closeAfterSave, false);
        const result = handleCompanion(companionPayload('source_workspace_update', {
          conversationId: state.conversationId,
          sourceIds: Object.keys(state.sourceWorkspaceSelection),
          followCurrentDocument: state.followCurrentDocument,
        }));
        state.sourceWorkspace.revision = result.workspace.revision;
        done(result);
      },
      validateSavedSourceWorkspace: (done) => {
        done(handleCompanion(companionPayload('source_workspace_validate', {
          conversationId: state.conversationId,
          sourceIds: Object.keys(state.sourceWorkspaceSelection),
          followCurrentDocument: state.followCurrentDocument,
          sourceWorkspaceRevision: state.sourceWorkspace.revision,
        })));
      },
    },
  );

  completeAutomaticDocumentSwitch(pending);

  assert.deepEqual(
    requests.map((request) => request.action),
    [
      'conversation_new',
      'source_workspace_get',
      'source_workspace_update',
      'source_workspace_validate',
    ],
  );
  assert.deepEqual(persistedConversation.sourceIds, sourceIds);
  assert.equal(persistedConversation.followCurrentDocument, false);
  assert.equal(persistedConversation.contextDocumentKey, state.context.contextDocumentKey);
  assert.equal(controller.isMigrationActive(), false);
});
