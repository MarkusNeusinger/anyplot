### Fixed

- **The plot-code validator refuses native code and raw memory reached through a value.**
  A second opinion of 2026-10-14 found that `np.zeros(1).ctypes._ctypes.CDLL(None)` and
  `type(...).from_address(0)` passed the SECURITY profile, because the private-name rule
  only applies to imported names. The validator now bans `ctypes`, `_ctypes`, `cffi`,
  `data_as`, `from_address`, `from_buffer`, `as_strided`, `dump`, `extbuild`,
  `get_rdataset` and `webuse` on any object, and `.to_string()` / `.info()` with a target.
  The catalogue's eligibility is unchanged (285 matplotlib and 287 seaborn files).
