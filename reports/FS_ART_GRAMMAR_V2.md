# Fashion Sense Permanent High-Detail Art Grammar V2

Status: implemented and statically validated across four unchanged Generator V2 recipes. This four-garment set has not yet been judged on a live Farmer, so community-quality parity and final runtime beauty remain unconfirmed.

## Scope and preserved contracts

This pass changes only the optional Fashion Sense high-detail renderer and its test outputs. It does not change Generator V2 semantic recipes, recipe validation, rarity, palette families, the vanilla renderer, TFWR, or the established Fashion Sense runtime contract.

Preserved runtime values:

- logical frame: 16×16;
- texture: 16×64 in front/right/left/back order;
- `Scale`: 2;
- `BodyPosition`: `(0,32)`;
- native animated arms with `SleeveColors`;
- binary-alpha, direct logical-pixel construction;
- no antialiasing, high-resolution source render, or downsampling.

`reports/GENERATOR_RENDERER_MIGRATION.md`, listed in the task's reading set, was not present in the project. The implemented boundary was verified directly from the existing renderer modules: V2 recipes contain semantics only, while structural coordinates and Fashion Sense fields remain inside the optional backend.

## Control recipes

No new recipes or style profiles were created.

| Recipe | Garment | Archetype | Rarity | Reason selected |
|---|---|---|---|---|
| `lifestyle-v2-16` | Mistral Lapel Layer Jacket | JACKET | Rare | layered panels, inner layer, wide collar, and the only prior permanent-FS comparison candidate |
| `lifestyle-v2-11` | Harbor Yoke Work Shirt | BUTTON_SHIRT | Rare | tailored closure plus yoke and lower-band semantics |
| `lifestyle-v2-19` | Garnet Yoke Top | SAILOR_TOP | Rare | dominant yoke/collar construction across directions |
| `lifestyle-v2-05` | Hearth Ribbed Sweater | SWEATER | Common | tests restraint, cloth mass, ribbing, and reduced shade-role activation |

The comparison uses the prior `POLISHED_HD` Fashion Sense Mistral as the jacket baseline. No prior Fashion Sense render existed for the other three recipes, so their existing vanilla V2 sprites are labeled as the baseline rather than inventing a fake “previous FS” result. Vanilla 8×8 at Scale 4 and FS 16×16 at Scale 2 are displayed at the same 32×32 footprint.

## Permanent grammar rules added

### Edge exposure and contour roles

The renderer now classifies occupied edge cells as:

- `neck_anchor`;
- `outer_side_anchor`;
- `underarm_anchor`;
- `overlap_anchor`;
- `hem_corner_anchor`;
- `shadow_edge`;
- `lit_edge`.

Dark contour is concentrated at anatomical and construction anchors. Upper-left shoulder slopes may use light or shadow rather than the darkest value. Long side anchors can receive one inward deep-crease reinforcement cell, but the backend never creates a blanket two-cell outline.

Across the control set, darkest exterior shares range from 27.08% to 48.15%, while 81.25% to 94.44% of declared dark-anchor cells retain dark visual weight. This avoids both a uniform sticker ring and a weak silhouette.

### Global light direction

The permanent policy is screen-upper-left light. It is recomputed after directional geometry is built; the left-facing sprite is not produced by mirroring shaded right-facing pixels. Light cells belong to connected upper/left cloth planes. An optional highlight can activate only as an attached two-cell pair that leaves a larger light plane intact. None of these four garments needed the optional highlight role after construction and palette were resolved.

### Construction-gesture hierarchy

Each archetype and view declares primary, secondary, subordinate, and micro region gestures. Contrast follows that hierarchy.

- Jacket front: lapel/opening first; hem and cuff second. Back: yoke first. Side: one collar/inner-opening descent first.
- Button shirt front: placket first; collar second. Yoke is primary at the back.
- Sailor front/back/side: yoke/collar first; hem second.
- Sweater: neckline or yoke first; ribbing second; sleeve folds subordinate.

The diagnostic rejects a secondary gesture if it exceeds the primary gesture's contrast weight by more than the declared tolerance. It also reports a missing primary internal boundary. The final four renders pass without warnings.

### Hem and cuff termination

Lower shading is no longer derived from generic region bounds alone.

- plain hems keep base cloth at the edge and attach shadows near corners;
- structured jacket hems terminate at left/right overlap corners instead of becoming a full-width bar;
- contrast bands retain a deliberate weaker top edge;
- ribbed hems use a broad semantic band with only two short crease positions;
- jacket, tailored-shirt, sailor, and sweater cuffs use archetype-specific termination depth.

The lower-bar guard rejects ≥80% dark lower rows unless the recipe explicitly calls for `contrast_band` or `ribbed` construction.

### Selective shade-role activation

The available role vocabulary remains exterior contour, deep crease, structural edge, shadow, base, light, and optional highlight. The garment activates only roles that survive rendering.

- the three Rare controls use six main-fabric roles;
- the Common sweater uses five and omits structural edge and highlight;
- fixed secondary fabric uses its existing shadow/base/light triplet only where its named semantic region exists.

Rarity permits a role; it does not force that role into the texture.

### Optical weight and cluster grammar

One 16×16 cell at Scale 2 has less displayed weight than one vanilla 8×8 cell at Scale 4. The renderer compensates with connected crease masses, dark anchor corners, and selective inward reinforcement. It does not double every line or recreate the vanilla sprite as 2×2 blocks.

Light and shadow are applied as connected planes. Major color regions are resolved before lighting and micro details. The backend does not distribute texture speckles, checker noise, or obligatory highlights.

## Side-view grammar

Side views are renderer-owned reconstructions rather than crops of the front.

Permanent deterministic template vocabulary:

- JACKET: `lapel_led`, `panel_led`, `layered_side`;
- BUTTON_SHIRT: `tailored_placket`, `panel_dominant`, `yoke_tailored`;
- SAILOR_TOP: `collar_sweep`, `yoke_panel`;
- SWEATER: `heavy_mass`, `soft_yoke`.

Panel-layout-specific templates take precedence. A stable SHA-256 selection over recipe seed, ID, archetype, and panel layout chooses among compatible templates.

Selected in this control set:

- Mistral: `lapel_led`;
- Harbor: `yoke_tailored`;
- Garnet: `yoke_panel`;
- Hearth: `heavy_mass`.

Each selected side retains its required semantic regions: collar/inner layer/sleeve for Mistral, collar/placket/yoke/sleeve for Harbor, yoke/sleeve for Garnet, and neckline/ribbing/sleeve for Hearth. All sleeve regions connect to the torso.

## Validation and diagnostics

Final result: `PASS_PERMANENT_FS_HD_GRAMMAR_STATIC_CONTRACT` with no warnings across all four garments.

The permanent diagnostic checks:

- connected garment occupancy;
- body-coverage envelope;
- torso-to-sleeve junction;
- front neck opening;
- darkest-exterior share and dark-anchor coverage;
- coherent asymmetric lighting;
- highlight cluster attachment and budget;
- construction-gesture hierarchy;
- accidental full-width lower shadow bars;
- active shade-role declaration versus actual pixels;
- side-view semantic region survival;
- deterministic side-template selection.

The output validator additionally verifies:

- exact 16×64 RGBA8 PNGs and four 16×16 frame positions;
- binary alpha and explicit unfiltered scanlines;
- exact 8× integer nearest-neighbor previews;
- Fashion Sense 7.5.0 content-pack properties;
- `Scale: 2`, `BodyPosition: (0,32)`, and direction source positions;
- grayscale recolor values and native `SleeveColors`;
- unchanged existing semantic recipes;
- deterministic rerendering;
- successful vanilla V2 rendering of all four unchanged recipes;
- no benchmark-pack access from the permanent renderer or output generator.

Machine-readable details are in `output/fashionsense/art-grammar-v2/validation.json`. These checks are rejection guardrails, not a numeric proof of taste.

## Visual result at gameplay footprint

### Jacket

Mistral keeps its split panels and light inner layer, but the new front has clearer lapel recesses and stronger upper-left form lighting. The structured hem no longer becomes a full-width dark bar. The back yoke is now a single dominant construction gesture, and the `lapel_led` sides maintain an outer/inner relationship instead of flattening the front.

The improvement over prior FS C is real but not dramatic. The pale inner layer remains visually strong and can still approach a vertical-stripe reading at normal scale. It is now framed as an opening by the lapel/crease geometry, but future palette-aware contrast moderation may improve very pale inner layers.

### Button shirt

Harbor's broad yoke, folded collar, continuous placket, and contrast lower termination survive the higher-density render. The front/back construction is clearer than the vanilla baseline. The `yoke_tailored` side preserves the correct regions, but this remains the weakest archetype: at gameplay size, its strong dark placket and tailored panel mass can still drift toward light-jacket vocabulary.

### Sailor top

Garnet gains the most obvious visual benefit. Its broad upper color block has a deliberate V-shaped front, strong back yoke, and diagonal side sweep. The body stays quiet, so the collar/yoke is unmistakably primary without relying on an emblem or noise.

### Sweater

Hearth demonstrates that Common clothing does not need the maximum palette. Five main roles, uninterrupted warm cloth mass, compact crew neck, and restrained ribbed termination read clearly. It is simple by design rather than under-rendered.

## Critical assessment

### Which archetype improved most?

The SAILOR_TOP improves most relative to its equal-footprint vanilla baseline because the additional cells make its yoke contour and side sweep legible without added decoration. The JACKET receives the most important targeted improvement relative to its prior Fashion Sense version: side reconstruction and construction hierarchy are materially clearer.

### Which remains weakest?

BUTTON_SHIRT remains weakest. Its front and back are credible, but the side still has the smallest identity margin from a jacket. This is a semantic compression problem, not a request for more pixels or decorative marks.

### Is the side-view problem solved?

Materially improved and sufficiently solved for this four-garment control set, but not universally solved. The renderer now has multiple deterministic, archetype-aware side constructions and the selected views preserve their required regions. Harbor shows that a valid tailored side can still be visually ambiguous. More existing recipes and live motion must be tested before side-view quality can be called production-stable.

### Is community-quality parity plausible?

Plausible, not established. The new grammar addresses the benchmark-derived gaps: selective anchors, one dominant gesture, deliberate color blocks, attached lighting, natural terminations, and reconstructed sides. The static garments are cleaner and more cohesive than the prior generic renderer. They still lack some of the exceptionally economical, authored visual decisions seen in the strongest community packs, and no static metric can certify desirability.

### Is the renderer ready for the first AoT-inspired stress test?

Yes, for one bounded external style-profile stress test after this four-garment pack receives a brief in-game review. The backend now has enough reusable collar, yoke, panel, closure, hem, and side-view vocabulary to test whether a more demanding style profile translates without per-garment pixel exceptions. It is not yet ready for bulk production or a claim of community parity.

## Outputs

- Permanent grammar data: `generator/data/fashionsense/hd_garment_grammar_v2.json`
- Permanent renderer: `generator/renderers/fashionsense/hd_garment_v2.py`
- Diagnostics: `generator/renderers/fashionsense/hd_quality.py`
- Generated assets: `output/fashionsense/art-grammar-v2/`
- Equal-footprint comparison: `output/comparisons/FS_ART_GRAMMAR_V2_COMPARISON.png`
- Isolated test pack: `test-packs/fashionsense/RNG-Clothing-HD-Art-Grammar-V2/`
- Generator/validator tools: `tools/generate_fs_art_grammar_v2.py`, `tools/validate_fs_art_grammar_v2.py`

## Test pack

With Fashion Sense 7.5.0 installed separately, copy the whole `RNG-Clothing-HD-Art-Grammar-V2` folder into `Stardew Valley/Mods/`, fully restart SMAPI, and run `fs_add_mirror` if a Hand Mirror is needed. The four entries appear under Shirts.

Nothing was installed automatically.
