# Matching Rules / 型号匹配规则

How to turn a cigar name into a catalogue record without corrupting a ledger.

## Why these rules are strict

A naive substring search across the 19,191-entry catalogue was tried first and
validated during development against an ordinary multi-row ledger. It scored
apparent "hits" on a majority of rows, but inspection showed many were wrong. The same failures will recur if
matching is loosened.

### Failure 1 — a bare digit hides inside another number

`"黄鹤楼 Huanghelou" + "雪之梦6"` matched `262-allegiance-corona`.

The digit `6` appeared inside `262`. Chinese domestic lines are frequently named
with a version number, so this is not a rare edge case.

**Rule:** digits compare as whole tokens, never as substrings.

### Failure 2 — a shared word crosses brands

`"金特罗 Quintero" + "Brevas"` matched `arturo-fuente-...-brevas-royal-i`.

`brevas` is a vitola name used by many houses. Other repeat offenders:
`robusto`, `toro`, `nica`, ` selección`, `edición`, `reserva`.

**Rule:** the brand must be locked first, and only that brand's own products are
considered afterwards.

### Failure 3 — dropping the size silently changes the cigar

While trying to improve recall, size words were treated as stop words. That
turned `"Macanudo Inspirado Red Robusto"` into `macanudo-inspirado-red-toro` and
`"AJ Fernandez Blend 15 Toro"` into `aj-fernandez-blend-15-robusto`.

The size is part of a cigar's identity. A Robusto and a Toro in the same line
are different products with different dimensions.

**Rule:** size words are identifying tokens. They are never discarded, and a
missing size token downgrades confidence.

## The three stages

All three are mandatory. Skipping any one reintroduces the failures above.

### Stage 1 — lock the brand

Take the brand as written, which may be bilingual (`奥利瓦 Oliva`). Strip the
CJK characters and accents, keeping only `[a-z0-9-]`.

Then require two guards before accepting a brand slug:

- At least **three alphabetic characters** in the slug. This is what stops
  `"Undercrown 10"` from locking onto the brand slug `10`. Catalogues legitimately
  contain numeric brand slugs (`1502`, `1845`, `1875`), so filtering numbers
  outright would break real brands — hence the alphabetic test instead.
- The slug must not be purely generic. Words like `selection`, `reserve`,
  `maduro`, `connecticut` appear as their own entries but carry no brand identity.

If no brand can be locked, stop. Report `no_brand_match` and ask for the Latin
brand spelling.

### Stage 2 — match the product line

Consider only products whose slug begins with `brand-slug-`. Score each by how
many of the requested model tokens appear, **on token boundaries**.

Weight distinguishing tokens above the rest: anything in the size vocabulary
counts double. Prefer the tightest fit — highest score, then fewest extra tokens.

### Stage 3 — verify the size

Check that every size word the user named actually appears. If any is missing,
the result is `size_confirmed: false` and confidence drops to `review`.

Confidence is decided by completeness plus disambiguation, not by raw token
count. One bug worth remembering: an earlier version required simply `score >= 3`,
which let short model names never reach `high` while simultaneously letting
under-specified requests reach it. Both directions were wrong.

The rule now requires that every requested token landed including any size, **and**
that the cigar is pinned down by one of:

1. **an exact match** — the product's own name is exactly the request
2. **uniqueness** — exactly one candidate satisfies the request

Each path covers the other's blind spot:

- Path 1 is why `Serie V Melanio Robusto` stays `high` even though
  `...-melanio-maduro-robusto` and `...-melanio-double-robusto` also satisfy the
  request. Maduro and double-robusto are different cigars, so a superset must not
  outrank what was literally asked for.
- Path 2 is why merely asking for `Oliva Robusto` does **not** get `high`. Every
  robusto in the line satisfies that request, so no single one can be asserted.

Everyday requests where the requested name genuinely does not identify one
product, and where asserting `high` would have named the wrong cigar:

| Request | Would have been asserted | Why it must stay `review` |
|---|---|---|
| Rocky Patel Vintage 1990 Robusto | `vintage-1990-broadleaf-robusto` | four variants also fit, including `2nds` (factory seconds) and `fumas` |
| AJ Fernandez San Lotano Toro | `san-lotano-oval-toro` | nine variants — oval, bull, dominicano, several wrappers |
| Montecristo Espada Guard | `espada-oscuro-guard` | two lines exist — Oscuro and by-Montecristo |
| AJ Fernandez New World Oscuro Toro | `...-oscuro-toro-redondo` | both redondo and gobernador fit

This is also what flags a coverage gap instead of silently accepting a neighbour.
Requesting a release the catalogue does not carry — say `Oliva Serie V Melanio
Edicion Ano 2025 Robusto Extra` when the line stops at 2023 — leaves `2025`,
`robusto` and `extra` unmatched and lands on the nearest sibling vitola, reported
at `review` rather than accepted.

A short model name is not by itself weak. A fully explained request such as
`"Quintero Brevas"` earns `high` even though its scores are small, because every
token landed and nothing was added.

## Interpreting the result

| Status | Meaning | Action |
|---|---|---|
| `high` | Every requested token landed, the size verified, and either an exact name match or a unique candidate | Present the specs |
| `review` | Matched, but a token is missing, the size did not verify, or several candidates satisfy the request equally | Present it labelled as unconfirmed; say which condition failed and list the rivals |
| `no_brand_match` | Brand could not be locked | Ask for the Latin brand name |
| `no_product_match` | Brand locked, nothing underneath it fits | Say the catalogue lacks an entry — do not substitute |

`lookup.py` always prints several candidates, not one. When two entries satisfy
the request — `rocky-patel-vintage-1990-broadleaf-robusto` against
`rocky-patel-2nds-vintage-maduro-1990-robusto`, for example — nothing in the
request distinguishes them, so ask rather than choosing.

## Known catalogue gaps

These absences are properties of the catalogue, not bugs in the matcher. Expect
`no_product_match` rather than forcing a substitute:

- **Cohiba Wide Short** — the catalogue holds 119 Cohiba entries but not this one
- **Guantanamera Coronas Tubo Gold Edition** — only 5 Guantanamera entries exist
- **Chinese domestic lines** (长城, 黄鹤楼) — not in this catalogue at all;
  use 雪茄 123 for domestic brands

Recent releases lag the market, so absence is expected for anything post-2023.

## Implementation notes

The index builds from the sitemap declared in `robots.txt`, which opens with a
blank `Disallow:` followed by `Allow: /`, and restricts only `/es/ajax`,
`/en/ajax` and `/scripts/`. That makes this approach permitted rather than merely
possible.

The catalogue has no usable keyword search endpoint — `?s=` returns the
homepage, and `?page=` is ignored — which is why every page is approached through
the sitemap-derived index instead of through search.

Product pages carry their specs as `<div class="nombre">label</div>` followed by
`<div class="valor">value</div>`. Strength is the exception: its value lives in
the `title` attribute of a star-rating input. `parse_detail()` in `lookup.py`
handles both.
