# Source Transfer Library

Derived from `catalog.json` + exact-reconstruction `families.json`. Third-party source is read-only.

- appearances: **319**
- deconstructed families: **53**

## Transfer policy

- **construction** — target template owns geometry; source donors never silently rewrite it
- **style** — family tone/value vocabulary may donate style relationships without donating silhouette
- **parts** — only FAMILY_REUSABLE parts with a satisfied target semantic zone are cross-template candidates
- **baseSpecific** — same-source-base only
- **alternateConstruction** — promote to a separate template; never overlay
- **roundTrip** — neutral template/source fidelity is mandatory before variation

## Part kinds

- **STYLE_PROFILE**: family-authored value/tone relationship
- **MATERIAL_PATTERN**: surface treatment that requires a target surface zone
- **MOTIF**: small decoration seated inside a declared surface zone
- **ATTACHMENT**: geometry added at an explicitly declared attachment edge
- **HARDWARE**: small rigid accent attached at an explicitly declared edge/zone
- **REUSABLE_COMPONENT**: proven family-reusable delta not yet semantically specialized
- **BASE_SPECIFIC**: exactly one authored base only
- **ALTERNATE_CONSTRUCTION**: different geometry; candidate template, never a composable part

## Counts

- ALTERNATE_CONSTRUCTION: **108**
- ATTACHMENT: **3**
- BASE_SPECIFIC: **43**
- HARDWARE: **3**
- MATERIAL_PATTERN: **1**
- MOTIF: **2**
- REUSABLE_COMPONENT: **3**
- STYLE_PROFILE: **53**

## Proven cross-template candidates

- **Belt (Chains 3)** — HARDWARE — Alt-Fashion Set / Belt — requires `attachment_edge`
- **Belt (Chains 4)** — HARDWARE — Alt-Fashion Set / Belt — requires `attachment_edge`
- **Neckerchief (3)** — REUSABLE_COMPONENT — Cottagecore Set / Neckerchief — requires `surface`
- **Shawl (2)** — REUSABLE_COMPONENT — Cottagecore Set / Shawl — requires `surface`
- **Suspenders (H)** — REUSABLE_COMPONENT — Cottagecore Set / Suspenders — requires `surface`
- **Beret (Leaf)** — MOTIF — Cottagecore Set / Beret — requires `surface`
- **Bows (Double, Small 2)** — ATTACHMENT — More Accessories and Stuff / Bows — requires `attachment_edge`
- **Decorative Bells (Doubles)** — HARDWARE — More Accessories and Stuff / DecorativeBells — requires `attachment_edge`
- **Earmuffs (Cat)** — ATTACHMENT — More Accessories and Stuff / Earmuffs — requires `attachment_edge`
- **Garland (Dried 2)** — MOTIF — More Accessories and Stuff / Garland — requires `surface`
- **Straw Hat (Messy)** — MATERIAL_PATTERN — More Accessories and Stuff / StrawHat — requires `surface`
- **Veil (Tiara)** — ATTACHMENT — More Accessories and Stuff / Veil — requires `attachment_edge`
