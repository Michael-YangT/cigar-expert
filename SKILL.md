---
name: cigar-expert
description: This skill should be used when the user asks about premium cigars — looking up a cigar's vitola, ring gauge, strength, wrapper/binder/filler, country or flavour profile; identifying an unknown or partially labelled cigar against a brand catalogue; explaining storage science such as humidity, plume versus mould, beetle risk, calibration or aging windows; assigning cigars to cross-flavour storage groups; or choosing which cigar to smoke now. Triggers include queries in Chinese such as 雪茄, 这支茄, 环径, 强度, 茄衣, 怎么养, 长白毛, 串味, 怎么搭配. It answers in Chinese with the original English name alongside. A second, optional layer reads the user's own ledger if one is configured. Sources are reference sites only, never retailers or price guidance.
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

## Output language

Answer in Chinese, and keep the original English product name next to any
Chinese rendering, because cigar names do not translate cleanly and the English
string is what identifies the cigar in a catalogue.

What that looks like:

- Correct: 「Plasencia Alma Fuerte Sixto II Hexagono（六边形），盒压完美型，Nicaraguan 茄芯」
- Wrong: 「普拉森西亚 六边形」（only Chinese, loses the searchable name）
- Wrong: an English-only answer, since the user reads these notes in Chinese

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

### Answering storage and leaf questions

`references/storage-terms.md` and `references/terroir.md` hold Cigar Capitol
entries verbatim so these answers work offline. Each entry has a definition, why
it matters, and a real usage sentence — quote or paraphrase those rather than
inventing phrasing.

One known conflict must be surfaced rather than smoothed over: the user's own
notes say tobacco beetles become active above **24°C**, while Cigar Capitol
states eggs hatch reliably above roughly **22°C (72°F)**. Mention both figures
and their sources. Never silently pick one.

### Assigning a storage flavour group

`references/flavour-groups.md` carries the user's own seven-group scheme — five
odour categories plus two structural groups — with the wrapper-to-group mapping
and the humidity that follows from each group. The governing insight is theirs:
**odour strength follows wrapper fermentation level and origin, not how strong the cigar tastes when smoked.** A mild-tasting Cuban
short-filler is a strong odour source; a medium Davidoff is clean.

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
| Vitola, ring gauge, strength, leaf components, flavour tags | Cigar Century | — |
| Terminology, terroir, storage science, city and factory history | Cigar Capitol | — |
| Authoritative 100-point scoring and tasting notes | Cigar Aficionado | 雪茄 123 scoring archive |
| Chinese-language models including Chinese domestic brands | 雪茄 123 | — |
| New releases, regional editions, official RRP | halfwheel | Cigar Aficionado news |

**Cigar Directory is not a source.** Its top-ten ranking is all tied at 5.0 with
no separation, and it lists a 178 mm cigar as 178 inches. Its data would
contaminate a ledger. See `references/data-sources.md` for the full assessment
of all seven sites.

## Boundaries

This skill does not do these things, ever:

- **No purchasing advice, retailers, links or price guidance.** The `lookup.py`
  script strips price fields from its output for this reason. The user's own
  data policy excludes commercial information.
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
| `references/data-sources.md` | Assessing which site can answer something, or whether a figure is trustworthy |
| `references/flavour-groups.md` | Assigning a storage group, deciding a humidity target |
| `references/storage-terms.md` | Any storage, humidity, mould, beetle or calibration question |
| `references/terroir.md` | Why a leaf tastes the way it does, or which region a wrapper came from |
