# The admin's chat is the visitors' page: one page, the same code

- Date: 2026-11-06
- Proposed: the admin had a chat page of his own at `/debug/agent`, apart from the visitors'
  `/agent`.
- Decided: one page for visitors and admins, with the admin's extras behind one menu, so that he
  never misses what a visitor meets. A test renders the page for a visitor, for an admin and for an
  admin viewing as a visitor, and compares them outside an explicit list.
- Where: #12589, `app/src/pages/AgentChatPage.parity.test.tsx`
