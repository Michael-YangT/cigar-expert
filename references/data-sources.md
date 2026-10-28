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
- Tobacco Atlas: 33 growing regions covering soil, elevation, seed and how the
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

The most authoritative scoring in the industry, on a 100-point scale from blind
panel tastings. Also the annual Top 25 and Cigar of the Week.

A rating page yields score, length, ring gauge, strength, wrapper / binder /
filler, country, the panel's tasting note, and earlier review scores for the same
cigar — the last being the most useful part, since scores drift across release
years.

- Rating URLs follow `/ratings/<id>/name/<slug>` and fetch cleanly
- Content skews to new releases and lifestyle features, so coverage of older or
  obscure lines is thin

**Constraints are real, and `fetch_rating.py` is built around them.**

- `robots.txt` disallows `/search` and `/ratings/search*`, and lists several AI
  user-agents as disallowed outright. So this is a **single-page tool**: one URL
  per invocation, never a crawl, never a sitemap walk.
- There is no local index of their IDs. Find a URL with an ordinary web search —
  `site:cigaraficionado.com/ratings <brand> <model>` — which costs one request
  instead of thousands.
- Every rating page prints an MSRP. It is stripped before output, along the same
  line as `lookup.py`, because this skill gives no commercial guidance.

Use it for scores and tasting notes, not for basic specifications.

### 雪茄 123 — xuejia123.com

The only Chinese-language source here, and the only one covering domestic Chinese
brands. Declared coverage: 27 Cuban brands / 264 vitolas, 28 non-Cuban brands /
212 vitolas, 4 domestic brands / 105 vitolas, a 1,224-entry scoring archive across
three publications, and a 577-entry limited-edition chronicle from 1960 onwards.

Also carries the most practical authentication material available — box seals,
barcode checks, and cut-open comparisons.

**Verified structure.** `fetch_domestic.py --build-index` walks 雪茄数据库 and
returns 1,767 detail pages in three sections — 国产 143, 古巴 1,084, 非古 540 —
discovered from 156 listing pages. The three section landing pages link only a
fraction of that; reaching the rest requires walking parent directories upward
from the pages already in hand, which is what the script does.

Detail pages are markedly better structured than most reference sites. Each gives
品牌, 系列, 工艺, 尺寸, 浓度, 包装, 产地, then free-text 原料配方, 风味品鉴 and
综合评价 blocks. The 尺寸 line packs length in mm, ring gauge, vitola name and
smoking time into one string, so `fetch_domestic.py --detail` splits those out
separately — which is precisely what makes it usable for identifying a cigar
whose label has been lost.

**Filtering is mandatory.** The same pages mix in large volumes of SEO filler
("XX 雪茄 2026 价格走势分析", "抖音热销爆款榜单"). Treat only the encyclopaedia,
chronicle and authentication sections as reference material.

Treat it as the authority for domestic brands specifically. Cigar Century holds no
Chinese domestic models at all, so for 长城、黄鹤楼、王冠、泰山 this is not a
fallback — it is the only source.

### halfwheel — halfwheel.com

Daily industry news: releases, set pricing, regional editions, festivals, plus a
weekly roundup. New lines surface here weeks or months ahead of any database, so
it answers "does this cigar exist?" when every catalogue lookup comes back empty.

Use it for what is new. It is not a specification database and should not be used
for one, and its retail prices are not relayed by this skill.

**Every script request is blocked.** The site sits behind a Cloudflare managed
challenge: `/`, `/feed/`, `/wp-json/`, `/sitemap_index.xml` and `/robots.txt` all
return 403 to plain HTTP clients, with or without browser-grade headers. No amount
of header tuning fixes this, and retrying only gets the address noticed.

The workable path is the built-in web-fetch tool, which reaches it fine, against
these stable URLs:

- `https://halfwheel.com/` — latest posts
- `https://halfwheel.com/date/YYYY/MM/DD/` — everything published that day
- `https://halfwheel.com/<post-slug>/<post-id>/` — one article
- `https://halfwheel.com/?s=<term>` — site search, browser only

Browse the date archive rather than searching: posts all carry a stable `/date/`
path, so an archive page answers "what appeared this week" in one request.

`fetch_news.py` encodes exactly this. It tries once, detects the challenge, and
returns `status: blocked` with these patterns attached. Treat that output as the
answer, not as something to retry past. Cached pages are not shipped, since
news ceases to be news.

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
