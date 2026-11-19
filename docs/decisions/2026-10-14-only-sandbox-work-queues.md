# Only the sandbox work waits in the queue; a chat answer comes at once

- Date: 2026-10-14
- Proposed: every chat turn went through the run queue, which he had set on 2026-10-09 with a rate
  and one render at a time, after spikes showed that one instance serves one sandbox at a time
  safely. In his live test, plain answers and even scope refusals waited about 60 seconds each for
  the queue's rate window.
- Decided: only the sandbox work queues, and per-user message limits bound chat turns instead. His
  note: "bei sowas muss schnell die antwort kommen" (with something like this, the answer has to
  come fast).
- Where: #12175, `docs/concepts/agent-network.md`, `docs/concepts/ai-workflow.md`
