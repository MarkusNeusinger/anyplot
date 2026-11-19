# People may plot their own personal data, and refusals come in every supported language

- Date: 2026-10-10
- Proposed: the chat's first guardrails had a contact filter, for which a name, an address, an
  e-mail address, a phone number or a web address could be a reason to refuse. A guardrail audit
  of 2026-10-10 went through them.
- Decided: personal data is allowed in data, plots and chat, and the contact filter is removed; the
  pull request refuses advertisements, calls to action and messages to other people by intent
  instead. Refusals come in every supported language. The design names the reason: users plot their
  own tax returns, contact lists and customer tables.
- Where: #12126, `docs/concepts/agent-network.md` ("ScopeGuard")
