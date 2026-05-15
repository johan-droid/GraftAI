import { test, mock } from 'node:test';
import assert from 'node:assert';
import { parseJsonSafe } from './json-utils.ts';

test('parseJsonSafe - valid JSON', () => {
  const input = '{"key": "value"}';
  const result = parseJsonSafe(input);
  assert.deepStrictEqual(result, { key: 'value' });
});

test('parseJsonSafe - empty string', () => {
  const result = parseJsonSafe('');
  assert.deepStrictEqual(result, {});
});

test('parseJsonSafe - malformed JSON', () => {
  const warnMock = mock.method(console, 'warn', () => {});
  const input = 'invalid json';
  const result = parseJsonSafe(input, 500);

  assert.deepStrictEqual(result, { __raw_text: 'invalid json' });
  assert.strictEqual(warnMock.mock.callCount(), 1);

  const call = warnMock.mock.calls[0];
  assert.strictEqual(call.arguments[0], '[API] Failed to parse JSON response (Status: 500):');
  assert.strictEqual(call.arguments[1].preview, 'invalid json');

  warnMock.mock.restore();
});

test('parseJsonSafe - long malformed JSON truncation', () => {
  const warnMock = mock.method(console, 'warn', () => {});
  const longInput = 'a'.repeat(500);
  const result = parseJsonSafe(longInput);

  const expectedPreview = 'a'.repeat(400) + '...';
  assert.deepStrictEqual(result, { __raw_text: expectedPreview });
  assert.strictEqual(warnMock.mock.calls[0].arguments[1].preview, expectedPreview);

  warnMock.mock.restore();
});
