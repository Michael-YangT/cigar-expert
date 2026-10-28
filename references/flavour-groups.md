# Flavour Groups / 气味组分盒

How to decide which cigars may share a sealed container.

## The governing insight

**Odour strength follows wrapper fermentation level and origin — not how strong
the cigar tastes when smoked.** This reversal is what makes cross-flavour hard to
reason about, and it is the usual cause of storage mistakes.

Two cases make the point:

- Cuban short-filler is mild on the palate yet **off-gasses strongly**. Storing it
  beside a gentle non-Cuban light wrapper is the classic error.
- A medium-plus Nicaraguan puro can read strong when smoked yet leave a clean and
  restrained odour.

Always judge a cigar's storage group by its leaf, never by its body.

## The five odour categories

Five categories derive from leaf character. Each carries its own RH target:

| Category | Odour character | Target RH | Typical leaf |
|---|---|---|---|
| Dark fermented (Maduro / Oscuro / San Andrés / Broadleaf) | **Strong source**, contaminates neighbours | **62%** | Mexican San Andrés, USA Broadleaf, Brazilian Maduro |
| Cuban | Distinctive; both emits and absorbs strongly | **65%** | Cuban-origin wrapper and filler |
| Neutral (Habano / Corojo / Sumatra) | Moderate | **65%** | Ecuadorian Habano, Corojo, Sumatra |
| Light (Connecticut Shade / Claro / mild Dominican) | **Overpowered easily** | **69%** | Connecticut Shade, Claro |
| Chinese domestic | Idiosyncratic; cross-contaminates worst with foreign leaf | **65%** | domestic Chinese leaf |

## The seven storage groups

Two structural groups extend those five, turning a taxonomy into a layout rule:

| # | Group | Target RH |
|---|---|---|
| ① | Cuban | 65% |
| ② | Dark fermented | **62%** |
| ③ | Light and delicate | **69%** |
| ④ | Neutral mainstream | 65% |
| ⑤ | Chinese domestic | 65% |
| ⑥ | **Unopened factory boxes** | as packed |
| ⑦ | **Pending verification** | 65% |

The cardinal rule: **one container holds exactly one group.** A group may span
several containers, but never the reverse.

Two additions carry most of the practical value:

- **⑥ unopened boxes are self-isolating.** A factory-sealed box is already a
  double barrier, so those cigars need no further separation. Do not break the
  seal for the sake of tidiness.
- **⑦ unverified cigars stay quarantined.** Anything whose brand or model is
  unknown gets its own pouch rather than joining a group. If it turns out to be
  something pungent, it has contaminated one pouch instead of a whole container.

The useful consequence overall: **sorting by odour group also sorts humidity
correctly.** Flavour group and humidity target are two faces of the same
variable — wrapper fermentation — so there is no trade-off to negotiate.

One practical corollary: keep whatever gets reached for most often at the easiest
access point. Shorter open time means less disturbance for everything else, which
makes accessibility a storage decision rather than a convenience.

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
  the actual `Wrapper` value. A line offered both ways can have one variant that
  lands in Dark fermented and another in Neutral.
- Box-pressed and figurado shapes say nothing about group. Only the leaf matters.

`references/terroir.md` explains why each wrapper behaves this way — San Andrés
ferments dark while keeping cocoa sweetness, some Nicaraguan valleys give black
pepper and dense grey ash, Connecticut Shade is restrained by design.

## Cross-flavour mechanics

Cross-contamination is adsorption–desorption equilibrium inside a sealed volume.
Tobacco is porous, high surface area, and holds sugars and oils, so volatile
compounds migrate from the strong source toward the mild one until the container
reaches a common smell.

Consequences that matter in practice:

1. **Contamination happens inside one sealed container only.** Air cannot
   penetrate a sealed box, so airflow around the outside cannot move smells
   between boxes. Cabinet airflow matters for a different reason — it dries
   humidity packs faster, which is a separate risk from cross-flavour.
2. **Cellophane and original boxes are barriers.** A factory-sealed box is a
   double barrier with near-zero risk; loose singles are fully exposed.
3. **Cold slows migration.** Below typical room temperature migration is markedly
   slower, which works in the collector's favour.

The corollary is that effort spent sealing containers pays off, while effort spent
arranging airflow does not address cross-flavour at all.

## Humidity pack discipline

Because the air inside a cooled cabinet is often far drier than target, pack life
is usually the dominant variable. An intact two-way pack holds its stated RH
across a normal temperature swing; once spent, the container degrades to passive
behaviour, where each 1°C of cooling adds roughly 4.4 points of RH.

Monthly squeeze test:

- Soft with a granular feel — fine
- **Hardened into a block — spent, replace now.** Once this happens the container
  loses its buffer and RH starts tracking temperature
- Turned to liquid — over-absorbed

## Cedar restriction

Spanish cedar buffers humidity and contributes aroma, which is prized during long
aging. In a mixed container it becomes a cross-flavour accelerator, absorbing one
group's odour and re-releasing it onto the others.

Assign one sleeve per container and never share or swap them between groups.
