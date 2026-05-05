import { test } from 'node:test';
import assert from 'node:assert';
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

// Helper to temporarily modify imports for Node.js test execution
const sourceFile = join(import.meta.dirname, 'timezone.ts');
const originalContent = readFileSync(sourceFile, 'utf8');

function setup() {
  const modifiedContent = originalContent.replace(
    'import { TimeSlot } from "./compute";',
    'import type { TimeSlot } from "./compute.ts";'
  );
  writeFileSync(sourceFile, modifiedContent);
}

function teardown() {
  writeFileSync(sourceFile, originalContent);
}

try {
  setup();
  // Now we can import it
  const { convertSlotToTimezone } = await import('./timezone.ts');

  test('convertSlotToTimezone - basic conversion UTC to America/New_York (EST)', () => {
    const slot: any = {
      start: new Date('2024-01-01T12:00:00Z'),
      end: new Date('2024-01-01T13:00:00Z'),
    };

    const converted = convertSlotToTimezone(slot, 'UTC', 'America/New_York');

    assert.strictEqual(converted.start.toISOString(), '2024-01-01T17:00:00.000Z');
    assert.strictEqual(converted.end.toISOString(), '2024-01-01T18:00:00.000Z');
  });

  test('convertSlotToTimezone - same timezone conversion', () => {
    const slot: any = {
      start: new Date('2024-05-01T10:00:00Z'),
      end: new Date('2024-05-01T11:00:00Z'),
    };

    const converted = convertSlotToTimezone(slot, 'UTC', 'UTC');

    assert.strictEqual(converted.start.toISOString(), slot.start.toISOString());
    assert.strictEqual(converted.end.toISOString(), slot.end.toISOString());
  });

  test('convertSlotToTimezone - conversion across DST (EST to EDT)', () => {
    const slot: any = {
      start: new Date('2024-03-10T01:00:00Z'),
      end: new Date('2024-03-10T02:00:00Z'),
    };

    const converted = convertSlotToTimezone(slot, 'UTC', 'America/New_York');
    assert.strictEqual(converted.start.toISOString(), '2024-03-10T06:00:00.000Z');

    const slotAfter: any = {
      start: new Date('2024-03-10T12:00:00Z'),
      end: new Date('2024-03-10T13:00:00Z'),
    };
    const convertedAfter = convertSlotToTimezone(slotAfter, 'UTC', 'America/New_York');
    assert.strictEqual(convertedAfter.start.toISOString(), '2024-03-10T16:00:00.000Z');
  });

  test('convertSlotToTimezone - day shift conversion', () => {
    const slot: any = {
      start: new Date('2024-01-01T23:00:00Z'),
      end: new Date('2024-01-02T00:00:00Z'),
    };

    const converted = convertSlotToTimezone(slot, 'UTC', 'Asia/Tokyo');

    assert.strictEqual(converted.start.toISOString(), '2024-01-01T14:00:00.000Z');
    assert.strictEqual(converted.end.toISOString(), '2024-01-01T15:00:00.000Z');
  });

  test('convertSlotToTimezone - complex fromTz to toTz', () => {
      const slot: any = {
          start: new Date('2024-01-01T10:00:00Z'),
          end: new Date('2024-01-01T11:00:00Z'),
      };

      const converted = convertSlotToTimezone(slot, 'Europe/London', 'America/New_York');
      assert.strictEqual(converted.start.toISOString(), '2024-01-01T15:00:00.000Z');
  });
} finally {
  teardown();
}
