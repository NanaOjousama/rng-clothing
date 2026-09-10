# Material Color Behavior

The machine-readable rules are in [`material_color_behavior.json`](../../specs/palettes/material_color_behavior.json). Material changes how semantic roles are spaced and placed; it never chooses rarity.

## Material summary

| Material | Value behavior | Color/texture behavior | Key rejection |
|---|---|---|---|
| Cotton/tee | stable midtone, modest shadow/light steps | broad clean field; one graphic or band | noisy texture or formal shine |
| Woven shirt | crisp collar/placket/cuff separation | ordered checks/stripes aligned to panels | center stripe masquerading as placket |
| Knit | close-to-moderate spacing | soft ramps, coherent ribbing/repeats | random speckle |
| Sweatshirt | soft moderate spacing, deeper ribbed edges | smooth fleece-like field; graphic/panel intentional | tee-flat hem or noisy fleece |
| Cardigan | soft outer ramp, clear inner-layer boundary | knit edges/cuffs/hem form one system | bright narrow center or hard lapel lighting |
| Denim/workwear | durable midtone, broader recess separation | large pockets, yoke, sparse wear cue | distressed noise or military default |
| Utility shell | clear planes around pockets/overlap | disciplined panels and one functional accent | tan/olive lock-in or harness clutter |
| Sport shell | crisp value/color blocks | minimal texture; bright accent can lead locally | every role saturated or fragmented neon |
| Bomber/outerwear | rounded shell planes, dark gathered bands | optional lining/sleeve contrast | straight hem or excessive gloss |
| Blazer/formal | clean broad hierarchy | sharp sparse lapel planes, minimal texture | black/gold shorthand or bright center slit |
| Ceremonial | broad layer separation with quiet fields | one signature material/focal system | multiple spectacle hooks |

## Material-specific hue shifting

Hue shift follows story and material together:

- Cotton and sweatshirt shadows often become slightly cooler or less saturated.
- Rustic woven/workwear can descend into warm charcoal, plum-brown, indigo or green-brown.
- Knit shifts should be gentle so its ramp remains soft.
- Sport and utility shells benefit from a shared cool/chromatic structural dark that cleanly separates panels.
- Formal fabric uses chromatic near-darks and sparse crisp highlights; black is optional.
- Ceremonial fabric may use a signature hue, but supporting roles must step down in saturation.

These are tendencies, not fixed hue rotations.

## Pattern interaction

- Knit patterns stay inside the knit ramp or add one controlled motif role.
- Woven checks/stripes use stable intervals and respect collar/placket/pocket boundaries.
- Workwear seams use StructuralDark and occasional PrimaryFabricLight; they do not need a unique stitch color everywhere.
- Sport shells use blocks as their primary surface system and usually avoid texture.
- Formal and ceremonial patterns remain subordinate to collar/lapel/layer geometry.

## Cross-material layering

Each substantial material receives its own coherent ramp only when enough area exists to read it. A cardigan over a shirt can justify primary and secondary ramps. A tiny tie, button or patch should use Accent, Trim or OptionalMetal instead of creating another fabric ladder.

At layer boundaries, value separation is mandatory even when hues are analogous. The renderer should prefer a readable garment relationship over subtle real-world color similarity.
