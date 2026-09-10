# Proposed Garment Grammars

The authoritative semantic records are in [`specs/reference_corpus/garment_grammars.json`](../../specs/reference_corpus/garment_grammars.json). They contain no source coordinates or artwork.

## Proposed vocabulary

### Basics and woven shirts

1. `FITTED_TEE` — close quiet body, small bound neck, short native sleeve.
2. `RELAXED_TEE` — boxier mass, wider neck, dropped shoulder cue.
3. `POLO_KNIT` — collar plus short placket.
4. `HENLEY` — collarless neck plus short placket. **Provisional:** reference coverage is thinner.
5. `BUTTON_SHIRT` — folded collar, full placket, cuff/yoke logic.
6. `OPEN_CASUAL_SHIRT` — two woven outer leaves around a broad inner tee.
7. `OVERSHIRT` — heavier boxy shirt shell with cuffs and practical pockets.
8. `SAILOR_TOP` — broad front/rear collar and deep V.

### Knit, sweatwear and vests

9. `CREWNECK_SWEATSHIRT` — soft volume and ribbed neck/cuff/hem.
10. `TEXTURED_KNIT` — coherent knit field and material-specific terminations.
11. `TURTLENECK` — tall continuous collar with side/rear depth.
12. `OPEN_CARDIGAN` — soft knit outer edges and broad inner layer.
13. `SWEATER_VEST` — bound knit armholes over visible shirt sleeves.
14. `FORMAL_WAISTCOAT` — deep V, buttons, tailored taper and shaped hem.
15. `UTILITY_VEST` — boxy sleeveless shell with practical pocket topology.

### Sport, streetwear and jackets

16. `TRUE_HOODIE` — real hood mass, sweatshirt body and pouch/zip structure.
17. `TRACK_JACKET` — stand collar, sport zipper and sleeve/shoulder stripe topology.
18. `CROPPED_BOMBER` — short rounded shell with gathered ribbed waist.
19. `VARSITY_JACKET` — contrast sleeves, snap front and striped ribbing. **Provisional:** needs broader non-character reference coverage.
20. `WORK_JACKET` — boxy shell, large pockets, straight heavy hem.
21. `FIELD_JACKET` — disciplined yoke, guarded opening and utility pockets.
22. `MOTO_JACKET` — asymmetric lapel/overlap and diagonal closure. **Provisional:** current evidence is selective.
23. `CROPPED_FASHION_JACKET` — independent short shell over visible inner layer, without bomber ribbing.
24. `STREETWEAR_BLOCK_TOP` — boxy/asymmetric mass organized by large directional blocks.

### Formal, period and statement

25. `FITTED_BLAZER` — tailored shoulders/waist, lapels and rear seam/vent logic.
26. `DOUBLE_BREASTED_FORMAL_TOP` — true overlapping front and paired-button topology.
27. `PERIOD_COAT_TOP` — nested collar/cravat/waistcoat hierarchy within safe upper bounds.
28. `OFFICER_UNIFORM_TOP` — upright high collar, disciplined closure, cuffs and yoke.
29. `WRAP_TOP` — real diagonal overlap with sash continuation.
30. `BELTED_TUNIC` — belt-divided torso and longer-looking split lower section within safe bounds.
31. `TABARD_TOP` — broad over-panel over an underlayer, with belt/shoulder attachment.
32. `TRADITIONAL_OFFSET_CLOSURE_TOP` — band collar and coherent offset fastening path.
33. `CEREMONIAL_FORMAL_TOP` — signature collar/layer hierarchy with one controlled ceremonial focal system.

## Neighbor separation requirements

- Tee vs sweatshirt: ribbed cuff/waist and volume, not graphics.
- Polo vs henley: collar mass.
- Button shirt vs overshirt: shell weight, pockets, cuff/hem firmness.
- Open shirt vs cardigan: woven collar versus soft knit edge.
- Sweater vest vs waistcoat: knit binding versus tailored buttons/shaped hem.
- Utility vest vs field jacket: visible inner sleeves/armholes versus full outer shell.
- Track vs bomber vs varsity: sport stripe/stand collar versus rounded gathered shell versus snaps/contrast sleeves.
- Work vs field jacket: large practical patch pockets/straight hem versus disciplined yoke/guarded utility construction.
- Moto vs wrap top: rigid asymmetric lapel/zip versus fabric overlap/sash.
- Blazer vs period coat-top: modern lapel/button stance versus nested high-collar/cravat/waist shaping.
- Tunic vs tabard: integrated belted garment versus distinct broad over-panel.

## Implementation readiness

This document proposes grammar; it does not authorize implementation. Strong-confidence families have repeated or clear evidence. Provisional families should receive additional targeted references before production. All grammars must later pass Farmer-composite tests, and safe upper-body bounds remain enforced even when a source implies a longer garment.
