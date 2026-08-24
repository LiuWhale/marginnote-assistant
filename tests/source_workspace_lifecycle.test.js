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
