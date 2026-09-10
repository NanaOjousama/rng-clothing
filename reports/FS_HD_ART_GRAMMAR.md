# Fashion Sense High-Detail Art Grammar

Status: implemented and statically validated for the controlled Mistral jacket comparison. B and C have not yet been judged on a live Farmer in-game, so this report does not claim final runtime beauty.

## Scope and invariants

This pass changes only Fashion Sense renderer-owned art grammar. All three treatments use the unchanged `lifestyle-v2-16` semantic recipe:

- category: Lifestyle;
- archetype: JACKET;
- rarity: Rare;
- relaxed/open/wide-collar/center-open construction;
- visible inner layer;
- structured hem;
- split outer panels;
- cool-neutral palette family;
- no micro details.

The Fashion Sense runtime contract is also unchanged: 16×16 logical frames, `Scale: 2`, `BodyPosition: (0,32)`, direction order front/right/left/back, native animated sleeves, and one recolorable outer-fabric mask. The vanilla renderer and its Mistral output remain byte-equivalent to the existing V2 renderer.

## Installed Stardew 1.6.15 study

The study read the installed native assets directly:

- `Characters/Farmer/shirts.png`, 256×608;
- `Characters/Farmer/farmer_base.png`, 288×672;
- `Data/Shirts.json` for sprite index and default dye data.

The quantitative shirt sample contains 34 representative garments and all four directions: 136 native 8×8 frames across T-shirts, sweaters, button shirts, jackets, and sailor tops. It is a tendency study, not a source of copied pixels.

Measured tendencies:

- opaque area: 53–64 pixels, median 59;
- meaningful rendered colors: 3–11, median 6;
- luminance range: median 154.26 in 8-bit sRGB-weighted luminance;
- exterior median was 38.99 luminance units darker than interior at the median frame;
- 83.3% of the darkest luminance quartile lay on the exterior at the median frame;
- every sampled garment frame was one connected opaque component;
- no sampled frame contained an isolated opaque garment pixel.

The darkest-edge tendency has exceptions. A motif or pale collar can make a particular exterior cell lighter, so V1’s lesson is not “outline every region in black.” The reusable rule is hierarchy: establish the clothing silhouette first, reserve nearly-dark values for real recesses, and use weaker internal boundaries only when they explain construction. Farmer pixels use the same separation principle: anatomy and neighboring materials stay readable through compact dark edge clusters rather than soft transitions.

The complete measurements are in `output/fashionsense/art-grammar-test/vanilla_edge_study.json`.

## Explicit edge and shade roles

The `FS_HIGH_DETAIL` profile uses these roles, in priority order:

| Role | Mask value | Purpose |
|---|---:|---|
| `EXTERIOR_CONTOUR` | 48 | Darkest garment value; separates the occupied silhouette and intentional neck opening from Farmer/body/background. |
| `DEEP_CREASE` | 68 | Panel overlap, lapel recess, collar recess, or comparably deep fold. |
| `STRUCTURAL_EDGE` | 96 | Weaker yoke/hem/construction boundary. It is not applied around every region. |
| `SHADOW` | 128 | Grouped lower-facing cloth mass. |
| `BASE` | 184 | Main outer-fabric mass. |
| `LIGHT` | 220 | Connected upper-facing cloth clusters. |
| `OPTIONAL_HIGHLIGHT` | 238 | Sparse attached pairs in C only. |

The ramp is grayscale in the pack and Fashion Sense multiplies it by the existing default cool-neutral dye `(112,130,145)`. At that tint, the outer role colors range from `(21,24,27)` contour through `(80,93,104)` base to `(104,121,135)` optional highlight. The contour is a hue-related near-black, not absolute black.

The fixed inner layer retains the existing cool-neutral secondary fabric: shadow `(117,127,137)`, base `(181,193,199)`, and light `(226,233,232)`. Its light is now limited to a short two-row cluster instead of running down the opening.

## Contrast validation

Validation uses both 8-bit perceived sRGB luminance and linear WCAG relative luminance. It does not use raw RGB distance as its sole proxy.

At the default dye, the implemented deltas are:

- exterior contour → base: 67.45 sRGB luminance and 0.096 WCAG luminance;
- shadow → base: 27.44 sRGB luminance;
- base → light: 18.51 sRGB luminance;
- outer base → inner base: 99.85 sRGB luminance.

The validator rejects a mask ramp when any required separation falls below its declared threshold. It also checks that the lighter inner layer cannot collapse into the outer panels.

These checks reject mud, but they do not prove attractiveness.

## Pixel-cluster and Stardew-blend rules

The high-detail renderer follows this priority:

1. body/anatomical coverage;
2. silhouette;
3. construction;
4. layering;
5. shading;
6. seams/cuffs/trim;
7. micro detail.

Implementation rules:

- all pixels are placed on the authoritative 16×16 integer grid;
- the occupied garment stays one connected component;
- light and shade use connected masses instead of the prior checker-like scatter;
- optional highlights are attached two-pixel clusters, with at most four cells per direction;
- default-tint frames use at most ten opaque colors; B and C use five to nine depending on direction;
- no texture speckles, gradients, antialiasing, resampling, or fractional transforms;
- a high-detail canvas is not a fill target: unused cells remain valid silhouette space;
- exterior contour owns silhouette separation; deep crease and structural edge cannot become duplicate all-purpose outlines.

## A/B/C treatments

### A — Current

A is byte-for-byte the corrected runtime-tested Mistral POC texture:

`49b1574211e70935a8c9d2c064f99874655d7080c9d055b2bcfc19acc4141ce5`

No pixel, mask, position, or metadata from that baseline was altered to manufacture the comparison. Its problem is visible at gameplay size: mid-value outer edges blend into the cloth mass, scattered light clusters make the body muddy, and the inner layer reads as a uniform light stripe.

### B — Stronger Stardew

B retains A’s exact structural regions and silhouette. Only art-role assignment changes:

- every true exterior cloth edge receives the darkest contour role;
- panel/inner-layer overlaps receive deep crease selectively;
- yoke and hem use the weaker structural edge;
- upper cloth lights become connected clusters;
- the inner-layer light is shortened;
- optional highlights are omitted.

Result: B is materially crisper and more separable than A. Its limitation is deliberate: the unchanged broad inner opening and two-row hem still look mechanically regular. B proves the outline/value grammar, not final construction polish.

### C — Polished HD

C applies the same edge hierarchy, then makes bounded renderer-level region refinements without changing the recipe, silhouette, coverage envelope, palette family, or footprint.

Exact construction ownership changes:

- front: cells `(6,5)` through `(6,13)` become left outer panel and `(9,5)` through `(9,13)` become right outer panel, narrowing the visible torso opening from four cells to two;
- front: row-14 hem cells `x=1..5` and `x=10..14` return to their respective outer panels, leaving one intentional lower hem row;
- back: row-14 hem cells `x=1..7` and `x=8..14` return to left/right outer panels;
- right: inner-layer cells `x=10..11, y=5..13` become outer panel, and row-14 hem cells `x=4..9` become outer panel;
- left mirrors the right-side changes (`x=4..5, y=5..13`; row-14 `x=6..11`).

No occupied cell is added or removed. The shoulder/body coverage envelope is therefore unchanged and still passes in all four directions.

C also adds:

- paired diagonal lapel light/crease stair-steps;
- four-pixel maximum attached highlight clusters;
- a restrained back-yoke rim instead of flat fill;
- a narrower side opening;
- a one-row hem identity instead of a thick horizontal band.

## Visual self-review

At the exact 32×32 Scale-2 footprint:

- A remains weak and muddy;
- B clearly fixes silhouette separation and reads more like Stardew clothing;
- C improves composition as well as detail: the panels occupy the body, the inner layer reads as an underlayer, and the hem/yoke no longer dominate as bars.

C is more attractive than A in the offline comparison and is not merely more detailed. It provisionally passes this art-grammar test. That judgment is intentionally limited: no reliable Farmer composite is available, and B/C still require a live in-game comparison before C can be called production-ready.

The weakest remaining view is the side lapel. It now has a coherent descending cluster and better panel-to-opening ratio, but it remains more diagrammatic than the front at normal zoom. Adding speckles or extra trim would not solve that; a future general FS jacket grammar will need more than one side-construction template.

## Validation result

Static validation passes:

- A exactly matches the corrected current POC;
- B/C native files are 16×64 RGBA8 with binary alpha and explicit unfiltered scanlines;
- all four logical frames are connected and non-overlapping;
- all previews are exact integer nearest-neighbor expansions from native logical output;
- body coverage passes front/back/left/right;
- the intentional front neck opening remains transparent;
- native sleeve coloring remains enabled and uses deep/base/light values from the outer mask;
- `Scale: 2`, `BodyPosition: (0,32)`, 16×16 frame size, and source positions remain unchanged;
- pack format targets Fashion Sense 7.5.0 and contains B/C only;
- the existing vanilla Mistral PNG remains byte-equivalent to the V2 vanilla renderer.

See `output/fashionsense/art-grammar-test/validation.json` for machine-readable values. Its explicit `beautyClaim` is `NOT_AUTOMATED`.

## Test pack

The isolated pack is:

`test-packs/fashionsense/RNG-Clothing-HD-Art-Grammar-Test/`

It contains:

- **Mistral Stronger Stardew** (B);
- **Mistral Polished HD** (C).

Copy that whole folder into `Stardew Valley/Mods/`, with Fashion Sense 7.5.0 installed separately, then fully restart SMAPI so it discovers the new content-pack manifest. Use `fs_add_mirror` if needed and compare the two entries in the Hand Mirror’s Shirts category. Keep the outer-fabric tint near `(112,130,145)` for the controlled test.

The project does not install this pack automatically.
