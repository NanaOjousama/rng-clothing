# Coastal Knit Polo Directional Micro-Fix

Status: **PASS**  
Scope: `POLO_SHIRT / POLO_CLASSIC / medium folded collar` only.

## What changed

- **Front:** 0 logical cells changed. The successful folded collar and short front-only placket are byte-identical to the prior atlas.
- **Back:** 12 logical cells changed. The explicit collar moved from `(x=5..10, y=1)` to `(x=5..10, y=0)`. Row 1 at `x=5..10` is now a restrained primary-knit light/base/shadow transition instead of a second low collar band.
- **Right:** 10 resulting logical cells changed: `(6,1)`, `(7,1)`, `(9,1)`, `(6,2)`, `(8,2)`, `(7,3)`, `(9,3)`, `(8,4)`, `(9,4)`, `(9,5)`.
- **Left:** 10 resulting logical cells changed: `(6,1)`, `(8,1)`, `(9,1)`, `(7,2)`, `(9,2)`, `(6,3)`, `(8,3)`, `(6,4)`, `(7,4)`, `(6,5)`.

The side compiler now normalizes the local upper-middle knit field in logical rows 1–5 and places one compact five-cell folded-collar wedge over it. This removes the inherited irregular dark cluster without adding decoration or changing alpha.

## Preserved contracts

- Family, canonical recipe, fit, material, and palette are unchanged.
- Front placket remains short and front-only.
- Back and sides contain no placket signal.
- Native Farmer sleeves remain enabled; there is no custom Sleeves appearance.
- Atlas remains 16×64, Scale 2, BodyPosition `(0,32)`, binary alpha.
- Every direction remains exactly one connected alpha component.
- No detached pixels or unsupported top-edge cells were introduced.

Full Phase 2 regression validation remains **PASS with zero errors**.
