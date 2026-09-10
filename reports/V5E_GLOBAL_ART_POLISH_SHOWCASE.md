# V5E Arm Correction, Global Art Polish, and Showcase

## Outcome

The blocking V5E arm regression is corrected at the content-contract level, the reusable upper-garment polish stage is implemented, the hoodie and structured-outwear families received bounded micro-polish, and a five-piece showcase was generated.

Static validation passes. Live V5E retesting is still required; this report does not convert the known-good implementation path into a false runtime claim.

## 1. V5E arm correction

The broken V5E pack equipped the same experimental custom Sleeves contract that previously failed in the hoodie branch:

- 32×64 logical sleeve frames;
- Scale 2;
- BodyPosition `(0,0)`;
- `DisableNativeOffset: true`;
- 384×1344 full-pose atlas;
- explicit generated `SleevesId`.

In both live tests that layer drew arm pieces below the Farmer. The final working hoodie arm architecture never calibrated that atlas; it removed it and used the native Farmer arm path.

V5E v1.2 now inherits that proven behavior:

- Shirt `HideSleeves: false`;
- three jacket-specific `SleeveColors`;
- native Shirt feature offsets;
- preset `SleevesId: None`;
- no custom `Sleeves/` directory.

The jacket body, article construction, Scale 2, BodyPosition `(0,32)`, and direction mapping are unchanged. The custom cuff silhouette is not falsely retained: the native sleeve color hierarchy preserves jacket material/cuff value intent, while arm attachment is delegated to the stable animated Farmer path.

Permanent guards are in:

- `generator/data/fashionsense/runtime_sleeve_contracts.json`;
- `generator/renderers/fashionsense/runtime_sleeve_contracts.py`.

They name `NATIVE_ANIMATED_SLEEVES_V1` as known-good and reject the failed custom atlas from current runtime packs.

## 2. Global post-V5E art grammar

The new `POST_V5E_GAMEPLAY_ART_POLISH` stage runs after article construction and before export. It is a shade-role and optical-weight pass, not a substitute for construction.

Permanent rules added:

- concentrate darkest values at neck recesses, outer sides, underarms, overlap points, and hem corners;
- allow connected upper-left mid-value/lit edge runs instead of a uniform black sticker outline;
- reinforce only selected inward shadow-side cells at Scale 2;
- preserve one dominant construction gesture per view;
- require bounded inner layers and authored side/back cues;
- reject full-width dark hems unless semantically intentional;
- reject texture speckle and unattached highlight noise;
- preserve rarity ceilings: one strong region for Common, two for Uncommon, three controlled regions for Rare;
- preserve every alpha cell and every Fashion Sense runtime field.

Implementation:

- `generator/data/fashionsense/art_polish_v5e.json`;
- `generator/renderers/fashionsense/art_polish_v5e.py`;
- updated rarity routing in `generator/data/rarity_renderer_architecture.json`.

The pass cannot repair a weak semantic design by decorating it. Its role is cleaner edge weight, clearer plane separation, and better gameplay-scale finishing after the article adapter has already established identity.

## 3. Hoodie micro-polish

The hoodie architecture remains Shirt + native sleeves + Hat/Hood + preset. No anchor, category, draw order, hair behavior, state behavior, or alpha boundary changed.

Art changes:

- rigid parallel drawstring bars became two connected inward-falling cords;
- string origins remain attached to the neck bridge;
- the two compact tips remain a subordinate accent;
- hood-down front received two connected fold clusters to clarify collapsed cloth;
- the existing rim, shoulder spread, front/side/back proportions, and runtime-tested origins remain intact.

The updated hoodie pack is version 1.9.0. Static hoodie validation remains clean with six Shirts, zero custom Sleeves, six Hats, zero Accessories, and six presets.

Critical limitation: the assembled hood sheet has no Farmer occlusion, so raised hoods look like large rings in diagnostics. That is not an honest substitute for live gameplay. The Farmer face/head occupies the transparent opening in game.

## 4. Structured outerwear micro-polish

Sunfield Pathfinder keeps the same field-jacket body and semantic direction:

- shaped lapels;
- bounded visible inner shirt;
- paired pocket-flap clusters;
- broken shoulder panel around the collar;
- side opening/pocket/seam reconstruction;
- one dominant back yoke and subordinate short seam;
- short structured hem.

The post-V5E pass strengthens neck/side/hem anchors, adds restrained shadow-side inward weight, and cleans the relationship between the pale lapel/inner planes and the shell. Alpha coverage, pockets, panel locations, and runtime fields are unchanged.

The front remains the strongest direction. Back construction is improved and intentional. Side views remain quieter and need live movement review; adding more side decoration would make them diagrammatic rather than better.

## 5. Five-piece showcase

The compact set demonstrates construction variety rather than recolors:

1. **Sunfield Pathfinder Jacket — Rare / Rare+**  
   Open tan field shell, folded lapels, bounded inner shirt, paired pockets, structured yoke.

2. **Ironleaf Dispatch Jacket — Rare / Rare+**  
   Closed high collar, ordered chest tabs, compact field waist, disciplined back yoke. It does not reuse Sunfield's open lapel/inner-shirt formula.

3. **Mosswave Charm Hoodie — Rare / Rare+**  
   True raised Hat hood, compact streetwear shell, inward-falling cords, and one restrained charm cue.

4. **Larkspur Evening Waistcoat — Uncommon / FS HD simple**  
   Deep V frame, visible ivory dress shirt, narrow buttons, and tailored lower points.

5. **Berry Signal Cross-Zip — Rare / Rare+**  
   Fitted asymmetric closure, one-shoulder panel, bright underlayer, and compact geometric focal.

The two jackets differ in opening, collar, inner-layer use, pocket rhythm, front hierarchy, and side read. The formal and casual pieces are not reduced jackets. The hoodie has a genuinely different head/shoulder silhouette.

## Critical visual assessment

The set is visibly cleaner and more varied than the older “dark torso plus center stripe” failure mode. The strongest construction reads are Sunfield, Larkspur, and Berry Signal. Berry Signal is the most immediately differentiated because its diagonal closure survives the tiny footprint without relying on texture.

Ironleaf is the weakest showcase piece. Its high collar and ordered tabs distinguish it from Sunfield, but at gameplay size its dark olive front can still approach generic uniform territory. It passes as a contrasting jacket branch, not as proof that every military palette is automatically desirable.

Mosswave has the strongest article silhouette when assembled, but the isolated Shirt remains less impressive than the complete preset. That is expected for a coordinated hoodie and is precisely why gameplay/preset evaluation is authoritative.

This pass moves the generator closer to the benchmark qualities—economical strong gestures, deliberate color regions, controlled dark anchors, and clearer article distinctions. It does not establish parity with the best human-authored packs. The comparison sheet and live Farmer review must decide whether the garments match the user's taste.

## Outputs

- Gameplay fronts: `output/fashionsense/v5e-art-polish-showcase/V5E_POST_POLISH_GAMEPLAY.png`
- Gameplay directional sheet: `output/fashionsense/v5e-art-polish-showcase/V5E_POST_POLISH_DIRECTIONS.png`
- Enlarged showcase: `output/comparisons/V5E_POST_POLISH_SHOWCASE.png`
- Before/after shade-role comparison: `output/comparisons/V5E_ART_POLISH_BEFORE_AFTER.png`
- Per-garment Shirt/Hood assets and summaries: `output/fashionsense/v5e-art-polish-showcase/`
- Static validation: `output/fashionsense/v5e-art-polish-showcase/filesystem-validation.json`

## Runtime packs

- Corrected/polished V5E jacket: `test-packs/fashionsense/RNG-Clothing-V5E-RarePlus-Field-Jacket/` (v1.2.0)
- Micro-polished hoodie family: `test-packs/fashionsense/RNG-Clothing-Hoodie-Layer-Correction/` (v1.9.0)

Remove older installed copies before copying replacements so stale custom `Sleeves/` files cannot survive a merge-copy.

## Final status

- V5E sleeve implementation: **STATIC PASS / LIVE RETEST REQUIRED**.
- Hoodie architecture: unchanged; micro-polished; static validation pass.
- Global art-polish grammar: implemented with frozen alpha/runtime contracts.
- Five-piece showcase: static validation pass; human gameplay beauty review required.
- No new garment family or variety generation was started beyond the requested compact showcase.
