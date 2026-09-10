# Mini Sailor prototype — architecture and schema

Scope: `SAILOR_TOP` / `CLASSIC_SQUARE_FLAP`, 16x16 logical frames, three authored
views (front, side, back) with left mirrored from side.

---

## 1. Stage contract

| Stage | Input | Output | May decide |
|---|---|---|---|
| 1 seed | int | int | nothing |
| 2 resolve | seed | candidate values | which value each variable takes |
| 3 dependency filter | candidate | accept / reject | whether a candidate may exist |
| 4 ResolvedSpec | accepted candidate | `ResolvedSpec` | derived numeric flags |
| 5 architecture | `ResolvedSpec` | `ArchitecturePlan` per view | where fabric is; which edges are free or attached |
| 6 art grammar | `ArchitecturePlan` | ordered `Op` list | how construction reads as pixels |
| 7 render | `Op` list | role/slot/system grids, RGBA | nothing; it executes ops |
| 8 preview | frames | sheets, JSON | nothing |

Two hard directions of travel:

- **No stage may re-decide an earlier stage's variable.** Rendering never asks
  "should this be a wide collar"; it is told.
- **Architecture never shades, art grammar never moves fabric.** Stage 5 emits no
  role. Stage 6 emits no new geometry.

---

## 2. Variables

Eight, no more. Values carry weights that define a prior, not a quality ranking.

| Variable | Values |
|---|---|
| `fit` | FITTED, REGULAR, RELAXED |
| `material` | COTTON, WOVEN, LIGHT_KNIT |
| `collar_width` | NARROW, STANDARD, WIDE |
| `rear_flap_depth` | SHALLOW, STANDARD, DEEP |
| `neckline` | SHALLOW_V, STANDARD_V |
| `trim_style` | NONE, SINGLE, DOUBLE |
| `center_detail` | NONE, TIE, BOW |
| `color_architecture` | DARK_BODY_LIGHT_COLLAR, LIGHT_BODY_DARK_COLLAR, MONOCHROME_WITH_CONTRAST_TRIM, LOW_CONTRAST_WITH_ACCENT |

Numeric consequences live beside the vocabulary so the whole design space is one
file:

```
COLLAR_SPAN   NARROW (4,11)   STANDARD (3,12)   WIDE (2,13)
FLAP_DEPTH    SHALLOW 5       STANDARD 7        DEEP 9      (capped at 9)
V_DEPTH       SHALLOW_V 5     STANDARD_V 7
FIT           FITTED tapers the lower body by 1 cell per side
              RELAXED widens collar span and flap depth by 1, clamped to (2,13) and 9
MATERIAL      COTTON  crisp edge, 1 fold
              WOVEN   crisp edge, 2 folds
              LIGHT_KNIT  soft edge, hem rib, no folds
```

---

## 3. Dependency rules

Data, not code paths. Each is `(id, reason, predicate)`; the predicate returns
True when the candidate is **invalid**. The resolver rerolls with a derived
sub-seed, up to 40 attempts, and logs every rejection into the spec.

| Rule | Rejects |
|---|---|
| `WIDE_COLLAR_NEEDS_BODY` | WIDE collar + SHALLOW flap |
| `NARROW_COLLAR_CANNOT_CARRY_DEEP_FLAP` | NARROW collar + DEEP flap |
| `DOUBLE_TRIM_NEEDS_COLLAR_AREA` | DOUBLE trim under 9 collar columns |
| `DOUBLE_TRIM_NEEDS_FLAP_DEPTH` | DOUBLE trim under 6 flap rows |
| `KNIT_CANNOT_HOLD_DOUBLE_TRIM` | LIGHT_KNIT + DOUBLE trim |
| `BOW_NEEDS_OPEN_NECKLINE` | BOW on a SHALLOW_V |
| `CENTER_DETAIL_NEEDS_OPENING` | TIE or BOW with no V opening |

A **pinned** combination that violates a rule raises instead of drifting, so the
controlled comparison pairs cannot be silently altered by the resolver.

---

## 4. ResolvedSpec

The contract. Serialisable; one JSON file per variant in `out/specs/`.

```jsonc
{
  "id": "v02_standard_standard", "seed": 4838175, "attempt": 0,
  "family": "SAILOR_TOP", "architecture": "CLASSIC_SQUARE_FLAP",
  "fit": "REGULAR", "material": "WOVEN",
  "collar_width": "STANDARD", "rear_flap_depth": "STANDARD",
  "neckline": "STANDARD_V", "trim_style": "SINGLE",
  "center_detail": "TIE", "color_architecture": "DARK_BODY_LIGHT_COLLAR",
  "palette_family": "HARBOUR_BLUE",
  "palette": { "body": {...}, "collar": {...}, "trim": {...}, "accent": {...} },
  "derived": {
    "collar_left": 3, "collar_right": 12, "collar_columns": 10,
    "flap_depth_rows": 7, "v_depth_row": 7, "fit_taper": 0,
    "relaxed_widening_applied": false,
    "crisp_collar_edge": true, "hem_rib": false, "fold_density": 2,
    "trim_lines": 1, "has_center_detail": true,
    "collar_body_contrast": 155.6, "trim_collar_contrast": 155.6
  },
  "rejected": [ ... ], "pinned": { ... }
}
```

`derived` is where design language becomes numbers. Everything downstream reads
`derived`, never the value strings, except where a value names a shape (TIE vs BOW).

---

## 5. Architecture decisions (stage 5)

Regions are described per row as inclusive spans, never as bitmaps, so geometry
scales with the variables instead of being authored per combination.

**Front collar.** Two leaves. The inner boundary is the V edge, interpolating
from the neck gap to the apex at `v_depth_row`. The outer boundary holds the full
shoulder span for the first three rows, then converges on a **convex curve**
(`t**1.8`) so the leaf keeps width down the chest and only pinches at the apex. A
linear outer edge produced 2-cell leaves that read as a drawn line rather than a
collar.

**Rear flap.** Rows 0 to `flap_depth_rows`, spanning the collar columns, with a
1-then-2 cell inward taper over the last three rows. Never a rectangle.

**Side.** One collar run crosses the whole shoulder from the back flap to the
front leaf, then a tab descends at each end. Front is +x in the right-facing
view, measured from installed vanilla shirts: the overalls bib and the sailor tie
both sit at higher x.

**Edge classification — the important part.**

```
ATTACHED   sewn or continuous with the body/collar. Never outlined.
FREE       hangs. Terminates the fabric and occludes what is behind it.
```

For the rear flap: row 0 is ATTACHED across its whole width; the side columns are
ATTACHED down to the shoulder line and FREE below it; the bottom row is FREE.
The flap therefore has no border along its top or upper sides, which is what
separates "fabric lying on the back" from "square pasted on the back".

For the front leaves the V edge is always FREE. The outer edge is ATTACHED at the
shoulder and becomes a second FREE edge only where the leaf is at least three
cells wide, because two outlines on a narrower leaf consume all its fabric.

**Occlusion** is computed from known geometry, not by scanning neighbours: the
body row under the flap's free bottom edge, and the body cell outside each free
side column.

---

## 6. Art grammar decisions (stage 6)

Six named rules. Each op records the system that emitted it, so any pixel is
attributable — `out/batch.json` lists the systems present in each garment.

| Rule | Behaviour |
|---|---|
| 1 OUTLINE POLICY | an outline is allowed on a FREE edge and forbidden on an ATTACHED edge |
| 1a CONTRAST-AWARE OUTLINE | a free edge earns the darkest step only when collar/body contrast is under 45; above that it takes the collar's own shadow. Installed vanilla sailor tops carry no outline around a white collar on navy: the value change is the edge |
| 2 OCCLUSION | body cells behind a free edge take the body **shadow**, never the darkest step, so an edge plus its shadow is not a two-pixel black bar |
| 3 LIGHT FIELD | screen upper-left, per region |
| 4 LIFT GRADIENT | a hanging panel is lighter where it lies flat on the shoulders and darker toward its free edge |
| 5 TRIM | parallel to the free edge, inset 1 (and 3 for DOUBLE), skipped on leaves under three cells wide |
| 6 MATERIAL | crisp materials take a hard free edge; knit takes a soft one and gains a hem rib |

---

## 7. Colour

Literal colours only. No derivation engine, no blending, no perceptual space.

Six families each supply `dark`, `light`, `mid` and `accent` four-step ramps.
`COLOR_ARCHITECTURE` maps ramps onto the four garment slots:

| Architecture | body | collar | trim | accent |
|---|---|---|---|---|
| DARK_BODY_LIGHT_COLLAR | dark | light | dark | accent |
| LIGHT_BODY_DARK_COLLAR | light | dark | light | accent |
| MONOCHROME_WITH_CONTRAST_TRIM | dark | dark | light | light |
| LOW_CONTRAST_WITH_ACCENT | mid | dark | mid | accent |

`MONOCHROME` deliberately gives the collar the body's own ramp: it is invisible
by colour, so its identity is carried entirely by the free-edge outline and the
trim. That case exists to exercise the contrast-aware outline path.

---

## 8. Render contract

`role` is one of base / light / shadow / deep. `slot` is one of body / collar /
trim / accent. Colour is `palette[slot][role]`, applied once.

Ops are applied in order, last writer wins, and an op is discarded if it falls
outside the body silhouette, so no stage can grow the garment beyond the torso.

Fashion Sense target: 16x16 logical, 16x64 atlas, front/right/left/back, Scale 2,
`BodyPosition (0,32)`, binary alpha, nearest-neighbour, native sleeves.
