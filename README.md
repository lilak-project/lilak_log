# lilak_log

The log services of the [LILAK Web Portal](https://github.com/lilak-project): records of things
that happened — when, which run, what was attached — rather than the managed lists of
[`lilak_rack`](https://github.com/lilak-project/lilak_rack).

| folder | what |
|---|---|
| `logbook/` | a general-purpose log: date, time, run number, category, tags, files, the parameter sets a run used |
| `parameters/` | parameter sets, kept once and reused: registered (and deduplicated by value hash) through `/api/register`, read as a table |
| `parlib/` | the parsers (`parse`/`render` per format, value and text hashes) — plain Python, no rack in it (`pip install -e parlib`) |
| `seed/` | each service's portal manifest |

Drawn with lilak_rack's frame (`racklist`, aliased as `../../lilak_rack/racklist`) and stored by
its `rackstore` — so the portal's stack needs `lilak_rack` beside this checkout — but installed,
built and versioned on their own. Their tags are their own set too: `capabilities.tags` is
`"log"` in each seed, and a tag box offers only the tags of services in the same group.
