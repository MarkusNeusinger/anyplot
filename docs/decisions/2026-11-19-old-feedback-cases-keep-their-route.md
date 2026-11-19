# A feedback case from before the new consent wording replays only where its sender was told

- Date: 2026-11-19
- Proposed: a visitor's feedback case, data file included, can be replayed in a test run on any
  model. Until 2026-11-18 the site named only Claude through Vertex AI in the EU and said a case is
  stored for the operator to read; since then it says cases are also read with AI coding assistants
  and in tests with other AI models. The options were a guard in the test harness with a cut-off at
  the change of wording, or no guard.
- Decided: the guard with the cut-off. A case sent before 2026-11-19 00:00 UTC replays only on Claude
  through Vertex AI in the EU; later cases and his own run anywhere. The same day he set its limit:
  the privacy rules must not grow beyond stopping an accident, so no rule guards against his own
  deliberate acts, none covers local copies, and none keeps a coding assistant from files on his
  machine.
- Where: #13200
