### Added

- **`.example_data()` in the agent chat.** While a session has no data, a line above the composer offers
  `# no data at hand?  .example_data()`, which asks the assistant for a made-up table to try the plot and counts the
  seconds while it works. It is a turn action (`example_data`), not the words "example data": the first typed message
  sets the session language, so typed English would have kept a German visitor in English, while the action leaves
  the language to the visitor's own first message. The assistant's prompt names the new control, the picture of the
  catalogue plot in the header and the columns ⓘ, so it can point visitors to them. (#12553)

### Changed

- **The chat header's columns ⓘ lists the spec's roles.** Opening a session now answers the spec's data roles
  (`POST /sessions` gains `roles`), and the ⓘ after the title names them as the data card's dropdowns do, with
  their kinds and whether a role is optional, takes one column per series or is computed by the plot; the spec's
  `data` bullets remain the fallback. (#12553)
- **The data box names code instead of example data.** Its placeholder now reads "or code that makes data (python,
  javascript, …)" and "or a formula", since `.example_data()` took over example data, and the card's ⓘ says that
  code or a formula that makes data works too, up to 2,000 characters. (#12553)
- **The public chat's notice says less in its line and more behind its ⓘ.** The line is now
  `experimental AI · answers can be wrong`; the ⓘ adds that the chat and the data live only in server memory and are
  deleted after an hour idle, that nothing is saved unless you send feedback, and that Claude runs via Google Cloud
  Vertex AI in the EU and is not trained on what you send, as the legal page says. (#12553)
