# Every crawler is welcome, and one is blocked only on evidence

- Date: 2026-11-09
- Proposed: robots.txt declined Bytespider, and a Cloudflare rule blocked Bytespider and
  TikTokSpider.
- Decided: every crawler is welcome, and the block rule was deleted the same night. Blocking returns
  only on evidence from the request logs. On 2026-11-12, after a second opinion on a first plan that
  served every verified bot, he chose the design by which a crawler that Cloudflare verified gets the
  prerendered page when its category is one that reads content.
- Where: #12868, #13073, `docs/reference/seo.md`
