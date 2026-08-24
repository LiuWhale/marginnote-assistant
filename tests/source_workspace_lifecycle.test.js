const test = require('node:test');
const assert = require('node:assert/strict');
const lifecycle = require('../extension/codex.mn.assistant/web/source_workspace_lifecycle.js');

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
