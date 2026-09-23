# Duplicate / Unwanted Clothing Targeting

Status: future gameplay design. Document now; implement after the content/generator pool is mature.

## Core loop

Unwanted clothing and duplicate rolls can be fed back into the clothing generator to steer future rolls.

Two inputs have separate jobs:
- Category Tokens control the broad clothing category.
- The actual sacrificed clothing item controls family/type bias inside that category.

Example:
3 Hat Tokens + 1 unwanted Beret -> guaranteed Hat roll + strong Beret-family bias.

The clothing item stays meaningful as a catalyst instead of being reduced to generic currency first.

## Category-token ladder

Initial proposed behavior:
- 0 matching tokens -> normal category RNG; catalyst gives only a weak family signal.
- 1 matching token -> strong category bias.
- 2 matching tokens -> very high category chance.
- 3 matching tokens -> guaranteed category.

Three Hat Tokens guarantee Hat. They do not by themselves guarantee Beret.

## Clothing-catalyst behavior

The sacrificed item's semantic identity can contribute:
1. Category: Hat, Shirt, Pants, Accessory, etc.
2. Family/type: Beret, Beanie, Headband, etc.
3. Optional future trait signal: motif/material/pattern/style tags.

Family/type is the main catalyst effect. A future expensive recipe can offer stronger family targeting without making the normal recycle loop fully deterministic.

## Rarity interaction

The sacrificed item's rarity should not directly copy onto the new result.
- A Common catalyst does not force Common.
- An Epic catalyst does not automatically print another Epic.

Higher-rarity sacrifices may instead contribute stronger targeting weight or more salvage value. Example tuning only: Common 1.00x, Uncommon 1.25x, Rare 1.50x, Epic 2.00x family influence. Exact values stay undecided until the economy and drop rates exist.

## Design goals

The system should make duplicates useful, preserve RNG excitement, provide progressively stronger control, avoid infinite rarity recycling, and reuse the generator's existing category/family/template metadata instead of inventing a second taxonomy.

Current bookmark:
**3 matching Category Tokens + 1 Clothing Catalyst = guaranteed category + strong catalyst-family bias.**

Do not implement this gameplay system until the content pool and rarity/family behavior are stable enough to tune around real output diversity.
