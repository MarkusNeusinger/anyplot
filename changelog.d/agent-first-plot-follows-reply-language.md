### Fixed

- **"Please answer in German" before the first plot gives a German plot.**
  In the chat of "Use with my data", a request for the replies in another
  language also fixed the plot's text to the language it had resolved to,
  English in a new session, even when no plot existed yet. A user who then
  typed a German title got it back translated into English. While the
  session has no plot, such a request now leaves the plot's language open,
  so the first plot follows the reply language. With a plot on the page
  nothing changes: the plot keeps its language until the user asks for its
  text in another one, and a plot language the user chose by itself stays.
