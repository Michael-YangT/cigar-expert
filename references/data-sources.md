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

## Source grades / 源等级

Every figure this skill reports carries a grade. The grade decides how the answer
is worded, so grade first, then answer.

| 等级 | Covers | Usage |
|---|---|---|
| **A** | A measured field read from a retrieved page — Cigar Century spec fields, Cigar Aficionado panel score and its per-year review table, 雪茄 123 detail pages restricted to the encyclopaedia, chronicle and authentication sections | State as fact. Name the site and the field. |
| **B** | Editorial reference with a declared method or its own confidence label — every Cigar Capitol entry (verified / reported / estimated), Cigar Aficionado tasting notes | State with attribution, and carry the source's own confidence label when it has one. |
| **C** | Opinion, trade commentary or promotional copy — halfwheel commentary and pricing talk, brand press material, the SEO sections of 雪茄 123 | Attribute explicitly ("reportedly", "the retailer claims"). Never state as fact. |
| **D** | Anything not tied to a retrieved page — remembered figures, plausible figures, assumed URLs | Never used, never paraphrased, never "rounded" into an answer. |

Two ways grade collapses, both common:

- **A number nobody fetched is grade D.** If no page was retrieved for it this
  session, it does not exist. Saying it in confident prose does not retrieve it.
- **A URL answering 200 upgrades nothing.** Fetch the page, then grade. See the
  traps below for the case where 200 and absence are identical.

## Conflicting sources / 冲突取舍

Sources disagree often, and the disagreement is usually the interesting part.
Never resolve it by blending. **Averaging two incompatible figures invents a third
figure that no source supports.**

1. **Different grades — take the higher.** The lower one is discarded, not carried
   alongside as balance.
2. **Same grade — give both**, each with its source and its number, and say they
   disagree. Still no midpoint.
3. **When the conflict drives a decision** (a hazard threshold, a discard call),
   act on the more conservative number and say plainly which source it came from
   and why it governs. Presenting both and letting the reader guess is not a
   decision.
4. **If only one of the two affects the answer**, say so and drop the noise.

Worked example already encoded in this skill: beetle risk is given as about 22°C
(72°F) by Cigar Capitol and 24°C by private notes. Both are printed, sources
attached, no midpoint offered. Where the question is what to do, the lower
threshold governs, because acting early costs little and acting late costs a
collection.

## Answering with receipts / 回答必须留痕

Any substantive number, term or criterion traced to a source states four things:

1. **The source** — site name and the field or entry it came from
2. **The grade** — A, B or C
3. **When it was retrieved**, or that it came from the offline cache
4. **Its limits** — a field absent from that source is reported as "not recorded
   there", never as absent, never as low

Forbidden substitutes for attribution: "generally accepted", "widely considered",
"industry standard". If it cannot be sourced, it belongs in grade D and does not
get said.

Lookup confidence returned by the scripts is not decoration — it goes in the
answer. A `review` result that reaches the user described as settled has had its
uncertainty laundered away.

## Known traps / 已知坑

Each of these was found by fetching and comparing real pages, not by reading
documentation. They are listed because guessing avoids none of them.

**A Cigar Capitol URL returning 200 does not mean the term exists.** A slug that
is not in the dictionary falls back to the homepage and answers 200. Two tells,
and use the first one:

1. **The page title is `Cigar Capitol — The archive of cigar civilisation`** —
   the site's own homepage title. Real entries answer with a title of the form
   `Dry-Boxing · Cigar Capitol`. This is the reliable test.
2. **The response is byte-identical to what any invented slug returns.** Compare
   against something known-absent, e.g. `zzz-not-a-term`.

Do not gate on an exact byte count. The homepage is around 111 KB but its size
drifts as its content is edited, so a hardcoded length fails later for no visible
reason. Compare against a fresh control request instead. Confirm every term
against `capitol-index.md` before citing it.

**Missing ratings on Cigar Century are not low ratings.** Many records carry no
score. Absence of a score carries no information.

**A missing Cigar Aficionado URL means it was not found.** There is no local
index of their IDs. When no URL is located, say it was not found rather than
supplying one that looks right.

**`status: blocked` from halfwheel is terminal.** The Cloudflare challenge blocks
all script traffic. Do not retry, do not route through `/?s=`. Use the built-in
fetch tool with the date-archive URLs listed above.

**雪茄 123 mixes SEO filler into the same directory** as its reference material.
Titles of the form "XX 雪茄 2026 价格走势分析" or "抖音热销爆款榜单" are not
reference content.

**A vitola name does not predict dimensions.** Corona and Petit Corona both fail
outright against the bands you would infer from their names. Size is looked up or
measured, never derived from the name — which is why `selection-guide.md` keys off
length × ring gauge rather than vitola labels.
