# Reference-derived style vocabulary

Research date: 2026-08-28. This document records reusable semantic traits only. It does not authorize copying any outfit, sprite, character, logo, or named franchise design.

## Taxonomy boundary

- **Category** describes why/where a garment is worn: lifestyle, workwear, formal, seasonal, themed, and so on.
- **Style profile** describes a repeatable visual language: silhouette, proportion, construction, trim, palette behavior, and detail rhythm.
- **Rarity** is reward-system metadata and is not inferred from a folder, theme, complexity, color, or source. Neither “Lifestyle” nor “Sailor” means common, rare, or any other rarity.

The inspected sets are:

- `references/lifestyle/`: four collages/concept sheets covering ordinary, seasonal, work, outdoor, festival, and fantasy-adjacent looks. Two sheets are substantially larger than Stardew source art and are treated only as semantic references. They must never be shrunk into game sprites.
- `references/style-profiles/SailorStyles /`: note the literal trailing space in the current folder name. This is a native Content Patcher clothing pack with shirts, pants, and hats, not a photo-reference folder. It demonstrates readable Stardew-scale construction and a broad coordinated fashion language. The source pack contains many everyday, formal, Japanese-inspired, and magical-uniform designs; its folder name does not mean every asset is nautical.

## Category: Lifestyle

### Design intent

Everyday clothing that reads as practical, approachable, seasonal, and characterful before it reads as themed. The collection ranges from simple town wear to farm, rain, winter, beach, festival, and mine-ready outfits. The transferable language is “recognizable garment archetype plus one strong identifying cue.”

### Silhouette families

- **Compact straight:** fitted T-shirt, pullover, button-up, cardigan, cropped jacket, straight trousers, and shorts. Minimal protrusion beyond the body.
- **Soft A-line:** knee/midi skirt, apron skirt, pinafore, or simple dress widening gradually below the waist.
- **Layered column:** long coat, open overshirt, raincoat, or jacket over a vertically continuous inner garment.
- **Top-heavy winter:** padded or broad coat, scarf/hood mass near the head and shoulders, narrow lower half.
- **Workwear block:** overalls, dungarees, apron, sturdy jacket, boots, and occasional backpack/helmet.
- **Waist-defined:** cropped top/cardigan over high-waisted skirt or trousers; belt/apron seam creates a clear midpoint.

### Garment archetypes

- Crew/V-neck tees, tanks, camisoles, crop tops, turtlenecks, sweaters, hoodies, button-ups, blouses, and cardigans.
- Cropped jackets, denim/work jackets, long coats, raincoats, winter coats, open overshirts, and lightweight wraps.
- Straight or relaxed trousers, jeans, shorts, overalls, short A-line skirts, long skirts, apron skirts, pinafores, and simple dresses.
- Boots, sneakers, sandals, work shoes, straw/winter/rain hats, scarves, belts, bows, bags, backpacks, and helmets.

### Proportions and fit

- Torso garments usually have one dominant length: crop, waist, hip, or coat-length. Mixing more than two vertical breakpoints makes the tiny sprite noisy.
- Relaxed/boxy upper layers pair with a narrower or visually quieter lower garment.
- A-line skirts start widening at a clear waist seam and keep the hem simple.
- Long garments favor uninterrupted vertical color fields, broken by a belt, opening, or hem band.
- Workwear uses broad straps/bibs and chunky footwear; delicate wear uses narrower trim and a more tapered torso.

### Layering vocabulary

- Open jacket/cardigan over a contrasting inner top.
- Shirt or blouse under sweater/vest, with only collar and/or cuffs visible.
- Pinafore/overalls/apron over a simpler base top.
- Scarf over coat with the scarf as the high-contrast focal point.
- Belt or waist seam linking upper and lower halves.
- Backpack/bag as a back-view cue, not merely a front-view accessory.

At Stardew scale, preserve at most two major clothing layers plus one accent. More layers should be encoded as color blocks/trim rather than separate outlines.

### Sleeve families

- Sleeveless/tank, cap/short sleeve, straight long sleeve, cuffed long sleeve, rolled sleeve, and padded/wide coat sleeve.
- Most references are symmetric. Sleeve asymmetry should be an intentional accent, not random noise.
- For a first generator, sleeve “style” should initially change torso-edge pixels and native sleeve colors only. Independent Fashion Sense sleeve geometry comes later.

### Collar and neckline families

- Crew, V, turtleneck, pointed shirt collar, rounded/Peter Pan-like collar, hood opening, lapel/open jacket, and scarf-covered neck.
- A collar should normally use one light/dark boundary and one center cue. Tiny lapels or strings that cannot survive four directions should be omitted.

### Hems and openings

- Straight, gently A-line, soft wave/scallop, ribbed band, coat split, apron edge, and short cuff.
- Center-front openings/buttons are common high-value cues.
- Back views should retain structural logic: collar back, hood, straps, center seam, coat split, or backpack. Do not mirror front ornament onto the back without a garment reason.

### Palette tendencies

- Common bases: navy/deep blue, denim blue, forest/olive green, brown/tan, cream/off-white, charcoal/black, muted pink, burgundy/red, mustard/yellow, and violet.
- Most readable outfits use two main hue families plus a neutral; occasional festival/fantasy looks add one bright accent.
- Seasonal tendencies: warm earthy autumn; pale pink/mint/cream spring; high-value yellow/blue summer/rain; deep blue/brown/green winter/workwear.
- Contrast is usually localized at collar, inner layer, cuffs, waist, trim, or accessory—not evenly scattered.
- Shading should be a small ordered ramp per material/palette role, not photographic gradients.

### Pattern and detail density

- Mostly solid fields with sparse stripes, checks, floral suggestions, ripped-knee marks, buttons, pockets, bibs, or trim.
- A tiny garment should have one focal feature: collar, opening, bib, stripe, bow/scarf, belt, or motif.
- Repeated patterns need a minimum logical spacing and must not become checkerboard noise on side/back views.
- Accessories are medium frequency, but large accessories (bag, scarf, hat, helmet) are typically the outfit's single dominant extra.

### Asymmetry

- Low overall. Useful asymmetry appears in an open jacket edge, side bag, offset patch/pocket, scarf tail, ripped knee, or one-sided hair/head accessory.
- Asymmetry should be declared by component and direction. Left/right sprites cannot be naïvely mirrored when an accessory changes sides in world space.

### Stardew-readable simplification

1. Choose one silhouette family.
2. Preserve one structural landmark (collar, bib, waist, opening, or hem).
3. Use one accent landmark (scarf, bow, pocket, stripe, or accessory).
4. Limit torso-scale palette roles to outline/shadow, base, light, and accent; add a second recolorable role only when it remains visually distinct.
5. Replace fine fabric texture with two-to-four strategically placed logical pixels.
6. Represent long layers through clean color fields and a hem/opening cue, never by shrinking the concept art.

### Safe early recipe vocabulary

```yaml
category: lifestyle
archetype: tee | blouse | sweater | cardigan | compact_jacket | work_shirt
fit: fitted | straight | relaxed
length: crop | waist | hip
neckline: crew | v | pointed_collar | rounded_collar | turtleneck | open_layer
sleeve: sleeveless | short | long | cuffed
layering: none | inner_top | vest | open_jacket | bib
focal_detail: none | buttons | stripe | tie | bow | pocket | bib
palette_family: neutral | earth | cool | warm | pastel | monochrome
contrast: low | medium | high_localized
pattern_density: none | sparse | moderate
asymmetry: none | declared_component
```

Long coats, long skirts, capes, backpacks, and helmets belong in later Fashion Sense profiles, not the first shirt generator.

## Style profile: Sailor

### Scope and interpretation

The Sailor set supplies two related vocabularies:

1. **Nautical/magical uniform language:** broad contrasting collar, center bow or tie, fitted upper torso, waist seam, short flared skirt or coordinated lower half, high-contrast trim, and emblem-like accents.
2. **Coordinated tailored language:** blouses, blazers, waistcoats, button-ups, ties/ascots, cardigans, formal jackets, tuxedos, kimono/yukata/hakama sets, bows, masks, and top hats.

The reusable profile is therefore not “copy a Sailor suit.” It is **disciplined uniform construction with strong collar/waist/trim landmarks and coordinated top-bottom color roles**.

### Silhouette families

- **Fitted uniform top:** narrow/straight torso, strong shoulder-to-collar wedge, center chest accent, crisp waist termination.
- **Cropped uniform + flare:** compact top above a clearly expanding short skirt.
- **Tailored jacket:** straight or slightly tapered blazer/coat with lapel or high collar, center opening, and contrasting inner shirt.
- **Waistcoat/formal column:** light inner shirt, dark vest/jacket, small tie/ascot, and straight trousers.
- **Wrapped robe:** diagonal or centered wrap cue with broad sash/obi and a long, relatively quiet lower field.
- **Pleated formal lower half:** hakama-like wide vertical rhythm with strong waistband and restrained fold marks.

### Structural motifs

- Broad back collar or shoulder yoke that is visibly different from the torso base.
- Center bow, tie, ascot, keyhole, brooch, or knot as a single focal mark.
- Parallel trim at collar, cuff, or hem; usually one or two bands, never many subpixel lines.
- High, clean waist seam and coordinated belt/obi.
- Symmetric front with intentional center alignment; back emphasizes collar/yoke and closure rather than front ornament.
- Coordinated set IDs/roles: top and bottom share a palette key or family while remaining separate garment components.

### Sleeve families

- Short fitted sleeve with contrast cuff.
- Long straight uniform sleeve with cuff band.
- Tailored jacket sleeve.
- Sleeveless waistcoat/crop top.
- Robe sleeve: wider and more rectangular, requiring Fashion Sense sleeves or a later validated template.

### Collar families

- Broad sailor/V collar, often with a light or contrasting trim edge.
- Pointed button-up collar with tie/ascot.
- Blazer lapel/open jacket.
- High formal collar/turtleneck.
- Wrapped kimono/yukata neckline with a clear diagonal overlap.

These must be represented as distinct component tags; “collar” is too broad for compatibility rules.

### Lower garments and hems

- Short flared/pleated skirt with a strong waistband and sparse pleat pixels.
- Straight formal trousers.
- Long dress/skirt color field with a light wave or banded hem.
- Wrapped robe lower half with minimal pattern and an optional center/side opening.
- Hakama-like wide lower silhouette with vertical fold rhythm.

Only compact skirts and straight trousers are early candidates. Robes, wide pleats, and long hems are later multi-frame targets.

### Palette tendencies

- Strong dark-light pairings: navy/white, black/white, deep blue/cream, green/white, burgundy/white.
- Saturated accent hues: red, magenta, teal, sky blue, yellow/gold, orange, violet.
- Pastel variants: aqua, lemon, peach, pink, lavender, mint, beige.
- Formal variants use black/charcoal/white with one jewel or floral accent.
- Wrapped garments often use one main fabric color plus sash and sparse floral/trim accents.
- The profile favors **role consistency** more than fixed colors: `base`, `collar_or_inner`, `trim`, `focal_accent`, and optionally `metal_or_brooch`.

Recommended early mask policy:

- Layer 1: `Base fabric`.
- Layer 2: `Collar/trim` or `Accent`, but not both unless the sprite has enough distinct pixels.
- Protected authored colors: outline/shadow and tiny emblem highlight.

### Contrast and visual complexity

- Medium-to-high localized contrast is central. The collar, inner shirt, tie/bow, waist, or trim should separate cleanly from the base.
- Visual complexity is moderate: several apparent garment parts, but each is simplified into a coherent block.
- Formal and robe looks raise detail density through trim/pattern, not noisy outlines.
- A garment should spend its logical-pixel budget on hierarchy: silhouette first, collar/waist second, accent third, texture last.

### Accessories

- Bows, brooches, ties/ascots, domino masks, shades, moon-like hair ornaments, and top hats recur in the pack.
- Use generic semantic forms—`center_bow`, `round_brooch`, `eye_mask`, `hair_pin`, `formal_hat`—not franchise-specific symbols, names, or arrangements.
- A coordinated accessory may share the garment's accent role, but should not be generated automatically when it creates a layer or hair collision.

### Pattern density

- Uniform/tailored tops: none to sparse; trim and seams carry the identity.
- Wrapped garments: sparse-to-moderate floral or geometric marks with large quiet regions.
- Formal hats/masks: small high-contrast ornament cluster.
- Any repeated motif must have a four-direction plan. A front-only emblem may legitimately disappear or become a closure mark on the back.

### Asymmetry

- Core uniform and formal constructions are strongly symmetric.
- Allowed asymmetry: diagonal wrap, single brooch/hair ornament, jacket overlap, scarf/ascot tail, floral cluster, or mask decoration.
- Do not randomize symmetry per pixel. Resolve an explicit construction choice before rasterization.

### Stardew-readable simplification

- Broad collar: one contrast wedge/band plus a back-yoke cue.
- Bow/tie: one center pixel cluster with separate shadow/accent roles.
- Pleats: two or three vertical value changes, not literal narrow folds.
- Trim: a single logical-pixel line only where it remains continuous; otherwise use corner/center markers.
- Wrapped neckline: one dominant diagonal edge and one sash band.
- Formal jacket: dark outer columns, light center, one tie/accent cluster.
- Coordinated set: share palette roles and waist alignment, not copied surface pixels.

### Safe early recipe vocabulary

```yaml
style_profile: sailor
construction_family: uniform | tailored | wrapped
silhouette: fitted_top | straight_jacket | waistcoat | cropped_top
collar: broad_v | pointed | lapel | high | wrapped
center_detail: none | bow | tie | ascot | brooch | buttons
trim: none | collar_band | collar_and_cuff | edge_band
sleeve: sleeveless | short_cuff | long_cuff | tailored_long
waist: plain | seam | belt | sash
palette_roles: [base, collar_or_inner, trim_or_accent]
contrast: medium | high_localized
pattern_density: none | sparse
symmetry: symmetric | explicit_wrap | explicit_accessory
```

Excluded from early generation: named character uniforms, franchise emblems, exact color-placement combinations tied to a recognizable character, kimono/yukata/hakama geometry, tuxedo sets, masks, and top hats. Those remain useful evidence about construction but require later templates and a similarity review.

## Cross-reference synthesis

### Shared vocabulary

- Clear silhouette families beat surface detail.
- Collar/neckline, waist, and hem are the most transferable garment landmarks.
- Two major layers plus one focal accent is a practical logical-pixel ceiling for compact sprites.
- Front/back coherence matters: straps, collars, hoods, openings, and bags need a back-view explanation.
- Color roles are more reusable than exact palettes.
- Most successful small garments are symmetric with one declared exception.

### Distinguishing the sets

| Dimension | Lifestyle category | Sailor style profile |
|---|---|---|
| Primary intent | ordinary/seasonal/work context | coordinated uniform/tailored language |
| Silhouette | relaxed variety | fitted or structurally disciplined |
| Landmark | archetype cue (hood, bib, coat, scarf) | collar + waist + center accent |
| Contrast | low to medium, localized | medium to high, sharply localized |
| Pattern | mostly solid, occasional sparse texture | trim bands or sparse formal/floral motif |
| Symmetry | mostly symmetric, practical exceptions | strongly symmetric except wraps/ornaments |
| Safe first output | compact cardigan/jacket/top | compact broad-collar or pointed-collar top |

### Compatibility tags implied by the references

```text
body_zone: torso | arms | legs | head | back
extent: compact | body_bound | oversized
fit: fitted | straight | relaxed | flared | wide
layer_role: base | inner | outer | trim | accessory
anchor_contract: native_torso | fs_body | fs_head
motion_class: static_offset | native_atlas | fs_static | fs_animated
requires: collar_space, waist_alignment, sleeve_pair, lower_pair
excludes: conflicting_collar, conflicting_outer, hair_collision, hem_collision
direction_rule: independent_four | mirror_safe | asymmetric_four
color_channels: zero | one | two
```

These are style/component tags, not rarity or reward weights.

## Reference-to-recipe rules

1. Record aggregate recurring traits, not per-file tracing instructions.
2. Never use reference pixels, crops, embeddings-to-image, or resized concept art in an exported PNG.
3. Resolve a recipe from vocabulary and compatibility constraints before any pixel cell is written.
4. Build geometry only from project-owned logical component templates.
5. Reject a recipe when its distinctive trait cannot be expressed at the target's logical resolution without copying a recognizable emblem or arrangement.
6. Keep provenance at the profile level (`lifestyle`, `sailor`) and record generated trait choices; do not name output after a reference outfit.
7. Run a visual-similarity review for themed profiles even when construction is procedural.

## First proof-of-concept profile

Use a deliberately generic hybrid that tests the pipeline without reproducing an outfit:

```yaml
category: lifestyle
style_profile: sailor
target: fashion_sense_shirt
construction_family: tailored
silhouette: straight_jacket
length: waist
collar: pointed
sleeve: long_cuff
layering: inner_top
center_detail: buttons
trim: collar_band
palette_roles: [base_fabric, inner_and_trim]
contrast: high_localized
pattern_density: none
symmetry: symmetric
animation: static_native_offsets
```

This combines broad reusable ideas—an everyday compact jacket and disciplined collar/trim hierarchy—without using a named uniform, emblem, exact reference palette, long hem, independent sleeve animation, or recognizable outfit layout.

## Rarity policy

Rarity is intentionally undefined here. A future reward layer may consider generation cost, number of validated components, animation coverage, palette variants, or acquisition rules, but it must never infer rarity from `lifestyle`, `SailorStyles`, palette brightness, cultural garment type, or perceived fanciness.
