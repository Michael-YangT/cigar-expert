# Data Sources / 数据源手册

Seven candidate sites were assessed by fetching them and inspecting real pages.
The verdicts below are what the fetches showed, not reputation.

## Recommended

### Cigar Century — cigarcentury.com

Primary source for cigar specifications. Around 19,191 English product records.

Each record provides origin, manufacturer, wrapper, binder, filler, vitola,
box-pressed flag, flavours, length, ring gauge, colour, strength, and separate
specialised and user ratings. That set of fields repairs several gaps in a typical
ledger at once.

- Faceted by country, rating band, price band, strength, flavour, vitola and wrapper
- Stable URLs: `/en/cigars/<brand>-<line>-<vitola>`, `/en/brand/<slug>`, `/en/country/<slug>`
- `robots.txt` permits the site and its sitemap
- **No usable search endpoint** — `?s=` returns the homepage, `?page=` is ignored.
  Use the index built by `scripts/build_index.py`
- Brand pages list only ~12 products before paginating, so they are not a
  complete substitute for the sitemap index

Known weakness: many records carry no rating at all, so absence of a score means
nothing rather than meaning low quality.

### Cigar Capitol — cigarcapitol.com

Highest content quality of the seven. A reference work rather than a review site,
and explicit that this is deliberate. Every record carries a confidence level —
verified, reported or estimated — and undisclosed blend components are marked as
undisclosed rather than guessed. That discipline matches this skill's refusal to
guess.

- Dictionary: 329 terms in 11 categories, each with pronunciation, definition,
  why it matters, a real usage sentence and related terms
- Tobacco Atlas: 26 growing regions covering soil, elevation, seed and how the
  leaf behaves
- Also city histories, a brand/factory encyclopedia, and a 90-cigar catalog
- URLs need a trailing slash: `/dictionary/<slug>/`
- The index page lists every term with a short gloss, so full discoveries take
  one request — `scripts/fetch_capitol.py` works that way rather than walking a
  hardcoded slug list

Terms are spread across categories in a way that defeats guessing. Six of the
eleven carry exactly what this skill answers, and all 183 are cached locally:

| Category | Terms | Answers |
|---|---|---|
| Storage & Aging | 19 | humidity, beetles, calibration, storage failures |
| Growing & Terroir | 33 | why a region's leaf behaves as it does |
| Tobacco & Leaf | 39 | wrapper varieties, decided by fermentation level |
| Production & Curing | 36 | fermentation stages, including Plume vs Mold |
| Anatomy | 36 | wrapper / binder / filler / priming grades |
| Flavor & Tasting | 20 | strength, body, finish, pairing |

`Plume vs Mold` sits under Production & Curing, **not** Storage & Aging. Fetching
only the latter silently loses the most-asked storage question, which is exactly
the failure the discovery-driven fetch now avoids.

All 329 terms, including the five uncovered categories, are indexed offline in
`capitol-index.md`. This is the offline backbone.

### Cigar Aficionado — cigaraficionado.com

The most authoritative scoring in the industry, on a 100-point scale with blind
tastings. Also the annual Top 25 and Cigar of the Week.

- Rating URLs follow `/ratings/<id>/name/<slug>` and fetch cleanly
- Content skews to new releases and lifestyle features, so coverage of older or
  obscure lines is thin

Use it for scores and tasting notes, not for basic specifications.

### 雪茄 123 — xuejia123.com

The only Chinese-language source here, and the only one covering domestic Chinese
brands. Declared coverage: 27 Cuban brands / 264 vitolas, 28 non-Cuban brands /
212 vitolas, 4 domestic brands / 105 vitolas, a 1,224-entry scoring archive across
three publications, and a 577-entry limited-edition chronicle from 1960 onwards.

Also carries the most practical authentication material available — box seals,
barcode checks, and cut-open comparisons.

**Filtering is mandatory.** The same pages mix in large volumes of SEO filler
("XX 雪茄 2026 价格走势分析", "抖音热销爆款榜单"). Treat only the encyclopaedia,
chronicle and authentication sections as reference material.

Treat it as the authority for domestic brands specifically.

### halfwheel — halfwheel.com

Daily industry news: releases, set pricing, regional editions, festivals, plus a
weekly roundup.

Use it for what is new and what things cost at retail announcement. It is not a
specification database and should not be used for one.

## Restricted

### Cigar Sense — cigarsense.com

Deliberately does not rate cigars. Builds a sensory profile instead, using an
ISO-based method and a trained panel, then recommends against that profile.

The approach is sound and the reasoning is published openly, but the useful part
is gated. Only articles are public; taste mapping needs an account.

Fine to draw on for tasting methodology. Not usable as a queryable data source.

## Rejected

### Cigar Directory — cigar.directory

Do not use. Two defects found directly:

- Its top-ranked list is tied at 5.0 across all ten entries, giving no separation
  and therefore no information
- It records a 178 mm cigar as `178"` — the length is printed in inches

Fewer fields than Cigar Century and lower reliability. Adding it to the source
set risks writing wrong values into a ledger, so it is excluded.
