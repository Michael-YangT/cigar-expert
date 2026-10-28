# Flavour Groups / 气味组分盒

How to decide which cigars may share a sealed container.

## The governing insight

**Odour strength follows wrapper fermentation level and origin — not how strong
the cigar tastes when smoked.** This is the user's own finding and it overrides
intuition.

It is the most common source of storage mistakes:

- Cuban short-filler (Quintero, José L. Piedra, Guantanamera) is mild to smoke but
  **off-gasses strongly**. Storing it beside a gentle non-Cuban light wrapper is
  the classic error.
- Davidoff Nicaragua Robusto reads medium-plus on the palate yet its odour stays
  clean and restrained.

## The five odour categories

At the base are five categories by leaf character. Each carries its own RH target:

| Category | Odour character | Target RH | Examples |
|---|---|---|---|
| Dark fermented (Maduro / Oscuro / San Andrés / Broadleaf) | **Strong source**, contaminates neighbours | **62%** | AJ Bellas Artes Maduro, Undercrown 10, Blackened S84 |
| Cuban | Distinctive; both emits and absorbs strongly | **65%** | Cohiba, Quintero, JLP, Guantanamera |
| Neutral (Habano / Corojo / Sumatra) | Moderate | **65%** | Montecristo 1935, Oliva Serie V, RP Vintage 1990 |
| Light (Connecticut Shade / Claro / mild Dominican) | **Overpowered easily** | **69%** | Casa García, Avo, Zino Platinum, Macanudo |
| Chinese domestic | Idiosyncratic; cross-contaminates worst with foreign leaf | **65%** | 黄鹤楼, 长城 |

## The seven storage groups

A working scheme extends those five with two structural groups, which is what
turns a taxonomy into a physical layout rule.

| # | Group | Pack | Boxes | Placement |
|---|---|---|---|---|
| ① | Cuban | 65% | 2 | Sealed separately, low-traffic spot |
| ② | Dark fermented | **62%** | 1 | Deep inside, opened rarely |
| ③ | Light and delicate | **69%** | 3 | **The most reachable shelves in the whole unit** |
| ④ | Neutral mainstream | 65% | 3 | Middle shelves |
| ⑤ | Chinese domestic | 65% | 1 | Isolated — if already correct, leave it alone |
| ⑥ | **Unopened factory boxes** | — | 3 crates | Anywhere; do not open them |
| ⑦ | **Pending verification** | 65% | 1 pouch | Staged alone temporarily |

The cardinal rule: **one container holds exactly one group.** A group may span
several containers, but never the reverse.

Two additions carry most of the practical value:

- **⑥ unopened boxes are self-isolating.** A factory-sealed box is already a
  double barrier, so those cigars need no further separation. Do not break the
  seal for the sake of tidiness.
- **⑦ unverified cigars stay quarantined.** Anything whose brand or model is
  unknown gets its own pouch rather than joining a group. If it turns out to be
  something pungent, it has contaminated one pouch instead of a whole box.

The useful consequence overall: **sorting by odour group also sorts humidity
correctly.** Flavour group and humidity target are two faces of the same
variable — wrapper fermentation — so there is no trade-off to negotiate.

Note also that putting group ③ on the easiest shelves is a storage action, not
merely convenience: less time with the door open means less disturbance for
everything else.

## Mapping a wrapper to a group

Take the `Wrapper` field from a Cigar Century record, then read across:

| Wrapper value | Group |
|---|---|
| Mexican San Andres Maduro, USA Connecticut Broadleaf, Brazilian Maduro, Oscuro | Dark fermented |
| Cuban | Cuban |
| Ecuadorian Habano, Corojo, Ecuadorian Sumatra, Nicaraguan (non-maduro) | Neutral |
| Connecticut Shade, Ecuadorian Connecticut, USA Connecticut Shade, Claro | Light |
| Chinese domestic leaf | Chinese domestic |

Two cautions:

- **Maduro in the line name is not the same as a maduro wrapper.** Verify against
  the actual `Wrapper` value. `Oliva Serie V Melanio Maduro Robusto` and
  `Oliva Serie V Melanio Robusto` differ exactly here, and they land in different
  groups.
- Box-pressed and figurado shapes say nothing about group. Only the leaf matters.

`references/terroir.md` explains why each wrapper behaves this way — San Andrés
ferments dark while keeping cocoa sweetness, Estelí gives black pepper and dense
grey ash, Connecticut Shade is restrained by design.

## Cross-flavour mechanics

Cross-contamination is adsorption–desorption equilibrium inside a sealed volume.
Tobacco is porous, high surface area, and holds sugars and oils, so volatile
compounds migrate from the strong source toward the mild one until the container
reaches a common smell.

Consequences that matter in practice:

1. **Contamination happens inside one sealed box only.** Air cannot penetrate a
   sealed box, so circulation around the outside cannot move smells between boxes.
   An earlier assumption that air-cooled cabinet airflow caused cross-flavour was
   withdrawn — the real consequence of that airflow is drying out humidity packs
   faster, which is a separate risk.
2. **Cellophane and original boxes are barriers.** A factory-sealed box is a double
   barrier with near-zero risk; loose singles are fully exposed.
3. **Cold slows migration.** At 16–18°C migration is markedly slower than at room
   temperature, which is an advantage.

## Humidity pack discipline

Because the air-cooled cellar sits around 30–50% RH, pack life is the dominant
variable. An intact two-way pack holds its stated RH within ±0.3% across normal
temperature swing; once spent, the container degrades to passive behaviour, where
each 1°C of cooling adds roughly 4.4 points of RH.

Monthly squeeze test:

- Soft with a granular feel — fine
- **Hardened into a block — spent, replace now.** This is the sole real risk source
- Turned to liquid — over-absorbed

## Cedar restriction

Spanish cedar buffers humidity and contributes aroma, which is prized during long
aging. In a mixed container it becomes a cross-flavour accelerator, absorbing one
group's odour and re-releasing it onto the others.

Assign one sleeve per container and never share or swap them between groups.
