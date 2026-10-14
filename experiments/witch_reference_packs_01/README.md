# witch_reference_packs_01: user-supplied witch-hat reference packs (2026-10-13)

The user downloaded three Fashion Sense packs (Nexus zips in ~/Downloads, 00:29) to show the witch hat in different
views, shapes and variants. Personal use only; author recorded per pack. Extracted here as REFERENCE (read-only);
NOT installed in the game, NOT in pack_study/library, NOT in any training set (that would need the user's OK).

| pack | author | UniqueID | version | zip |
|---|---|---|---|---|
| Hats and Horns | PlatinumCats | PC.Hats | 1.1.2 | Hats and Horns-17405-1-1-2-1711166837.zip |
| Luny's Witch Hats | Luny | Luny.WitchHats | 1.1.0 | Luny's Witch Hats for FS-25195-1-0-1718463110.zip |
| [FS] Witch Hats | Kailey | kailey.witchhats | 1.0.0 | Witch Hats-13735-1-0-1662847938.zip |

Contents: data only (52 png, 55 json). 24 witch-type hats (7 PlatinumCats incl. veiled / horn / mossy / vines,
3 Luny white 22x20, 14 Kailey 20x20 incl. flower crown / forest / straw); Hats and Horns also has 21 non-witch hats.
Sheet: `out/witch_refs_x6.png` (front | right | left | back).

## First measurement (side view, R)
Every one of the 17 distinct reference witch hats leans the crown tip toward the BACK of the head
(-0.5 .. -5 px from the bbox centre). Side bbox width 15-21 px (Kailey / Luny 19). Our witch s8: -3.5 (agrees);
witch s9: +1.5 (leans toward the face) -> likely the "side looks a little deformed" note. Used for
witch_side_repair_01 variant s9.D.
