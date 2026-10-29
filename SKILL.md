---
name: cigar-expert
version: 1.1.0
display_name: 雪茄顾问
display_name_en: Cigar Expert
agent_created: true
description: This skill should be used when the user asks about premium cigars — looking up a cigar's vitola, ring gauge, strength, wrapper/binder/filler, country or flavour profile; identifying an unknown or partially labelled cigar against a brand catalogue; explaining storage science such as humidity, plume versus mould, beetle risk, calibration or aging windows; assigning cigars to cross-flavour storage groups; or choosing which cigar to smoke now. Triggers include queries in Chinese such as 雪茄, 这支茄, 环径, 强度, 茄衣, 怎么养, 长白毛, 串味, 怎么搭配. It answers in Chinese with the original English name alongside. A second, optional layer reads the user's own ledger if one is configured. Sources are reference sites only, never retailers or price guidance.
description_zh: 查雪茄型号参数，含尺寸、环径、强度与茄衣茄套茄芯；识别认不准或标不全的型号并给出候选与置信度；解释养护科学，含湿度、开花与发霉之别、虫害风险、醒茄与老化窗口；按茄衣气味组分盒；引用权威百分制评分并剔除价格。中文作答，保留英文原名，只引参考站，不给购买建议。
description_en: Look up a cigar's vitola, ring gauge, strength and leaf components; identify an unknown or partially labelled cigar against a brand catalogue; explain storage science such as humidity, plume versus mould, beetle risk and aging windows; assign cigars to cross-flavour storage groups; and cite published 100-point scores. Answers in Chinese while keeping the English name alongside. Reference sites only, with no purchasing or pricing guidance.
---

# Cigar Expert / 雪茄顾问

A reference tool for premium cigars.

Two layers. The general layer answers lookup, storage and flavour-group questions
for anyone. The personal layer is optional and stays inert until a ledger is
configured, so this skill ships with no collection data of its own.

Everything here was validated against real data before it was written. The
matching rules in `references/matching-rules.md` exist because a naive search
was tried first and produced wrong answers on three separate kinds of input.
Do not replace them with a simpler search.

## Before the first answer

```
python3 scripts/check_environment.py
```

It reports one of three states and exits non-zero only when nothing can run:

| State | Meaning | What to do |
|---|---|---|
| `ready` | Indexes and offline references present | Answer normally |
| `partial` | Offline references present, catalogue index missing | Storage, terminology and flavour-group questions still work; run `python3 scripts/build_index.py` before any lookup |
| `needs_setup` | Python too old, or `scripts/` / `references/` incomplete | Stop and follow `references/setup-guide.md` |

`partial` is the common state on a fresh clone, and it is not an error. Do not
report a lookup failure as "this cigar does not exist" while the index is
missing — say the catalogue is not built yet and offer the one command.

`references/setup-guide.md` carries the five reference domains, what each source
needs, and what still works when a source is unreachable.

## Output language

Answer in Chinese, and keep the original English product name next to any
Chinese rendering, because cigar names do not translate cleanly and the English
string is what identifies the cigar in a catalogue.

What that looks like:

- Correct: 「Arturo Fuente Hemingway Classic（海明威经典），Perfecto 型，Cameroon 茄衣」
- Wrong: 「阿图罗·富恩特 海明威」（only Chinese, loses the searchable name）
- Wrong: an English-only answer to a question asked in Chinese

Trade terms such as wrapper / binder / filler also stay bilingual — write
「茄衣（wrapper）」rather than picking one language.

## What this skill does

### Looking up one cigar

Given a brand and a model name, resolve it against the local index first, then
fetch the spec sheet. The index and the three-stage rules are mandatory; see
`references/matching-rules.md` for the reasoning and reproduced failure cases.

```
python3 scripts/lookup.py --brand "奥利瓦 Oliva" --model "Serie V Melanio Robusto"
python3 scripts/lookup.py --url "https://www.cigarcentury.com/en/cigars/<slug>"
```

The first command prints JSON with candidates and a confidence field. The
second prints the resolved spec sheet: origin, manufacturer, wrapper, binder,
filler, vitola, box-pressed flag, flavours, length, ring gauge, colour,
averaged expert and user ratings, and strength.

Read the confidence field and act on it:

| Confidence | What to do |
|---|---|
| `high` | Present the specs directly, cite the URL |
| `review` | Present the candidate but say plainly that the size or some tokens did not match, and list what was missing |
| absent (`no_brand_match`, `no_product_match`) | Say the catalogue has no confident entry. Do **not** substitute a similar product |

If the indexes are missing, build them once:

```
python3 scripts/build_index.py
```

### Chinese domestic cigars — a different route entirely

Cigar Century carries **no** Chinese domestic models, so asking it about 长城,
黄鹤楼, 王冠 or 泰山 returns nothing useful. 雪茄 123 is the only source that
documents them, and it is the primary—not fallback—source for anything Chinese.

```
python3 scripts/fetch_domestic.py --build-index          # once
python3 scripts/fetch_domestic.py --find 长城
python3 scripts/fetch_domestic.py --detail <url>
```

Its detail pages are unusually complete, and map onto the columns a typical
ledger actually wants: 品牌, 系列, 工艺, 尺寸 (length in mm, ring gauge, vitola
name and smoking time in one line), 浓度, 包装, 产地, plus free-text 原料配方 and
风味品鉴 blocks.

Search the local index by Chinese **or** English keyword. Because it holds every
model of a given line with bilingual names, it is the right tool for identifying
a partially labelled cigar — match on ring gauge and length, then present the
few candidates that fit and let the user choose. Do not guess between them.

### Scoring and tasting notes

Blind-panel scores come from Cigar Aficionado, which uses the 100-point scale
everyone quotes. It is corroborating evidence, never the sole answer.

There is no searchable index and the site forbids scripted search, so finding
the page is a separate step. Run the first command below to get the exact query,
run that query with the web-search tool, then hand the URL it returns to the
second command:

```
python3 scripts/fetch_rating.py --find "Tatuaje Cabinet Tainos"
python3 scripts/fetch_rating.py --url https://www.cigaraficionado.com/ratings/<id>/name/<slug>
```

`--find` prints `status: needs_web_search` and a `search_query` of the form
`site:cigaraficionado.com/ratings <brand> <model>`. It performs no request of its
own — do not report a rating off that output alone. `--url` refuses anything that
is not a single rating page, because an index page parses into blank fields that
read like "no score published" instead of "wrong page". One page per request,
never a crawl.

The page yields score, length, ring gauge, strength, wrapper/binder/filler,
country, the panel's tasting note, and any earlier review scores for the same
cigar — the most useful part, since a cigar's score drifts across release years.

**Price is stripped before anything is printed**, because commercial guidance is
out of scope.

### New releases and news

New lines appear on halfwheel weeks or months before any database has them. When
a user asks about a cigar no catalogue recognises, check here before concluding
it does not exist.

```
python3 scripts/fetch_news.py
python3 scripts/fetch_news.py --date 2026/10/27
```

Expect `status: blocked` — halfwheel sits behind a Cloudflare managed challenge
that no script can pass. That is not an error and **must not** be fixed by
retrying. Use the built-in web-fetch tool instead, and browse the stable date
archive rather than the site search:

- `https://halfwheel.com/` — latest
- `https://halfwheel.com/date/YYYY/MM/DD/` — everything published that day

### Answering storage and leaf questions

Cigar Capitol entries are cached locally so these answers work offline. Each
entry carries a definition, why it matters, and a real usage sentence — quote or
paraphrase those rather than inventing phrasing.

`references/capitol-index.md` lists **all 329 terms** the dictionary publishes,
with a one-line gloss and the slug for each. **Search it before answering** —
relevant terms are scattered across categories, so guessing which file holds an
answer is unreliable:

```bash
grep -n -i 'plume\|mold\|beetle' references/capitol-index.md
grep -n -i 'maduro\|oscuro\|wrapper' references/capitol-index.md
```

Full entries are cached for the six categories this skill depends on:

| File | Category | Covers |
|---|---|---|
| `storage-terms.md` | Storage & Aging | 19 — humidity, beetles, calibration, storage failures |
| `terroir.md` | Growing & Terroir | 33 — why a region's leaf behaves as it does |
| `leaf-varieties.md` | Tobacco & Leaf | 39 — wrapper varieties that decide flavour group |
| `production-curing.md` | Production & Curing | 36 — fermentation, including **Plume vs Mold** |
| `anatomy.md` | Anatomy | 36 — wrapper / binder / filler / priming grades |
| `flavour-tasting.md` | Flavor & Tasting | 20 — strength, body, finish |

Note where `Plume vs Mold` lives. It is the most-asked storage question and it
sits under Production & Curing, not Storage & Aging — which is why a
category-scoped cache missed it. The distinction is also decisive: plume brushes
off cleanly and leaves no mark; mould is raised, patchy, stains the leaf and
smells musty.

If a term exists only in the index, fetch it live with the slug shown there:
`https://cigarcapitol.com/dictionary/<slug>/`

One known conflict must be surfaced rather than smoothed over. Sources disagree
on the temperature at which tobacco beetles become active: some guidance cites
**24°C**, while Cigar Capitol states eggs hatch reliably above roughly
**22°C (72°F)**. Mention both figures and attribute each, then let the user
decide which margin to work to. Never silently pick one.

### Assigning a storage flavour group

`references/flavour-groups.md` carries a seven-group scheme — five odour
categories plus two structural groups — with the wrapper-to-group mapping and the
humidity that follows from each group. Its governing insight drives every answer
here: **odour strength follows wrapper fermentation level and origin, not how
strong the cigar tastes when smoked.** A mild-tasting Cuban short-filler is a
strong odour source; many mainstream non-Cuban puros are comparatively clean.

Sorting by wrapper therefore sorts both odour risk and humidity at the same time,
so there is no trade-off to negotiate between the two.

### Working against the personal ledger

This layer is optional and inert until configured, so the published version of
the skill carries no personal data.

If a ledger is configured at the path in `references/personal-ledger.md`, that
file is the authority for anything about quantities, locations or aging windows.
Copy `references/personal-ledger.example.md` to `personal-ledger.md`, fill in
your own path and figures, and the layer switches on. With no `personal-ledger.md`
present, answer general questions only and never assume a collection exists.

When a ledger row is uncertain, produce a candidate list with a confidence
label and let the user decide. Never write to the ledger — this skill only
produces suggestions.

Never quote totals, row counts or holdings from the skill itself. Read them from
the configured ledger, which is always more current.

## Source priority

| Purpose | Use first | Fall back to |
|---|---|---|
| Vitola, ring gauge, strength, leaf components, flavour tags | Cigar Century via `lookup.py` | 雪茄 123 via `fetch_domestic.py` |
| Chinese domestic brands (长城, 黄鹤楼, 王冠, 泰山) | **雪茄 123** | nothing else covers them |
| Terminology, terroir, storage science, city and factory history | Cigar Capitol via cached references | live fetch of one dictionary slug |
| Authoritative 100-point scoring and tasting notes | Cigar Aficionado via `fetch_rating.py` | 雪茄 123 tasting blocks |
| Identifying a partially labelled cigar | cross-check length and ring gauge across both indexes | — |
| New releases, limited and regional editions | halfwheel via the built-in fetch tool | Cigar Aficionado news |

Three of these need a web search to locate a URL: Cigar Aficionado rating pages
cannot be enumerated from here, and neither their robots rules nor common sense
permit scraping one into existence.

**Cigar Directory is not a source.** Its top-ten ranking is all tied at 5.0 with
no separation, and it lists a 178 mm cigar as 178 inches. Its data would
contaminate a ledger. See `references/data-sources.md` for the full assessment
of all seven sites.

## Boundaries

This skill does not do these things, ever:

- **No purchasing advice, retailers, links or price guidance.** Both `lookup.py`
  and `fetch_rating.py` strip price fields for this reason — Cigar Aficionado
  prints an MSRP on every rating page and halfwheel reports official retail
  prices in release coverage. Quote a verdict or a spec; never a price.
  Commercial information is out of scope entirely.
- **No authentication verdicts.** Provide counterfeit criteria and observable
  checks only, never a genuine/fake conclusion on a specific cigar.
- **No writing to the ledger.** Suggestions only, marked with confidence.
- **No guessing a cigar identity.** When matching fails, say it failed. A wrong
  answer written into a personal ledger is worse than no answer.
- **No total counts or quantity arithmetic from memory.** The ledger is the only
  authority for numbers.

Smoking harms health. This is reference material for adults.

## Reference files

| File | Read when |
|---|---|
| `references/matching-rules.md` | Before any catalogue lookup — the three-stage rule and the failures that motivated it |
| `references/capitol-index.md` | **Search first** for any terminology, leaf or production question — all 329 terms with glosses |
| `references/storage-terms.md` | Humidity, beetles, calibration, seasoning, storage failures |
| `references/leaf-varieties.md` | Identifying a wrapper type, deciding fermentation level |
| `references/production-curing.md` | Plume vs mold, fermentation stages, wrapper aging |
| `references/terroir.md` | Why a leaf tastes the way it does, or which region a wrapper came from |
| `references/anatomy.md` | Explaining wrapper / binder / filler / priming fields from a spec sheet |
| `references/flavour-tasting.md` | Strength, body and finish questions, or drink pairing calls |
| `references/flavour-groups.md` | Assigning a storage group, deciding a humidity target |
| `references/data-sources.md` | Assessing which site can answer something, or whether a figure is trustworthy |

Two notes on cost. `capitol-index.md` holds all 329 terms with glosses and is
too large to read whole — grep it, then open only the category file a term
belongs to; each of the six is small enough to read directly. And the 雪茄 123
and Cigar Aficionado routes are live lookups, so prefer the cached Cigar Capitol
files when the question is general enough for them to answer.
