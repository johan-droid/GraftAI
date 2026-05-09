import { test } from 'node:test';
import assert from 'node:assert';
import { convertSlotToTimezone } from './timezone.ts';
import type { TimeSlot } from './compute';

test('convertSlotToTimezone - basic conversion UTC to America/New_York (EST)', () => {
  const slot: TimeSlot = {
    start: new Date('2024-01-01T12:00:00Z'),
    end: new Date('2024-01-01T13:00:00Z'),
  };

  const converted = convertSlotToTimezone(slot, 'UTC', 'America/New_York');

  assert.strictEqual(converted.start.toISOString(), '2024-01-01T17:00:00.000Z');
  assert.strictEqual(converted.end.toISOString(), '2024-01-01T18:00:00.000Z');
});

test('convertSlotToTimezone - same timezone conversion', () => {
  const slot: TimeSlot = {
    start: new Date('2024-05-01T10:00:00Z'),
    end: new Date('2024-05-01T11:00:00Z'),
  };

  const converted = convertSlotToTimezone(slot, 'UTC', 'UTC');

  assert.strictEqual(converted.start.toISOString(), slot.start.toISOString());
  assert.strictEqual(converted.end.toISOString(), slot.end.toISOString());
});

test('convertSlotToTimezone - conversion across DST (EST to EDT)', () => {
  const slot: TimeSlot = {
    start: new Date('2024-03-10T01:00:00Z'),
    end: new Date('2024-03-10T02:00:00Z'),
  };

  const converted = convertSlotToTimezone(slot, 'UTC', 'America/New_York');
  assert.strictEqual(converted.start.toISOString(), '2024-03-10T06:00:00.000Z');

  const slotAfter: TimeSlot = {
    start: new Date('2024-03-10T12:00:00Z'),
    end: new Date('2024-03-10T13:00:00Z'),
  };
  const convertedAfter = convertSlotToTimezone(slotAfter, 'UTC', 'America/New_York');
  assert.strictEqual(convertedAfter.start.toISOString(), '2024-03-10T16:00:00.000Z');
});

test('convertSlotToTimezone - day shift conversion', () => {
  const slot: TimeSlot = {
    start: new Date('2024-01-01T23:00:00Z'),
    end: new Date('2024-01-02T00:00:00Z'),
  };

  const converted = convertSlotToTimezone(slot, 'UTC', 'Asia/Tokyo');

  assert.strictEqual(converted.start.toISOString(), '2024-01-01T14:00:00.000Z');
  assert.strictEqual(converted.end.toISOString(), '2024-01-01T15:00:00.000Z');
});

test('convertSlotToTimezone - complex fromTz to toTz (BST to EDT)', () => {
    // July 1, 2024: London is BST (UTC+1), NY is EDT (UTC-4)
    // Wall clock 10:00 in London (BST) is 09:00 UTC
    const slot: TimeSlot = {
        start: new Date('2024-07-01T09:00:00Z'),
        end: new Date('2024-07-01T10:00:00Z'),
    };

    // Convert from London wall clock 10:00 to NY wall clock 10:00
    // NY wall clock 10:00 in July is 14:00 UTC
    const converted = convertSlotToTimezone(slot, 'Europe/London', 'America/New_York');
    assert.strictEqual(converted.start.toISOString(), '2024-07-01T14:00:00.000Z');
});
