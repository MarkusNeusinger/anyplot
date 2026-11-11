### Fixed

- **The chat no longer repeats a refusal for the next, valid message.** After a
  refused message, the refusal text stayed in the assistant's own context,
  joined to the next message, and the assistant sent the same fixed text
  again for a question the scope check had passed (two of the six typed turns
  right after a refusal in a persona round). The refused turns are now taken
  out of the assistant's request; the session keeps them, so the scope check
  and the count of refusals read what they read before. Behind it, a reply
  check asks the assistant once more when it still answers a passed message
  with a fixed refusal. The turn record names the new check as `root_refusal`
  (`reasked` or `kept`).
