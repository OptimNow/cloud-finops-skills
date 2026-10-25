# Fixtures for `get_live_figures`

Saved copies of what OptimToken served, so the test suite runs offline.
Fetched on 2026-10-25 at 09:45 UTC from <https://optimtoken.optimnow.io>:

- `savings-plans-vs-reserved-instances.json`, `arm-against-x86.json`,
  `batch-api-economics.json`: each guide's `figures.json`, byte for byte.
- `llms.txt`: an excerpt of <https://optimtoken.optimnow.io/llms.txt>, the
  title block, the three "Figures as JSON" guide lines and two guide lines
  without figures (which the parser must skip), copied verbatim.

Refresh them when the envelope changes shape; the figures inside can stay old.
