# V6 Production Batch and Quality Gate

## Outcome

V6 generated exactly 30 deterministic garments under the locked renderer split: 12 Common vanilla shirts, 12 Uncommon single/simple Fashion Sense articles, and 6 Rare+ premium Fashion Sense garments. No event, reward, installation, or runtime integration was added.

All exported garments pass the static direct-pixel, binary-alpha, value-contrast, palette-restraint, direction-reconstruction, and batch-diversity gates. Static passing is not a production promotion and does not replace live Farmer review.

## Rarity read

- **Common** stays deliberately small: 8x8 logical vanilla shirt art at the normal 4x display footprint. Variation comes from fit, neckline, placket/yoke/block construction, ribbing, and palette—not added garment categories.
- **Uncommon** moves to 16x16 Scale-2 Fashion Sense art. Its visible jump comes from collars, openings, layered fronts, knit bands, vest frames, jacket panels, and reconstructed side/back views.
- **Rare+** uses the strongest current article grammars at the same 32px footprint. Its premium read comes from construction hierarchy and coordinated regions rather than denser noise. The set intentionally does not consume future animation/VFX or maximal-layer headroom.

The equal-footprint sheet shows a credible tier jump, though rarity is clearest when comparing within related article roles rather than treating an intentionally bold Common color block as automatically inferior to every muted Rare+ palette.

## Visual review

The strongest Common pieces are Harbor Block Tee, Bluebell Fitted Tee, Hearth Ribbed Sweater, Cedar Placket Shirt, and Ivory Harbor Sail Top. Each communicates one compact idea immediately.

The strongest Uncommon pieces are Coralglass Club Shirt, Bluebell Ridge Knit, Fernpaw Relaxed Knit, Silver Reed Waistcoat, Rosewood Morning Cardigan, Cinderlane Moto Jacket, Night Relay Zip Jacket, Rosewake Sail Blouse, and Saffron Harbor Bomber. These best demonstrate that Uncommon is where article variety becomes visibly exciting.

The strongest Rare+ pieces are Midnight Laurel Blazer, Copperwick Gentleman Top, Amethyst Wayfarer Tunic, Emberward Tabard Armor, and Berry Static Cross-Zip Top. Their openings, focal regions, and silhouettes remain distinct without relying on palette alone.

Sunfield Pathfinder remains **promising but needs live art review**. Its native-arm attachment is frozen and proven, but the jacket/vest distinction depends partly on the assembled Farmer arms and therefore cannot be judged conclusively from the isolated shirt square. Cloudberry Pouch Hoodie is also promising rather than strongest: the pouch reads, but a simple single-layer Uncommon hood cannot match the Rare+ coordinated hood template.

Tidewire Rolled Shirt and Brassleaf Work Vest remain useful but less distinctive than their strongest same-tier siblings. Several Commons are intentionally plain and belong in the promising tier because their appeal depends on clean dye choices more than unique construction.

## Self-ranking

### Strongest

- Harbor Block Tee (Common)
- Bluebell Fitted Tee (Common)
- Hearth Ribbed Sweater (Common)
- Cedar Placket Shirt (Common)
- Ivory Harbor Sail Top (Common)
- Coralglass Club Shirt (Uncommon)
- Bluebell Ridge Knit (Uncommon)
- Fernpaw Relaxed Knit (Uncommon)
- Silver Reed Waistcoat (Uncommon)
- Rosewood Morning Cardigan (Uncommon)
- Cinderlane Moto Jacket (Uncommon)
- Night Relay Zip Jacket (Uncommon)
- Rosewake Sail Blouse (Uncommon)
- Saffron Harbor Bomber (Uncommon)
- Midnight Laurel Blazer (Rare+)
- Copperwick Gentleman Top (Rare+)
- Amethyst Wayfarer Tunic (Rare+)
- Emberward Tabard Armor (Rare+)
- Berry Static Cross-Zip Top (Rare+)

### Promising but needs polish or live review

- Saltwind Everyday Tee (Common)
- Cloudmint Round Tee (Common)
- Pinecream V-Knit (Common)
- Garnet Crew Sweater (Common)
- Sageband Work Shirt (Common)
- Bluebell Button Shirt (Common)
- Mistral Yoke Top (Common)
- Tidewire Rolled Shirt (Uncommon)
- Brassleaf Work Vest (Uncommon)
- Cloudberry Pouch Hoodie (Uncommon)
- Sunfield Pathfinder Jacket (Rare+)

### Reject

- No garment in the final exported thirty is an automatic reject.
- Rainline Zip Hoodie was rejected before export because it read as a zipped shirt at gameplay size.
- Duplicate-prone Common sweater and button-shirt candidates were rerolled before export.

## Critical limitations

- This is still a static production-candidate batch. It does not prove animation, dye behavior, or assembled gameplay appeal for every item.
- Uncommon long-sleeve intent uses the safe native Farmer sleeve path in future runtime packaging; the rejected custom Sleeves atlas remains excluded.
- Some simple articles remain dependent on palette choice. They pass the basic-shirt brief but are not the first production candidates.
- Post-V5E polish improves edge roles and contrast but cannot turn a weak semantic concept into a strong garment. The pre-export Rainline rejection demonstrates that the human gameplay-footprint gate is still necessary.

## Recommendation

Use the strongest list as the first candidate pool, then select a smaller cross-tier subset for live Farmer screenshots. Do not package all thirty for production before that review.
