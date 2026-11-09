### Removed

- **The nginx user-agent entry for the Windows 10 Chrome crawler farm.** The `$is_headless_client` entry
  from #12860 matched Windows 10 Chrome 100 to 139 and answered those clients' Plausible events with an
  empty `202`. The farm moved to Chrome 148 to 150 on Windows and macOS the same day, so the entry caught
  14 events all day, while it kept dropping the events of about 1.8 % of real visits, people on a pinned
  old Chrome. The Cloudflare Managed Challenge for four hosting-network ASNs (Tencent, Leaseweb, Huawei
  Cloud) is the one mechanism against the farm now, and a person it catches sees the challenge and can
  pass it; `infra/cloudflare/README.md` records it as applied. `app/nginx.conf` holds no entry that
  matches a browser's user agent, and a unit test fails if one comes back. (#13033)
