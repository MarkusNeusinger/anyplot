### Changed

- **The agent's adapter may think and answer up to about 50,000 tokens.** In the
  Makie eval matrix, 9 of 139 adapter calls stopped at the old cap of 16,384
  tokens with nothing written: each had spent the whole cap thinking, while the
  finished calls thought up to 14,315 tokens. Each such call cost a repair round.
  The Claude adapter's output cap is now 40,960 tokens for edits and for full
  files, with its 8,192 tokens of thinking room on top (49,152). The Vertex
  client sets its own 300-second timeout, because the Anthropic SDK refuses a
  non-streaming request that large otherwise. An answer that needs fewer tokens
  costs and takes what it did before; the root and the reviewer keep their caps.
