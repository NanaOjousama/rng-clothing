# Stardew-only v8 mixed capability batch

This experiment remains isolated from the production generator. It combines the previously proven vanilla-only layers with the conservative reviewed grammar from v7.

Batch:
- hats: 52, 66, 79, 98
- shirts: 225, 228, 239, 572, 584, 535

Shirt grammar coverage is deliberately mixed:
- 225: horizontal stripe / band
- 228: placket / buttons
- 239: compact graphic
- 572: checker / plaid
- 584: region/material-only control, no shirt graphic grammar
- 535: low-capacity fallback, no shirt graphic grammar

Hats do not use a universal motif system. They stay on source-safe colorway / region / wrap-trim axes only.

Important boundary: reviewed vanilla donor examples are used as grammar evidence (scale/placement/type), not literal pixel-transfer parts. No rarity logic and no production promotion are included here.
