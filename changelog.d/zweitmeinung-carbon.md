### Changed

- **Second opinions run on Gemini 4 Carbon.** `/zweitmeinung` now defaults to
  `gemini-4-carbon` when the owner asks for a second opinion; Gemini 4 Argon was
  the default until 2026-11-16. Google describes Carbon as its strongest
  reasoning model and Argon as the efficient one, at the same price per token,
  so a second opinion, which runs only on request, gets the stronger reader.
  Argon stays one flag away (`--model gemini-4-argon`) for the case that Carbon
  is not reachable, and the report names the model that ran. The Flash check
  before a code pull request opens is unchanged.
