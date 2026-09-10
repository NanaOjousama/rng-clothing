# Hood-Up Side Hair Policy Refinement

> Superseded by the side-Hat visual masking experiment in `reports/HOOD_UP_SIDE_VISUAL_MASK.md`. `HideBackOnly` is again the default because side Hair is preserved and covered by hood fabric instead of hidden.

## Runtime finding

`HideBackOnly` solves rear-hair conflict but preserves right/left hair. Live gameplay now shows that preserved side hair can clip through the raised side hood. This is a policy mismatch, not a hood geometry, anchor, draw-order, or weather-state failure.

## Default evaluation

- `HideBackOnly` preserves more hairstyle identity, but leaves the observed side clipping unresolved.
- `PreserveFrontOnly` preserves the most important visible hairstyle cue—front bangs/fringe—while hiding hair anywhere the raised hood encloses the head mass.

Therefore `PreserveFrontOnly` is the better default for this hood silhouette.

| Mode | Front | Right | Back | Left | Purpose |
|---|---|---|---|---|---|
| `PreserveHair` | preserve | preserve | preserve | preserve | permissive option |
| `HideBackOnly` | preserve | preserve | hide | preserve | for hairstyles that do not clip at the sides |
| `PreserveFrontOnly` | preserve | hide | hide | hide | default; preserves bangs while preventing side/back clipping |
| `HideHair` | hide | hide | hide | hide | safest fallback for large front hair |

Hood-down always preserves Hair in all directions.

## Scope

Only the Content Patcher appearance-data policy changed. Fashion Sense Hat art, Shirt art, anchors, frame mapping, scale, draw order, weather conditions, native sleeves, and drawstrings remain unchanged. The FS child remains `1.4.0`; the CP child is `1.2.0`.

## Focused retest

- Hood up front: bangs/front hair remain visible through the opening.
- Hood up right and left: Hair is hidden and no clipping remains.
- Hood up back: Hair is hidden.
- Hood down front/right/back/left: Hair is restored.
- Turning between directions restores/hides Hair immediately and leaves no stale layer.
