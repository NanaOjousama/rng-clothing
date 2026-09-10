# RNG Clothing Color Grammar

## Pipeline position

The color system operates after structural garment grammar and material selection:

`Garment grammar → construction topology → material behavior → palette story → active semantic roles → directional placement → worn-scale validation`

Palette never selects garment family, rarity, or construction. It expresses an already coherent garment.

## Semantic roles

The machine contract is [`color_roles.json`](../../specs/palettes/color_roles.json).

| Role | Purpose | Typical coverage |
|---|---|---|
| `DeepShadow` | deepest recess and selected contour anchor | very low |
| `StructuralDark` | seams, layer boundaries, pockets, cuffs, controlled contours | low–moderate |
| `PrimaryFabric` | dominant garment fabric | high |
| `PrimaryFabricLight` | restrained primary light-facing plane | low |
| `SecondaryFabric` | meaningful second fabric or layer | moderate when present |
| `SecondaryFabricLight` | second material's own light-facing plane | very low–low |
| `Trim` | repeated edge/termination system | low |
| `Accent` | localized high-attention color | very low |
| `OptionalMotif` | original motif cluster | very low |
| `OptionalMetal` | button, zip, buckle or clasp hardware | minimal |

Not every garment activates every role. A tee may use four roles; formal layering may use seven; a statement garment may add one motif. Unused roles remain absent.

## Ramp rules

### Shadow behavior

- Derive fabric shadows by moving through lightness, hue and chroma—not by multiplying RGB.
- DeepShadow may be shared between fabrics when it remains legible against both.
- StructuralDark must remain distinct from DeepShadow and the dominant midtone at Farmer scale.
- Collar recess, underarm, overlap and hem overhang receive the deepest values; flat fabric interiors do not.

### Highlight behavior

- PrimaryFabricLight describes a plane or edge with form significance.
- Highlights are optional on small or limited designs.
- Natural cloth generally uses softer, lower-chroma highlights; crisp formal/synthetic material may use sharper plane separation.
- Do not add light pixels merely because a role exists.

### Shared darks and neutrals

A small set of chromatic dark concepts may recur across palette stories: violet charcoal, blue graphite, warm charcoal, forest ink, plum charcoal, or soft slate. Recurrence is cohesion, not convergence, provided dominant fabrics and topology differ.

## Role-set examples

- **One-fabric tee:** DeepShadow, StructuralDark, PrimaryFabric, PrimaryFabricLight; optional Accent.
- **Open shirt/cardigan:** add SecondaryFabric and its light if the inner garment is substantial.
- **Knit:** use Trim for ribbing and OptionalMotif for a coherent repeat; do not create a second fabric ramp for every diamond.
- **Sport shell:** two broad fabrics, quiet trim and one vivid accent.
- **Formal layering:** outer fabric, broad shirt/inner fabric, lapel/trim and optional tiny hardware.
- **High-contrast statement:** one light/dark dominant field relationship and one focal accent; do not activate every vivid role equally.

## Color topology follows construction

- Single fabric follows the whole article mass.
- Open layers allocate broad outer leaves and a substantial inner field.
- Shoulder/sleeve blocks continue over the shoulder and onto sides/back.
- Yokes wrap across upper sides and back.
- Collar/cuff/hem triads repeat at actual garment terminations.
- Wrap and moto color regions follow overlapping panel masses.
- Tabard color occupies a broad over-panel, never a stripe.

## Directional behavior

- **Wrap:** yokes, sleeve bands, ribbed hems, sashes, all-over fabric patterns.
- **Compress:** one cardigan edge, one lapel plane, one pocket edge, inner-shirt field.
- **Terminate:** front placket, chest motif, diagonal harness accent, zipper pull.
- **Disappear at back:** front opening, tie knot, paired chest pockets.
- **Reconstruct at back:** rear collar, yoke, hood, tailored seam/vent, knit field, sash or tabard attachment.

Left/right asymmetry is preserved when the garment is structurally asymmetric. Back views use coherent rear fabric fields rather than mirrored front layouts.

## Rarity neutrality

- No hue is Common, Rare, Legendary, or Mythic.
- Common may be pastel, colorful, pale or high contrast when its structural complexity remains Common.
- Premium garments may be monochrome, earth-toned or neutral.
- Black/gold/purple, neon, ivory, metal and celestial colors are not automatic rarity signals.

## Quality gates

Reject when the dominant fabric cannot be read as a coherent field; StructuralDark becomes a uniform outline; two layers merge at gameplay size; Accent occupies multiple unrelated regions; hue-shifted shadow reduces value readability; or the palette only works on the isolated sprite rather than the worn Farmer.
