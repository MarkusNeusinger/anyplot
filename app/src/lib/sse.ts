/**
 * Server-sent events over `fetch`.
 *
 * `EventSource` cannot POST, send the CSRF header, or carry the admin token,
 * so the agent chat reads its stream from `fetchWithAuth(...).body.getReader()`
 * and assembles events here, following the WHATWG event-stream rules:
 *
 * - lines end in LF, CRLF or a lone CR, and a chunk may split anywhere,
 *   including inside a CRLF pair or a multi-byte UTF-8 character;
 * - a line starting with `:` is a comment — the BFF's `: ping` keep-alives —
 *   and is ignored;
 * - `event:` sets the type, every `data:` line appends to the data (joined with
 *   LF), `id:` and `retry:` are ignored (the chat never reconnects);
 * - a blank line dispatches the event; an event without data is dropped, and
 *   so is an unfinished event when the stream ends.
 *
 * The parser knows nothing about the agent protocol; `src/lib/agent.ts` types
 * the events of `anyplot/1`.
 */

export interface SseEvent {
  /** The `event:` field, `message` when the event named none. */
  event: string;
  /** The `data:` lines joined with LF. */
  data: string;
}

/** A line longer than this without a terminator is a broken stream, not an event. */
export const MAX_SSE_LINE_CHARS = 1024 * 1024;

export class SseStreamError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SseStreamError';
  }
}

/** Incremental event-stream parser: feed decoded text, get complete events back. */
export class SseParser {
  private buffer = '';
  private eventType = '';
  private dataLines: string[] = [];
  private hasData = false;

  /** Parse one chunk of decoded text; returns the events it completed. */
  feed(chunk: string): SseEvent[] {
    this.buffer += chunk;
    const events: SseEvent[] = [];
    let start = 0;
    for (;;) {
      const lf = this.buffer.indexOf('\n', start);
      const cr = this.buffer.indexOf('\r', start);
      if (lf === -1 && cr === -1) break;
      let end: number;
      let next: number;
      if (cr !== -1 && (lf === -1 || cr < lf)) {
        // A CR at the very end may be the first half of a CRLF split across chunks.
        if (cr === this.buffer.length - 1) break;
        end = cr;
        next = this.buffer[cr + 1] === '\n' ? cr + 2 : cr + 1;
      } else {
        end = lf;
        next = lf + 1;
      }
      // The limit holds for a line that ends inside this chunk as well as for the
      // unfinished remainder below; an oversized line is refused before it is parsed.
      if (end - start > MAX_SSE_LINE_CHARS) {
        throw new SseStreamError('event stream line too long');
      }
      const event = this.line(this.buffer.slice(start, end));
      if (event) events.push(event);
      start = next;
    }
    this.buffer = this.buffer.slice(start);
    if (this.buffer.length > MAX_SSE_LINE_CHARS) {
      throw new SseStreamError('event stream line too long');
    }
    return events;
  }

  /** The stream ended: a lone trailing CR still ends its line; an unfinished event is dropped. */
  end(): SseEvent[] {
    const events = this.buffer.endsWith('\r') ? this.feed('\n') : [];
    this.buffer = '';
    this.reset();
    return events;
  }

  private line(line: string): SseEvent | null {
    if (line === '') {
      const event = this.hasData
        ? { event: this.eventType || 'message', data: this.dataLines.join('\n') }
        : null;
      this.reset();
      return event;
    }
    if (line.startsWith(':')) return null;
    const colon = line.indexOf(':');
    const field = colon === -1 ? line : line.slice(0, colon);
    let value = colon === -1 ? '' : line.slice(colon + 1);
    if (value.startsWith(' ')) value = value.slice(1);
    if (field === 'event') {
      this.eventType = value;
    } else if (field === 'data') {
      this.dataLines.push(value);
      this.hasData = true;
    }
    return null;
  }

  private reset(): void {
    this.eventType = '';
    this.dataLines = [];
    this.hasData = false;
  }
}

/**
 * Read every complete event of a streamed response body.
 *
 * Resolves when the stream ends; rejects when it fails or `signal` aborts
 * (the reader is cancelled either way, so the connection closes).
 */
export async function* readSseEvents(
  body: ReadableStream<Uint8Array>,
  signal?: AbortSignal
): AsyncGenerator<SseEvent, void, undefined> {
  const reader = body.getReader();
  const decoder = new TextDecoder('utf-8');
  const parser = new SseParser();
  const onAbort = () => {
    void reader.cancel().catch(() => undefined);
  };
  signal?.addEventListener('abort', onAbort, { once: true });
  try {
    for (;;) {
      if (signal?.aborted) throw new DOMException('The stream was aborted', 'AbortError');
      const { done, value } = await reader.read();
      if (done) break;
      yield* parser.feed(decoder.decode(value, { stream: true }));
    }
    if (signal?.aborted) throw new DOMException('The stream was aborted', 'AbortError');
    yield* parser.feed(decoder.decode());
    yield* parser.end();
  } finally {
    signal?.removeEventListener('abort', onAbort);
    void reader.cancel().catch(() => undefined);
  }
}
