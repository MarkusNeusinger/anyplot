### Fixed

- **A person in Snapchat's in-app browser is no longer treated as a crawler.**
  nginx's crawler map matched the word `snapchat`, which the app's in-app
  browser carries in its user agent as well as Snap's link-preview fetcher: a
  person opening a link inside Snapchat would have got the prerendered page
  instead of the app, and their analytics events would have been dropped. The
  entry now names the fetcher (`Snap URL Preview Service`). The entry `signal`
  is gone: Signal's fetcher signs as WhatsApp, so the word matched no fetcher.
  The site's request log held no such request in the 30 days before, so nobody
  was served the wrong page. The share counter reads Snapchat the same way.
  (#13069)
