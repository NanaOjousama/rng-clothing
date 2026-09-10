# V5 Stardew / Fashion Sense Procedural Clothing Generator
## Canonical Merged Architecture + Modded AA/AG Research Implementation Handoff
### September 2026

## PURPOSE OF THIS DOCUMENT

This is the current **canonical merged V5 generator specification**.

It combines:

1. The new hierarchical constrained-generation decision architecture.
2. The revised Slot → Family → Design Architecture model.
3. The locked invariant ledger.
4. The Family Vocabulary vs Architecture Commitment split.
5. The new Style Context model.
6. The new complexity-budget and semantic-occupancy systems.
7. The post-render diversity model.
8. The Fashion Sense / modded-clothing corpus findings from studying 1,669 garments across roughly 35 packs.
9. The best AA/AG findings from the Sailor experiment.
10. The decision to build a **new V5 Construction + AA + AG + Projection pipeline** rather than preserve the old renderer.

The old renderer, old AA, old AG, old Sailor renderer, old 16×16 assumptions, and old `rngc` rendering architecture are **reference-only**.

**Do not build V5 around preserving the old renderer or old AA/AG.**

The goal is to build one new coherent pipeline using the new decision architecture **plus the lessons learned from high-quality third-party Fashion Sense mods**.

---

# 1. PRODUCT GOAL

The player performs **one clothing roll**.

Internally that roll resolves many hidden dependent decisions and produces **one coherent finished garment**.

The generator is not a flat random component mixer.

Bad model:

```text
random collar
+ random sleeve
+ random bib
+ random buttons
+ random lapel
+ random pattern
= garment
```

Required model:

```text
ONE PLAYER ROLL
        ↓
Roll Context
        ↓
Slot
        ↓
Garment Family
        ↓
Design Architecture
        ↓
Architecture publishes legal child schema
        ↓
Only valid variables come into existence
        ↓
Scoped structural decisions
        ↓
Material
        ↓
Color Architecture + Chromatic Resolution
        ↓
Surface
        ↓
Ornament / Detail
        ↓
Resolved Garment Specification
        ↓
NEW Construction realization
        ↓
NEW AA
        ↓
NEW AG
        ↓
Deterministic Projection
        ↓
Front / Side / Back
        ↓
Rendered Quality + Diversity Gate
        ↓
ONE FINISHED GARMENT
```

Foundational rule:

> RNG chooses among valid design decisions. It never constructs clothing atom-by-atom through independent random features.

---

# 2. IMPLEMENTATION BOUNDARY

The following systems are now historical/reference material only:

- old `rngc` rendering assumptions;
- old 16×16 renderer;
- old Sailor mini renderer;
- old Sailor parametric rendering pipeline;
- old AA implementation;
- old AG implementation;
- old geometry that conflicts with the new model;
- old 16×16 pieces merely because they already exist;
- resolution-reduction experiments;
- old visual rules superseded by the corpus study.

They may be inspected for:

- Fashion Sense export knowledge;
- known edge cases;
- useful algorithms;
- tests worth preserving conceptually;
- lessons already learned.

They must **not** dictate the new architecture.

Required result:

```text
ONE NEW GENERATOR
+
ONE NEW CONSTRUCTION SYSTEM
+
ONE NEW AA SYSTEM
+
ONE NEW AG SYSTEM
+
ONE DETERMINISTIC PROJECTION PIPELINE
+
ONE POST-RENDER QUALITY / DIVERSITY GATE
```

---

# 3. EMPIRICAL TARGET FROM MODDED FASHION SENSE RESEARCH

A study measured 1,669 Fashion Sense garments across approximately 35 packs.

Key findings:

- 1,472 / 1,669 modded shirts (88%) use **8×8 at Scale 4**.
- Zero sampled garments use the former 16×16 / Scale 2 target.
- Richness comes primarily from **colour count, region architecture, accents, and frame extent**, not pixel-density inflation.
- At identical resolution, modded garments use a median around **10 colours**, compared with vanilla around 6.
- Corpus ramp depth often reaches roughly **4–6 steps**.
- Only about **11.6%** of measured garments contain near-black, confirming there is no global outline convention.
- Region partition is a dominant construction device; 77.6% of measured fronts contain a contrasting centre column.
- Roughly 86% of the corpus contains 1–2 pixel high-contrast accents.
- Good mods sometimes extend the frame rather than subdividing pixels: examples include 8×7 crops, 8×9–8×11 coats, and wider shoulder envelopes.

Therefore the canonical V5 target is:

```text
PRIMARY AUTHORING DENSITY
8×8 native
Scale 4
```

This is not a 16→8 reduction pipeline.

The renderer must think natively at the target envelope.

---

# 4. FRAME ENVELOPE

Envelope is a first-class rendering capability.

Standard initial envelope:

```text
width = 8
height = 8
scale = 4
body_position = standard
```

The data model must be capable of representing:

```text
Envelope
    width
    height
    body_position          INTEGER — see AMENDMENT AA-2
    scale                  per DIRECTION, not per garment — see AMENDMENT AA-1
    optional directional body-position overrides
```

Future valid envelopes may include:

- 8×7
- 8×9
- 8×11
- 10×8
- other validated Fashion Sense-compatible extents

Initial prototype content remains standard 8×8.

Extended-envelope capability should exist without turning the first prototype into a coat/animation project.

---

# 5. FIVE CONCEPT CLASSES

Every concept must be classified before implementation.

## Grammar
Universal or render-class law. Never rolled.

## Family Vocabulary
Defines what is conceivable for a garment family.

## Architecture Commitment
Defines how a specific construction tradition is built.

## Scoped Variable
A genuinely unresolved choice made legal by its parents.

## Derived Data
Computed from previous decisions with no additional design entropy.

Misclassifying one of these is a major source of incoherent generation.

---

# 6. CANONICAL DECISION SPINE

```text
SLOT
 ↓
GARMENT FAMILY
 ↓
DESIGN ARCHITECTURE
 ↓
SCOPED VARIABLES
```

Family and Architecture have different ownership:

> **Family defines possibility. Architecture commits construction.**

---

# 7. TIER 0 — GRAMMAR

Grammar contains zero design RNG.

It should define:

- core garment representation laws;
- rendering-class rules;
- envelope semantics;
- named landmarks;
- semantic spatial zones;
- occupancy modes;
- palette/ramp capabilities;
- base lighting;
- body-template transforms;
- projection continuity;
- wrap semantics;
- legibility constraints;
- free/attached edge semantics;
- occlusion composition;
- Fashion Sense export constraints.

Prefer layering the grammar conceptually:

```text
CORE GARMENT GRAMMAR
        +
RENDER-CLASS GRAMMAR
        +
FASHION SENSE EXPORT CONTRACT
```

Target-system quirks should not be mistaken for universal clothing laws.

---

# 8. TIER 1 — ROLL CONTEXT

One player roll creates a hidden Roll Context.

Initial fields:

```text
seed
complexity_budget
formality
chromatic_temperament
novelty_tier
```

Reserved future Style Context axes:

```text
idiom
condition
```

---

# 9. STYLE CONTEXT

Style Context is a **bias system**, not a content source.

## Formality — implement first

Ordinal:

```text
work
casual
smart
formal
```

It may reweight already-legal options such as:

- Family probability;
- Architecture probability;
- material;
- contrast;
- saturation;
- hardware finish;
- ornament restraint.

## Idiom — reserve for later

Possible categorical examples:

```text
nautical
gothic
pastoral
athletic
historical
fantasy
```

## Condition — reserve for later

Possible examples:

```text
pristine
worn
distressed
mended
```

Critical invariant:

> Style Context may only reweight options that Family or Architecture already declared. It may never introduce new content.

A gothic bias can make a legal dark blazer palette more likely.

It cannot add chains, spikes, or a cape unless those options were already legal for the Family/Architecture.

---

# 10. TIER 2 — SLOT

Initial Slots:

```text
TOP
BOTTOM
ONE_PIECE
```

Slot resolves first because it determines representation capabilities.

Slot may derive:

- render class;
- dye-mask availability;
- colour capabilities;
- coverage axis;
- eligible Families;
- target-specific restrictions.

Choosing Bottom should annihilate irrelevant top-only concepts before those concepts ever exist.

---

# 11. TIER 3 — GARMENT FAMILY

Family answers:

> What design vocabulary is conceivable for this kind of garment?

Examples:

```text
TEE
SAILOR_TOP
BLAZER
CARDIGAN
OVERALLS
```

A Family contract may own:

- candidate Architecture table;
- closure vocabulary;
- aperture vocabulary;
- limb vocabulary;
- possible layer-slot vocabulary;
- material vocabulary;
- broad coverage domain;
- broad fit domain where useful;
- broad surface capabilities;
- Family-compatible color-architecture vocabulary;
- Style Context weight hooks.

Family does not make final construction commitments.

---

# 12. TIER 4 — DESIGN ARCHITECTURE

Architecture answers:

> How is this specific construction tradition built?

Examples:

```text
BLAZER
    SINGLE_BREASTED
    DOUBLE_BREASTED
    SHAWL

SAILOR_TOP
    CLASSIC_SQUARE_FLAP
```

Architecture commits:

- structural topology;
- closure behavior;
- aperture;
- required structural pieces;
- authored silhouette set;
- actual layer slots opened;
- narrowed coverage range;
- narrowed fit range;
- surface domains;
- ornament affinities;
- base complexity cost;
- semantic occupancy;
- declared child schema;
- parameter domains;
- dependencies.

Only Architecture may declare downstream structural variables.

---

# 13. ARCHITECTURE VS PARAMETER

Do not create architectures for every independent modifier.

Example:

```text
CROPPED_BLAZER
```

should normally not be its own Architecture.

Prefer:

```text
Family = BLAZER
Architecture = SINGLE_BREASTED
Coverage = CROPPED
```

provided the Architecture allows that value.

Classification test:

> If the difference changes construction topology, closure, aperture, seam logic, layering logic, or other correlated structural commitments, it may be an Architecture.

> If it changes a dimension inside the same construction, it is a scoped parameter.

---

# 14. TIER 5 — SCOPED STRUCTURAL VARIABLES

Only variables explicitly declared by the selected Architecture exist.

Possible categories include:

## Coverage / Proportion
- cropped
- regular
- longline
- etc.

## Fit
- fitted
- regular
- relaxed
- oversized

Only keep values that prove visually meaningful at 8×8.

## Aperture / Edge
- neckline
- collar type
- collar depth
- lapel style
- lapel depth
- placket length
- hem treatment
- cuff treatment

## Limb
- sleeve length
- shoulder treatment
- strap treatment

## Layer
- under-layer occupancy
- neck accessory
- bib
- waist layer

Only through Architecture-opened slots.

---

# 15. ABSENT ≠ NONE

Locked rule.

A Tee should not contain:

```text
lapel_style = none
```

The `lapel_style` variable should not exist at all.

Invalid concepts:

- are never instantiated;
- are not serialized;
- cannot be mutated;
- cannot be rerolled;
- should not appear as irrelevant controls.

Generated records contain only concepts that actually exist.

---

# 16. CLOSURE AS A DEPENDENCY CARRIER

Closure is structural.

Example:

```text
closure = PULLOVER
```

may enable:

- neckline;
- short placket;

while removing:

- lapel subtree;
- full front opening;
- full button row;
- open-front under-layer logic.

Example:

```text
closure = OPEN_FRONT
```

may enable:

- front-edge construction;
- exposed under-layer;
- lapel/shawl logic;
- divided front surface domains.

---

# 17. LAYER SLOTS

Layering occurs only through declared slots.

Family defines possible slots.

Architecture opens actual slots.

Example:

```text
BLAZER FAMILY
possible:
    under_layer
    neck_accessory

SINGLE_BREASTED ARCHITECTURE
opens:
    under_layer
    optional neck_accessory
```

No opened slot means no corresponding child variable exists.

---

# 18. COMPLEXITY BUDGET

Use one shared complexity pool initially.

Suggested conceptual range:

```text
1–5
skewed low
```

Spend order:

```text
Construction first
Surface second
Ornament last
```

Every spend must be tagged:

```text
STRUCTURAL
SURFACE
ORNAMENT
```

Do not split the pool until measurement proves that separate budgets are needed.

---

# 19. SEMANTIC SPATIAL OCCUPANCY

The scarce resource is semantic garment space, not just row numbers.

Possible zones:

```text
collar:center

chest:left
chest:center
chest:right

midriff:center

waist:girth

hip:left
hip:right

hem:girth
```

Claims support:

## Exclusive
Conflicting features cannot coexist.

## Conditional-share
Features may coexist when visibility/contrast conditions are satisfied.

## Overlay
One feature intentionally paints over another.

Example:

```text
stripe surface
+
chest emblem
```

should be resolved through Overlay, not a pair-specific exception.

---

# 20. MATERIAL

Material is separate from Color Architecture.

Material controls rendering behavior and compatibility.

At 8×8, useful material levers may include:

- ramp amplitude;
- highlight extent;
- edge treatment;
- pattern eligibility;
- contrast behavior;
- local texture shorthand where readable;
- cuff/hem rendering treatment.

Material must earn its entropy.

A semantic material distinction that produces no meaningful visible difference should not count as a distinct design.

---

# 21. COLOR ARCHITECTURE

Color Architecture is an explicit design layer describing color relationships.

Examples:

```text
DARK_BODY_LIGHT_COLLAR
LIGHT_BODY_DARK_COLLAR
MONOCHROME_CONTRAST_TRIM
LOW_CONTRAST_STRONG_ACCENT
SPLIT_BODY_ACCENT
CONTRAST_UNDER_LAYER
```

This represents relationships, not literal colours.

---

# 22. CHROMATIC RESOLUTION

Pipeline:

```text
Color Architecture
        ↓
semantic roles
        ↓
harmony
contrast tier
base hue
temperament
        ↓
material-aware ramps
        ↓
concrete pixel colours
```

Garment pieces never independently roll arbitrary RGB values.

---

# 23. ROLE-BASED COLOR INHERITANCE

Canonical semantic role vocabulary should support at least:

```text
body
shadow
mid
highlight
trim
accent
secondary_accent
hardware
```

Components reference roles.

Examples:

```text
collar → trim
button → hardware
undershirt → accent
```

All views share one garment-level palette system.

---

# 24. RICHER COLOR CAPACITY

The former 4-role / 8-colour assumptions are obsolete.

The new renderer must support richer controlled color usage informed by the corpus:

- modded median around 10 colours;
- p90 around 17;
- common ramp depth roughly 4–6 steps.

These are capability/distribution targets, not quotas that every garment must hit.

More colors must still be driven by role-based coherent palette logic.

---

# 25. SURFACE

Surface is separate from Ornament.

Possible Surface types:

- solid;
- horizontal stripe;
- vertical stripe;
- check;
- repeating motif;
- panel treatment;
- texture shorthand.

Surface may resolve:

```text
pattern_family
pattern_domain
period
phase
registration
role_map
```

Surface is doubly gated:

1. Material must permit it.
2. The resolved Architecture must leave enough area for it to read.

If a repeating pattern cannot render meaningfully, drop it rather than compress it into noise.

---

# 26. ORNAMENT

Ornament represents discrete added detail.

Examples:

- buttons;
- pockets;
- trim;
- piping;
- emblem;
- buckle;
- brooch;
- hardware;
- stitching accent.

Ornament resolves after Surface using:

- remaining complexity budget;
- semantic occupancy;
- Architecture affinity;
- readability/contrast constraints.

It is valid for Ornament to receive no budget.

---

# 27. DETAIL PACKAGE / ACCENT ECONOMY

Small high-contrast accents are a major identity mechanism at 8×8.

The mod corpus found 1–2 pixel high-contrast accents in roughly 86% of garments.

Support coordinated Detail Packages rather than random independent accent pixels.

Example:

```text
SUBTLE_GOLD
    gold hardware role
    optional cuff accent
    optional tiny lapel pin
```

---

# 28. REGION / PANEL STRUCTURE

Region architecture is a core construction mechanism.

The mod corpus found contrasting centre-region partitioning on 77.6% of measured fronts.

Therefore major region/panel structure should usually be owned by Architecture.

Examples:

- centre opening;
- split front;
- bib;
- collar region;
- lower torso region;
- side panel;
- under-layer exposure.

Do not independently reroll major panel topology after Architecture selection unless that Architecture explicitly exposes alternatives.

---

# 29. CONSTRUCTION REPRESENTATION

The new construction system should be:

```text
AUTHORED-PIECE FIRST
+
BOUNDED PARAMETRIC MODIFICATION
```

Authored geometry should be preferred for high-information identity shapes:

- blazer lapels;
- sailor collars/flaps;
- bibs;
- pockets;
- bows;
- unusual collars;
- complex openings;
- seam/panel topologies.

Parametric geometry is appropriate where a variable is genuinely dimensional:

- collar width;
- flap depth;
- neckline depth;
- lapel depth;
- bib height;
- strap width.

Do not build a universal procedural garment CAD system.

---

# 30. SILHOUETTES

Silhouettes come from authored closed sets.

Architecture may expose:

```text
tailored_regular
relaxed_regular
tailored_longline
```

RNG may select among Architecture-approved footprints.

RNG may not procedurally carve outlines or invent silhouette pixels.

Corpus opaque-cell measurements may be used as validation evidence, not as permission for procedural carving.

---

# 31. NEW AA — ART ARCHITECTURE

The old AA implementation is not the target.

Build a new AA system around the semantic Garment Specification and modded-corpus findings.

AA receives a coherent garment spec and determines large visual organization.

AA responsibilities:

- major visual masses;
- construction hierarchy;
- region hierarchy;
- focal hierarchy;
- front/back emphasis;
- surface placement;
- ornament placement;
- accent economy;
- contrast distribution;
- color-region hierarchy;
- perceptual balance;
- readability at 8×8.

AA must understand semantic meaning.

A lapel and a decorative stripe are not equivalent merely because both occupy two pixels.

AA may not invent undeclared garment features.

---

# 32. NEW AG — ART GRAMMAR

The old AG implementation is not the target.

Build new AG from:

- vanilla Stardew baseline;
- measured successful Fashion Sense mod practices;
- valid findings from the Sailor experiment;
- real garment-construction semantics;
- the new Construction/AA representation.

AG responsibilities:

- ramp application;
- selective outlines;
- contrast-aware edge separation;
- local occlusion;
- material rendering;
- trim rendering;
- fold/detail shorthand where readable;
- small accent handling;
- pixel simplification;
- directional consistency;
- 8×8 legibility.

---

# 33. FREE VS ATTACHED EDGES

Retain the concept in the new Construction semantics.

Boundaries are classified:

```text
ATTACHED
FREE
```

Attached:
- fabric structurally continues;
- generally should not receive a strong termination just because two regions meet.

Free:
- fabric terminates over/above something;
- may qualify for stronger separation, local shadow, termination, or selective outlining.

The semantic truth belongs to the structural feature.

---

# 34. CONTRAST-AWARE OUTLINING

Do not use a universal dark-outline pass.

Instead determine whether existing color/value contrast already separates adjacent semantic regions.

If separation is sufficient:
- do not add a dark outline.

If separation is insufficient:
- add appropriate edge treatment based on semantic edge type.

Previously measured luminance thresholds may be used for calibration, not hard-coded as eternal laws.

---

# 35. BASE LIGHTING + LOCAL OCCLUSION

Within a render class, base illumination is Grammar.

Garments cannot author arbitrary global gradients.

Construction may add deterministic local shadows.

A relevant structural feature may declare:

```text
shadow footprint
darkening in ramp steps
```

Examples:

- Sailor rear flap;
- blazer lapel;
- layered hem;
- belt;
- bow;
- folded cuff.

Multiple shadow stamps compose using:

```text
MAX
```

not addition.

Occlusion modifies existing ramp indices; it does not generate arbitrary new colours.

---

# 36. BACK-VIEW SIMPLIFICATION

The corpus suggests backs are often visually simpler than fronts.

Treat roughly reduced back complexity as a descriptive target, not a hard gate.

Front, side, and back must describe the same garment, but they do not need identical visual density.

Do not mechanically clone front ornament onto the back.

---

# 37. PROJECTION

Projection contains:

```text
ZERO DESIGN RNG
```

The Garment Specification resolves once.

Projection derives:

- front;
- side;
- back;
- supported body-template variants;
- wrap continuation;
- plane-feature termination;
- dye mask;
- Fashion Sense export metadata.

Projection must never independently change:

- color;
- pattern;
- ornament;
- trim;
- layer occupancy;
- Architecture;
- silhouette.

If the views disagree, it is a bug.

---

# 38. WRAP SEMANTICS

Features declare propagation behavior.

At minimum:

## Girth / wrapping
May continue through front/side/back.

Examples:
- belts;
- hems;
- waistbands;
- horizontal stripes.

## Plane / local
Does not automatically wrap.

Examples:
- emblems;
- ties;
- plackets;
- front bibs.

Do not infer physical continuity from arbitrary neighboring pixels.

---

# 39. BOUNDED LOCAL REPAIR

No global backtracking search.

Lower passes cannot reopen:

- Slot;
- Family;
- Architecture;
- resolved structural commitments.

A current variable may perform bounded repair within its own existing domain.

Valid:

```text
pattern_family = stripe
period 2 fails
→ try period 3
```

Invalid:

```text
stripe fails
→ switch to check
```

Repair must:

- remain inside the variable domain;
- use the same deterministic seed stream;
- have capped attempts;
- drop optional features if repair ultimately fails.

---

# 40. GENERATED GARMENT RECORD

A resolved record contains only instantiated concepts.

Conceptual shape:

```text
seed
slot
family
architecture

roll_context:
    complexity
    formality
    temperament
    novelty

parameters:
    only active scoped variables

layers:
    only opened / occupied layer slots

material

color_architecture
chromatic_roles

surface:
    only when present

ornaments:
    only accepted ornaments

silhouette_ref

construction_refs
```

Never serialize invalid concepts as `none`, `false`, or `null` if they never existed.

---

# 41. QUALITY / DIVERSITY GATE

Generation validity and visual diversity are separate.

```text
GENERATOR
    ↓
valid garment spec

NEW CONSTRUCTION + AA + AG
    ↓
raster

QUALITY / DIVERSITY GATE
    ↓
meaningfully distinct?
```

Two semantically different specs may rasterize identically.

Do not count metadata differences as visual diversity.

Potential comparison dimensions:

- silhouette;
- opaque-mask structure;
- value structure;
- palette/color architecture;
- major region partition;
- semantic landmark signature;
- focal region;
- accents;
- perceptual raster distance.

The final exact metric is still being researched.

---

# 42. DIVERSITY GATE DOES NOT MUTATE THE GENERATOR

Possible output classifications:

```text
ACCEPT
NEAR_DUPLICATE
IDENTITY_TOO_WEAK
LEGIBILITY_FAILURE
```

Do not introduce global search/backtracking because a rendered result was too similar.

Instead collect batch statistics and improve authoring/weighting later.

---

# 43. VISUAL SIGNIFICANCE CLASSES

Tag variables conceptually as:

## Structural / Identity
Must meaningfully alter design.

Examples:
- Design Architecture;
- lapel style;
- major collar topology;
- flap construction.

## Appearance
Clearly visible variation without changing fundamental construction.

Examples:
- Color Architecture;
- surface;
- strong material differences;
- detail package.

## Semantic / Subtle
May not produce enough visible difference to count as unique design.

Examples:
- tiny fit distinctions;
- materials whose rendering differences collapse at 8×8.

Rendered output determines whether subtle variables actually earn entropy.

---

# 44. CANONICAL INVARIANT LEDGER

## INV-01
Family defines possibility; Architecture commits construction.

## INV-02
Style Context only reweights already-legal possibilities.

## INV-03
Invalid concepts are absent, never `none`.

## INV-04
Every variable has exactly one owner tier and one resolution pass.

## INV-05
Lower passes cannot reopen structural decisions above them.

## INV-06
Bounded repair stays inside the current variable's existing domain.

## INV-07
One complexity pool initially; every spend is tagged.

## INV-08
Semantic space uses exclusive, conditional-share, and overlay claims.

## INV-09
Base lighting is Grammar; local occlusion is declared Construction metadata.

## INV-10
Silhouettes come from authored closed sets, never procedural carving.

## INV-11
Projection contains zero design entropy.

## INV-12
Validity is solved during generation; meaningful diversity is measured after rendering.

## INV-13
Visual richness comes from intentional construction, color architecture, AA/AG, accents, and envelope capability—not artificial pixel-density inflation.

## INV-14
The V5 decision model and V5 Construction/AA/AG form one new canonical pipeline; legacy rendering systems are reference-only.

---

# 45. CANONICAL LOGICAL PASSES

## Pass 1 — Roll Context
Resolve:
- seed;
- complexity;
- Style Context;
- temperament;
- novelty.

## Pass 2 — Slot
Resolve representation capabilities.

## Pass 3 — Family
Choose Family and publish vocabulary.

## Pass 4 — Architecture
Choose Architecture and publish commitments/child schema.

## Pass 5 — Structural Parameters
Resolve:
- coverage;
- fit;
- aperture;
- closure-dependent parameters;
- limb;
- layers;
- bounded dimensions.

## Pass 6A — Material
Resolve material/render behavior.

## Pass 6B — Color Architecture / Chromatic
Resolve:
- semantic color architecture;
- harmony;
- contrast;
- base hue;
- role palette;
- material-aware ramps.

## Pass 7 — Surface
Resolve valid Surface.
Use bounded local repair.
Drop/refund if necessary.

## Pass 8 — Ornament / Detail
Use remaining:
- complexity;
- occupancy;
- Architecture affinities;
- readability constraints.

## Pass 9 — Garment Specification Finalization
Produce one immutable semantic garment specification.

## Pass 10 — NEW Construction Realization
Resolve:
- authored structural pieces;
- authored silhouette;
- bounded geometry parameters;
- region topology;
- edge semantics;
- wrap semantics;
- occupancy footprint;
- occlusion stamps.

## Pass 11 — NEW AA
Resolve visual hierarchy and placement.

## Pass 12 — NEW AG
Rasterize using the new art grammar.

## Pass 13 — Deterministic Projection / Export
Produce final views and Fashion Sense metadata.

## Pass 14 — Quality / Diversity Gate
Evaluate rendered output.

---

# 46. CANONICAL AUTHORED DATA DOMAINS

The new project should conceptually separate:

1. Grammar Library
2. Family Library
3. Architecture Library
4. Material Library
5. Color Architecture Library
6. Surface Library
7. Ornament / Detail Library
8. Structural Asset Library
9. Generated Garment Specification
10. New AA/AG intermediate realization data
11. Rendered Output + Quality Record

Exact class/file layout is implementation-defined.

---

# 47. ONE OWNER / ONE PASS

Every resolvable variable should declare:

```text
owner
resolution_pass
domain
activation condition
constraints
repair policy
visual significance
```

No value should be independently written by multiple stages.

Derived values also have one authoritative derivation stage.

---

# 48. FAMILY AUTHORING SUCCESS CRITERION

Adding a new Family should ideally require:

```text
Family contract
+
one or more Architecture contracts
+
required new structural/art assets
+
optional vocabulary additions
```

It should not require editing core generator control flow.

If every Family requires custom resolver code, the contract system is underpowered.

---

# 49. OUT OF SCOPE FOR FIRST PROTOTYPE

Do not expand the first build into the whole clothing system.

Defer:

- 20–30 Families;
- Idiom implementation;
- Condition implementation;
- separate complexity budgets;
- extended-envelope garment content;
- 16×16 experimental rendering;
- automated diversity-table reweighting;
- procedural silhouette generation;
- universal procedural garment CAD;
- broad bottom/pants expansion unless required by shared infrastructure.

---

# 50. FIRST IMPLEMENTATION TARGET

Build the first real test using:

```text
SAILOR_TOP
    ↓
CLASSIC_SQUARE_FLAP
```

Only.

This is not a retrofit of the old Sailor generator.

This is the first test specimen for the **new V5 pipeline**.

---

# 51. MINIMUM SAILOR FAMILY VOCABULARY

Implement only what the prototype needs:

```text
Family:
SAILOR_TOP

slot:
TOP

closure vocabulary:
PULLOVER

aperture vocabulary:
SAILOR_FLAP

limb:
SLEEVED

layer-slot vocabulary:
NECK_ACCESSORY

material vocabulary:
small validated test set

coverage:
REGULAR initially

architectures:
CLASSIC_SQUARE_FLAP only
```

Keep the prototype narrow.

---

# 52. CLASSIC_SQUARE_FLAP ARCHITECTURE

Initial commitment should include:

- pullover construction;
- Sailor collar/flap topology;
- front V/insert relationship;
- rear flap;
- sleeves;
- optional neck-accessory slot;
- authored standard silhouette;
- standard 8×8 envelope;
- Architecture-specific surface domains;
- Architecture-specific occupancy;
- base complexity cost.

Scoped variables may initially include:

```text
collar_width
rear_flap_depth
neckline_depth
collar_trim
neck_accessory
material
color_architecture
surface
limited ornament
```

Fit can remain diagnostic/deferred until its 8×8 visual significance is proven.

---

# 53. FIRST SAILOR TEST MUST EXERCISE THE NEW FULL PIPELINE

Required path:

```text
NEW Resolver
↓
NEW Family Contract
↓
NEW Architecture Contract
↓
NEW Garment Spec
↓
NEW Construction System
↓
NEW AA
↓
NEW AG
↓
NEW Deterministic Projection
↓
actual 8×8 sprites
↓
Quality / Diversity review
```

That is the point of the prototype.

---

# 54. DO NOT CHEAT THE SAILOR TEST

Do not:

- import an old final Sailor sprite;
- use the old Sailor renderer as the final realization path;
- simply resize old 16×16 output;
- manually repair the final raster;
- special-case chosen test seeds;
- encode one complete garment template and call it generation.

The Architecture must produce genuine bounded design variation through the new pipeline.

---

# 55. WHAT THE FIRST SAILOR BATCH MUST DEMONSTRATE

Generated garments should be:

- recognizably Sailor;
- structurally coherent;
- visibly varied;
- free of Frankenstein combinations;
- readable at native 8×8;
- coherent across front/side/back;
- not dependent on global dark outlines;
- capable of rich but controlled color;
- capable of real fabric-over-fabric layering;
- capable of meaningful free-edge treatment;
- capable of tasteful accents;
- capable of separate Surface and Ornament behavior.

---

# 56. SAILOR IDENTITY REQUIREMENT

The old mini test revealed that low-contrast/no-trim/no-detail variants could lose Sailor identity.

The new system must solve that through stronger Construction + AA/AG.

Do not simply force decoration.

Sailor identity should primarily come from:

- region topology;
- front/rear flap relationship;
- silhouette/mass hierarchy;
- edge structure;
- collar/body organization.

Decoration reinforces identity; it should not be the only source of identity.

---

# 57. FIRST BATCH REVIEW MATRIX

Evaluate:

- Construction identity
- Structural coherence
- Front/side/back continuity
- Palette coherence
- Color richness
- Selective outlining quality
- Free-edge behavior
- Local occlusion
- Material readability
- Surface-domain correctness
- Ornament correctness
- Accent economy
- Diversity across seeds
- Near-duplicate rate
- Native Stardew/Fashion Sense readability
- Whether outputs resemble high-quality native mod art rather than reduced high-resolution artwork

---

# 58. CORPUS-INFORMED RENDERER ACCEPTANCE TARGETS

The new renderer should be capable of:

- native 8×8 authoring;
- Scale 4 export;
- multi-step role-based ramps;
- controlled use above the old 8-colour ceiling;
- selective rather than global outlines;
- Architecture-owned region partition;
- strong 1–2px accents;
- envelope-aware rendering architecture;
- coherent lower-detail side/back realization.

Do not force every garment to match corpus medians.

These are distribution/capability targets.

---

# 59. TESTS TO BUILD WITH THE PROTOTYPE

## Schema
- Absent ≠ None.
- One owner / one pass.
- Architecture cannot introduce Family-illegal options.
- Style Context cannot resurrect illegal options.
- Child variables instantiate only when declared.

## Determinism
- Same seed/config → same Garment Spec.
- Same Garment Spec → same rendered views.

## Repair
- Repair stays inside current variable domain.

## Budget
- All spends are tagged.
- No overspending.

## Occupancy
- Exclusive conflict.
- Conditional-share behavior.
- Overlay behavior.

## Projection
- No RNG after Garment Spec finalization.

## Envelope
- Standard 8×8.
- Synthetic extended-envelope contract tests.

## Color
- Components use semantic roles.
- Views do not independently introduce palette decisions.

## Edge
- Free vs attached behavior is respected.

## Occlusion
- Declared shadow stamps compose by max.

## Quality
- Near-duplicate evaluation interface exists even if the final metric remains provisional.

---

# 60. IMPLEMENTATION FREEDOM

The conceptual architecture above is mandatory behavior, not a demand for exact class/file names.

Claude may choose the cleanest implementation representation.

Claude should challenge any requirement that creates a real contradiction, but should explain the contradiction before changing a locked architectural principle.

---

# 61. REQUIRED IMPLEMENTATION REPORT AFTER FIRST SAILOR BUILD

Report:

1. Did Family + Architecture contracts work without Sailor-specific resolver control flow?
2. Which schema fields were unnecessary?
3. Which missing fields were required?
4. Did authored-piece-first Construction work at native 8×8?
5. Which scoped parameters generated real visual diversity?
6. Which collapsed into near-duplicates?
7. Did Material produce visible differences?
8. Did Color Architecture produce coherent rich palettes?
9. Did the complexity budget improve busyness control?
10. Did semantic occupancy remove special-case exclusions?
11. Did Surface and Ornament stay cleanly separated?
12. Did the new AA/AG produce convincing layered fabric?
13. Did contrast-aware outlining outperform global outlining?
14. Did local occlusion work without crushing ramps?
15. Were side/back views naturally coherent?
16. What percentage of outputs were accepted, near-duplicate, weak-identity, or illegible?
17. What architectural changes are recommended before attempting Blazer?

---

# 62. STOP CONDITION AFTER SAILOR

Do not immediately scale to many Families.

After the first Sailor batch:

```text
STOP
↓
review outputs
↓
review implementation findings
↓
amend architecture if required
```

Only then stress-test:

```text
BLAZER
```

Blazer should test:

- topology-heavy Construction;
- lapels;
- closure;
- layering;
- subtle same-material region separation;
- buttons/pockets;
- semantic occupancy;
- authored geometry.

Then test:

```text
TEE
```

to ensure a simple Family stays simple and does not inherit unnecessary complexity.

---

# 63. FINAL TARGET ARCHITECTURE

Long-term:

```text
ONE GENERIC RESOLVER
       +
DATA-DRIVEN FAMILY VOCABULARIES
       +
DATA-DRIVEN ARCHITECTURE CONTRACTS
       +
NEW SEMANTIC CONSTRUCTION SYSTEM
       +
NEW AA
       +
NEW AG
       +
DETERMINISTIC PROJECTION
       +
POST-RENDER QUALITY / DIVERSITY EVALUATION
```

Adding a new clothing Family should primarily be authoring work, not engine programming.

---

# 64. CANONICAL SUMMARY

Slot establishes representation.

Family defines what can exist.

Design Architecture commits how the garment is built.

The Architecture Contract instantiates only meaningful child variables.

Scoped variables vary that construction without contradicting it.

Style Context only reweights legal possibilities.

Complexity budget and semantic occupancy control visual busyness.

Material defines rendering behavior.

Color Architecture defines chromatic relationships.

Surface and Ornament resolve separately.

The result becomes one immutable semantic Garment Specification.

A **new authored-piece-first Construction system** realizes that specification natively at 8×8.

A **new AA system** organizes visual masses, region hierarchy, accents, focal structure, and contrast distribution using the semantic garment model.

A **new AG system** turns that semantic design into native Stardew/Fashion Sense pixel art using richer role-based ramps, selective contrast-aware edges, material-aware behavior, meaningful tiny accents, local declared occlusion, and small-scale simplification.

Projection introduces zero design RNG and derives all views from the same garment.

Finally, raster-level quality and perceptual distance determine whether the result is meaningfully distinct.

## MOST IMPORTANT IMPLEMENTATION DIRECTIVE

**Do not build the new generator around the old renderer.**

**Do not build the new AA/AG around preserving the old AA/AG.**

**Build the new V5 Decision + Construction + AA + AG + Projection pipeline as one canonical system, using the modded Fashion Sense corpus study as the empirical artistic and technical target.**


---

# AMENDMENTS FROM THE OFFICIAL FASHION SENSE REFERENCE

Added 2026-09-08 from `references/fashion-sense-official/` (official GitHub
`development` branch, wiki, Example Pack, and the C# appearance models;
latest release v7.5.0). Each amendment cites its reference entry. **This is a
targeted audit: only assumptions contradicted or expanded by official behaviour
are changed.**

## Confirmed unchanged

* **§3 / §4 — 8x8 native at Scale 4 as the canonical target.** Confirmed:
  `Scale` defaults to `4.0` "to match the default scale of Stardew Valley
  itself". The empirical 88% finding stands.
* **§5 five concept classes, §6 decision spine, §7 grammar layering, §8 roll
  context, §9 style context.** Untouched — these are our decision architecture
  and the framework has nothing to say about them.
* **§7's insistence that target-system quirks are not universal clothing laws.**
  Reinforced: the FS export contract below is now explicitly its own layer.

## AA-1. `Scale` is a per-direction property, and we had it recorded wrong
* **Was:** the Envelope carried a single `scale`, and `authored/fit.json`
  recorded *"Fashion Sense ignored a top-level Scale field"*.
* **Now:** `Scale` is a property of each direction model
  (`AppearanceModel.cs`: `public float Scale { get; set; } = 4f;`). Our
  experiment set it at the top level of `hat.json`, where it belongs to nothing.
  FS did not ignore it; we never set it. Runtime scaling **is** available.
* **Status:** the false note in `authored/fit.json` is corrected. The
  correction is **untested in-game** — no Example Pack file declares `Scale`,
  so this rests on the C# field and the wiki. Re-test before relying on it.
* **Reference:** BEHAVIOR_MAP A1.

## AA-2. Positions are integers, and a float destroys the whole model
* `Position` is `int X, int Y` (`Position.cs`). A float in `HeadPosition`,
  `BodyPosition` or `StartingPosition` makes Fashion Sense reject the entire
  appearance **silently** — the pack loads with zero appearances.
* This project hit that exact failure and recorded it empirically; it now has a
  source-level explanation, and the exporter asserts integrality before writing.
* **Reference:** BEHAVIOR_MAP A4.

## AA-3. All four directions are mandatory
* A facing whose model is absent draws nothing. There is no mirroring, no
  fallback, no inheritance from another direction. `Flipped` exists to point a
  model at a mirrored region, but the model itself must still be declared.
* The Envelope's "optional directional overrides" remains valid; what is not
  optional is the *existence* of all four direction models.
* **Reference:** BEHAVIOR_MAP A2, A3.

## AA-4. Hair interaction belongs in the architecture, not in art
* `HideHair` and `UseBaldHead` are per-direction properties. `UseBaldHead`
  swaps the farmer to the bald sprite, changing the head silhouette itself.
* The V5 headwear work treated "the hat reads as sitting under the hairstyle"
  as a pure silhouette problem across four capture sessions. It is at least
  partly a declarable behaviour, and is now modelled as an explicit per-base,
  per-direction **hair policy** (`v5/hairpolicy.py`: KEEP / HIDE / BALD).
* Default is KEEP, from measurement: 114 of 116 source hats keep hair.
* **Reference:** BEHAVIOR_MAP B1.

## AA-5. Layering is declarative
* Default draw order is **Pants → Shoes → Shirts → Hair → Sleeves →
  Accessories → Hat**, each over the previous. Hats already draw over hair, so
  a hat reading as *under* the hair is coverage, not layering.
* `DrawOrderOverride` (`Preposition` × `AppearanceType`) moves an appearance
  relative to any other type including `Player`. v7.5.0 allows per-animation-
  frame overrides.
* **Reference:** BEHAVIOR_MAP C1, C2.

## AA-6. Per-slot defaults differ — do not copy a hat's JSON shape to a shirt
* `HideWhileSwimming` and `HideWhileWearingBathingSuit` default **false for
  hats but true for shirts**. v7.5.0 further changed the bathing-suit property
  to override bathing skin when false for shirts/pants/shoes.
* The exporter must resolve defaults per appearance type, not per project.
* **Reference:** BEHAVIOR_MAP G.

## AA-7. `Format` is a real field we never emitted
* `AppearanceContentPack.Format` is a `Version`, defaulting to `1.0.0`.
  Official examples declare `5.3.0` / `6.3.0`. We now emit `7.5.0`.
* **Reference:** BEHAVIOR_MAP A5.

## AA-8. Capability the architecture does not yet model
Recorded so they are decisions rather than omissions:

* **Animation** — `UniformAnimation` / `IdleAnimation` / `MovementAnimation`,
  frames addressed as `StartingPosition + Size * Frame` along +X. Uniform is
  ignored when either of the others is present.
  `EndWhenFarmerFrameUpdates` ties a frame to the farmer's own sprite updates
  and is the documented approach for sleeves and pants.
* **Conditions** — ~45 named conditions (weather, tool state, swimming,
  sitting, mines, health/stamina, `RandomChance`, `GameStateQuery`) gate
  individual frames; a failing frame is skipped. v7.5.0 added `IsMoving` and
  the `NotEqualTo` operator.
* **`Item` / `FromItemId`** — an appearance can also be a real wearable item.
* **`IsPrismatic`**, **`SkinToneMasks`**, **`IsLocked`**, **`AppearanceSyncing`**.
* **Bodies** — 33 properties, the largest model; not in scope for V5.
* **Reference:** BEHAVIOR_MAP E, F, H.

## AA-9. The export contract is now a written layer

§7 diagrams a `FASHION SENSE EXPORT CONTRACT` layer but never specified it.
Minimum contract for any appearance we emit:

```text
REQUIRED
    all four direction models present
    StartingPosition, <Type>Size, and the type's anchor
        (HeadPosition for Hats/Hairs/Accessories,
         BodyPosition for Shirts/Pants/Sleeves/Shoes)
    every Position component an INTEGER
DECLARED
    Format
    DisableGrayscale when colour is baked
    hair policy for hats (HideHair / UseBaldHead)
MUTUALLY EXCLUSIVE
    DisableGrayscale: true  disables ALL colour masks
DEFAULTED BY TYPE
    HideWhileSwimming, HideWhileWearingBathingSuit
```
