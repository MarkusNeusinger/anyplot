### Changed

- **Sum or mean is your choice, not a silent mean.** In the chat of "Use
  with my data", rows that share the plot's key (several amounts per month,
  several scores per hour) were combined into one value each by the mean
  for most plot types, and a line said so afterwards. Two of three test
  users with such data meant the sum, and each needed one more data step
  and one more plot. Where the plot type leaves it open, the assistant now
  asks once, before any plot is made, and the answer decides. Nothing is
  combined or drawn until then, and a wish sent with the plot request is
  kept for that plot. Plot types whose marks add up by what they are, such
  as a pie or a stacked bar, are summed without a question, as before.
