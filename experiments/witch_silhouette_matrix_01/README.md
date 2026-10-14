# witch_silhouette_matrix_01 — witch-hat silhouette matrix (REFERENCE study, 2026-10-13)

User direction (2026-10-13): pause s8/s9 cleanup (all results kept in `witch_cleanup_01`), map the witch-hat
**silhouette families** across the reference packs, separating structure from decoration and colour; the goal
is to eventually represent every family, not variations of one hat.

Sources (all read-only REFERENCE, none in training):
| tag | pack | author | folder |
|---|---|---|---|
| HnH | Hats and Horns (Nexus) | PlatinumCats | `witch_reference_packs_01/raw` (only the 7 witch hats) |
| Luny | Luny's Witch Hats (Nexus) | Luny | `witch_reference_packs_01/raw` |
| Kailey | [FS] Witch Hats (Nexus) | Kailey | `witch_reference_packs_01/raw` |
| Naver | [FS] Witch Hat 492815 | 내편엘리엇 / Mychocolate | `witch_reference_packs_02/raw` |
| Wildwood | [FS] Wildwood Collection | mushlune | `wildwood_reference_01/raw` (from `good hats/`); in the PROPOSED phase-4 dataset only (not trained) |
| Bloom | [FS] Bloom Collection (hats only) | mushlune (`mushlune.lunebloom`) | `bloom_reference_01/raw` (added 2026-10-14); same, phase-4 proposal only |

Tools: `tools/collect.py` (41 witch hats -> `out/refs.json`, `out/ref_fronts_x6.png` F+R),
`tools/unique.py` (group by exact FRONT alpha mask -> 21 silhouettes, `out/silhouettes.json`, `out/unique_fronts_x8.png`).
Classification below is by eye on those sheets.

## Structure (what the silhouette is)

| family | groups | crown height | crown posture | tip | brim | frame |
|---|---|---|---|---|---|---|
| **Short compact** | G13, G15 Naver short; G00 HnH Long (front); G03 HnH Horn; G05 HnH Vines (body) | low, 4-7 rows | upright, wide base | small nub / short curl | gull-wing, ends droop (Naver); wide arch (Vines) | 16-20 wide |
| **Tall floppy** | G09 Kailey (G10, G11 = same body + decoration); G14 Naver tall; G12 Kailey Straw | tall, 9-12 rows | upright lower crown, top third bends | hooks over and hangs down | flat-wide (Kailey), gull-wing (Naver), ragged (Straw) | 20 |
| **Low sweeping** | G06-G08 Luny; G16 Wildwood Bow/Celestial; G17 Elegant; G18 Forager's; G19 Herbalist's; G20 Straw; G21-G27 Bloom (8 hats, one body, flower/leaf/pumpkin decoration; Fall/Spring Crown are flower crowns, not witch hats) | very low, 5-8 rows | crown laid over sideways, nearly at brim level | long tube to one side, often a bulb/rounded end past the brim | wide, tilted; Elegant has a scroll-curled end | 22 |
| **Classic pointed** | G01, G02 HnH Veiled; G04 HnH Mossy; (vanilla Witch Hat) | tall | straight upright cone | sharp point, at most a small crook | flat / ragged; veil hangs below (Veiled) | 20-32 |

Structural sub-features worth keeping separate from decoration: ragged/tattered brim edge (Kailey Straw, Mossy),
scroll-curled brim end (Elegant), veil hanging from the brim (HnH Veiled; an attachment that changes the outline).

## Decoration (on top of a structure; does not change the family)
band/ribbon (Kailey, Naver, most Wildwood) · flower crown (Kailey G10, HnH Vines) · single flower (Kailey G11) ·
bow (Wildwood Bow) · moon/stars (Wildwood Celestial) · forage/mushroom (Forager's) · herb sprigs (Herbalist's) ·
moss/vines (HnH Mossy, Vines) · horn texture (HnH Horn) · tip bell/ornament (Naver gold tip) · straw texture
(Kailey Straw, Wildwood Straw).

## Colour
black (Kailey, Naver, Elegant, Herbalist's) · purple (HnH Veiled, Celestial) · red (HnH Veiled Red, Naver) ·
blue/teal (Kailey Blue, Naver) · green (Kailey Green/Forest) · brown/tan/straw (Horn, Forager's, Straw) · pink (Bow) ·
grey/white = FS colour-mask versions (Luny, Kailey Colourable/Prismatic, Wildwood ColorMaskLayers).
Same silhouette in many colours: Naver 2 shapes x 5 colours; Kailey 1 body x 8 colour/ribbon variants.
