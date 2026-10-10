import { describe, expect, it } from 'vitest';

import { MAX_SSE_LINE_CHARS, readSseEvents, SseParser, SseStreamError } from 'src/lib/sse';

/** A response body that delivers `chunks` (strings or raw bytes) one read at a time. */
function bodyOf(chunks: (string | Uint8Array)[], { close = true } = {}) {
  const encoder = new TextEncoder();
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(typeof chunk === 'string' ? encoder.encode(chunk) : chunk);
      }
      if (close) controller.close();
    },
  });
}

async function collect(body: ReadableStream<Uint8Array>, signal?: AbortSignal) {
  const events = [];
  for await (const event of readSseEvents(body, signal)) events.push(event);
  return events;
}

describe('SseParser', () => {
  it('assembles an event from its fields and dispatches it on the blank line', () => {
    const parser = new SseParser();
    expect(parser.feed('event: status\ndata: {"step":"adapting"}\n')).toEqual([]);
    expect(parser.feed('\n')).toEqual([{ event: 'status', data: '{"step":"adapting"}' }]);
  });

  it('joins several data lines with a line feed and defaults the type to message', () => {
    const parser = new SseParser();
    expect(parser.feed('data: one\ndata: two\n\n')).toEqual([
      { event: 'message', data: 'one\ntwo' },
    ]);
  });

  it('ignores comments (pings), id and retry fields, and events without data', () => {
    const parser = new SseParser();
    const events = parser.feed(
      ': ping\n\nid: 7\nretry: 1000\nevent: done\n\nevent: ready\ndata: {}\n\n'
    );
    expect(events).toEqual([{ event: 'ready', data: '{}' }]);
  });

  it('accepts CRLF and lone CR line endings, including a CRLF split across chunks', () => {
    const parser = new SseParser();
    expect(parser.feed('event: a\r\ndata: 1\r')).toEqual([]);
    expect(parser.feed('\n\r\n')).toEqual([{ event: 'a', data: '1' }]);
    expect(parser.feed('event: b\rdata: 2\r\r')).toEqual([]);
    expect(parser.end()).toEqual([{ event: 'b', data: '2' }]);
  });

  it('removes exactly one space after the colon and keeps a field without a colon', () => {
    const parser = new SseParser();
    expect(parser.feed('data:  two spaces\ndata\n\n')).toEqual([
      { event: 'message', data: ' two spaces\n' },
    ]);
  });

  it('drops an unfinished event when the stream ends', () => {
    const parser = new SseParser();
    parser.feed('event: plot\ndata: {"status":"ok"}\n');
    expect(parser.end()).toEqual([]);
  });

  it('refuses a line that never ends', () => {
    const parser = new SseParser();
    expect(() => parser.feed('data: ' + 'x'.repeat(MAX_SSE_LINE_CHARS + 1))).toThrow(
      SseStreamError
    );
  });

  it('refuses an oversized line even when its newline arrives in the same chunk', () => {
    const parser = new SseParser();
    const oversized = 'data: ' + 'x'.repeat(MAX_SSE_LINE_CHARS + 1) + '\n\n';
    expect(() => parser.feed(oversized)).toThrow(SseStreamError);
  });

  it('accepts a line at exactly the limit', () => {
    const parser = new SseParser();
    const line = 'data: ' + 'x'.repeat(MAX_SSE_LINE_CHARS - 'data: '.length);
    expect(parser.feed(line + '\n\n')).toHaveLength(1);
  });
});

describe('readSseEvents', () => {
  it('reads events split anywhere across chunks, pings in between', async () => {
    const wire =
      'event: ready\ndata: {"v":"anyplot/1","run_id":"r1"}\n\n: ping\n\n' +
      'event: status\ndata: {"step":"queued","position":2,"waiting":3}\n\n' +
      'event: done\ndata: {"llm_calls":4,"tokens":10}\n\n';
    const chunks = wire.match(/[\s\S]{1,7}/g) ?? [];
    const events = await collect(bodyOf(chunks));
    expect(events.map(event => event.event)).toEqual(['ready', 'status', 'done']);
    expect(JSON.parse(events[1].data)).toEqual({ step: 'queued', position: 2, waiting: 3 });
  });

  it('decodes a multi-byte character split between two reads', async () => {
    const bytes = new TextEncoder().encode('event: message\ndata: {"text":"Grüße"}\n\n');
    const split = bytes.indexOf(0xc3) + 1; // inside the two-byte "ü"
    const events = await collect(bodyOf([bytes.slice(0, split), bytes.slice(split)]));
    expect(JSON.parse(events[0].data)).toEqual({ text: 'Grüße' });
  });

  it('rejects with an AbortError when the signal aborts a stream that stays open', async () => {
    const controller = new AbortController();
    const body = bodyOf(['event: ready\ndata: {}\n\n'], { close: false });
    const seen: string[] = [];
    const reading = (async () => {
      for await (const event of readSseEvents(body, controller.signal)) {
        seen.push(event.event);
        controller.abort();
      }
    })();
    await expect(reading).rejects.toMatchObject({ name: 'AbortError' });
    expect(seen).toEqual(['ready']);
  });
});
