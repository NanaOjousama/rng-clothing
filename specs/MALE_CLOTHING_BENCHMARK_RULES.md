# Male Clothing Benchmark Rules

## Purpose

`references/benchmark/male clothing/` is the dedicated masculine-fashion quality corpus for future RNG Clothing studies. It is a style and craftsmanship benchmark, never a pixel source or a set of copy targets.

This document is a corpus-routing policy. It does **not** claim that every image in the directory has already passed visual classification.

## Folder classification

Normalize a top-level folder name before routing it:

1. remove an optional leading `[FS]` marker;
2. trim whitespace;
3. test whether the resulting name begins with `Mixed_`.

This normalization is required because the current corpus contains both `[FS] Mixed_...` and `[FS]Mixed_...` names.

### Primary masculine corpus

The current non-Mixed folders are primary evidence:

- `[FS] Adventurer's Armour and Outfits 1.0.0`
- `[FS] Bonestealer Pack`
- `[FS] Coats and Jackets Pack`
- `[FS] Colourable Basics (Tops)`
- `[FS] Frogwares Sherlock Pack`
- `[FS] Gentleman's Collection`
- `[FS] Project Hail Mary ...`
- `[FS] TGAAClothing`
- `Male_Pants`

These folders currently contain 358 raw PNG files. That number is an inventory count, not a count of accepted garment examples: screenshots, instructions, hairs, hats, accessories, and other non-garment assets must still be excluded or routed by their actual purpose.

### Selective secondary mixed corpus

The current Mixed folders are secondary evidence:

- `[FS] Mixed_Ani's colour collection`
- `[FS] Mixed_Shire Collection`
- `[FS]Mixed_Ani's Farmer Set 1`

These contain 241 raw PNG files. No Mixed asset may influence masculine article/silhouette grammar merely because it is stored in this corpus.

## Per-asset use classification

Every candidate from a Mixed folder must be classified from its visible construction, not inferred from pack name, palette, author, or file path.

Use one of these roles:

| Role | May teach masculine article grammar? | May teach general pixel/design craft? |
|---|---:|---:|
| Masculine-suitable garment | Yes | Yes |
| Genuinely unisex / neutral garment | Yes, with its actual construction labels | Yes |
| Strongly feminine garment | No | Yes |
| Ambiguous without visual inspection | No, until reviewed | No, until reviewed |
| Non-garment/reference UI image | No | No |

Strongly feminine Mixed examples may still inform:

- connected pixel clusters;
- motif and pattern composition;
- color-block boundaries;
- value hierarchy and shading;
- trim, piping, and surface-design technique;
- directional continuity.

They may not set masculine silhouette, neckline, shoulder, fit, article, or proportion defaults unless the individual garment is independently suitable.

## Masculine grammar is multidimensional

Never define masculine clothing as merely dark, broad-shouldered, plain, or jacket-like. Preserve at least these distinct branches when the evidence supports them:

- casual;
- workwear and farmwear;
- streetwear;
- hoodie and sweatwear;
- cardigan and knitwear;
- formalwear;
- vest and waistcoat;
- jacket and outerwear;
- military and fieldwear;
- period and gentleman tailoring;
- fantasy and adventurer clothing;
- armor;
- tunic and tabard;
- uniform.

Each branch should be studied through independent design axes:

- article and garment role;
- fit and ease;
- shoulder-to-sleeve relationship;
- neckline and collar;
- opening and closure;
- torso/waist/hem proportion;
- layering;
- panels, seams, pockets, and utility rhythm;
- motif and pattern placement;
- silhouette in front, side, and back views;
- palette/value composition;
- material implication;
- gameplay-size readability and desirability.

## Required extraction method

For a masculine-fashion study or style profile:

1. inspect the installed Stardew 1.6.15 clothing data, assets, and renderer contract first;
2. inspect the primary non-Mixed corpus as the main community benchmark;
3. classify Mixed garments individually before using them;
4. extract aggregate tendencies across multiple garments rather than copying one item;
5. separate article grammar from general pixel technique;
6. convert findings into semantic construction and surface vocabulary with no raw coordinates;
7. render through the established 16×16 Scale-2 Fashion Sense grammar;
8. compare at exact gameplay footprint, not only in enlarged previews;
9. reject outputs that reduce masculine variety to dark generic jackets;
10. preserve source-pack independence: generation code must never read benchmark PNGs.

## What to study at Stardew scale

For every accepted garment, explain why it reads successfully using visible evidence:

- which shape or major region establishes the article first;
- which construction gesture is dominant;
- how shoulders, sleeves, collar, torso, and hem relate;
- which details survive gameplay size;
- how the side and back preserve identity;
- where contrast is concentrated;
- how surface design supports rather than substitutes for construction;
- why the item feels styled or collectible.

Do not assign masculinity based only on color, body width, or a subjective label. Record the actual construction language.

## Translation boundary

The corpus may influence semantic traits such as:

- structured or relaxed fit;
- workwear panels;
- hoodie volume;
- cardigan opening;
- waistcoat layering;
- lapel/collar rhythm;
- utility or armor segmentation;
- tunic/tabard proportion;
- restrained or decorative pattern density.

It may not contribute copied pixels, traced silhouettes, sampled palettes, logos, emblems, named character outfits, or source-specific layouts. The output must remain original and deterministic.

## Quality gate

Before accepting a masculine garment, remove its name and theme label and ask:

1. Is the article immediately readable?
2. Is its masculine or genuinely unisex construction legible without relying on dark color?
3. Does it occupy a different design branch from its batch siblings?
4. Does construction remain interesting without shading?
5. Did the 16×16 logical budget improve proportion, layering, pattern, or detail clarity?
6. Are front, right, back, and left deliberate reconstructions?
7. Is it at least as clear and charming as the relevant vanilla baseline?
8. Would a player plausibly want to collect or wear it?

Failure on article identity, construction, or batch variety cannot be repaired by adding decoration.
