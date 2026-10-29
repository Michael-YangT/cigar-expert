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

**The size words do not predict size.** Measured across real catalogue pages:
"half corona" is consistently 3" × 44–46; "petit corona" ranges 4"–5" with rings
from 35 to 44; "robusto" spans 4" to 6". Screening candidates by name therefore
throws away correct answers. Screen by the measured numbers instead.

| Length ↓ / Ring → | ≤ 42 | 43–46 | 47–50 | 51–54 | 55+ |
|---|---|---|---|---|---|
| **≤ 4"** | 20–30 | 20–30 | 25–35 | 30–40 | 35–45 |
| **4–5"** | 30–40 | 30–45 | 35–50 | 45–60 | 50–70 |
| **5–6"** | 40–55 | 40–55 | 45–65 | 50–70 | 60–80 |
| **6–6.5"** | 50–70 | 55–75 | 60–80 | 65–90 | 75–100 |
| **6.5–7.5"** | 60–85 | 65–90 | 75–105 | 80–110 | 90–130 |
| **7.5"+** | 70–100 | 80–110 | 90–125 | 95–135 | 110–150 |

These are estimates, not measurements. No published source gives smoking times,
and pace dominates: the same cigar runs 30% shorter for a fast smoker, and a
damp or tightly packed one runs longer. State the range and say it is an
estimate.

Both dimensions matter. A long thin cigar takes as long as a short fat one, and
a 3-inch cigar is the only honest answer to a 25-minute window.

Name examples, for locating pages — **not** for judging size: Half Corona ≈ 3" ×
44–46 · Petit Corona ≈ 4"–5" × 35–44 · Corona / Corona Gorda ≈ 5"–6" × 42–46 ·
Robusto ≈ 4"–6" × 50–54 · Toro ≈ 6"–6.5" × 50–52 · Churchill ≈ 7" × 50–54.

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

The catalogue returns strength as one of exactly four strings — `Mild`, `Medium`,
`Medium To Full`, `Full`. Quote the page's own wording rather than rounding it
into a bracket of your own: `Medium To Full` is a real value, not an ambiguity to
be resolved. Never upgrade a `Medium` to `Medium To Full` because the brand is
known for strong blends.

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
