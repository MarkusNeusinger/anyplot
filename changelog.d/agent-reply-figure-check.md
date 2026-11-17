### Added

- **The chat checks the figures in the assistant's own reply before it goes
  out.** A figure the reply writes in digits must stand in a tool result, the
  session's facts, your own messages, a limit the service states, the plot
  memory, or a plot's notes, code or drawn texts. A reply may round a figure
  to fewer decimals, and may write the value of a tool result, the session,
  your messages or a limit with more zeros (`12.50` for `12.5`); a minus or
  plus it writes before a figure, also in an equation it restates, must match
  the source's. The check reads number shapes only (the marks of every
  language the service writes, numbers beside Chinese, Japanese, Korean, Thai,
  Lao, Khmer and Myanmar text without spaces, full-width digits, percent
  signs, dates, times and scientific notation), so it works for any model. A
  figure spelled out in words is not read, and a token whose marks fit no
  number, such as a version `3.10.1`, stands where a source holds the same
  token and is otherwise only counted. The check ships counting only
  (`AGENT_NUMBER_PROVENANCE=log`, the default): each reply that states a
  figure leaves a line with the verdict and counts, never a figure or a word,
  and no reply is changed, asked for again or withheld. That shows on real
  replies what the stricter mode would do before it is switched on. With
  `enforce`, when a turn ran no tool and its reply states a figure no source
  holds, the assistant is asked once more to compute it with a tool, give it
  as its source writes it, or say it is not known; a reply that still states
  such a figure is withheld, and the page says so with a next step
  (`error{code:"unverified_figure"}`). A turn that ran a tool and was not
  asked again is only logged, and the new replies of the language and length
  re-asks may add no unsourced figure where the check enforces. `off` switches
  the check off, and the turn record names it as `number_provenance`. The prep eval counts the check's verdicts and has nine
  new cases for it, which run only when you name their tag
  (`--tags figures`); both eval harnesses count a withheld reply as the
  model's miss, never as an outage. (#13145)
