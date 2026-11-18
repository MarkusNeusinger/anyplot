# The admin can plot one table in every library at once, and only the admin

- Date: 2026-10-28
- Proposed: his own request, for his tests: plot the confirmed table in every library of the page at
  once.
- Decided: `.plot_all()` was built so. On 2026-11-01, when a fan-out to 15 libraries took about 20
  minutes behind the public caps, he decided that it stays admin-only, also after the public launch,
  in an admin lane that runs five plots at once.
- Where: #12417, #12507, `docs/concepts/agent-network.md`
