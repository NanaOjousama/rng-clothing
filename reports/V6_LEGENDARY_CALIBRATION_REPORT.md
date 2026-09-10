# V6 Legendary Design Rebuild and Farmer Diversity Gate

## Result

The six Legendary garments were rebuilt around their approved, locked palette stories. Construction—not palette—now separates the batch on the installed Stardew Valley 1.6.15 Farmer idle frames.

All fifteen pairwise comparisons pass the Farmer-preview diversity gate. The first rebuild attempt did not: Jade Conservatory Coat and Pearl Nocturne Ceremonial Blazer were rejected at mask IoUs of 0.922 front, 0.936 side, and 0.948 back. Jade was rebuilt with a flared divided lower coat mass and projected side edges. Crimson Arc and Frostguard were then reviewed as the closest remaining outerwear pair; Frostguard received a sharper lower field-shell taper, reducing that pair to 0.904 front, 0.915 side, and 0.914 back, with a distinct overall Farmer read.

## Farmer preview contract

The static composites use the installed authoritative asset:

`/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/farmer_base.png`

They use vanilla standing frames 0 (front), 6 (right/left), and 12 (back), with left mirroring, vanilla style-0 hair, the native Farmer at Scale 4, and Fashion Sense Shirt art at Scale 2 using the established BodyPosition `(0,32)` idle placement. Graphite Tide additionally uses its proven head-relative hood composition, preserving front/side hair and suppressing rear hair in the back diagnostic.

These are authoritative static idle source-contract composites, but they are not a substitute for live movement/runtime testing.

## Rebuilt garment identities

### Graphite Tide Hood

- True head-framing raised hood.
- Cropped pouch body and dropped streetwear shoulder read.
- Teal opening, pale lower fabric, and graphite rim remain attached to hood/pouch construction.
- It cannot be confused with a crewneck in the Farmer composite.

### Crimson Arc Relay Jacket

- Cropped square-shoulder shell.
- Open folded lapels and divided lower opening.
- Paired relay bars and centered back arc reinforce the split-shell identity.
- It reads broader and shorter than Frostguard or Pearl Nocturne.

### Jade Conservatory Coat

- High cravat and offset period closure.
- Flared lower coat mass with a deliberate center split.
- Side views project the rear coat edge; the back resolves into divided tails and a descending seam.
- It no longer shares Pearl Nocturne's fitted mask.

### Pearl Nocturne Ceremonial Blazer

- Narrow-waist fitted formal body.
- Deep midnight lapels over a clean pearl field.
- Gold meridian provides one ceremonial diagonal rather than a repeated center stripe.
- Compact pointed front termination and quiet formal back keep it elegant instead of bulky.

### Frostguard Standard Jacket

- Guarded high collar and broad upper shoulder architecture.
- Paired chest discipline with a silver standard/yoke system.
- Sharply tapered lower field-shell corners distinguish side and back from Crimson Arc.
- This remains the intentionally borderline piece, but it now clears the Rare field-jacket read through a named shoulder/yoke identity and directionally preserved standard.

### Sundown Waymark Tunic

- One-shoulder wrapped construction.
- Broad amber diagonal terminating at a belt.
- Asymmetric tunic hem rather than a jacket bar.
- Side and back reduce the sash deliberately while retaining nape and belt cues.

## Pairwise diversity

The full ten-axis, fifteen-pair matrix is in `reports/V6_LEGENDARY_PAIRWISE_DIVERSITY.md`. It compares silhouette, family, neckline, opening, dominant gesture, surface composition, side, back, palette, and overall Farmer-scale read.

The matrix uses direct geometry IoU for front/side/back and explicit semantic comparisons for construction. Palette never substitutes for a failing overall Farmer read.

## Rare ceiling comparison

The Farmer comparison includes:

- Uncommon 21 — Night Relay Zip Jacket
- Uncommon 22 — Rosewake Sail Blouse
- Rare — Juniper Vale Cardigan
- Rare — Nocturne Silver Waistcoat

The Legendary pieces add named silhouette/construction systems absent from the Rare anchors: raised hood mass, split relay shell, flared period tails, ceremonial meridian lapels, guarded standard/yoke, and asymmetric waymark wrap.

## Self-critique

**Strongest Legendary:** Graphite Tide Hood. Its silhouette changes the full head-and-shoulder read and remains immediately identifiable without color.

**Strongest single-layer garment:** Sundown Waymark Tunic. Its wrap and hem geometry survive every direction and do not depend on a center stripe.

**Best rebuild:** Jade Conservatory Coat. The failed fitted-top mask was replaced by a bounded but visibly flared period construction.

**Weakest Legendary:** Frostguard Standard Jacket. It passes after rework, but remains closest to a premium Rare because the short field-jacket family has limited silhouette freedom inside the proven Shirt footprint. Its silver standard and guarded yoke must remain protected during future customization.

**Closest pair:** Crimson Arc and Frostguard. They are still related short outerwear, but no longer strongly overlap geometrically and differ in collar, closure, hem, focal composition, palette, and back treatment.

**Other geometric overlap:** Pearl Nocturne and Sundown Waymark retain related underlying fitted torso coverage. Their worn reads remain distinct because symmetric formal lapels/pointed hem and asymmetric shoulder wrap/belted tunic termination reconstruct differently across all directions.

**Too close to Rare:** none accepted. Frostguard is the narrowest pass and should be the first item challenged in any future live review.

**Accidental Mythic drift:** none. There are no VFX, transformations, animated motifs, extreme costume silhouettes, or multi-stage spectacle systems.

## Outputs

- `output/comparisons/V6_LEGENDARY_CONTACT.png`
- `output/comparisons/V6_LEGENDARY_GAMEPLAY.png`
- `output/comparisons/V6_LEGENDARY_FARMER_DIRECTIONS.png`
- `output/comparisons/V6_RARE_VS_LEGENDARY.png`
- `output/fashionsense/v6-legendary-calibration/pairwise-diversity.json`
- `reports/V6_LEGENDARY_PAIRWISE_DIVERSITY.md`
- `reports/V6_LEGENDARY_PALETTE_STORIES.md`
- `reports/V6_LEGENDARY_GARMENT_IDENTITIES.md`

No runtime pack was generated. Mythic, Emily customization, event integration, and reward hookup remain untouched.
