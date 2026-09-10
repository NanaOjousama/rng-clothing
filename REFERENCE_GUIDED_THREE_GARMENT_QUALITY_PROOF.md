# Reference-Guided Three-Garment Quality Proof

Status: **PASS_STATIC_VISUAL_REVIEW_REQUIRED**. Pack: **PASS_STATIC_RUNTIME_NOT_TESTED**. Runtime remains **NOT TESTED**.

## Method and reference safety

Exactly three human-authored references were selected for non-overlapping construction lessons. The semantic design specification was written before rendering at `specs/reference_guided/three_garment_quality_proof.json`. Runtime code does not load `ref_codex`; it loads only that original semantic specification. No reference raster, coordinate map, exact palette, logo, insignia, character costume, or source asset is copied or redistributed.

The render route is `semantic reference design -> existing V5/HD carrier -> render_fs_hd_v2 -> V4/V5B/V5D construction where applicable -> named-surface reset to proven HD planes -> authored garment construction -> polish_upper_frames -> soften_shared_rear_neck -> material/palette adapter -> Fashion Sense export`. `reference_grammar.render_controlled_garment` is absent.

## Garments

### Harborfold Camp Shirt

- **Reference:** `[FS] Luny's Cottagecore Shirts` — `Casual Button-up Shirt` (`ref_codex/masc clothing/[FS] Luny's Cottagecore Shirts/Shirts/Casual Button-up Shirt`), used read-only.
- **Architectural lessons:** relaxed larger shirt footprint; folded collar; shaped side edge; rear hem/yoke continuity.
- **Original transformation:** The source's exact white/gray arrangement and pixel layout are discarded; the new design uses a camp collar, one-pocket asymmetry, box pleat, coastal role topology, and newly authored four-direction proportions.
- **Semantic concept:** A breezy harbor-market shirt with a soft camp collar and curved split shirttail.
- **Construction:** regular upper chest easing into a softly widened lower woven body; wide two-piece camp collar around a shallow open neck; no necktie or narrow V stamp; short open upper placket that settles into a quiet buttoned woven front rather than a full contrasting stripe; rounded shirttail with small directional side split and a slightly lower-looking rear termination
- **Directions:** front — camp collar and off-open neck lead into an interrupted placket; pocket balances the opening without mirroring it Right/left — collar depth, pocket edge on the appropriate side, convex hanging seam, and visible side split retain the draped shirt read Back — wide shallow collar band, broad shoulder yoke, short box pleat, and curved rear hem; no front placket mirrored onto the back
- **Material / palette:** `WOVEN_SHIRT` / `COASTAL_MIST`. fog-aqua main cloth, sand undercollar and neck recess, harbor-teal construction edges, one tiny coral pocket tab
- **Renderer systems reused:** `render_fs_hd_v2`, V4/V5B construction carrier, `polish_upper_frames`, `soften_shared_rear_neck`, semantic material/palette ramps, native `SleeveColors`.
- **Farmer-scale assessment:** Reads as a relaxed woven camp shirt: the collar/open neck, one-pocket imbalance, curved side termination, rear yoke and box pleat survive the Farmer composite. It does not read as a fitted jacket.
- **Reference preservation without copying:** **PASS** — the useful article logic survives, while source pixels, coordinates, exact colors, graphics and complete layout do not enter output.
### Alderwick Knit Vest

- **Reference:** `[FS] Gentleman's Collection` — `Brown Sweater Vest` (`ref_codex/masc clothing/FS Gentlemans Collection.zip :: Shirts/Brown Sweater Vest`), used read-only.
- **Architectural lessons:** deep V; economical sleeveless knit mass; shirt-layer exposure; coherent quiet back.
- **Original transformation:** The brown source colors and plain rectangular field are not reused; the new vest adds an original tapered contour, layered folded collar, wide ribbed binding, quiet paired ribs, and light-primary academic role layout.
- **Semantic concept:** A light academic knit vest shaped around a crisp woven shirt layer.
- **Construction:** compact knit body with visibly cut-in armholes; broad deep V with a two-cell knit binding and a visible folded inner-shirt collar; closed pullover knit; the V is neckline topology, not an open cardigan or zipper; continuous ribbed knit band with a shallow center ease, not a jacket hem
- **Directions:** front — deep bound V and shirt collar dominate; restrained rib columns articulate knit structure without a crest or motif Right/left — bound armhole curve, knit side seam, shirt sleeve exposure, and ribbed hem preserve vest layering Back — shallow rounded rear neck band, plain coherent knit back, two upper-back shaping ribs, continuous hem
- **Material / palette:** `KNIT` / `CREAM_ACADEMIC`. warm cream knit is dominant, dusty plum binds neck and armholes, antique tan supports ribbing, pale shirt remains broad
- **Renderer systems reused:** `render_fs_hd_v2`, V4/V5B construction carrier, `polish_upper_frames`, `soften_shared_rear_neck`, semantic material/palette ramps, native `SleeveColors`.
- **Farmer-scale assessment:** Reads immediately as a layered sweater vest: cut-in bound armholes, deep knit V, visible shirt collar/native sleeves and ribbed lower band dominate. The side islands are one anchored Shirt frame around an intentionally exposed native arm, not separate FS components.
- **Reference preservation without copying:** **PASS** — the useful article logic survives, while source pixels, coordinates, exact colors, graphics and complete layout do not enter output.
### Bluecurrent Saddle Shell

- **Reference:** `[FS] Gentleman's Collection` — `Teal Windbreaker` (`ref_codex/masc clothing/FS Gentlemans Collection.zip :: Shirts/Teal Windbreaker`), used read-only.
- **Architectural lessons:** high collar; boxy sport mass; large upper blocks; native long-sleeve relationship; plain disciplined back.
- **Original transformation:** The teal reference palette and its exact vertical block layout are discarded; the new design uses a curved saddle, contained half-zip, slant pockets, gathered waist, blue/cream topology, and original directional reconstruction.
- **Semantic concept:** A bright technical shell built around a curved shoulder saddle and gathered lower band.
- **Construction:** broad upper shell with a slightly bloused body; tall guarded stand collar with a small recessed throat opening; short half-zip contained inside the collar and upper chest; no full-height center stripe; wide gathered elastic band that pulls the boxy body inward
- **Directions:** front — stand collar and short zip sit above a broad curved saddle; low pocket diagonals and gathered band carry the lower read Right/left — collar projection, saddle termination, one slant pocket entry, full shell depth, and gathered band author each side Back — broad curved rear saddle, uninterrupted main shell field, two short shaping seams, and continuous gathered band
- **Material / palette:** `SPORT_SHELL` / `BRIGHT_SPORT`. bright blue shell field, cream saddle/lining blocks, navy structural anchors and band, one localized orange zipper pull/tab
- **Renderer systems reused:** `render_fs_hd_v2`, V4/V5B construction carrier, V5D work-shell carrier, `polish_upper_frames`, `soften_shared_rear_neck`, semantic material/palette ramps, native `SleeveColors`.
- **Farmer-scale assessment:** Reads as a boxy sport windbreaker: stand collar, contained half zip, broad saddle, slant pockets and gathered band remain visible. It is the only jacket-like member and does not share the casual shirt or sleeveless topology.
- **Reference preservation without copying:** **PASS** — the useful article logic survives, while source pixels, coordinates, exact colors, graphics and complete layout do not enter output.

## Farmer-scale diversity gate

| Left | Right | Shared high-impact topology fields (of 5) | Result |
|---|---|---:|---|
| HARBORFOLD_CAMP_SHIRT | ALDERWICK_KNIT_VEST | 0 | PASS |
| HARBORFOLD_CAMP_SHIRT | BLUECURRENT_SADDLE_SHELL | 0 | PASS |
| ALDERWICK_KNIT_VEST | BLUECURRENT_SADDLE_SHELL | 0 | PASS |

Human review without counting palette finds three immediate reads: relaxed woven shirt, sleeveless knit vest, and boxy sport shell. Their silhouette, neckline, opening, sleeve relationship, hem, and rear carrier differ. **No candidate reads as another generic fitted jacket.** Static Farmer previews do not simulate native sleeve recoloring, so actual arm colors and motion remain a live Fashion Sense test item.

## Quality-anchor context

| Existing anchor | Active front colors | Dominant front fill | Luminance range |
|---|---:|---:|---:|
| Sunfield Pathfinder Jacket | 11 | 27.3% | 189.96 |
| Juniper Vale Cardigan | 8 | 29.4% | 181.59 |
| Orchard Reserve Workshirt | 10 | 25.2% | 182.15 |

The comparison is a discipline check, not a demand to imitate an anchor. The three garments use connected light/shadow planes, selective dark anchors, authored neck/hem/pocket/yoke carriers, and direction-owned reconstruction. The reference-guided concepts materially outperform a name-driven generic topology, but live Farmer screenshots remain authoritative for final desirability.

## Outputs

- Experimental Fashion Sense pack: `/run/media/deck/USD00/RNG_clothing/test-packs/fashionsense/RNG-Clothing-Reference-Guided-Three-Garment-Proof`
- Per-garment assets and design specs: `/run/media/deck/USD00/RNG_clothing/output/fashionsense/reference-guided-three-garment-quality-proof`
- Isolated Front/Right/Back/Left: `/run/media/deck/USD00/RNG_clothing/output/comparisons/REFERENCE_GUIDED_THREE_ISOLATED_DIRECTIONS.png`
- Farmer Front/Right/Back/Left: `/run/media/deck/USD00/RNG_clothing/output/comparisons/REFERENCE_GUIDED_THREE_FARMER_DIRECTIONS.png`
- Gameplay-scale front comparison: `/run/media/deck/USD00/RNG_clothing/output/comparisons/REFERENCE_GUIDED_THREE_GAMEPLAY_FRONTS.png`
- Large three-garment comparison: `/run/media/deck/USD00/RNG_clothing/output/comparisons/REFERENCE_GUIDED_THREE_LARGE_COMPARISON.png`
- Enlarged nearest-neighbor inspection: `/run/media/deck/USD00/RNG_clothing/output/comparisons/REFERENCE_GUIDED_THREE_8X_INSPECTION.png`
- Static validation: `/run/media/deck/USD00/RNG_clothing/output/fashionsense/reference-guided-three-garment-quality-proof/static-validation.json`

Stop state: exactly three garments, no rarity labels, no custom Sleeves, no VFX, no batch generation, and no propagation into procedural generation.
