# pack_study — clean-slate study of third-party hat packs → generator

Started 2026-10-09. **Deliberately independent of the old generator**: nothing under
`generator/`, `generator/data/`, `tools/catalog.py` classes or `test-packs/` is used.
Only runtime facts (Fashion Sense source/docs) and the QC Bridge are shared.

## Pipeline (run from repo root)

    source tools/env.sh                                   # analysis steps use PIL/numpy
    python3 -I pack_study/tools/inventory.py pack_study/data/inventory.json <roots...>
    python3 pack_study/tools/extract_hats.py              # -> data/hats/*.png, data/hats.json
    python3 pack_study/tools/analyze_hats.py              # -> data/hat_features.json, per-author table
    python3 pack_study/tools/variants.py                  # -> data/variant_sets.json
    python3 pack_study/tools/families.py 0.72             # -> data/families.json
    python3 pack_study/tools/build_library.py             # -> data/library.json
    python3 -I pack_study/gen/generate.py pack_study/out/gen 32 <seed>   # pure Python, no deps
    python3 -I pack_study/gen/demo_restyle.py             # shape x style matrix

Roots used: scratchpad extracts of every clothing/hat archive in ~/Downloads and
`references/*.zip|7z|rar`, plus `~/Downloads`, `generator content/`, `references/`,
`[FS] Jedone's Casual Hat Pack`. Repo-root folders of unclear provenance (`Beret/`,
`BERET_MATERIAL…`, `beret_variant1/`, `good hats/`) were excluded.

## Corpus

- Inventory: 1449 unique FS items, ~40 authors (shirts, pants, sleeves, shoes,
  accessories, hats). **Only hats have been studied so far.**
- Hats: 492 unique 4-view hats from 22 authors (FS packs + CP sheets from Coii,
  Seyph/Kawaii Revamp, lovisity/Ragnarok, Kailey CP). 35 vanilla hats were found
  inside two replacement sheets (identical at the same index in both, ±1 rounding
  tolerated) and attributed to ConcernedApe. HatsnHats (52×37, not Stardew format)
  was skipped. Vanilla `hats.xnb` is LZX-compressed and not yet decoded.

## Findings (measured)

1. **Authors build by variation sets.** 187 hats belong to same-mask sets inside one
   author: pure recolours (bijective colour map), pattern variants (CuteBeret
   solid↔plaid), and identity-preserving add-ons (16 verified: Kailey flower crown
   + bird, plurffle straw hat + messy straw, headband + cat ears, earmuffs + cat,
   bells single→double, bows; h young beanie + dot texture).
2. **Mask containment alone is not evidence.** The loose add-on test produced 97
   pairs, most of them coincidences (a small clip "fits inside" any big hat). Only
   pairs where the base survives pixel-identical and is ≥20% of the result are kept.
3. **Kookoroo's bow is redrawn per construction**, not pasted (25–80% verbatim).
   Kookoroo/CuteBeret vary by colour + pattern, not by stacking parts.
4. **Outline style** (edge/interior lightness ratio): hard ≈0.3 (vanilla, Seyph,
   marmuruah), tonal 0.45–0.65 (Coii, Kailey, CuteBeret, lovisity, plurffle grey),
   soft ≥0.8 (h young, Kookoroo, TiaoTiao, JIAOJIAO). The metric misreads Jedone and
   orangeblossom visually, so it is a hint, not a gate.
5. **Cross-author shape families** at IoU 0.72: caps (Jedone+h young), berets
   (CuteBeret+Kookoroo), straw/sun hats (plurffle+Kailey+Coii), cowboy, tall/top,
   hoods/trappers, party hats. Some big "dome" families are coincidental.

## Generator v0 rules (`gen/generate.py`)

- Style unit = author. No hat mixes two authors' pixels except via **restyle**.
- Tiers: common 50% (author recolour) · restyled 25% · uncommon 17% (author's
  pattern variant) · rare 8% (author's proven add-on).
- Recolour: rotate hue of MATERIAL indices of a proven colourway; FIXED indices keep
  colour. Any hue only if the author's own colourways span ≥90°; else proven arc ±20°.
- Greyscale-colourable sources: bake `grey × tint` (FS multiplies; BEHAVIOR_MAP D1).
- **Restyle** (user direction 2026-10-09: "take the shape and use the original
  shading"): shape + internal value structure from any single-material
  construction, ramp + edge level from the target author. Multi-material shapes are
  excluded (they would merge e.g. ribbon into crown).
- Only constructions with all 4 views are eligible. Output = FS pack, baked colour,
  source HeadPosition per direction.

## Not yet proven / known issues

- **No worn in-game capture yet** (game was not running). Packs in `out/gen/` are
  untested in FS.
- Restyle onto a target ramp with few levels flattens detail (CuteBeret navy).
- Too many tiny head accessories relative to hats; plurffle layered hoods look
  broken when flattened to one frame.
- Clothing (shirts/pants/sleeves) not studied yet.

## Crown × brim combination (straw family) — 2026-10-09

    python3 pack_study/tools/brimmed_parts.py          # split proposal (analysis, PIL)
    python3 -I pack_study/gen/combine_brimmed.py       # all compatible combos -> out/brimmed_combos.png
    python3 -I pack_study/gen/export_brimmed.py        # FS pack -> out/gen/[FS] PackStudy Brimmed

- Split = per-view junction row where material width jumps most (widths ignore
  decoration/band pixels). Pool: Kailey straw (blue band), plurffle straw / sun /
  sun-ribbon, Seyph hats_4, orangeblossom (20×25, no 20×20 partner yet), sombrero.
- Excluded: Coii straw + plurffle boater (side-view brim tilted, not row-splittable);
  Kailey sunflower (flower hue ≈ straw hue; **solvable** by diffing against Kailey's
  plain straw hat, or hue+sat+lightness+own-outline); Kailey colourable (duplicate).
- Compatibility: crown base widths within 2 px in every view. Placement: crown base
  row on the brim's junction−1, centres aligned. 20 compatible (crown, brim, style).
- Shading: per-part histogram match onto the target hat's tonal distribution;
  outer edges take the target's edge level (re-outlines the seam). Band/decoration,
  FS colour-mask pixels and semi-transparent shadow pixels keep source colour.
- Bugs found and fixed: FS ColorMasks/ColorMaskLayers — only listed colours are
  tinted (generator previously tinted every pixel); Kailey's semi-transparent
  shadow (0,0,0,99) was being used as the darkest ramp step.
- Result: ~14/20 read as one coherent hat in all four views by eye; failures all
  involve plurffle's ribbon hat (ribbon tails straddle the junction). 8 exported.
- Not yet proven: worn capture.

## Decorations moved between hats — 2026-10-09

    python3 pack_study/tools/decorations.py            # candidates -> data/decorations.json, out/decorations_*.png
    python3 -I pack_study/gen/demo_decorate.py          # decoration x target matrix -> out/decorate_matrix.png

- Discovery: same-author pairs aligned per view; ONE colour map A->B learned by
  majority vote (so a recoloured base still counts — Kailey's sunflower hat is her
  straw hat in a different straw colour); leftover pixels = candidate. Keep the
  direction whose leftovers differ most from the hat's dominant colour; require
  ≥3 views. 57 candidates -> reviewed by eye -> 6 approved in
  `data/decorations_approved.json` (sunflower, bird, leaf sprig, cat ears = perched;
  orangeblossom white ribbon, Kailey blue dotted band = band). Rejections recorded there.
- Placement (perched): same horizontal fraction of the hat's width per view, lowered
  onto the target's top surface to the same depth it sat on its source; rejected if
  it leaves the frame, floats, or is >90% of target width. Source colours kept.
- Matrix result: sunflower seats on 9/10 varied hats, leaf 10/10, bird 1/10 (too
  wide), cat ears 1/10.
- Generator tiers now: common 38 · restyled 20 · combined (crown×brim) 15 ·
  uncommon (pattern) 12 · rare 15 (own add-on, else a moved decoration; retries
  other hats by the same author until one seats).

### Step 1 still to do
- Bands (needs crown-base width fitting by repeating/cutting middle columns).
- Pattern transfer (CuteBeret plaid onto other single-piece hats).
- Crown×brim for cowboy / top / bucket; peak×crown for caps.
- Decoration outline restyle (sunflower keeps Kailey's dark outline on soft hats).
