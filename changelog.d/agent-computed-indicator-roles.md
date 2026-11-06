### Fixed

- **Indicator lines the plot can compute no longer take a price column.** The
  SMAs of `indicator-sma`, the EMAs of `indicator-ema` and the Ichimoku lines
  were required roles, so a stock table bound `Open`, `High` and `Low` as the
  three moving averages and the chat had nothing left to compute. They are now
  computed roles like the Bollinger bands: bound when a column clearly holds
  one (`SMA 50`, `Long MA`, `EMA 12`, `Tenkan-sen`, `MACD Signal`), otherwise
  computed by the plot code from the close or the high and low. The same
  holds for every catalogue role with a fixed formula over the spec's other
  roles: the MACD signal line and histogram, the ideal burndown line, a
  climograph's annual mean and total, the total error of a bias-variance
  curve, chain-ladder development factors, Weibull plotting positions, a SHAP
  waterfall's prediction and a decision tree's rollback. A test audits the
  role wording of every spec, so a new role worded as a formula fails until it
  is listed or named as data with the reason. An EMA or weighted average is
  no longer read as a simple moving average. (#12588)
