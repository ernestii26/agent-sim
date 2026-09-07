# pd_matched pilot — 20 runs per condition, 2026-08-24

The run that established the behavioural effect and the effect size everything since was
sized against (design-log sections 4 and 8). Archived here on 2026-08-26 because it is
not comparable to anything produced after it, and leaving it in `results/pd_matched/`
meant two designs' summaries sitting in one directory distinguished only by timestamp.

Its design differs from the current one on five counts:

- cast of 10, not 5, and the neutrals were fixed rather than rotating (section 15)
- the candidates voted in their own contest, so 2 of 10 ballots were a rival's (section 16)
- P and D were drawn from independent samplers, so the bank-paired P_i/D_i almost never
  met and the within-run trait gap was random (section 13's header)
- personas still carried `leadership_style` and `style.register` (section 17)
- the `threat_check` manipulation check was administered to all eight neutrals — the
  entire electorate — immediately before they voted, on the live agents, because the
  survey fork was silently failing (section 21). Its own numbers are clean; the votes it
  preceded are primed

The `_20260826_0104*` summaries are re-reports of this same data, not new runs.

Results: H1 p = 0.483, H2 p = 0.002, interaction p = 0.007. Superseded by the 10-run
comparison in design-log section 22, which reproduces H2 and the interaction under every
correction at once.
