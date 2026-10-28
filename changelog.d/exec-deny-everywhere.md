### Security

- **Every in-process run requires the harness's exec filter.** The seccomp filter
  that has the kernel refuse every program start was required for lets-plot alone;
  a lets-plot render in the live chat showed that Cloud Run's sandbox admits it, so
  the renderer and the local backend now require it for every render, data run and
  conversion. A run whose filter is not in place stops before its code starts: a
  data run reports that the fault is not the code's, and a conversion answers
  `503 convert_unavailable`. `RENDERER_EXEC_DENY=optional` lifts the requirement
  without a code change, should the platform stop admitting the filter. (#12414)
