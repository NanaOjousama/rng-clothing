# Headwear V5 — HEADWEAR_MEMORY

> Compact persistent memory for Headwear V5.
> Read after `PROJECT_MEMORY.md`.
> Read `KNOWLEDGE_BASE.md` and `GAP_LOG.md` only when deeper evidence is needed.

## Current Goal
Prove that Headwear V5 can intentionally express a broad range of vanilla-quality hat constructions, then transfer those learned construction rules back into the normal random generator.

Current sequence:
1. close remaining reconstruction blockers
2. visual side-by-side QC
3. fresh random generator batch
4. in-game normal-scale QC
5. only after that, expand broadly into non-standard headwear

Do not expand prematurely into halos/masks/etc. unless a current reconstruction directly proves the needed Architecture concept.

## Slot / Resolution
- Headwear defaults to native vanilla parity: 20x20.
- Placement matters more than raw occupied coverage.
- `HEAD_BOX`, crown top, overhang, `HeadPosition.Y`, and derived occupied bbox are placement concepts.
- `HeadPosition.X` should be derived/formulaic where possible rather than independently rolled.

## Hair Policy
Fashion Sense custom hats can effectively preserve full hair or hide hair; they cannot request vanilla's obscured/covered-hair variant.

Rules:
- normal BRIMMED and BRIMLESS hats default to `PRESERVE`
- do **not** globally hide hair
- `HIDE` should be reserved for future enclosing forms whose geometry truly earns it
- bald-looking output is a real wearability bug, not a cosmetic nit

## Architecture Legality
Headwear legality must be declarative per Architecture.

Do not weaken BRIMMED/BRIMLESS globally because future headwear needs exceptions.

Capabilities may be declared per Architecture, for example:
- allows_directional_pieces
- allows_split_rows
- allows_detached_mass
- allows_enclosed_holes
- allows_extreme_asymmetry

Future likely structural classes include:
- brimmed/crowned
- close-fit/brimless
- projecting appendages
- circlet/ring/crown
- floating/orbiting
- rigid shell
- draped/enclosing
- one-sided/small attached ornament

Do not force all of these through BRIMMED/BRIMLESS.

## Core Projection Rule
Projection adds **zero design entropy**.

A hat resolves once.
Front/side/back are deterministic realizations of that same hat.

Per-direction structure is allowed only as a declared construction capability:
- do not reroll design by direction
- preserve placement stability
- a declared piece may be present/absent/differently realized by direction when that is part of the Architecture

## Side-View Rule Learned from Vanilla
Do not impose fake perspective skew on side brims.

Locked:
- `HAT_SIDE_BRIM_SKEW = 0`
- same width by default
- side brim line may rise one row (`HAT_SIDE_BRIM_RISE = 1`)

Fine side-view differences should come from authored construction, not a global skew formula.

## Outline / Shading
Headwear differs from shirts:
- vanilla hats overwhelmingly use darker outlines
- headwear should retain a darker-outline render class
- shading should communicate form/construction, not just fill a silhouette with highlight

Major visual lesson:
**silhouette + outline + highlight is not enough.**
Vanilla-quality hats need internal authored construction such as bands, seams, panels, cuffs, visors, knit segmentation, creases, crown structure, brim structure, and ornaments where appropriate.

## Current Reconstruction Benchmarks
- Top Hat: 0% difference — exact
- Bowler: 2%
- Witch: 3%
- Santa: 8%
- Cowboy: 10%
- Trucker: 11%

Regression controls:
- Top Hat
- Bowler
- Witch

Remaining targets:
- Santa
- Cowboy
- Trucker

## Adopted Capabilities / Vocabulary
### Odd-width rows
ADOPTED.
- profile insets may be half-integers
- `span()` supports stable declared `odd_bias`
- same half-pixel side is used consistently within a hat
- scoped by `has_odd_rows(profile)` or equivalent
- integer-inset profiles remain bit-identical

### Crown profiles
Active/learned vocabulary:
- ROUND
- DOMED
- SHALLOW
- TALL_FLAT
- STOVEPIPE
- PINCHED
- STEPPED
- FAST
- CONE
- DROOP

Important:
- Bowler proved crown insets must reach 5
- `FAST` supports fast-shoulder caps
- `CONE` is narrow by design and needs a declared exemption from generic anti-chess-piece proportion rules
- `DROOP` helps soft non-monotonic crowns but does not yet fully solve Santa construction

### Brims
Active learned vocabulary:
- TAPERED
- SHARP
- DIPPED
- STEPPED
- CURLED
- SWEEP

`SWEEP` fills the previously missing 4-row brim cardinality.

### Hem taper
ADOPTED as a closed vocabulary rather than one hardcoded sequence:
- TIGHT
- DROP
- FLARE
- SOFT

Pairings must be QC-checked; individually valid choices can still form a bad combination.

### Controlled asymmetry
Known motif concepts:
- TIP_LEAN
- CROWN_DENT
- BRIM_FLICK

`SIDE_TUFT` remains disabled/weight-0 because it read as a wart/nub.
Protrusion/asymmetry combinations should remain guarded when they conflict.

### Protrusions
- `EARS_SIDE` is anchored to a meaningful widest-row shoulder
- declared protrusions must actually render
- detached floating clusters are QC-detected
- `EARS_TALL` remains weight-0 until geometry supports it

## Current Proven Blockers
### Trucker
Needs a direction-specific visor concept.

Constraint:
- identical crown anchoring fixed a real placement bug
- do not globally undo that rule
- solve via Architecture-declared directional authored pieces

### Cowboy
`CROWN_CREASE` reproduces the apex cue.

Remaining:
- brim wings
- `BRIM_WINGS` is conceptually reasonable but currently unreachable
- crown must remain narrower until the brim line to create clearance

Need:
- reusable narrow-to-brim crown profile
- then re-evaluate `BRIM_WINGS`

### Santa
Odd-width + DROOP improved fidelity, but missing:
- stronger progressive droop path
- split lower hem / split lobe
- cuff
- pom/tassel

Do not globally legalize split rows or detached mass to solve one hat.

## Experimental / Not Yet Adopted
- `BRIM_WINGS`: weight 0 until supporting crown geometry exists
- direction-specific visor/pieces
- split-row construction
- progressive droop beyond current DROOP profile
- palette-from-reference path

## Out-of-Scope Structures Proven by Reconstruction
### Cat Ears
Needs a separate EARED/HORNED-like Architecture with declared detached-mass/enclosed-hole legality.

### Butterfly Bow
Needs an explicitly one-sided Architecture; it should not be represented as mild asymmetry inside normal hats.

## Reconstruction Method
For a reference hat:
- search every legal V5 parameter combination for the closest silhouette
- residual mask difference is an upper bound on current grammar expressiveness
- do not hand-copy final pixels
- classify mismatch as pipeline / Architecture / authoring / QC

Reconstruction catches expressiveness gaps that corpus statistics can miss.

## Current Phase
Phase 3: close remaining high-value reconstruction blockers.

Focus:
1. Trucker — direction-specific visor
2. Cowboy — narrow-to-brim crown + brim wings
3. Santa — progressive droop + split lower hem + cuff/pom

Regression controls:
- Top Hat
- Bowler
- Witch

For meaningful prototypes report:
- limitation addressed
- why current vocabulary is insufficient
- hats benefiting
- before/after fidelity
- normal-generator impact
- regressions
- complexity/maintenance risk
- ADOPT / KEEP EXPERIMENTAL / REJECT

## After Phase 3
Do **not** immediately declare Headwear complete.

Next:
1. inspect side-by-side reconstructions visually
2. generate a fresh varied random hat batch
3. test in game at normal Stardew scale
4. inspect hair preservation, face clearance, vertical placement, turning stability, construction richness, silhouette diversity, and whether outputs still read as generic blobs
5. only lock normal hats if the user considers the output visually acceptable

## Deep References
Consult only when needed:
- `KNOWLEDGE_BASE.md`
- `GAP_LOG.md`
- Fashion Sense capability/source audit
- vanilla/corpus measurements
