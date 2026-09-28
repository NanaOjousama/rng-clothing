# Stardew-only v7 capability audit

This experiment is isolated from the production generator. It scans all vanilla hats/shirts to discover candidate decoration grammars and then narrows those into a conservative reviewed donor seed vocabulary.

## Important boundary
- Machine capability buckets are discovery aids only; they contain false positives.
- `vanilla_donor_vocabulary_reviewed.json` is the conservative reviewed seed set.
- Reviewed seeds are grammar evidence, not approved literal pixel-transfer parts.
- Vanilla hats are not given a universal motif axis; their variety is treated primarily as construction/component variation for a later donor-compatibility pass.
- Vanilla shirts support compact graphics, stripes/bands, checker/plaid, and placket/button grammar at 8x8 when target capacity allows.

## Next
V8 should generate a small mixed vanilla-only batch using only target-supported capabilities and the reviewed vanilla grammar seeds, with no rarity logic yet.
