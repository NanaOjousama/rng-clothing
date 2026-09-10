# RNG Clothing — Hybrid Garment Compiler Study Guide v3

## Final design philosophy

The generator has two separate jobs:

### A. Architecture Authoring / Learning
Use **real-world clothing photos + technical fashion flats + the neutral translation flat** to learn what a garment physically is.

This produces a **versioned architecture definition**.

### B. Normal Procedural Generation
Use the **versioned architecture database** to autonomously generate original clothing.

Normal generation must NOT depend on Codex loosely remembering how a garment looks and must NOT reinterpret a real-world photo on every roll.

---

# 1. FINAL NORMAL GENERATOR

```text
SEED
 ↓
RARITY
 ↓
GARMENT FAMILY
 ↓
LOAD VERSIONED ARCHITECTURE
 ↓
DESIGN INTENT
 ↓
FIT PROFILE
 ↓
COMPATIBLE COMPONENT GRAPH
 ↓
MATERIAL
 ↓
CANONICAL GARMENT MODEL
 ↓
PHYSICAL VALIDITY
 ↓
FRONT / RIGHT / BACK / LEFT PROJECTION
 ↓
SEMANTIC FLAT DEBUG PREVIEW
 ↓
PIXEL-GRAMMAR COMPILER
 ↓
SEMANTIC PIXEL REGIONS
 ↓
PALETTE
 ↓
RARITY POLISH
 ↓
PROVEN V5/HD RENDERER
 ↓
FARMER COMPOSITE
 ↓
QUALITY + DIVERSITY GATE
 ↓
ACCEPT / REROLL
```

The **canonical garment model** is the key new layer.

It is the single structured source from which all four directions are derived.

---

# 2. ARCHITECTURE AUTHORING MODE

Use this only when:
- adding a new garment family;
- repairing a weak architecture definition;
- learning a construction feature the project does not yet understand.

```text
REAL-WORLD PHOTO / TECHNICAL FLAT
 ↓
EXTRACT PHYSICAL CONSTRUCTION
 ↓
MAP FEATURES TO NEUTRAL FLAT
 ↓
DEFINE COMPONENT GRAPH
 ↓
DEFINE ATTACHMENT RULES
 ↓
DEFINE DIRECTIONAL VISIBILITY
 ↓
DEFINE FIT VARIANTS
 ↓
DEFINE PIXEL PRIORITY
 ↓
VALIDATE
 ↓
SAVE VERSIONED ARCHITECTURE DATA
```

The real image is the **physical truth**.
The neutral flat is the **translation/debug canvas**.
The structured architecture file is the **production truth**.

Generated instructional art is never physical ground truth.

---

# 3. EXAMPLE — POLO

A polo should be represented compositionally:

```text
POLO_SHIRT
=
T_SHIRT / KNIT_BODY
+
FOLDED_COLLAR
+
SHORT_CENTER_PLACKET
```

Canonical model example:

```text
body.type = knit_shirt
body.fit = regular
neck.type = folded_collar
opening.type = short_placket
opening.end = upper_chest
sleeve.type = short
hem.type = straight
rear.collar_band = true
rear.opening = false
```

Directional projection:

**FRONT**
- both collar leaves;
- short placket;
- both sleeves.

**RIGHT / LEFT**
- one collar fold;
- sleeve;
- side torso;
- no fake full placket.

**BACK**
- rear collar band;
- uninterrupted knit back.

Pixel priority:
1. collar;
2. correct short placket;
3. sleeve/shoulder silhouette;
4. hem;
5. optional tiny buttons.

---

# 4. WHY THE CANONICAL MODEL EXISTS

Without it, Codex can independently improvise:
- front;
- side;
- back.

That causes impossible clothing.

With it, the generator first builds ONE garment:

```text
BODY
COLLAR
OPENING
ARMHOLE
POCKETS
HEM
REAR STRUCTURE
```

Then each direction is only a view of that same object.

---

# 5. COMPONENT GRAPH

Reusable components include:

- body
- collar
- lapel
- hood
- sleeve
- armhole
- opening
- placket
- zipper
- belt
- pocket
- yoke
- waistband
- hem
- cuff
- rear panel
- lining
- ribbing
- storm flap
- vent

Every component requires:

```text
component id
parent attachment
compatible families
compatible materials
visible directions
wraparound behavior
pixel priority
silhouette effect
```

Random selection only happens inside family-compatible options.

Never generate:

```text
random collar
+ random zipper
+ random belt
+ random pockets
```

without compatibility validation.

That creates Frankenstein clothing.

---

# 6. RARITY

Rarity still rolls FIRST.

Rarity controls:
- allowed garment-family pool;
- architecture-complexity budget;
- surface-design budget;
- sophistication ceiling.

Rarity does NOT control basic art competence.

### Common
Simple everyday architecture. Clean finished pixel art.

### Uncommon
More fit, layering, material, and construction variation.

### Rare
Premium but restrained. Better architecture and finish, not spectacle.

### Legendary
Signature construction/silhouette/theme. Strong identity. Spectacle only when coherent.

---

# 7. DESIGN INTENT

After family selection, roll ONE dominant design idea.

Example:

```text
CARDIGAN
intent = ACADEMIC

dominant:
wide V + clean inner shirt

supporting:
ribbed edge

avoid:
heavy pockets
large motif
random asymmetry
```

Another:

```text
CARDIGAN
intent = RELAXED_WEEKEND

dominant:
wide open front

supporting:
large lower pockets

fit:
boxy relaxed
```

This produces meaningful variety inside one family without changing its identity.

---

# 8. FIT PROFILE

Male / female / unisex remain proportion profiles.

Do not maintain separate color-coded gender databases.

Examples:

```text
MASC_RELAXED
broader shoulder tendency
low waist suppression
normal-long body
relaxed volume
```

```text
FEM_FITTED
narrow-medium shoulder
medium waist suppression
normal-cropped body
fitted volume
```

```text
UNISEX_BOXY
medium shoulder
no waist suppression
normal body length
boxy volume
```

Any compatible garment may use these tendencies.

---

# 9. MATERIAL

Material is selected after architecture and before pixel rendering.

Material influences:
- stiffness;
- fold behavior;
- ribbing;
- seam prominence;
- value spacing;
- highlight behavior;
- bulk.

Material never invents garment architecture.

---

# 10. THE NEUTRAL FLAT

Keep `REAL_TO_PIXEL_TRANSLATION_FLAT.png`.

But its role is now:

**authoring + debugging visualization**

It is NOT the production garment itself.

Useful debugging chain:

```text
CANONICAL MODEL
 ↓
SEMANTIC FLAT
 ↓
PIXEL-GRAMMAR MAP
 ↓
FINAL SPRITE
```

If a weird line appears:

- wrong in canonical model → architecture/design bug;
- model correct but flat wrong → directional projection bug;
- flat correct but pixel map wrong → pixel compiler bug;
- pixel map correct but sprite wrong → renderer bug.

This is how we stop guessing where regressions came from.

---

# 11. REPRODUCIBILITY

Every accepted garment must save:

```text
seed
rarity
garment family
architecture version
design intent
fit profile
components
component parameters
material
semantic regions
palette
rarity polish profile
renderer route
```

Same seed + same architecture/data version must reproduce the same semantic recipe.

---

# 12. REAL-WORLD STUDY POLICY

Real-world clothing is used to:
- create architecture definitions;
- validate architecture;
- repair architecture.

It is NOT copied.

Do not copy:
- exact pixels;
- exact graphics/logos;
- branding;
- exact print artwork.

Extract:
- silhouette;
- collar/opening;
- armhole/sleeve relationships;
- panel topology;
- belts;
- pockets;
- yokes;
- hems;
- front/side/back behavior.

---

# 13. PROVEN RENDERER LAW

The V5/HD renderer is the frozen drawing backend.

The renderer:
- receives semantic structure;
- executes pixel construction;
- does not invent what a polo/blazer/cardigan should be.

Do not rewrite the renderer because the design generator made a bad garment.

Fix upstream architecture/design data first.

---

# 14. QUALITY GATE

Reject:
- physically impossible garment construction;
- side view that is merely squeezed front art;
- back copied from front;
- floating colored lines;
- belts that vanish on side/back;
- vest side that reads like a sleeve;
- hoodie whose hood disappears on back;
- sailor top without rear sailor panel;
- cardigan rendered as blazer;
- polo with full-length placket;
- design that is structurally too similar to accepted garments;
- detail that only works at 8× zoom.

Farmer gameplay-scale appearance is authoritative.

---

# 15. FINAL PRINCIPLE

**Your real-world study workflow teaches the generator.**

**The structured architecture/compiler workflow runs the generator.**

That gives the project both:
- human fashion realism;
- procedural reproducibility.
