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

## Vanilla Hats Extended (Nexus 26851, Tea-Loving Lad) — 2026-10-09

    source tools/env.sh
    python3 pack_study/tools/vhe_study.py "<unzipped Hat Version dir>" "<unzipped Accessory Version dir>"
    # -> data/vhe/{items,pairs,internal_sets,parts,moves,mask_layers,summary}.json
    #    out/vhe_vs_vanilla.png, out/vhe_alt_pairs.png, out/vhe_parts.png  (base | item | diff)

Vanilla authority: the game's unpacked `Content (unpacked)/Characters/Farmer/hats.png`
+ `Data/hats.json` (122 hats) — no more inferring vanilla from replacement sheets.
Matching is name-first (Alts inherit their sibling's base), shape only as fallback with
>=50% shared pixels kept, and **per-view shift-aligned** (a moved part is not a new part).

- 157 hat-version items: **116 are vanilla unchanged** (incl. 1px whole-sprite shifts),
  8 are touch-ups (<=8 px), ~30 are distinct new evidence after collapsing recoloured
  copies (Party Hat Alt x3, Goggles/Radioactive Goggles Alt).  None were in the corpus.
- **Author splits of vanilla hats (best evidence):** 13 parts removed from ConcernedApe
  art (Knight plume, Squire crest, Infinity Crown upper gems, Party Hat tied tassel tuft, Forager
  leaf sprig, propeller vs cap, Totem face vs leaf ring, cat ears vs whiskers) + 3 added
  by Tea-Loving Lad (Hard Hat lamp, Tricorn ribbon, Archer feather tip).  A human drew
  those boundaries; still candidates until approved by eye (like decorations_approved).
  Deluxe Pirate / Jester / Swashbuckler splits are flecks (13–27 px), low value.
- **Placement evidence:** 18 items are the same art moved with a consistent per-view
  offset, e.g. masks raised to sit on the head: front (0,-4), right (-1,-4),
  left (+1,-4), back (0,-1); goggles lowered to the eyes: (0,4)/(0,5)/(0,5)/(0,1).
  Side views move horizontally in opposite directions; back moves least.
- **Vanilla's own variant sets** (same mask): Blue/Pink/White Bow, Red/Blue/Green
  Party Hat, Copper/Steel/Gold/Iridium Pan, Blue/Dark Cowboy (pure recolour),
  Dark Ballcap/Sports Cap, Goggles/Radioactive Goggles (partial: only lens role changes).
- **Palette roles (Accessory version):** 89 hats carry author-named `ColorMaskLayers`
  (2–5 per hat, 5-step grey ramps offset by 1 per layer), covering 94.7% of opaque
  pixels.  Each named layer spans 1–8 original vanilla colours (mean 3.5) -> an
  author-labelled region + its vanilla ramp.  Names (Brim, Band, Feather, Strap, Visor,
  Plume, Lens/Frame, Gemstone ...) are the author's claims: per CLAUDE.md §3 they are
  positive evidence, not promotion; verify location before using a label.
- **Corpus hygiene found:** 24 corpus hats credited to **Seyph** are pixel-identical
  vanilla (unchanged cells of the Kawaii Revamp sheet) -> `data/vhe/corpus_vanilla_identical.json`.
  With "style unit = author" the generator currently treats them as Seyph's style.
  Not yet fixed (needs a decision).  Corpus holds 59/122 vanilla hats.

## Corpus agrees with real vanilla — 2026-10-09

    python3 pack_study/tools/vanilla_corpus.py        # rerunnable; run after extract_hats.py

- 24 hats credited to **Seyph** were unchanged vanilla cells of the Kawaii Revamp sheet ->
  recredited to ConcernedApe (`creditFix` keeps the old author, `foundIn` the pack).
  ids/names kept, so approvals/demos still resolve.  The approved leaf sprig
  (`seyph__hats_90`) is vanilla's Forager's Hat -> now ConcernedApe.
- 63 missing vanilla hats added from `Content (unpacked)` (`concernedape__hats_<i>__vanilla`);
  nothing was present moved by <=2 px.  ConcernedApe = all 122 vanilla hats.
- **Finding 4 corrected:** Seyph measures `tonal_outline` (edge/inner 0.49), not hard;
  the "hard" reading was vanilla's style (0.32) credited to Seyph.
- Downstream rerun: 555 hats, 498 constructions; vanilla brings its own recolour/pattern
  sets (Pans, Party Hats, Goggles, Cowboy) into the library.

## Reseating rule (measured) — 2026-10-09

    python3 -I pack_study/tools/reseat_rule.py        # data/vhe/moves.json -> data/reseat_rule.json

- From 7 authored head-piece moves (VHE Alts; removals and recoloured twins excluded):
  front dy -> side dy x1.0 (0.5-1.5), side dx 0.25*|dy| toward the back of the head
  (right -x, left +x), back dy x0.33 (0-0.75).  "down" has n=1 -> marked unusable.
- `gen/decorate.py`: front stays the anchor.  A side/back view that cannot seat is placed
  by the rule instead of rejecting the pairing; a side view that disagrees by >2 px takes
  the rule (A/B by eye: keeps a perched part on top in profile, as in front); the back view
  keeps its surface seat (A/B: a perched part seen from behind pokes above the crown).
  `reseat(pixels, front_dy)` moves a headpiece along the head.
- **Headroom:** parts may rise 6 rows above the frame; the writer grows the canvas upward
  and adds the same to HeadPosition.Y.  FS uses HeadPosition as the draw origin
  (src/DrawManager.cs) -> confirmed in source, **not yet by a worn capture**.
- Decoration matrix (10 targets): bird 1->10, cat ears 1->3, tassel tufts 10, plume 5,
  propeller 6, crown gems 6, lamp 10, ribbon 10, leaf 10, sunflower 10.  Crest 0: it
  follows the helmet's curve in profile, only a helmet-shaped target could take it.

## VHE parts in the pool — 2026-10-09

    python3 pack_study/tools/vhe_parts.py "<unzipped Hat Version dir>"   # -> data/vhe/decorations.json

Approved (data/decorations_approved.json, keys `vhe__...`): perched = plume, crest, crown
gems, tied tassel tuft x3 colours (first labelled pompom), propeller (the Alt itself; the cap is its base), lamp, ribbon.
headpiece (worn on the head, never placed on a hat) = whiskers, vanilla cat ears, totem
face, leaf ring.  Rejected: Archer feather tip (extension of its own feather), Forager
leaf (duplicate), flecks.  Addons include pixels painted over the base (lamp's front face).

## Band transfer — 2026-10-09

    python3 -I pack_study/gen/demo_band.py            # -> out/band_matrix.png

- `gen/band.py`: band rows keep their offset from the crown/brim junction (per view);
  each row is resampled to the target crown width by keeping 2 edge columns and CYCLING
  the middle ones, so a dotted band keeps its dot spacing.  Target outline never painted.
- Targets need NAME evidence of a brim (straw/sun hat/boater/cowboy/fedora/bowler/top hat/
  sombrero/fishing/bucket/witch hat) and must not already carry one (ribbon/band/bow in the
  name).  A width jump alone admitted a veil, a plague-doctor mask, a crown and a beret;
  shape-family membership admitted a mask and a headscarf -- both rejected as evidence.
- Matrix: blue dotted band 9/9, white ribbon band 6/9.  Generator: bands join the rare
  tier's decoration pool on eligible hats.

## Pattern transfer (plaid) — 2026-10-09

    python3 pack_study/tools/patterns.py              # candidates -> data/patterns.json, out/patterns.png
    python3 -I pack_study/gen/demo_pattern.py         # self-check + out/pattern_matrix.png

- 75 library "pattern variants" -> 14 periodic candidates -> **1 approved by eye**:
  CuteBeret plaid (2 colourways).  Rejected: inherent textures (straw weave, knit),
  recolours, colour blocks, reshades (data/patterns_approved.json).
- Measured layout (not a tile): horizontal lines every 3 rows from 2 below the top;
  vertical lines symmetric about the centre (2.5 px half-gap, then every 3 px);
  crossings darker (-0.18..-0.21 OKLab L) than lines (-0.11..-0.13).  Both colourways
  measure the same layout.  Self-check reproduces 82% of the author's own plaid.
- Applied as a lightness change on the target's own colour, interior only.
- **Targets need proven colourways**: only the author's MATERIAL pixels take plaid.
  Measurement (chroma share, lightness break) could not tell Santa fur trim, bunny inner
  ears or panda patches from highlights, so unproven hats take no pattern.
- Generator: uncommon tier transfers plaid when the author has no pattern of their own.

## Larger crown x brim matrix — 2026-10-09

    python3 -I pack_study/tools/brimmed_family.py     # named brimmed constructions -> data/brimmed_family_all.txt
    python3 pack_study/tools/brimmed_parts.py data/brimmed_family_all.txt _all
    python3 -I pack_study/gen/combine_brimmed.py _all # -> data/brimmed_combos_all.json, out/brimmed_combos_all.png

- 36 named brimmed constructions -> 33 splittable -> 86 cross-author combos (brim step
  >= 2 in every view; style = the brim's author).  Same-author mixes excluded: near-copies.
- Reviewed by eye: **78 approved**, 8 rejected (flower-heavy crowns, beekeeper veil,
  one muddled overlap) -> data/brimmed_combos_all_approved.json.  The generator's
  combined tier uses the reviewed straw set + these.  Mostly plurffle x vanilla:
  only possible after the vanilla backfill.
- Not done: peak x crown for caps (needs a verified visor split, CLAUDE.md s3).

## Semantic attachment classes — 2026-10-09

Seating answers "does it fit?"; it does not answer "does it belong?". A leaf sprig
seats on 378 constructions, ball caps included. `gen/semantics.py` +
`data/attachment_profiles.json` add a taste filter **on top of** seating (never
instead of it):

* **class**: `surface` (plaid) · `structural` (bands; crown/brim combos) ·
  `ornament` (physical attached parts) · `headpiece` (worn on the head, never on a hat).
* **transfer**: `broad` · `family-limited` · `novelty-only` · `headpiece-only`.
* **host family** from author/vanilla **names only** (same evidence rule as bands):
  straw, floral, cottage, western, formal, cavalier, cap, knit, fantasy, regal,
  helmet, party, animal, hair, mask, hood. A hat can have several. 162 of 498
  constructions have opaque names (Coii `female_N`, Seyph/h young `hats_N`,
  Kookoroo, TiaoTiao, …) → `unknown`. `data/host_labels.json` (empty) takes hand
  labels, by eye only.
* **verdict** per part × host: `reject` (never, not even novelty; it wins over
  prefer, e.g. Plague Doctor Mask is fantasy AND mask) → `prefer` (weight 1) →
  `allow` (0.4) → `unknown` (profile's `unknownHost`, 0 for every part now) →
  otherwise `novelty` (a named host outside the profile).
* **generator**: `decorate()` orders parts by weight. 8% of decorated rolls are an
  intentional novelty: they use off-family hosts only and are logged as
  `decoration.novelty`. Plaid also needs a host the plaid profile accepts.
* **placement anchor** per profile (`top-centre` / `top-side` / `front-mount` /
  `crown-brim-junction` / `material-interior` / face / head). `gen/demo_semantics.py`
  checks it against the part's measured position on its source hat. Three of my
  declared anchors were wrong and are now corrected to the measured position: bird
  and cat ears sit top-centre, the leaf sprig sits top-side.

`python3 -I pack_study/gen/demo_semantics.py` → `data/attachment_report.json`,
`out/semantics_{0,1}.png` (front views; green = kept, olive = novelty, red =
rejected or unknown host).

| part | class | transfer | seats | prefer | allow | novelty | reject | unknown host |
|---|---|---|---|---|---|---|---|---|
| white ribbon band | structural | broad (brim-named hosts) | 15 | 15 | | | | |
| blue dotted band | structural | broad (brim-named hosts) | 30 | 30 | | | | |
| sunflower | ornament | family-limited | 370 | 75 | 45 | 88 | 26 | 136 |
| bird | ornament | family-limited | 336 | 73 | 41 | 80 | 21 | 121 |
| leaf sprig | ornament | family-limited | 378 | 93 | 51 | 69 | 25 | 140 |
| cat ears (plurffle) | ornament | family-limited | 3 | 3 | | | | |
| plume | ornament | family-limited | 190 | 20 | 20 | 40 | 31 | 79 |
| crest | ornament | family-limited | 54 | 2 | 1 | 13 | 25 | 13 |
| crown gems | ornament | family-limited | 201 | 2 | 11 | 39 | 83 | 66 |
| tied tassel tuft ×3 | ornament | family-limited | 292 | 23 | 43 | 105 | 22 | 99 |
| ribbon (cockade) | ornament | family-limited | 376 | 20 | 63 | 129 | 26 | 138 |
| lamp | ornament | family-limited | 363 | 8 | | 140 | 83 | 132 |
| propeller | ornament | novelty-only | 225 | | | 108 | 35 | 82 |
| plaid | surface | family-limited | 15 | 5 | 2 | | 1 | 7 |
| whiskers, cat ears (vanilla), totem face, leaf ring | headpiece | headpiece-only | — | | | | | |

No part is broad-transfer except the two bands, and they are broad only because
`band.eligible()` already limits them to hats named as brimmed. The 78 approved
crown × brim combos all pair straw/western/formal/cottage/witch hats (counted by
host family), so they need no extra filter.

Effect on generation (300 hats, seed 7): 29 decorated before, 14 now (1 novelty);
the rare tier falls from 53 to 28 hats, the rest demoted to common. The loss is mostly unknown hosts.
Labelling the 162 opaque names by eye is the lever that recovers it.

### Visual host labels — 2026-10-09

`data/host_labels.json`: all 162 hosts with opaque names were labelled by eye from
4-view contact sheets (×4; ambiguous ones re-checked at ×8). These are explicit
visual labels, not shape similarity. Each label has `families`, a `confidence`
(high 96 / medium 53 / low 13) and a note.
Only high and medium labels are used. **22 stay unknown:**
- 13 low-confidence ambiguous hats: plain smooth domes (beret, skullcap or beanie?),
  black domes (riding helmet, cloche or bonnet?), a yellow side lump, a pink puffed cap,
  a frilled bonnet or ghost hood, and a zig-zag band.
- 9 clearly readable hats that need a family the vocabulary lacks, recorded as
  `proposedFamily`, not forced: **prop/gag** ×6 (sword through head, Garbage Hat,
  4 vanilla pans), **food novelty** ×2 (turnip-sprout hat, strawberry hat) and
  **aviator** ×1 (pilot cap with goggles).

Other labelling choices:
- The vanilla Living Hat precedent puts a leafy bush hat in floral.
- Costume heads that cover the face (pumpkin, box, creature) are labelled mask.

300 hats, seed 7:

| | before semantics | semantics, no labels | with labels |
|---|---|---|---|
| rare tier | 53 | 28 | 46 |
| decorated | 29 | 14 | 30 (2 novelty) |

Nonsense that still survives (`hair` is too broad: it covers headbands, clips,
earmuffs and goggles alike):
- A sunflower on Lucille's Earmuffs, 3 times; in profile it sits on the ear cup.
- A bird on vanilla Radioactive Goggles.

Proposed fix, not applied: split `hair` into soft hair pieces (headband, bow,
clip, kerchief) and worn devices (earmuffs, goggles, headphones, sleeping mask),
and reject large ornaments on devices.

### Label fix — 2026-10-09

The three VHE Party Hat Alt parts were labelled "pompom". A ×12 look at vanilla
Party Hat shows the cone tip pinched by a purple tie and splayed into a
yellow/peach starburst. That is a **tied tassel tuft**: not a round pompom, and
not a bow (no loops). Only the label changed. The approval keys
(`vhe__{red,blue,green}_party_hat_alt__removed`) are unchanged, and the old label
is kept as `formerLabel`. Host profile unchanged: prefer party/knit, allow
fantasy/cottage/hood (on a beret it reads as the stalk).

### Roll concepts + `device` split — 2026-10-09

**Concept weighting (RNG only, not a visual change).** Profiles can name a
`concept`. The red, blue and green tied tassel tufts share `tied tassel tuft`.
`decorate()` first orders concepts by weight, picks one, and only then picks a
colour variant, so the three colourways count as one attachment. IDs and approvals
are unchanged. Over 5 seeds × 300 hats (119 decorated either way), tufts went from
31 to 18 decorated hats (26% → 15%). No other part has colour-variant records.

**`hair` split.** Soft hair pieces (headband, bow, clip, ribbon, kerchief, veil)
stay `hair`. Earmuffs, goggles, sunglasses, headphones and sleeping masks are now
`device`: a regex on names, plus 7 visual labels moved from hair to device. Every
hat-ornament profile rejects `device`, except cat ears, whose own source is earmuffs.
27 hosts are devices, Lucille's Earmuffs and Radioactive Goggles among them. Same
5×300 run: 0 decorations on devices. Soft-hair hosts still take birds, sprigs and
sunflowers on Kookoroo bow headbands. A bird on the large bow (Kookoroo_6) is
borderline, but in-family.

### In-game QC pack — 2026-10-09

`python3 -I pack_study/gen/qc_pack.py <generate out dir> <dest>` picks one generated
hat per open worn check. It copies each into `[FS] PackStudy QC` (UniqueID
`PackStudy.QC`) under a self-describing name starting `PSQC NN`, and writes
`qc_index.json` saying what each hat tests. It is installed in the game's
`Mods/` folder: 11 hats (baseline, 2 above-frame decorations, tuft, band, sprig,
ribbon, novelty, plaid, crown × brim, restyle). The folder is new, so the game
needs a restart before Fashion Sense draws it.

### Worn QC v1 results + QC v2 — 2026-10-10

User's worn check of QC v1:

| Hat | Verdict |
|---|---|
| PSQC 03 propeller above frame | **PASS, golden reference.** Above-frame growth (HatSize + HeadPosition.Y) is proven worn. |
| PSQC 02 / 06 leaf sprig | FAIL. Hat seated, sprig floats. Frame padding was not the cause (06 has none). |
| PSQC 04 tied tassel tuft | FAIL. Malformed on a flat beanie top. |
| PSQC 05 band, PSQC 07 ribbon | acceptable |

Causes, read from the extraction (`gen/decorate.py`):
- **Sprig**: it touches the source crown's *wall*, in the notch where the narrow crown widens, not its top. The surface seat anchored it by whole-hat width and dropped it to the top surface, so it landed on outer corners and brim tips. New `seat: side` (`place_side`) finds the stem root, keeps its offset from the crown wall at the same depth below the hat top, and takes the run nearest the hat centre, so it lands on the crown, not a brim tip or an ear. Seated hosts: 378 → 149. A cap has no such notch, so the v1 novelty-on-cap case no longer seats.
- **Tuft**: it is tied *round* a narrow cone tip (part pixels left and right of the tip). New `fit: wrap` needs a host that is present and lies inside the tie in those rows. It now fits 2 hosts (Lovisity party hat, vanilla hats_113), down from 292. Neither has a proven recolour, so **the generator no longer rolls the tuft at all**; QC v2 checks the fit rule on their own authored colourways.
- **All placements**: a placed part must touch its new host at least half as many times as it touched its source (`need_contact`). This removes floaty seats of other parts too (sunflower 370 → 320, bird 336 → 285, propeller 225 → 190). **The golden propeller is pixel-identical** (checked by `qc_v2.py`, which exits if it changes).
- **Devices**: cat ears now reject `device` like every other ornament. The goggled pilot cap (mok&Tinora Hat 02) is labelled `device`. Seed-7 test: 0 decorations on devices. Decorated hats per 300 fell 30 → 17.

**Provenance.** `gen/provenance.py` hooks a loaded generate module and records, per hat:
- type: recolor / restyle / attachment / structural combination
- the BASE pixels before any part was added
- the FINAL pixels
- every source part, with the exact extracted pixels

`gen/qc_replay.py` reruns an archived commit's generator (`git archive <commit> pack_study`) to reproduce hats already worn in game. `tools/provenance_sheet.py` (PIL) draws, per hat: SOURCE hats, EXTRACTED part (on a grey source silhouette), BASE, FINAL, FINAL vs BASE with changed pixels boxed, the v1 hat for A/B, and a check that **the installed hat.png equals FINAL**. All 11 v1 hats replay exactly from `6c6671e`.

Rebuild, run from `pack_study/`:

    git -C .. archive 6c6671e pack_study | tar -x -C out/qc_work/v1code
    python3 -I gen/qc_replay.py out/qc_work/v1code/pack_study/gen out/qc_work/v1replay out/qc_work/v1_records.json 300 1 <PS1 names>
    python3 -I gen/qc_v2.py out/qc_work/v1_records.json out/qc_work out/qc_work/v2_records.json
    python3 tools/provenance_sheet.py out/qc_work/v2_records.json "<pack>/provenance" "<pack>"

`[FS] PackStudy QC v2` (UniqueID `PackStudy.QC2`, names `PSQC2 NN`) is installed with `provenance/` sheets, and the v1 pack has its own `provenance/` too. It holds 6 hats:
- 01 propeller control
- 02, 03 sprig on the v1 hosts, with v1's exact pixels and colours
- 05 sprig on a straw hat
- 06, 07 tuft, labelled PRIMITIVE ONLY

The 04 slot is empty: no host seats the cap novelty.

### Final leaf-sprig policy — 2026-10-10

The worn capture of QC v2 is at `qc_bridge/captures/20261010-195657/`. The tuft and control pass. The sprig sits correctly on straw (05). On the beanie and dome cap (02, 03) it is attached but juts out sideways: those hosts have no crown-over-brim notch to tuck it into.

The user's policy:
- **normal** on brimmed straw / cottage hosts (western allowed)
- **rejected** on dome / beanie / cap hosts
- no sprig novelty rolls

It is recorded as `hostClass` and `policy` in the profile. Both gates must pass:
- **Name evidence:** profile `requires: ['brimmed']`. `semantics.host_families` adds the *trait* `brimmed` (not a family) from brim words in the names (band's list plus sou'wester) or in the visual label note. Without it, berets, bonnets and headscarves passed the geometry, because their puff overhangs like a brim.
- **Geometry:** `placement.host = 'brim-shelf'`, so `decorate.brim_shelf` must hold for the side seat in every view. Within 3 rows below the part, the host must reach out under the part's outer edge, at least 2 px past the crown edge at the part's top row. This holds on the source in all 4 views and on v2 05. It fails on v2 02 and 03.

`python3 -I gen/sprig_hosts.py` writes `data/sprig_hosts.json`:

| Class | Hosts |
|---|---|
| normal | 11 (6 straw, 4 brimmed cottage, 1 western) |
| rejected: family | 345 |
| rejected: off-family | 7 |
| rejected: no shelf | 7 (e.g. boaters, flat narrow brim) |
| rejected: no seat | 22 |

Only 2 normal hosts are generator-eligible, so the generator rolls the sprig rarely: 0 times in 5×300.

The rebuilt `qc_v2.py` now *asserts* that 02, 03 and 04 are rejected. The 4 surviving hats are pixel-identical to the installed pack, so the installed QC v2 stays as the worn record.

`attachment_report`: leaf seated 149 → 32. Every other part is unchanged.

### Verified brim structure, boater seat, sprig frequency — 2026-10-10 (follow-up)

**Verified structure, not names** (user: imported packs must not be excluded for naming differently).

`data/host_structure.json` gives every one of the 392 hosts a `brim`:

| brim | Hosts |
|---|---|
| wide | 46 |
| narrow | 15 |
| upturned | 3 |
| none | 328 |

These were verified by eye on the source sprite (CLAUDE.md §3): a 3× front+right sheet for every host, and 6× in all 4 views for the uncertain ones. The name words and `band.junction` geometry are recorded only as `proposals`, and neither is used. The geometry disagreed with the eye on about half the hosts, because beanies and berets widen downward too. The names missed real brims, e.g. the Forager's Hat itself, Lovisity HatOfGirl, Sherlock/Watson, top hats and mage hats.

`semantics.host_families` now adds the traits `brimmed` and `brim-narrow` from this registry only. A host missing from it, such as one from a newly imported pack, has no brim trait, so brim-requiring parts reject it until it is reviewed and added.

*Still name-based:* the families themselves (`straw`, `cottage`, ...) for named hosts. Only the 162 opaque-name hosts have visual family labels. Moving every family into a verified registry is the next step for imported packs.

**Boater measure** (`decorate.stem_on_brim`): this applies only when the host is verified `brim-narrow` and the part's profile has `placement.host='brim-shelf'`.
- A boater lip, 1–2 px, cannot reach under the leaves, so the *stem* must rest on it: the pixel under the stem root is hat, and that row reaches at least 1 px past the crown edge.
- The seat may slide −3…+3 rows and up to 2 px toward the hat centre.
- The global `brim_shelf` rule is unchanged for every other host. The propeller control and QC v2 01/05/06/07 are pixel-identical.

The 3 plurffle boaters and Kailey's boater-shaped straw hats now seat in all 4 views. Installed as **PSQC2 08 / 09 / 10** into the existing QC v2 folder (fs_reload or restart, then worn capture); they are not yet worn-verified.

Sprig hosts (`data/sprig_hosts.json`): **18 normal**, up from 11.

**Why the sprig is rare** (`python3 -I gen/sprig_funnel.py 1000 1,2,3,4,5` → `data/sprig_funnel.json`, 5000 hats):

| Bottleneck | Measured |
|---|---|
| attachment eligibility | 43 hosts seat it; 25 of those are rejected by family/trait (intended) |
| **no proven recolour** | **11 of the 18 compatible hosts** are never rendered by the generator (`generate.eligible`) |
| **rare-pool host selection** | plurffle's rare pool is only its add-on bases, so its 4 compatible hats (3 boaters, Messy straw) never reach `decorate()` |
| competition (sunflower / band / bird) | *not* the bottleneck: on a compatible host the sprig wins 19–41% (sampled), and won 6 of 21 decorations in the 5000-hat run |

**Frequency:** 6 sprigs in 5000 hats (about 1 in 830), all on Kailey straw hats.

A scratch simulation (not adopted) that lets an author's rare pool include its large non-add-on hats gave 34 decorations on compatible hosts instead of 21, and 7 sprigs instead of 6. Both options below are generator-wide, so they await a decision:
- the rare-pool change
- rendering non-recolourable compatible hosts in their authored colourway

