# Personal Ledger Configuration / 个人台账配置

`personal-ledger.md` is **gitignored** and never leaves your machine. Only this
example ships in the repository. This split exists so the public skill can support
a personal collection without ever containing one.

Point it at whatever CSV or Markdown ledger you actually maintain.

## Setup

```
cp references/personal-ledger.example.md references/personal-ledger.md
```

Then fill it in. With the file absent the skill simply answers general questions.

## Template

---

Storage path: `<absolute path to your ledger CSV or notes directory>`

Read that path before answering anything about holdings, storage placement or
aging order. Totals come from the file and are never stated by the skill.

### Ledger shape

Document your own columns here. Example shape used by one installation:

```
box | humidity_zone | temp | box_name | position | brand | line/vitola | qty |
strength | intake_date | source/order | batch/year | last_checked | aging_stage |
dimensions | notes
```

Keep one rule above all: quantity recorded is **original purchase quantity**,
with consumption noted separately in remarks rather than subtracted.

### Consumption tiers

Record your own tiering, e.g. A / B / C with the counting logic and row counts,
so the skill can cite figures that match your ledger instead of guessing.

### Storage setup

Record equipment and target RH:

- Device: e.g. compressor wine cooler, or cabinet humidor
- Humidification: e.g. two-way packs, and which RH per container
- Measured temperature range
- Open-air RH inside the unit, if known

Include whichever corrections you have already reached — for example, note
whether your system buffers RH by salt solution rather than passively, since
that changes whether temperature swing affects humidity at all.

### Open questions

List unresolved items: unlabelled cigars, models awaiting identification,
strength values needing confirmation. This is exactly what the lookup scripts
exist to close.

### Boundaries you keep

Restate your own constraints here so they override the skill's general defaults,
for example "no purchase channels, no commercial links, authentication only as
criteria rather than verdicts".
