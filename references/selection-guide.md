# Choosing What to Smoke / 选茄

Which cigar, right now, given the time available and the state the cigar is in.

This is a narrowing problem, not a recommending problem. The answer has to end on
a specific cigar the user can actually reach, so the first question is never
"what's good" but "what's here".

## The order is fixed

Four constraints, hardest first. Do not let a soft preference outrank a hard one.

| # | Constraint | Hardness | Why it comes here |
|---|---|---|---|
| 1 | **State** — is it smokable today | Absolute | A wet or just-shipped cigar cannot be fixed by picking a better one |
| 2 | **Time** — how long the user actually has | Physical | Running out of time mid-cigar wastes the whole thing |
| 3 | **Strength** — nicotine load | Physical | Overload ends the session regardless of how good it tasted |
| 4 | **Flavour direction** — what they feel like | Soft | Only decides between cigars that already passed 1–3 |

A user asking "what should I smoke tonight" has answered nothing yet. Time and
palate are both open, and guessing either produces a confident wrong answer.

## Step 1 — read the ledger first, always

If `references/personal-ledger.md` is configured, everything on the ledger
outranks anything from a catalogue. The user owns the cigars; recommending a
purchase when 600 are already resting is not advice.

Filter the ledger in this order: smokable now → matches the time slot → within
the strength ceiling → flavour direction. Report what the ledger filter leaves,
with quantities, and stop. A short honest list of four is better than a broad
list of twenty the user would have to re-filter themselves.

Strength on the ledger is a recorded value, not an estimate — cite it as
recorded. Where the column is blank, say so rather than filling it in from
reputation; `scripts/lookup.py` exists to close exactly those blanks.

## Step 2 — only then reach for the catalogue

With no ledger, or when nothing on it fits, narrow by vitola and verify each
candidate individually. **The catalogue index holds brand and model only — it
carries no strength data.** That means:

- Do not name a cigar's strength from memory or reputation. Fetch the page:
  `python3 scripts/lookup.py --brand "<brand>" --model "<model>"`
  and read the `Strength` field.
- Do not claim to have filtered the catalogue by strength. There is no such
  index. Sizes come from the index; strength comes from a page fetch, one cigar
  at a time.
- If a strength cannot be verified, present the cigar as "strength unconfirmed"
  rather than ranking it.

### Sizing by available time

Ranges rather than point values, because fill, humidity and pace move these by a
good margin. Both dimensions matter: a long thin cigar takes as long as a short
fat one.

| Size | Length × ring | Realistic time | Note |
|---|---|---|---|
| Petit Corona / Half Corona | 4.0–4.5" × 40–44 | 25–35 min | The honest answer for a short break |
| Corona | 5.5–6.0" × 42–44 | 40–55 min | Reference size; flavours read clearest |
| Robusto | 4.9–5.5" × 48–54 | 45–65 min | Short but full-bodied; fits most evenings |
| Toro | 6.0" × 50–54 | 60–80 min | |
| Churchill | 7.0" × 47–50 | 80–110 min | |
| Double Corona | 7.5–8.0" × 49–54 | 110–150 min | Requires a real commitment |
| Panatela / Lancero | 6.0–7.5" × 34–38 | 60–90 min | Thin ring burns hot if rushed |

Rule of thumb: **under 90 minutes available, stay at 54 ring or below and 6
inches or below.** Anything larger will be set down half-smoked.

## Strength ceiling by experience

Strength is not a quality axis. Full-bodied is not better, and a beginner given a
ligero-heavy cigar reads the resulting nausea as "cigars are not for me".

| Experience | Ceiling | Sizing that pairs with it |
|---|---|---|
| First few cigars | Mild to medium | Petit Corona, Corona |
| Occasional | Medium | Robusto, Corona Gorda |
| Regular | Medium to full | Toro, Churchill |
| Habitual | No ceiling | Whatever the palate asks for |

Two things commonly mistaken for strength and worth separating out:

- **Body** is the weight of the smoke in the mouth; **strength** is nicotine
  delivery. A medium-body cigar can be strong.
- **A young cigar** reads harsher than the same cigar with two years on it.
  Ammonia on the cold draw means it needs rest, not a lower strength bracket.

## Step 3 — the state check, before anything else

Run this before considering flavour at all. Any "yes" means the answer is "not
tonight", plus what to do instead:

| Check | If it fails |
|---|---|
| Arrived within the last two weeks | Rest it. Shipping and travel unsettle the leaf; two to four weeks at target RH is the usual wait |
| Squeezes hard and crackles, or feels brittle | Too dry — see `references/defect-diagnosis.md` |
| Feels spongy, or the wrapper is slick | Too wet — will burn badly and taste sour |
| Ammonia on the cold draw | Not rested; months, not days |
| Any mould that is not plainly plume | Isolate it; see `references/defect-diagnosis.md` before smoking anything from that container |

## Anti-recommendations

A recommendation without this section is incomplete. State these explicitly.

| Do not | Because |
|---|---|
| Give a beginner a full-strength ligero blend | Nausea on the first cigar ends the hobby |
| Hand a beginner a Double Corona or Churchill | 90+ minutes; most are abandoned half-smoked |
| Suggest a first cigar with an unusual or unverifiable origin | No way to judge quality, no way to learn from it |
| Pick from the humidor without checking arrival date | Two weeks' rest is the difference between harsh and clean |
| Recommend a large cigar for a stated 30-minute window | The constraint is physical, not a preference |
| Reach for a cigar straight from a cold delivery box | Thermal shock cracks wrappers |
| Answer a "what should I smoke" with a shopping list | The user asked what to smoke, not what to buy |

## What this guide will not do

- **No prices, no sellers, no "worth buying".** If a source page states a price,
  quote it verbatim through `price_reference` and nothing more — no range, no
  currency conversion, no shop.
- **No tasting note invented for a cigar not fetched.** Flavour language comes
  from the page or it does not come at all.
- **No aging prediction stated as fact.** "This will improve" needs evidence;
  otherwise say what is known and what is guesswork.

## Where the neighbouring questions go

| Question | Reference |
|---|---|
| Which container may these cigars share | `flavour-groups.md` |
| Why is it burning or drawing wrong | `defect-diagnosis.md` |
| What to drink with it | `drink-pairing.md` |
| What the descriptive terms mean | `capitol-index.md` |
| Whether a figure from a site is trustworthy | `data-sources.md` |
